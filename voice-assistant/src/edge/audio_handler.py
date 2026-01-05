"""
Audio Handler for Edge Devices
Handles audio capture, playback, and preprocessing on Raspberry Pi and similar devices.
"""

import logging
from typing import Optional, Callable
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class AudioHandler:
    """
    Audio handling for edge devices.

    Manages microphone input, speaker output, and audio preprocessing.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        device_index: Optional[int] = None,
    ):
        """
        Initialize audio handler.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            chunk_size: Size of audio chunks for streaming
            device_index: Specific audio device index (None for default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.stream = None
        self.is_recording = False

    def list_devices(self) -> list:
        """List available audio devices."""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            device_list = []
            for i, device in enumerate(devices):
                device_list.append({
                    "index": i,
                    "name": device["name"],
                    "channels": device["max_input_channels"],
                    "sample_rate": device["default_samplerate"],
                })
            return device_list
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            return []

    def record(
        self,
        duration: float,
        output_path: Optional[str] = None,
    ) -> np.ndarray:
        """
        Record audio for specified duration.

        Args:
            duration: Recording duration in seconds
            output_path: Optional path to save recording

        Returns:
            Audio data as numpy array
        """
        try:
            import sounddevice as sd

            logger.info(f"Recording {duration} seconds of audio...")

            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                device=self.device_index,
            )
            sd.wait()

            logger.info("Recording complete")

            # Save if path provided
            if output_path:
                self.save_audio(audio_data, output_path)

            return audio_data.squeeze()

        except Exception as e:
            logger.error(f"Recording failed: {e}")
            raise

    def record_until_silence(
        self,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        max_duration: float = 30.0,
    ) -> np.ndarray:
        """
        Record audio until silence is detected.

        Args:
            silence_threshold: RMS threshold for silence
            silence_duration: Duration of silence to stop recording
            max_duration: Maximum recording duration

        Returns:
            Audio data as numpy array
        """
        try:
            import sounddevice as sd

            logger.info("Recording until silence...")

            audio_chunks = []
            silence_chunks = 0
            chunks_for_silence = int(silence_duration * self.sample_rate / self.chunk_size)
            max_chunks = int(max_duration * self.sample_rate / self.chunk_size)

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                device=self.device_index,
            ) as stream:
                for _ in range(max_chunks):
                    chunk, _ = stream.read(self.chunk_size)
                    audio_chunks.append(chunk)

                    # Check for silence
                    rms = np.sqrt(np.mean(chunk ** 2))
                    if rms < silence_threshold:
                        silence_chunks += 1
                        if silence_chunks >= chunks_for_silence:
                            break
                    else:
                        silence_chunks = 0

            audio_data = np.concatenate(audio_chunks)
            logger.info(f"Recording complete: {len(audio_data) / self.sample_rate:.2f} seconds")

            return audio_data.squeeze()

        except Exception as e:
            logger.error(f"Recording failed: {e}")
            raise

    def play(self, audio: np.ndarray, blocking: bool = True):
        """
        Play audio through speaker.

        Args:
            audio: Audio data as numpy array
            blocking: Wait for playback to complete
        """
        try:
            import sounddevice as sd

            logger.info(f"Playing audio: {len(audio) / self.sample_rate:.2f} seconds")

            sd.play(audio, samplerate=self.sample_rate)
            if blocking:
                sd.wait()

        except Exception as e:
            logger.error(f"Playback failed: {e}")
            raise

    def play_file(self, file_path: str, blocking: bool = True):
        """
        Play audio from file.

        Args:
            file_path: Path to audio file
            blocking: Wait for playback to complete
        """
        try:
            import soundfile as sf

            audio, sr = sf.read(file_path)
            if sr != self.sample_rate:
                # Simple resampling (for production, use librosa or scipy)
                logger.warning(f"Sample rate mismatch: {sr} vs {self.sample_rate}")

            self.play(audio, blocking)

        except Exception as e:
            logger.error(f"Failed to play file: {e}")
            raise

    def save_audio(self, audio: np.ndarray, file_path: str):
        """
        Save audio to file.

        Args:
            audio: Audio data
            file_path: Output file path
        """
        try:
            import soundfile as sf

            sf.write(file_path, audio, self.sample_rate)
            logger.info(f"Audio saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise

    def preprocess(self, audio: np.ndarray) -> np.ndarray:
        """
        Preprocess audio for ASR.

        Args:
            audio: Raw audio data

        Returns:
            Preprocessed audio
        """
        # Normalize
        if audio.max() > 0:
            audio = audio / np.abs(audio).max()

        # Remove DC offset
        audio = audio - np.mean(audio)

        return audio
