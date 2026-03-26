"""
XiaoZhi Protocol Bridge
Implements the XiaoZhi WebSocket protocol so ESP32-based voice devices
(like EdgeX D1-EN) can connect to our voice assistant backend.

Protocol: https://github.com/78/xiaozhi-esp32/blob/main/docs/websocket.md
"""

import logging
import uuid
import time
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Track connected devices
connected_devices = {}


@router.post("/xiaozhi/ota/")
@router.get("/xiaozhi/ota/")
async def xiaozhi_ota(request: Request):
    """
    OTA endpoint - tells the device where to connect via WebSocket.
    The device calls this on boot to discover the server.
    """
    device_id = request.headers.get("device-id", "unknown")
    client_id = request.headers.get("client-id", "unknown")
    model = request.headers.get("device-model", "unknown")

    logger.info(f"OTA request from device={device_id}, model={model}")

    # Get server IP - use the host the request came in on
    host = request.headers.get("host", "192.168.1.101:8000").split(":")[0]
    server_port = 8000

    return JSONResponse({
        "server_time": {
            "timestamp": int(time.time() * 1000),
            "timezone_offset": 330,  # IST
        },
        "firmware": {
            "version": "1.0.0",
            "url": "",
        },
        "websocket": {
            "url": f"ws://{host}:{server_port}/xiaozhi/v1/",
            "token": "",
        },
    })


@router.websocket("/xiaozhi/v1/")
async def xiaozhi_websocket(websocket: WebSocket):
    """
    XiaoZhi WebSocket endpoint for device communication.

    Flow:
    1. Device connects and sends "hello" handshake
    2. Device sends "listen" start + binary opus audio
    3. Server processes audio through our pipeline
    4. Server sends back "stt", "tts" messages + binary audio
    """
    await websocket.accept()

    device_id = websocket.headers.get("device-id", "unknown")
    client_id = websocket.headers.get("client-id", str(uuid.uuid4()))
    session_id = str(uuid.uuid4())

    logger.info(f"XiaoZhi device connected: {device_id}")
    connected_devices[device_id] = {
        "session_id": session_id,
        "connected_at": time.time(),
        "websocket": websocket,
    }

    # Get orchestrator reference
    from src.api.main import orchestrator, db

    audio_buffer = bytearray()
    is_listening = False

    try:
        while True:
            message = await websocket.receive()

            if "text" in message:
                data = json.loads(message["text"])
                msg_type = data.get("type", "")

                if msg_type == "hello":
                    # Handshake - respond with server hello
                    logger.info(f"Hello from device {device_id}")
                    await websocket.send_json({
                        "type": "hello",
                        "transport": "websocket",
                        "session_id": session_id,
                        "audio_params": {
                            "sample_rate": 24000,
                        },
                    })

                elif msg_type == "listen":
                    state = data.get("state", "")

                    if state == "start":
                        is_listening = True
                        audio_buffer = bytearray()
                        logger.info(f"Device {device_id} started listening")

                    elif state == "stop":
                        is_listening = False
                        logger.info(f"Device {device_id} stopped listening, processing...")
                        await _process_audio_or_text(
                            websocket, session_id, audio_buffer,
                            orchestrator, db, device_id
                        )
                        audio_buffer = bytearray()

                    elif state == "detect":
                        # Wake word detected
                        wake_text = data.get("text", "")
                        logger.info(f"Wake word detected: {wake_text}")
                        await websocket.send_json({
                            "type": "tts",
                            "state": "start",
                        })
                        await websocket.send_json({
                            "type": "tts",
                            "state": "sentence_start",
                            "text": "I'm listening.",
                        })
                        await websocket.send_json({
                            "type": "tts",
                            "state": "stop",
                        })

                elif msg_type == "abort":
                    logger.info(f"Device {device_id} aborted playback")
                    is_listening = False

                else:
                    logger.debug(f"Unknown message type: {msg_type}")

            elif "bytes" in message:
                # Binary audio data (Opus encoded)
                if is_listening:
                    audio_buffer.extend(message["bytes"])

    except WebSocketDisconnect:
        logger.info(f"XiaoZhi device disconnected: {device_id}")
    except Exception as e:
        logger.error(f"XiaoZhi WebSocket error: {e}")
    finally:
        connected_devices.pop(device_id, None)


async def _process_audio_or_text(
    websocket: WebSocket,
    session_id: str,
    audio_buffer: bytearray,
    orchestrator,
    db,
    device_id: str,
):
    """
    Process received audio through the voice assistant pipeline.
    Since we may not have ASR loaded, we use a text-based fallback
    for the demo and send text responses back.
    """
    # For the demo, if we can't decode opus audio, use a fallback
    transcribed_text = ""

    if len(audio_buffer) > 0:
        try:
            # Try to decode opus audio and run ASR
            transcribed_text = await _try_asr(audio_buffer)
        except Exception as e:
            logger.warning(f"ASR failed: {e}, using demo fallback")
            transcribed_text = ""

    if not transcribed_text:
        # Fallback: treat as a general query for demo purposes
        transcribed_text = "Hello, how are you?"
        logger.info(f"Using fallback text: {transcribed_text}")

    # Send STT result to device
    await websocket.send_json({
        "type": "stt",
        "text": transcribed_text,
    })

    # Process through our agent orchestrator
    response_text = "I'm here to help!"
    intent = "general_chat"

    if orchestrator:
        try:
            result = orchestrator.process(transcribed_text, "en")
            response_text = result.get("response", response_text)
            intent = result.get("intent", intent)
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")

    # Log to database
    if db:
        try:
            from src.api.main import _log_conversation
            _log_conversation(
                user_text=transcribed_text,
                response_text=response_text,
                language="en",
                intent=intent,
            )
        except Exception as e:
            logger.warning(f"Failed to log conversation: {e}")

    # Send LLM emotion
    await websocket.send_json({
        "type": "llm",
        "emotion": "happy",
        "text": response_text,
    })

    # Send TTS response as text (device can use its own TTS or we send audio)
    await websocket.send_json({
        "type": "tts",
        "state": "start",
    })
    await websocket.send_json({
        "type": "tts",
        "state": "sentence_start",
        "text": response_text,
    })
    await websocket.send_json({
        "type": "tts",
        "state": "stop",
    })

    logger.info(f"Sent response to device {device_id}: {response_text[:50]}...")


async def _try_asr(audio_buffer: bytearray) -> str:
    """Attempt to decode opus audio and run ASR."""
    # This is a placeholder - full implementation would:
    # 1. Decode opus frames to PCM using pyogg/opuslib
    # 2. Run Whisper/Pingala ASR on the PCM audio
    # For the demo, we raise to trigger the fallback
    raise NotImplementedError("Full ASR pipeline not connected yet")


def get_connected_devices():
    """Return list of connected XiaoZhi devices."""
    return {
        device_id: {
            "session_id": info["session_id"],
            "connected_at": info["connected_at"],
            "uptime_seconds": time.time() - info["connected_at"],
        }
        for device_id, info in connected_devices.items()
    }
