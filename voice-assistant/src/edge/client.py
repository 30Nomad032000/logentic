"""
Edge Client for Server Communication
Handles communication between edge device and processing server.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class EdgeClient:
    """
    Client for edge device to communicate with processing server.

    Supports WebSocket for real-time streaming and HTTP for request/response.
    """

    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        ws_url: Optional[str] = None,
    ):
        """
        Initialize edge client.

        Args:
            server_url: HTTP server URL
            ws_url: WebSocket URL (defaults to server_url with ws:// scheme)
        """
        self.server_url = server_url.rstrip("/")
        self.ws_url = ws_url or server_url.replace("http", "ws") + "/ws"
        self.ws_connection = None
        self.session = None

    async def connect_websocket(self):
        """Establish WebSocket connection for streaming."""
        try:
            import websockets

            logger.info(f"Connecting to WebSocket: {self.ws_url}")
            self.ws_connection = await websockets.connect(self.ws_url)
            logger.info("WebSocket connected")

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    async def disconnect_websocket(self):
        """Close WebSocket connection."""
        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None
            logger.info("WebSocket disconnected")

    async def send_audio_stream(self, audio_chunks):
        """
        Stream audio chunks to server via WebSocket.

        Args:
            audio_chunks: Async iterator of audio chunks
        """
        if not self.ws_connection:
            await self.connect_websocket()

        try:
            async for chunk in audio_chunks:
                await self.ws_connection.send(chunk.tobytes())

            # Signal end of stream
            await self.ws_connection.send(json.dumps({"type": "end_stream"}))

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            raise

    async def receive_response(self) -> Dict[str, Any]:
        """
        Receive response from server via WebSocket.

        Returns:
            Response dictionary
        """
        if not self.ws_connection:
            raise RuntimeError("WebSocket not connected")

        try:
            response = await self.ws_connection.recv()
            return json.loads(response)

        except Exception as e:
            logger.error(f"Failed to receive response: {e}")
            raise

    async def process_audio(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send audio for processing via HTTP.

        Args:
            audio_data: Audio bytes
            language: Optional language hint

        Returns:
            Processing result
        """
        try:
            import aiohttp

            if not self.session:
                self.session = aiohttp.ClientSession()

            url = f"{self.server_url}/api/process"

            data = aiohttp.FormData()
            data.add_field(
                "audio",
                audio_data,
                filename="audio.wav",
                content_type="audio/wav",
            )
            if language:
                data.add_field("language", language)

            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    logger.error(f"Server error: {error}")
                    raise RuntimeError(f"Server returned {response.status}")

        except Exception as e:
            logger.error(f"Processing request failed: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check server health.

        Returns:
            True if server is healthy
        """
        try:
            import aiohttp

            if not self.session:
                self.session = aiohttp.ClientSession()

            url = f"{self.server_url}/health"
            async with self.session.get(url) as response:
                return response.status == 200

        except Exception:
            return False

    async def close(self):
        """Clean up resources."""
        await self.disconnect_websocket()
        if self.session:
            await self.session.close()
            self.session = None


# Synchronous wrapper for simple usage
class SyncEdgeClient:
    """Synchronous wrapper for EdgeClient."""

    def __init__(self, server_url: str = "http://localhost:8000"):
        self.client = EdgeClient(server_url)
        self._loop = None

    def _get_loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop

    def process_audio(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronous audio processing."""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.client.process_audio(audio_data, language)
        )

    def health_check(self) -> bool:
        """Synchronous health check."""
        loop = self._get_loop()
        return loop.run_until_complete(self.client.health_check())

    def close(self):
        """Clean up."""
        if self._loop:
            self._loop.run_until_complete(self.client.close())
            self._loop.close()
