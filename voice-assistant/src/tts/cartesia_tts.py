"""
Cartesia TTS Implementation
High-quality online TTS with streaming support.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union, Generator
import numpy as np

logger = logging.getLogger(__name__)


class CartesiaTTS:
    """
    Cartesia TTS for high-quality text-to-speech.

    Features:
    - High quality voices
    - Streaming support for low latency
    - Multiple languages including Indian languages
    """

    # Cartesia voice IDs (examples - check docs for latest)
    VOICES = {
        "default": "a0e99841-438c-4a64-b679-ae501e7d6091",  # Default voice
        "female_indian": None,  # To be configured
        "male_indian": None,  # To be configured
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        model_id: str = "sonic-3",
    ):
        """
        Initialize Cartesia TTS.

        Args:
            api_key: Cartesia API key (or set CARTESIA_API_KEY env var)
            voice_id: Voice ID to use
            model_id: Model to use (sonic-2, sonic-english, etc.)
        """
        self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
        self.voice_id = voice_id or self.VOICES["default"]
        self.model_id = model_id
        self.client = None
        self.sample_rate = 24000  # Cartesia default

        if not self.api_key:
            logger.warning("No Cartesia API key provided. Set CARTESIA_API_KEY env var.")

    def _init_client(self):
        """Initialize the Cartesia client."""
        try:
            from cartesia import Cartesia

            self.client = Cartesia(api_key=self.api_key)
            logger.info("Cartesia client initialized")

        except ImportError:
            logger.error("cartesia package not installed. Run: pip install cartesia")
            raise ImportError("Please install cartesia: pip install cartesia")

    def synthesize(
        self,
        text: str,
        language: str = "en",
        output_path: Optional[Union[str, Path]] = None,
        voice_id: Optional[str] = None,
        stream: bool = False,
    ) -> Union[np.ndarray, str, Generator]:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            language: Language code
            output_path: Optional path to save audio file
            voice_id: Override voice ID
            stream: If True, returns a generator for streaming

        Returns:
            Audio array, path to saved file, or generator for streaming
        """
        if self.client is None:
            self._init_client()

        voice = voice_id or self.voice_id

        logger.info(f"Synthesizing with Cartesia: '{text[:50]}...'")

        try:
            if stream:
                return self._synthesize_stream(text, language, voice)
            else:
                return self._synthesize_full(text, language, voice, output_path)

        except Exception as e:
            logger.error(f"Cartesia synthesis failed: {e}")
            raise

    def _synthesize_full(
        self,
        text: str,
        language: str,
        voice_id: str,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Union[np.ndarray, str]:
        """Full synthesis (non-streaming)."""
        import struct

        # Generate audio - Cartesia SDK v2.0 API
        audio_chunks = []
        for chunk in self.client.tts.bytes(
            model_id=self.model_id,
            transcript=text,
            voice={"mode": "id", "id": voice_id},
            language=language,
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": self.sample_rate,
            },
        ):
            audio_chunks.append(chunk)

        audio_data = b"".join(audio_chunks)

        # Convert bytes to numpy array
        audio_array = np.array(
            struct.unpack(f"{len(audio_data) // 4}f", audio_data),
            dtype=np.float32
        )

        # Save to file if path provided
        if output_path:
            import soundfile as sf
            sf.write(str(output_path), audio_array, samplerate=self.sample_rate)
            logger.info(f"Audio saved to {output_path}")
            return str(output_path)

        return audio_array

    def _synthesize_stream(
        self,
        text: str,
        language: str,
        voice_id: str,
    ) -> Generator[bytes, None, None]:
        """Streaming synthesis for low-latency playback."""
        # Stream audio chunks - Cartesia SDK v2.0 API
        for chunk in self.client.tts.bytes(
            model_id=self.model_id,
            transcript=text,
            voice={"mode": "id", "id": voice_id},
            language=language,
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": self.sample_rate,
            },
        ):
            yield chunk

    def list_voices(self) -> list:
        """List available voices."""
        if self.client is None:
            self._init_client()

        try:
            voices = self.client.voices.list()
            return [{"id": v.id, "name": v.name} for v in voices]
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []

    def clone_voice(
        self,
        name: str,
        audio_path: str,
        description: str = "",
    ) -> Optional[str]:
        """
        Clone a voice from audio sample.

        Args:
            name: Name for the cloned voice
            audio_path: Path to audio sample
            description: Voice description

        Returns:
            Voice ID of cloned voice
        """
        if self.client is None:
            self._init_client()

        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            voice = self.client.voices.clone(
                name=name,
                description=description,
                clip=audio_data,
            )

            logger.info(f"Voice cloned successfully: {voice.id}")
            return voice.id

        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return None


# Convenience function
def synthesize_cartesia(
    text: str,
    language: str = "en",
    output_path: Optional[str] = None,
    stream: bool = False,
) -> Union[np.ndarray, str, Generator]:
    """
    Quick Cartesia synthesis function.

    Args:
        text: Text to synthesize
        language: Language code
        output_path: Optional output file path
        stream: Enable streaming mode

    Returns:
        Audio array, path to saved file, or stream generator
    """
    tts = CartesiaTTS()
    return tts.synthesize(text, language=language, output_path=output_path, stream=stream)
