"""
FastAPI Application for Voice Assistant
Main API endpoints + Dashboard for the hyper-localized multilingual voice assistant.
"""

import logging
import time
from typing import Optional
from pathlib import Path
import tempfile

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"

# Initialize FastAPI app
app = FastAPI(
    title="Hyper-Localized Voice Assistant API",
    description="Multilingual voice assistant with edge computing and agentic workflows",
    version="0.2.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# XiaoZhi protocol bridge for EdgeX/ESP32 devices
from src.api.xiaozhi_bridge import router as xiaozhi_router
app.include_router(xiaozhi_router)


# ── Response models ──

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    language_name: str
    confidence: Optional[float] = None


class ProcessResponse(BaseModel):
    transcription: str
    intent: str
    response_text: str
    language: str


class HealthResponse(BaseModel):
    status: str
    version: str
    components: Optional[dict] = None


# ── Global instances ──

asr_engine = None
tts_engine = None
llm_engine = None
translator = None
orchestrator = None
app_config = None
db = None


# ── Startup / Shutdown ──

@app.on_event("startup")
async def startup_event():
    """Initialize models and database on startup."""
    global asr_engine, tts_engine, llm_engine, translator, orchestrator, app_config, db

    logger.info("Initializing voice assistant components...")

    # Database
    from src.db import get_db
    db = get_db()
    logger.info("Database initialized")

    try:
        from src.config import load_config

        app_config = load_config()

        # ASR
        try:
            if app_config.asr.engine == "mms":
                from src.asr import create_asr
                asr_engine = create_asr(device=app_config.asr.device)
            elif app_config.asr.engine == "pingala":
                from src.asr import PingalaASR
                asr_engine = PingalaASR(device=app_config.asr.device)
            elif app_config.asr.engine == "indic_whisper":
                from src.asr import IndicWhisperASR
                asr_engine = IndicWhisperASR(device=app_config.asr.device)
            elif app_config.asr.engine == "whisper":
                from src.asr import WhisperASR
                asr_engine = WhisperASR(
                    model_size=app_config.asr.whisper_model_size,
                    device=app_config.asr.device,
                )
            else:
                from src.asr import WhisperASR
                asr_engine = WhisperASR(model_size="base")
            logger.info(f"ASR initialized: {type(asr_engine).__name__}")
        except Exception as e:
            logger.warning(f"ASR initialization failed (non-critical): {e}")

        # TTS
        try:
            from src.tts import TTSEngine
            tts_engine = TTSEngine(
                backend=app_config.tts.engine,
                device=app_config.tts.device,
                variant=app_config.tts.indic_variant,
            )
            logger.info(f"TTS initialized: {app_config.tts.engine}")
        except Exception as e:
            logger.warning(f"TTS initialization failed (non-critical): {e}")

        # LLM
        try:
            from src.llm import get_llm
            llm_engine = get_llm(
                model_size=app_config.llm.model_size,
                device=app_config.llm.device,
                engine=app_config.llm.engine,
                backend=app_config.llm.backend,
            )
            llm_engine.load_model()
            logger.info(f"LLM initialized: {app_config.llm.engine} {app_config.llm.model_size}")
        except Exception as e:
            logger.warning(f"LLM initialization failed (will use fallback responses): {e}")
            llm_engine = None

        # Translation
        try:
            from src.translation import IndicTranslator
            translator = IndicTranslator(
                device=app_config.translation.device,
                model_variant=app_config.translation.model_variant,
            )
            # Pre-load both directions
            translator.load_models(["indic-en", "en-indic"])
            logger.info(f"Translation initialized: IndicTrans2 ({app_config.translation.model_variant})")
        except Exception as e:
            logger.warning(f"Translation initialization failed (non-critical): {e}")
            translator = None

        # Agent orchestrator — pass LLM so agents can generate real responses
        from src.agents import AgentFactory
        orchestrator = AgentFactory.create(
            backend=app_config.agents.orchestrator,
            config={
                "gateway_url": app_config.agents.clawgo_gateway_url,
                "llm_provider": app_config.agents.clawgo_llm_provider,
                "llm_model": app_config.agents.clawgo_llm_model,
                "workspace_dir": app_config.agents.clawgo_workspace_dir,
            },
            llm=llm_engine,
        )

        logger.info(
            f"Components initialized: ASR={app_config.asr.engine}, "
            f"LLM={'loaded' if llm_engine else 'fallback'}, "
            f"TTS={app_config.tts.engine}, "
            f"Agents={app_config.agents.orchestrator}"
        )

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        # Ensure orchestrator exists even if config fails
        if orchestrator is None:
            from src.agents import AgentFactory
            orchestrator = AgentFactory.create(backend="langgraph", llm=None)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    if db:
        db.close()


# ── Static files (Vite build output) ──

if (STATIC_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")


# ── Dashboard API ──

@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    return {
        "total_conversations": db.count_conversations(),
        "avg_latency": db.get_avg_latency(hours=24),
        "languages": db.get_language_stats(),
        "intents": db.get_intent_stats(),
    }


@app.get("/api/dashboard/conversations")
async def dashboard_conversations(limit: int = 30, offset: int = 0):
    """Get recent conversations for the dashboard."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    convs = db.list_conversations(limit=limit, offset=offset)
    return {
        "conversations": [
            {
                "id": c.id,
                "session_id": c.session_id,
                "language": c.language,
                "started_at": c.started_at,
                "ended_at": c.ended_at,
                "status": c.status,
                "intent": c.intent,
                "asr_time_ms": c.asr_time_ms,
                "translation_time_ms": c.translation_time_ms,
                "llm_time_ms": c.llm_time_ms,
                "tts_time_ms": c.tts_time_ms,
                "total_time_ms": c.total_time_ms,
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "language": m.language,
                        "timestamp": m.timestamp,
                    }
                    for m in c.messages
                ],
            }
            for c in convs
        ],
        "total": db.count_conversations(),
    }


@app.get("/api/dashboard/conversations/{conv_id}")
async def dashboard_conversation_detail(conv_id: str):
    """Get a single conversation with full details."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conv.id,
        "session_id": conv.session_id,
        "language": conv.language,
        "started_at": conv.started_at,
        "ended_at": conv.ended_at,
        "status": conv.status,
        "intent": conv.intent,
        "asr_time_ms": conv.asr_time_ms,
        "translation_time_ms": conv.translation_time_ms,
        "llm_time_ms": conv.llm_time_ms,
        "tts_time_ms": conv.tts_time_ms,
        "total_time_ms": conv.total_time_ms,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "language": m.language,
                "timestamp": m.timestamp,
            }
            for m in conv.messages
        ],
    }


@app.get("/api/dashboard/devices")
async def dashboard_devices():
    """Get connected XiaoZhi/EdgeX devices."""
    from src.api.xiaozhi_bridge import get_connected_devices
    return {"devices": get_connected_devices()}


# ── Tasks ──

@app.get("/api/tasks")
async def list_tasks(status: Optional[str] = None):
    """List tasks, optionally filtered by status (pending/done)."""
    tasks = db.list_tasks(status=status)
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "created_at": t.created_at,
                "completed_at": t.completed_at,
            }
            for t in tasks
        ]
    }


@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: str, status: str = Form(...)):
    """Update a task's status (pending/done)."""
    if status not in ("pending", "done"):
        raise HTTPException(status_code=400, detail="Status must be 'pending' or 'done'")
    if not db.update_task_status(task_id, status):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True, "id": task_id, "status": status}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task by ID."""
    cur = db.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True, "id": task_id}


# ── Helper: log conversation to DB ──

def _log_conversation(
    user_text: str,
    response_text: str,
    language: str,
    intent: str = "",
    asr_ms: float = 0,
    translation_ms: float = 0,
    llm_ms: float = 0,
    tts_ms: float = 0,
    total_ms: float = 0,
):
    """Log a conversation exchange to the database."""
    if not db:
        return
    from src.db.models import Conversation, Message
    from datetime import datetime

    conv = Conversation(
        language=language,
        intent=intent,
        status="completed",
        asr_time_ms=asr_ms,
        translation_time_ms=translation_ms,
        llm_time_ms=llm_ms,
        tts_time_ms=tts_ms,
        total_time_ms=total_ms,
        ended_at=datetime.utcnow().isoformat(),
    )
    conv.messages = [
        Message(role="user", content=user_text, language=language),
        Message(role="assistant", content=response_text, language="en"),
    ]
    db.save_conversation(conv)


# ── Core API Endpoints ──

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    components = {
        "asr": type(asr_engine).__name__ if asr_engine else "not loaded",
        "translation": "IndicTrans2" if translator else "not loaded",
        "tts": type(tts_engine).__name__ if tts_engine else "not loaded",
        "llm": type(llm_engine).__name__ if llm_engine else "fallback",
        "orchestrator": type(orchestrator).__name__ if orchestrator else "not loaded",
        "database": "connected" if db else "not loaded",
    }
    return HealthResponse(
        status="healthy",
        version="0.2.0",
        components=components,
    )


@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """Transcribe audio to text."""
    if asr_engine is None:
        raise HTTPException(status_code=503, detail="ASR engine not initialized")

    try:
        # Determine file extension from upload content type
        content_type = audio.content_type or ""
        if "webm" in content_type:
            suffix = ".webm"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "mp4" in content_type or "m4a" in content_type:
            suffix = ".m4a"
        else:
            suffix = ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Noise reduction before ASR
        from src.asr.denoise import denoise_audio
        clean_path = denoise_audio(tmp_path)

        result = asr_engine.transcribe(clean_path, language=language)
        Path(tmp_path).unlink(missing_ok=True)
        if clean_path != tmp_path:
            Path(clean_path).unlink(missing_ok=True)

        return TranscriptionResponse(
            text=result["text"],
            language=result["language"],
            language_name=result["language_name"],
        )

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process", response_model=ProcessResponse)
async def process_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """Full processing pipeline: ASR -> NLU -> Agent -> Response."""
    if asr_engine is None or orchestrator is None:
        raise HTTPException(status_code=503, detail="Components not initialized")

    try:
        content_type = audio.content_type or ""
        if "webm" in content_type:
            suffix = ".webm"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "mp4" in content_type or "m4a" in content_type:
            suffix = ".m4a"
        else:
            suffix = ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Noise reduction before ASR
        from src.asr.denoise import denoise_audio
        clean_path = denoise_audio(tmp_path)

        asr_result = asr_engine.transcribe(clean_path, language=language)
        transcription = asr_result["text"]
        detected_lang = asr_result["language"]

        agent_result = orchestrator.process(transcription, detected_lang)

        Path(tmp_path).unlink(missing_ok=True)
        if clean_path != tmp_path:
            Path(clean_path).unlink(missing_ok=True)

        response_text = agent_result.get("response", "")
        intent = agent_result.get("intent", "unknown")

        _log_conversation(
            user_text=transcription,
            response_text=response_text,
            language=detected_lang,
            intent=intent,
            llm_ms=agent_result.get("llm_time_ms", 0),
            total_ms=agent_result.get("llm_time_ms", 0),
        )

        return ProcessResponse(
            transcription=transcription,
            intent=intent,
            response_text=response_text,
            language=detected_lang,
        )

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts")
async def synthesize_speech(
    text: str = Form(...),
    language: str = Form("hi"),
    emotion: str = Form("neutral"),
):
    """Synthesize speech from text."""
    if tts_engine is None:
        raise HTTPException(status_code=503, detail="TTS engine not initialized")

    try:
        from fastapi.responses import FileResponse as FR

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tts_engine.synthesize(
                text=text,
                language=language,
                output_path=tmp.name,
            )
            return FR(tmp.name, media_type="audio/wav", filename="response.wav")

    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming."""
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        while True:
            data = await websocket.receive_bytes()
            response = {"status": "received", "bytes": len(data)}
            await websocket.send_json(response)
    except Exception as e:
        logger.info(f"WebSocket disconnected: {e}")


@app.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """Streaming WebSocket: full STT -> Translation -> LLM -> Translation -> TTS."""
    await websocket.accept()
    logger.info("Streaming WebSocket client connected")

    try:
        while True:
            data = await websocket.receive_bytes()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                # Noise reduction before ASR
                from src.asr.denoise import denoise_audio
                clean_path = denoise_audio(tmp_path)

                if asr_engine:
                    asr_result = asr_engine.transcribe(clean_path)
                    if clean_path != tmp_path:
                        Path(clean_path).unlink(missing_ok=True)
                    transcription = asr_result["text"]

                    if orchestrator and transcription.strip():
                        agent_result = orchestrator.process(
                            transcription, asr_result.get("language", "en")
                        )
                        response_text = agent_result.get("response", "")

                        _log_conversation(
                            user_text=transcription,
                            response_text=response_text,
                            language=asr_result.get("language", "en"),
                            intent=agent_result.get("intent", ""),
                            llm_ms=agent_result.get("llm_time_ms", 0),
                        )

                        await websocket.send_json({
                            "type": "response",
                            "transcription": transcription,
                            "language": asr_result.get("language"),
                            "response": response_text,
                            "intent": agent_result.get("intent"),
                        })
                    else:
                        await websocket.send_json({
                            "type": "transcription",
                            "text": transcription,
                            "language": asr_result.get("language"),
                        })
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        logger.info(f"Streaming WebSocket disconnected: {e}")


@app.post("/api/text")
async def process_text(
    text: str = Form(...),
    language: str = Form("en"),
):
    """
    Process text input through the full pipeline (skip ASR).

    Pipeline: Input → Translate(src→EN) → LLM → Translate(EN→src) → Response
    If input is already English, translation steps are skipped.
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        total_start = time.perf_counter()
        translation_ms = 0.0
        english_input = text
        original_input = text

        # Step 1: Translate input to English (if not English)
        if language != "en" and translator:
            try:
                t_start = time.perf_counter()
                english_input = translator.translate(text, source_lang=language, target_lang="en")
                translation_ms += (time.perf_counter() - t_start) * 1000
                logger.info(f"Translated input ({language}→en): {english_input[:80]}")
            except Exception as e:
                logger.warning(f"Input translation failed, using raw text: {e}")
                english_input = text

        # Step 2: Process through agent orchestrator (LLM)
        llm_start = time.perf_counter()
        result = orchestrator.process(english_input, "en")
        llm_ms = (time.perf_counter() - llm_start) * 1000

        english_response = result.get("response", "")
        intent = result.get("intent", "")

        # Step 3: Translate response back to original language (if not English)
        final_response = english_response
        if language != "en" and translator and english_response:
            try:
                t_start = time.perf_counter()
                final_response = translator.translate(english_response, source_lang="en", target_lang=language)
                translation_ms += (time.perf_counter() - t_start) * 1000
                logger.info(f"Translated response (en→{language}): {final_response[:80]}")
            except Exception as e:
                logger.warning(f"Response translation failed, returning English: {e}")
                final_response = english_response

        total_ms = (time.perf_counter() - total_start) * 1000

        _log_conversation(
            user_text=original_input,
            response_text=final_response,
            language=language,
            intent=intent,
            translation_ms=translation_ms,
            llm_ms=llm_ms,
            total_ms=total_ms,
        )

        response_data = {
            "input": original_input,
            "intent": intent,
            "response": final_response,
            "language": language,
            "agent": result.get("agent", "unknown"),
            "translation_ms": round(translation_ms, 1),
            "llm_ms": round(llm_ms, 1),
            "total_ms": round(total_ms, 1),
        }
        # Include translated texts for display when input is non-English
        if language != "en" and english_input != original_input:
            response_data["translated_input"] = english_input
        if language != "en" and english_response and english_response != final_response:
            response_data["english_response"] = english_response
        sources = result.get("sources", [])
        if sources:
            response_data["sources"] = sources
        thinking = result.get("thinking", "")
        if thinking:
            response_data["thinking"] = thinking
        return response_data

    except Exception as e:
        logger.error(f"Text processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── SPA catch-all (must be last) ──

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """Serve React SPA — static files first, then index.html for client routing."""
    file_path = STATIC_DIR / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(STATIC_DIR / "index.html")


# Run with: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
