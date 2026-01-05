"""
FastAPI Application for Voice Assistant
Main API endpoints for the hyper-localized multilingual voice assistant.
"""

import logging
from typing import Optional
from pathlib import Path
import tempfile

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hyper-Localized Voice Assistant API",
    description="Multilingual voice assistant with edge computing and agentic workflows",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
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


class TTSResponse(BaseModel):
    audio_url: str
    duration: float


class HealthResponse(BaseModel):
    status: str
    version: str


# Global instances (initialized on startup)
asr_engine = None
tts_engine = None
orchestrator = None


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup."""
    global asr_engine, tts_engine, orchestrator

    logger.info("Initializing voice assistant components...")

    try:
        from src.asr import WhisperASR
        from src.tts import IndicTTS
        from src.agents import AgentOrchestrator

        # Initialize ASR (lazy loading - model loads on first use)
        asr_engine = WhisperASR(model_size="base")

        # Initialize TTS (lazy loading)
        tts_engine = IndicTTS(default_language="hi")

        # Initialize agent orchestrator
        orchestrator = AgentOrchestrator()
        orchestrator.setup()

        logger.info("Voice assistant components initialized")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        # Continue anyway - components will be None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """
    Transcribe audio to text.

    Args:
        audio: Audio file (WAV, MP3, etc.)
        language: Optional language hint (e.g., 'hi', 'ml', 'en')

    Returns:
        Transcription result with detected language
    """
    if asr_engine is None:
        raise HTTPException(status_code=503, detail="ASR engine not initialized")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Transcribe
        result = asr_engine.transcribe(tmp_path, language=language)

        # Clean up
        Path(tmp_path).unlink()

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
    """
    Full processing pipeline: ASR -> NLU -> Agent -> Response.

    Args:
        audio: Audio file
        language: Optional language hint

    Returns:
        Complete processing result with response
    """
    if asr_engine is None or orchestrator is None:
        raise HTTPException(status_code=503, detail="Components not initialized")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Step 1: Transcribe
        asr_result = asr_engine.transcribe(tmp_path, language=language)
        transcription = asr_result["text"]
        detected_lang = asr_result["language"]

        # Step 2: Process through agent orchestrator
        agent_result = orchestrator.process(transcription, detected_lang)

        # Clean up
        Path(tmp_path).unlink()

        return ProcessResponse(
            transcription=transcription,
            intent=agent_result.get("intent", "unknown"),
            response_text=agent_result.get("response", ""),
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
    """
    Synthesize speech from text.

    Args:
        text: Text to synthesize
        language: Language code
        emotion: Emotion for synthesis

    Returns:
        Audio file
    """
    if tts_engine is None:
        raise HTTPException(status_code=503, detail="TTS engine not initialized")

    try:
        from fastapi.responses import FileResponse

        # Generate audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tts_engine.synthesize(
                text=text,
                language=language,
                emotion=emotion,
                output_path=tmp.name,
            )

            return FileResponse(
                tmp.name,
                media_type="audio/wav",
                filename="response.wav",
            )

    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming.

    Handles continuous audio streaming from edge devices.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        while True:
            # Receive data from client
            data = await websocket.receive_bytes()

            # Process audio chunk
            # In production, implement proper streaming ASR
            response = {"status": "received", "bytes": len(data)}

            await websocket.send_json(response)

    except Exception as e:
        logger.info(f"WebSocket disconnected: {e}")


@app.post("/api/text")
async def process_text(
    text: str = Form(...),
    language: str = Form("en"),
):
    """
    Process text input directly (skip ASR).

    Useful for testing and text-based interaction.
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        result = orchestrator.process(text, language)
        return {
            "input": text,
            "intent": result.get("intent"),
            "response": result.get("response"),
            "language": language,
        }

    except Exception as e:
        logger.error(f"Text processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
