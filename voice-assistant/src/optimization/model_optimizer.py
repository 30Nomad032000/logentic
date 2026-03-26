"""Model optimization utilities for edge deployment.

Provides memory profiling, quantization helpers, edge feasibility
estimation, and lazy model loading.
"""

import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Graceful imports
try:
    import tracemalloc
except ImportError:
    tracemalloc = None

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class MemoryProfile:
    """Memory profile for a model."""
    model_name: str
    param_count: int
    fp32_mb: float
    fp16_mb: float
    int8_mb: float
    int4_mb: float

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "param_count": self.param_count,
            "param_count_human": _human_readable(self.param_count),
            "fp32_mb": round(self.fp32_mb, 1),
            "fp16_mb": round(self.fp16_mb, 1),
            "int8_mb": round(self.int8_mb, 1),
            "int4_mb": round(self.int4_mb, 1),
        }


def _human_readable(n: int) -> str:
    if n >= 1e9:
        return f"{n / 1e9:.1f}B"
    if n >= 1e6:
        return f"{n / 1e6:.1f}M"
    if n >= 1e3:
        return f"{n / 1e3:.1f}K"
    return str(n)


class ModelOptimizer:
    """Static utilities for model optimization."""

    @staticmethod
    def profile_model_memory(model_name: str, param_count: Optional[int] = None) -> MemoryProfile:
        """Estimate memory usage of a model at different precisions.

        Args:
            model_name: Name or HuggingFace ID of the model.
            param_count: Number of parameters. If None, estimates from model name.
        """
        if param_count is None:
            param_count = ModelOptimizer._estimate_params(model_name)

        bytes_per_param = {"fp32": 4, "fp16": 2, "int8": 1, "int4": 0.5}
        return MemoryProfile(
            model_name=model_name,
            param_count=param_count,
            fp32_mb=param_count * bytes_per_param["fp32"] / (1024 ** 2),
            fp16_mb=param_count * bytes_per_param["fp16"] / (1024 ** 2),
            int8_mb=param_count * bytes_per_param["int8"] / (1024 ** 2),
            int4_mb=param_count * bytes_per_param["int4"] / (1024 ** 2),
        )

    @staticmethod
    def _estimate_params(model_name: str) -> int:
        """Estimate param count from model name."""
        name = model_name.lower()
        size_map = {
            "0.5b": 500_000_000, "0.6b": 600_000_000,
            "1.5b": 1_500_000_000, "1.7b": 1_700_000_000,
            "3b": 3_000_000_000, "4b": 4_000_000_000,
            "7b": 7_000_000_000, "13b": 13_000_000_000,
            "211m": 211_000_000, "1b": 1_000_000_000,
        }
        for key, count in size_map.items():
            if key in name:
                return count
        return 500_000_000  # default

    @staticmethod
    def get_quantization_config(strategy: str) -> dict:
        """Get quantization configuration for a given strategy.

        Args:
            strategy: One of "int8", "int4", "fp16", "dynamic".
        """
        configs = {
            "dynamic": {
                "method": "torch.quantization.quantize_dynamic",
                "description": "Dynamic quantization (weights only)",
                "dtype": "qint8",
                "layers": ["torch.nn.Linear"],
                "memory_reduction": "~2x",
                "accuracy_impact": "minimal (<1%)",
            },
            "int8": {
                "method": "bitsandbytes / torch int8",
                "description": "8-bit weight quantization",
                "dtype": "int8",
                "memory_reduction": "~4x vs FP32",
                "accuracy_impact": "low (1-2%)",
                "config": {"load_in_8bit": True},
            },
            "int4": {
                "method": "GPTQ / bitsandbytes 4-bit",
                "description": "4-bit weight quantization with grouping",
                "dtype": "int4",
                "memory_reduction": "~8x vs FP32",
                "accuracy_impact": "moderate (2-5%)",
                "config": {
                    "load_in_4bit": True,
                    "bnb_4bit_compute_dtype": "float16",
                    "bnb_4bit_quant_type": "nf4",
                },
            },
            "fp16": {
                "method": "torch.float16",
                "description": "Half-precision floating point",
                "dtype": "float16",
                "memory_reduction": "~2x vs FP32",
                "accuracy_impact": "negligible",
                "config": {"torch_dtype": "float16"},
            },
        }
        if strategy not in configs:
            raise ValueError(f"Unknown strategy '{strategy}'. Choose from: {list(configs.keys())}")
        return configs[strategy]

    @staticmethod
    def estimate_edge_feasibility(
        model_configs: Dict[str, int],
        target_ram_gb: float = 4.0,
    ) -> dict:
        """Estimate if models can run on an edge device.

        Args:
            model_configs: Dict of {model_name: param_count}.
            target_ram_gb: Target device RAM in GB.
        """
        target_mb = target_ram_gb * 1024
        os_overhead_mb = 512  # OS + runtime overhead
        available_mb = target_mb - os_overhead_mb

        profiles = {}
        total = {"fp32": 0, "fp16": 0, "int8": 0, "int4": 0}

        for name, params in model_configs.items():
            p = ModelOptimizer.profile_model_memory(name, params)
            profiles[name] = p.to_dict()
            total["fp32"] += p.fp32_mb
            total["fp16"] += p.fp16_mb
            total["int8"] += p.int8_mb
            total["int4"] += p.int4_mb

        feasibility = {}
        for precision, mb in total.items():
            feasibility[precision] = {
                "total_mb": round(mb, 1),
                "fits": mb <= available_mb,
                "utilization_percent": round(mb / available_mb * 100, 1),
            }

        # Recommendation
        if feasibility["int4"]["fits"]:
            rec = "INT4 quantization recommended for edge deployment"
        elif feasibility["int8"]["fits"]:
            rec = "INT8 quantization required for edge deployment"
        elif feasibility["fp16"]["fits"]:
            rec = "FP16 sufficient for deployment"
        else:
            rec = f"Models too large for {target_ram_gb}GB device. Consider smaller models or offloading."

        return {
            "target_device": f"{target_ram_gb}GB RAM",
            "available_mb": round(available_mb, 1),
            "models": profiles,
            "total_by_precision": {k: round(v, 1) for k, v in total.items()},
            "feasibility": feasibility,
            "recommendation": rec,
        }

    @staticmethod
    def optimize_for_inference(model: Any, strategy: str = "dynamic") -> Any:
        """Apply quantization to a PyTorch model.

        Args:
            model: A PyTorch nn.Module.
            strategy: Quantization strategy ("dynamic" or "fp16").

        Returns:
            The optimized model.
        """
        try:
            import torch
        except ImportError:
            logger.warning("PyTorch not available, returning model unchanged")
            return model

        if strategy == "dynamic":
            try:
                quantized = torch.quantization.quantize_dynamic(
                    model,
                    {torch.nn.Linear},
                    dtype=torch.qint8,
                )
                logger.info("Applied dynamic INT8 quantization")
                return quantized
            except Exception as e:
                logger.warning("Dynamic quantization failed: %s", e)
                return model

        elif strategy == "fp16":
            try:
                model = model.half()
                logger.info("Converted model to FP16")
                return model
            except Exception as e:
                logger.warning("FP16 conversion failed: %s", e)
                return model

        else:
            logger.warning("Strategy '%s' not supported for optimize_for_inference", strategy)
            return model


class MemoryTracker:
    """Context manager for tracking memory usage.

    Usage:
        with MemoryTracker() as tracker:
            # do work
        print(tracker.peak_mb, tracker.delta_mb)
    """

    def __init__(self):
        self.peak_mb: float = 0.0
        self.delta_mb: float = 0.0
        self._start_mb: float = 0.0
        self._use_psutil = psutil is not None

    def __enter__(self):
        if self._use_psutil:
            proc = psutil.Process()
            self._start_mb = proc.memory_info().rss / (1024 ** 2)
        elif tracemalloc is not None:
            tracemalloc.start()
        return self

    def __exit__(self, *args):
        if self._use_psutil:
            proc = psutil.Process()
            end_mb = proc.memory_info().rss / (1024 ** 2)
            self.peak_mb = end_mb
            self.delta_mb = end_mb - self._start_mb
        elif tracemalloc is not None:
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            self.peak_mb = peak / (1024 ** 2)
            self.delta_mb = self.peak_mb


class LazyModelLoader:
    """Generic lazy model loader with thread-safe loading and unloading.

    Usage:
        loader = LazyModelLoader(lambda: load_heavy_model())
        model = loader.get()  # loads on first call
        loader.unload()       # free memory
    """

    def __init__(self, load_fn: Callable[[], Any], name: str = "model"):
        self._load_fn = load_fn
        self._name = name
        self._model: Optional[Any] = None
        self._lock = threading.Lock()
        self._load_time_ms: float = 0

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def load_time_ms(self) -> float:
        return self._load_time_ms

    def get(self) -> Any:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    logger.info("Lazy loading %s...", self._name)
                    start = time.perf_counter()
                    self._model = self._load_fn()
                    self._load_time_ms = (time.perf_counter() - start) * 1000
                    logger.info("%s loaded in %.0fms", self._name, self._load_time_ms)
        return self._model

    def load(self) -> Any:
        return self.get()

    def unload(self) -> None:
        with self._lock:
            if self._model is not None:
                logger.info("Unloading %s", self._name)
                del self._model
                self._model = None
                self._load_time_ms = 0

                # Try to free GPU memory
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass
