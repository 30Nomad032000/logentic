"""
ONNX Runtime Inference Backend
Provides accelerated CPU inference for ASR and TTS models using ONNX Runtime.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Union
import numpy as np

logger = logging.getLogger(__name__)


class ONNXInferenceBackend:
    """
    ONNX Runtime inference backend for accelerated CPU/GPU execution.

    Used by ASR and TTS modules for faster inference on edge devices.
    Supports CPUExecutionProvider (default) and CUDAExecutionProvider.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        providers: Optional[List[str]] = None,
        session_options: Optional[Dict] = None,
    ):
        """
        Initialize ONNX inference backend.

        Args:
            model_path: Path to ONNX model file
            providers: Execution providers (default: ["CPUExecutionProvider"])
            session_options: Optional session configuration
        """
        self.model_path = model_path
        self.providers = providers or ["CPUExecutionProvider"]
        self.session_options = session_options or {}
        self._session = None

    def load(self, model_path: Optional[str] = None):
        """
        Load ONNX model into inference session.

        Args:
            model_path: Override model path (optional)
        """
        import onnxruntime as ort

        path = model_path or self.model_path
        if not path:
            raise ValueError("model_path must be provided")

        if not Path(path).exists():
            raise FileNotFoundError(f"ONNX model not found: {path}")

        logger.info(f"Loading ONNX model: {path}")
        logger.info(f"Providers: {self.providers}")

        # Configure session options
        opts = ort.SessionOptions()
        if self.session_options.get("intra_op_num_threads"):
            opts.intra_op_num_threads = self.session_options["intra_op_num_threads"]
        if self.session_options.get("inter_op_num_threads"):
            opts.inter_op_num_threads = self.session_options["inter_op_num_threads"]
        if self.session_options.get("graph_optimization_level"):
            opts.graph_optimization_level = getattr(
                ort.GraphOptimizationLevel,
                self.session_options["graph_optimization_level"],
                ort.GraphOptimizationLevel.ORT_ENABLE_ALL,
            )
        else:
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self._session = ort.InferenceSession(
            path,
            sess_options=opts,
            providers=self.providers,
        )

        logger.info("ONNX model loaded successfully")

    def run(
        self,
        inputs: Dict[str, np.ndarray],
        output_names: Optional[List[str]] = None,
    ) -> List[np.ndarray]:
        """
        Run inference on the model.

        Args:
            inputs: Dictionary mapping input names to numpy arrays
            output_names: Specific output names to return (None for all)

        Returns:
            List of output numpy arrays
        """
        if self._session is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        results = self._session.run(output_names, inputs)
        return results

    def get_input_names(self) -> List[str]:
        """Get model input names."""
        if self._session is None:
            raise RuntimeError("Model not loaded.")
        return [inp.name for inp in self._session.get_inputs()]

    def get_output_names(self) -> List[str]:
        """Get model output names."""
        if self._session is None:
            raise RuntimeError("Model not loaded.")
        return [out.name for out in self._session.get_outputs()]

    def get_input_shapes(self) -> Dict[str, list]:
        """Get model input shapes."""
        if self._session is None:
            raise RuntimeError("Model not loaded.")
        return {
            inp.name: inp.shape for inp in self._session.get_inputs()
        }

    @property
    def loaded(self) -> bool:
        """Check if model is loaded."""
        return self._session is not None
