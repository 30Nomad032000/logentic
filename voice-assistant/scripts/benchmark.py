"""Performance benchmarking suite for the voice assistant pipeline.

Benchmarks individual components (ASR, Translation, LLM, TTS) and the
full pipeline, measuring latency, memory, and throughput.

Usage:
    python scripts/benchmark.py --component all --iterations 10
    python scripts/benchmark.py --component translation --iterations 20 --output reports/bench.json
"""

import argparse
import json
import os
import platform
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Graceful imports
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@dataclass
class BenchmarkResult:
    """Result of benchmarking a single component."""
    component: str
    iterations: int
    latencies_ms: List[float] = field(default_factory=list)
    errors: int = 0
    peak_memory_mb: float = 0.0
    status: str = "skipped"

    @property
    def min_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0

    @property
    def max_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0

    @property
    def avg_ms(self) -> float:
        return statistics.mean(self.latencies_ms) if self.latencies_ms else 0

    @property
    def p50_ms(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0

    @property
    def p95_ms(self) -> float:
        if len(self.latencies_ms) < 2:
            return self.max_ms
        sorted_l = sorted(self.latencies_ms)
        idx = int(len(sorted_l) * 0.95)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def p99_ms(self) -> float:
        if len(self.latencies_ms) < 2:
            return self.max_ms
        sorted_l = sorted(self.latencies_ms)
        idx = int(len(sorted_l) * 0.99)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def throughput(self) -> float:
        if not self.latencies_ms:
            return 0
        avg_s = self.avg_ms / 1000
        return 1.0 / avg_s if avg_s > 0 else 0

    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "status": self.status,
            "iterations": self.iterations,
            "errors": self.errors,
            "peak_memory_mb": round(self.peak_memory_mb, 1),
            "latency_ms": {
                "min": round(self.min_ms, 1),
                "max": round(self.max_ms, 1),
                "avg": round(self.avg_ms, 1),
                "p50": round(self.p50_ms, 1),
                "p95": round(self.p95_ms, 1),
                "p99": round(self.p99_ms, 1),
            },
            "throughput_per_sec": round(self.throughput, 2),
        }


def get_system_info() -> dict:
    """Collect system information."""
    info = {
        "python_version": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
    }

    if HAS_PSUTIL:
        info["cpu_count"] = psutil.cpu_count(logical=True)
        info["cpu_count_physical"] = psutil.cpu_count(logical=False)
        mem = psutil.virtual_memory()
        info["ram_total_gb"] = round(mem.total / (1024 ** 3), 1)
        info["ram_available_gb"] = round(mem.available / (1024 ** 3), 1)

    if HAS_TORCH:
        info["torch_version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_memory_gb"] = round(
                torch.cuda.get_device_properties(0).total_mem / (1024 ** 3), 1
            )

    return info


def get_memory_mb() -> float:
    """Get current process memory in MB."""
    if HAS_PSUTIL:
        return psutil.Process().memory_info().rss / (1024 ** 2)
    return 0.0


def run_benchmark(
    name: str,
    setup_fn: Callable,
    run_fn: Callable,
    iterations: int = 10,
    warmup: int = 2,
) -> BenchmarkResult:
    """Run a benchmark for a component."""
    result = BenchmarkResult(component=name, iterations=iterations)

    # Setup
    try:
        ctx = setup_fn()
    except Exception as e:
        print(f"  [{name}] Setup failed: {e}")
        result.status = "setup_failed"
        return result

    if ctx is None:
        print(f"  [{name}] Component not available, skipping")
        result.status = "not_available"
        return result

    # Warmup
    print(f"  [{name}] Warming up ({warmup} iterations)...")
    for _ in range(warmup):
        try:
            run_fn(ctx)
        except Exception:
            pass

    # Benchmark
    mem_before = get_memory_mb()
    peak_mem = mem_before

    print(f"  [{name}] Running {iterations} iterations...")
    for i in range(iterations):
        try:
            start = time.perf_counter()
            run_fn(ctx)
            elapsed = (time.perf_counter() - start) * 1000
            result.latencies_ms.append(elapsed)

            current_mem = get_memory_mb()
            peak_mem = max(peak_mem, current_mem)
        except Exception as e:
            result.errors += 1
            if result.errors == 1:
                print(f"  [{name}] Error: {e}")

    result.peak_memory_mb = peak_mem
    result.status = "completed" if result.latencies_ms else "all_failed"
    return result


# ---- Component benchmarks ----

SAMPLE_ML_TEXT = "നമസ്കാരം, എനിക്ക് സഹായം വേണം. ഇന്നത്തെ കാലാവസ്ഥ എങ്ങനെയാണ്?"
SAMPLE_EN_TEXT = "Hello, I need help. How is the weather today in Kerala?"
SAMPLE_TTS_TEXT = "Hello, how can I help you today?"


def bench_translation(iterations: int, warmup: int) -> List[BenchmarkResult]:
    results = []

    # ML -> EN
    def setup_ml2en():
        try:
            from src.translation import IndicTranslator
            t = IndicTranslator()
            t.load_models(directions=["indic-en"])
            return t
        except Exception:
            return None

    results.append(run_benchmark(
        "translation_ml2en",
        setup_ml2en,
        lambda t: t.translate(SAMPLE_ML_TEXT, "ml", "en"),
        iterations, warmup,
    ))

    # EN -> ML
    def setup_en2ml():
        try:
            from src.translation import IndicTranslator
            t = IndicTranslator()
            t.load_models(directions=["en-indic"])
            return t
        except Exception:
            return None

    results.append(run_benchmark(
        "translation_en2ml",
        setup_en2ml,
        lambda t: t.translate(SAMPLE_EN_TEXT, "en", "ml"),
        iterations, warmup,
    ))

    return results


def bench_llm(iterations: int, warmup: int) -> List[BenchmarkResult]:
    def setup():
        try:
            from src.llm import get_llm
            llm = get_llm()
            llm.load_model()
            return llm
        except Exception:
            return None

    return [run_benchmark(
        "llm",
        setup,
        lambda llm: llm.chat("What is the capital of India?"),
        iterations, warmup,
    )]


def bench_tts(iterations: int, warmup: int) -> List[BenchmarkResult]:
    def setup():
        try:
            from src.tts import MMSTTS
            tts = MMSTTS()
            tts.load_model("en")
            return tts
        except Exception:
            return None

    return [run_benchmark(
        "tts_mms",
        setup,
        lambda tts: tts.synthesize(SAMPLE_TTS_TEXT, language="en"),
        iterations, warmup,
    )]


def bench_asr(iterations: int, warmup: int) -> List[BenchmarkResult]:
    # ASR needs audio input - create a silent sample
    def setup():
        try:
            import numpy as np
            from src.asr import create_asr
            asr = create_asr("whisper")
            asr.load_model()
            # 1 second of silence at 16kHz
            audio = np.zeros(16000, dtype=np.float32)
            return (asr, audio)
        except Exception:
            return None

    return [run_benchmark(
        "asr",
        setup,
        lambda ctx: ctx[0].transcribe(ctx[1], language="ml"),
        iterations, warmup,
    )]


def print_report(results: List[BenchmarkResult], sys_info: dict):
    """Print a formatted benchmark report."""
    print("\n" + "=" * 72)
    print("  VOICE ASSISTANT BENCHMARK REPORT")
    print("=" * 72)

    # System info
    print("\n  System Information:")
    print(f"    OS:          {sys_info.get('os', 'N/A')}")
    print(f"    Python:      {sys_info.get('python_version', 'N/A')}")
    print(f"    CPU:         {sys_info.get('processor', 'N/A')}")
    if "cpu_count" in sys_info:
        print(f"    CPU Cores:   {sys_info['cpu_count_physical']}P / {sys_info['cpu_count']}L")
    if "ram_total_gb" in sys_info:
        print(f"    RAM:         {sys_info['ram_total_gb']} GB total, {sys_info['ram_available_gb']} GB free")
    if sys_info.get("cuda_available"):
        print(f"    GPU:         {sys_info.get('gpu_name', 'N/A')} ({sys_info.get('gpu_memory_gb', '?')} GB)")
    else:
        print("    GPU:         None (CPU-only)")

    # Results
    print("\n" + "-" * 72)
    print(f"  {'Component':<25} {'Status':<12} {'Avg (ms)':<10} {'P95 (ms)':<10} {'Throughput':<12} {'Memory':<10}")
    print("-" * 72)

    for r in results:
        if r.status == "completed":
            print(
                f"  {r.component:<25} {'OK':<12} {r.avg_ms:<10.1f} {r.p95_ms:<10.1f} "
                f"{r.throughput:<12.2f} {r.peak_memory_mb:<10.0f}"
            )
        else:
            print(f"  {r.component:<25} {r.status:<12} {'N/A':<10} {'N/A':<10} {'N/A':<12} {'N/A':<10}")

    print("-" * 72)

    # Summary
    completed = [r for r in results if r.status == "completed"]
    if completed:
        total_avg = sum(r.avg_ms for r in completed)
        print(f"\n  Pipeline total (sum of averages): {total_avg:.0f}ms")
        print(f"  Components benchmarked: {len(completed)} / {len(results)}")

    print("=" * 72 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Voice Assistant Benchmark Suite")
    parser.add_argument(
        "--component",
        choices=["asr", "translation", "llm", "tts", "all"],
        default="all",
        help="Component to benchmark (default: all)",
    )
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations (default: 10)")
    parser.add_argument("--warm-up", type=int, default=2, help="Warmup iterations (default: 2)")
    parser.add_argument("--output", type=str, help="Save results to JSON file")
    args = parser.parse_args()

    print("\nVoice Assistant Benchmark Suite")
    print(f"Component: {args.component} | Iterations: {args.iterations} | Warmup: {args.warm_up}\n")

    sys_info = get_system_info()
    results: List[BenchmarkResult] = []

    component_map = {
        "asr": bench_asr,
        "translation": bench_translation,
        "llm": bench_llm,
        "tts": bench_tts,
    }

    if args.component == "all":
        components = ["translation", "llm", "tts", "asr"]
    else:
        components = [args.component]

    for comp in components:
        print(f"\nBenchmarking: {comp}")
        bench_fn = component_map[comp]
        results.extend(bench_fn(args.iterations, args.warm_up))

    print_report(results, sys_info)

    # Save JSON
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "system": sys_info,
            "config": {
                "iterations": args.iterations,
                "warmup": args.warm_up,
            },
            "results": [r.to_dict() for r in results],
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
