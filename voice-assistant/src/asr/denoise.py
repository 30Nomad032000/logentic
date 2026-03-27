"""
Audio Noise Reduction
Spectral-gating denoiser applied before ASR to improve transcription accuracy.
"""

import logging
import tempfile
import subprocess
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

TARGET_SR = 16000


def _load_audio(file_path: str) -> tuple[np.ndarray, int]:
    """Load audio from any format as mono float32 at 16kHz."""
    path = Path(file_path)

    # WAV files: try soundfile directly
    if path.suffix.lower() == ".wav":
        try:
            import soundfile as sf
            data, sr = sf.read(file_path)
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            return data.astype(np.float32), sr
        except Exception:
            pass

    # Non-WAV (webm, ogg, m4a): convert via ffmpeg to WAV
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", file_path, "-ar", str(TARGET_SR), "-ac", "1", "-f", "wav", tmp.name],
            capture_output=True, check=True,
        )
        import soundfile as sf
        data, sr = sf.read(tmp.name)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        return data.astype(np.float32), sr
    finally:
        Path(tmp.name).unlink(missing_ok=True)


def denoise_audio(file_path: str) -> str:
    """
    Apply noise reduction to an audio file.

    Loads the audio, applies spectral-gating noise reduction,
    and writes the cleaned audio to a new temp WAV file.

    Args:
        file_path: Path to the input audio file (any format).

    Returns:
        Path to the denoised WAV file (caller should delete after use).
    """
    try:
        import noisereduce as nr

        data, sr = _load_audio(file_path)

        # Apply spectral gating noise reduction
        cleaned = nr.reduce_noise(
            y=data,
            sr=sr,
            stationary=True,      # assume stationary background noise
            prop_decrease=0.85,   # aggressive reduction — ASR cares about clarity, not naturalness
            n_fft=1024,
            n_std_thresh_stationary=1.2,
        )

        # Normalize to prevent clipping
        peak = np.abs(cleaned).max()
        if peak > 0:
            cleaned = cleaned / peak * 0.95

        # Write cleaned audio to temp WAV at 16kHz mono
        import soundfile as sf
        out = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        out.close()
        sf.write(out.name, cleaned, sr)
        logger.info(f"Denoised audio: {file_path} → {out.name}")
        return out.name

    except Exception as e:
        logger.warning(f"Noise reduction failed, using original audio: {e}")
        return file_path
