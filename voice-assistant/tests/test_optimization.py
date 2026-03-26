"""
Tests for the model optimization module.
Covers MemoryProfile, ModelOptimizer, MemoryTracker, and LazyModelLoader.
"""

import pytest
from src.optimization.model_optimizer import (
    MemoryProfile, ModelOptimizer, MemoryTracker, LazyModelLoader, _human_readable,
)


class TestHumanReadable:
    """Tests for the _human_readable utility."""

    def test_billions(self):
        assert _human_readable(1_700_000_000) == "1.7B"

    def test_millions(self):
        assert _human_readable(211_000_000) == "211.0M"

    def test_thousands(self):
        assert _human_readable(4_500) == "4.5K"

    def test_small(self):
        assert _human_readable(42) == "42"


class TestMemoryProfile:
    """Tests for MemoryProfile dataclass."""

    def test_creation(self):
        p = MemoryProfile(
            model_name="test", param_count=1_000_000,
            fp32_mb=4.0, fp16_mb=2.0, int8_mb=1.0, int4_mb=0.5,
        )
        assert p.model_name == "test"
        assert p.param_count == 1_000_000

    def test_to_dict(self):
        p = MemoryProfile(
            model_name="qwen3-1.7b", param_count=1_700_000_000,
            fp32_mb=6400.0, fp16_mb=3200.0, int8_mb=1600.0, int4_mb=800.0,
        )
        d = p.to_dict()
        assert d["model_name"] == "qwen3-1.7b"
        assert d["param_count"] == 1_700_000_000
        assert d["param_count_human"] == "1.7B"
        assert d["fp32_mb"] == 6400.0
        assert d["int4_mb"] == 800.0


class TestModelOptimizer:
    """Tests for ModelOptimizer static methods."""

    def test_profile_model_memory(self):
        profile = ModelOptimizer.profile_model_memory("test-model", param_count=1_000_000)
        assert profile.model_name == "test-model"
        assert profile.param_count == 1_000_000
        # fp32: 1M * 4 bytes = 4MB / (1024^2) ~ 3.81MB
        assert profile.fp32_mb == pytest.approx(1_000_000 * 4 / (1024 ** 2), rel=0.01)
        assert profile.fp16_mb == pytest.approx(1_000_000 * 2 / (1024 ** 2), rel=0.01)
        assert profile.int8_mb == pytest.approx(1_000_000 * 1 / (1024 ** 2), rel=0.01)
        assert profile.int4_mb == pytest.approx(1_000_000 * 0.5 / (1024 ** 2), rel=0.01)

    def test_estimate_params_from_name(self):
        assert ModelOptimizer._estimate_params("qwen3-0.6b") == 600_000_000
        assert ModelOptimizer._estimate_params("qwen3-1.7b") == 1_700_000_000
        assert ModelOptimizer._estimate_params("indictrans2-211m") == 211_000_000
        assert ModelOptimizer._estimate_params("model-7b") == 7_000_000_000

    def test_estimate_params_default(self):
        # Unknown model name should return default
        result = ModelOptimizer._estimate_params("unknown-model")
        assert result == 500_000_000

    def test_profile_model_auto_estimate(self):
        profile = ModelOptimizer.profile_model_memory("qwen3-1.7b")
        assert profile.param_count == 1_700_000_000

    def test_get_quantization_config_dynamic(self):
        config = ModelOptimizer.get_quantization_config("dynamic")
        assert config["dtype"] == "qint8"
        assert "dynamic" in config["method"].lower() or "dynamic" in config["description"].lower()

    def test_get_quantization_config_int8(self):
        config = ModelOptimizer.get_quantization_config("int8")
        assert config["dtype"] == "int8"
        assert "config" in config

    def test_get_quantization_config_int4(self):
        config = ModelOptimizer.get_quantization_config("int4")
        assert config["dtype"] == "int4"
        assert config["config"]["load_in_4bit"] is True

    def test_get_quantization_config_fp16(self):
        config = ModelOptimizer.get_quantization_config("fp16")
        assert config["dtype"] == "float16"

    def test_get_quantization_config_invalid(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            ModelOptimizer.get_quantization_config("invalid")

    def test_estimate_edge_feasibility_fits(self):
        models = {"small-model": 100_000_000}  # 100M params
        result = ModelOptimizer.estimate_edge_feasibility(models, target_ram_gb=4.0)
        assert result["target_device"] == "4.0GB RAM"
        assert result["feasibility"]["int4"]["fits"] is True
        assert "recommendation" in result

    def test_estimate_edge_feasibility_too_large(self):
        models = {"huge-model": 70_000_000_000}  # 70B params
        result = ModelOptimizer.estimate_edge_feasibility(models, target_ram_gb=4.0)
        assert result["feasibility"]["fp32"]["fits"] is False
        assert "too large" in result["recommendation"].lower() or "offload" in result["recommendation"].lower()

    def test_estimate_edge_feasibility_multiple_models(self):
        models = {
            "asr-model": 211_000_000,
            "llm-model": 1_700_000_000,
            "tts-model": 300_000_000,
        }
        result = ModelOptimizer.estimate_edge_feasibility(models, target_ram_gb=8.0)
        assert len(result["models"]) == 3
        assert "total_by_precision" in result


class TestMemoryTracker:
    """Tests for MemoryTracker context manager."""

    def test_basic_usage(self):
        with MemoryTracker() as tracker:
            _ = [0] * 10000  # allocate some memory
        # Just verify it runs without error and produces numbers
        assert isinstance(tracker.peak_mb, float)
        assert isinstance(tracker.delta_mb, float)

    def test_attributes_initialized(self):
        tracker = MemoryTracker()
        assert tracker.peak_mb == 0.0
        assert tracker.delta_mb == 0.0


class TestLazyModelLoader:
    """Tests for LazyModelLoader."""

    def test_not_loaded_initially(self):
        loader = LazyModelLoader(lambda: "loaded_model", name="test")
        assert not loader.is_loaded
        assert loader.load_time_ms == 0

    def test_lazy_load_on_get(self):
        load_count = [0]

        def load_fn():
            load_count[0] += 1
            return {"model": "data"}

        loader = LazyModelLoader(load_fn, name="test")
        result = loader.get()
        assert result == {"model": "data"}
        assert loader.is_loaded
        assert load_count[0] == 1
        assert loader.load_time_ms > 0

    def test_only_loads_once(self):
        load_count = [0]

        def load_fn():
            load_count[0] += 1
            return "model"

        loader = LazyModelLoader(load_fn, name="test")
        loader.get()
        loader.get()
        loader.get()
        assert load_count[0] == 1

    def test_load_alias(self):
        loader = LazyModelLoader(lambda: 42, name="test")
        result = loader.load()
        assert result == 42
        assert loader.is_loaded

    def test_unload(self):
        loader = LazyModelLoader(lambda: "model", name="test")
        loader.get()
        assert loader.is_loaded
        loader.unload()
        assert not loader.is_loaded
        assert loader.load_time_ms == 0

    def test_reload_after_unload(self):
        load_count = [0]

        def load_fn():
            load_count[0] += 1
            return f"model_v{load_count[0]}"

        loader = LazyModelLoader(load_fn, name="test")
        v1 = loader.get()
        assert v1 == "model_v1"
        loader.unload()
        v2 = loader.get()
        assert v2 == "model_v2"
        assert load_count[0] == 2
