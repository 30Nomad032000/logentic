"""
Generate all matplotlib figures for the project report.
Outputs PNGs into report_assets/
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

OUT = os.path.join(os.path.dirname(__file__), "report_assets")
os.makedirs(OUT, exist_ok=True)

# ── Shared style ──────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})

BLUE = "#2b5797"
LIGHT_BLUE = "#d6e4f0"
DARK = "#1a1a2e"
GREEN = "#27ae60"
RED = "#e74c3c"
ORANGE = "#f39c12"
PURPLE = "#8e44ad"
TEAL = "#16a085"
GRAY = "#95a5a6"


# ══════════════════════════════════════════════════════════════
# 1. PIPELINE FLOW DIAGRAM
# ══════════════════════════════════════════════════════════════
def draw_pipeline():
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 3.5)
    ax.axis("off")
    ax.set_title("Fig 3.1 — End-to-End Voice Processing Pipeline", fontsize=12, fontweight="bold", pad=12)

    boxes = [
        (0, 2, "Audio\nInput", "#ecf0f1", DARK),
        (1.6, 2, "ASR\n(Whisper/MMS)", LIGHT_BLUE, BLUE),
        (3.4, 2, "Translation\nML → EN\n(IndicTrans2)", LIGHT_BLUE, BLUE),
        (5.3, 2, "Intent\nDetection\n(NLU)", "#fdebd0", ORANGE),
        (7.2, 2, "Agent\nOrchestrator\n(LangGraph)", "#d5f5e3", GREEN),
        (9.2, 2, "LLM\n(Qwen 2.5)", "#e8daef", PURPLE),
        (9.2, 0, "Translation\nEN → ML\n(IndicTrans2)", LIGHT_BLUE, BLUE),
        (7.2, 0, "TTS\n(MMS-TTS)", LIGHT_BLUE, BLUE),
        (5.3, 0, "Audio\nResponse", "#ecf0f1", DARK),
    ]

    for x, y, label, fc, ec in boxes:
        bbox = FancyBboxPatch((x - 0.65, y - 0.55), 1.3, 1.1,
                              boxstyle="round,pad=0.1", facecolor=fc, edgecolor=ec, linewidth=1.5)
        ax.add_patch(bbox)
        ax.text(x, y, label, ha="center", va="center", fontsize=7.5, fontweight="bold", color=DARK)

    # Forward arrows (top row)
    for i in range(5):
        xs = [b[0] for b in boxes]
        x1 = xs[i] + 0.65
        x2 = xs[i + 1] - 0.65
        ax.annotate("", xy=(x2, 2), xytext=(x1, 2),
                     arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))

    # Down arrow (LLM to Translation)
    ax.annotate("", xy=(9.2, 0.55), xytext=(9.2, 1.45),
                 arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))

    # Backward arrows (bottom row)
    ax.annotate("", xy=(7.2 + 0.65, 0), xytext=(9.2 - 0.65, 0),
                 arrowprops=dict(arrowstyle="<-", color=BLUE, lw=1.5))
    ax.annotate("", xy=(5.3 + 0.65, 0), xytext=(7.2 - 0.65, 0),
                 arrowprops=dict(arrowstyle="<-", color=BLUE, lw=1.5))

    # Agent sub-labels
    agents = ["Info", "Task", "Chat", "Smart\nHome"]
    for i, a in enumerate(agents):
        ax.text(6.6 + i * 0.55, 1.15, a, ha="center", va="center", fontsize=5.5,
                color=GREEN, fontstyle="italic")

    fig.savefig(os.path.join(OUT, "pipeline_flow.png"))
    plt.close(fig)
    print("  -> pipeline_flow.png")


# ══════════════════════════════════════════════════════════════
# 2. THREE-TIER ARCHITECTURE DIAGRAM
# ══════════════════════════════════════════════════════════════
def draw_architecture():
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("Fig 3.1a — Three-Tier System Architecture", fontsize=12, fontweight="bold", pad=12)

    tiers = [
        (5, 6.8, 9, 1.6, "PRESENTATION TIER", "#e8daef", PURPLE,
         ["React 18 + TypeScript Dashboard", "TailwindCSS + Radix UI", "WebSocket Streaming", "Voice Visualizer + TryIt Panel"]),
        (5, 4.2, 9, 2.2, "PROCESSING TIER", LIGHT_BLUE, BLUE,
         ["FastAPI REST API + WebSocket Server", "ASR: Whisper / MMS / Pingala", "Translation: IndicTrans2 (ML\u2194EN)",
          "LLM: Qwen 2.5 (Transformers / llama.cpp)", "Agent Orchestrator: LangGraph", "Cache: LRU + TTL | DB: SQLite WAL"]),
        (5, 1.5, 9, 1.6, "EDGE TIER", "#d5f5e3", GREEN,
         ["Raspberry Pi 5 (BCM2712 Cortex-A76)", "Audio I/O: USB Mic + Speaker", "Wake Word Detection",
          "Edge Client: Async HTTP/WS"]),
    ]

    for cx, cy, w, h, title, fc, ec, items in tiers:
        rect = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                              boxstyle="round,pad=0.12", facecolor=fc, edgecolor=ec, linewidth=2)
        ax.add_patch(rect)
        ax.text(cx, cy + h/2 - 0.25, title, ha="center", va="center",
                fontsize=10, fontweight="bold", color=ec)
        for i, item in enumerate(items):
            ax.text(cx, cy + h/2 - 0.55 - i * 0.28, item, ha="center", va="center",
                    fontsize=7.5, color=DARK)

    # Arrows between tiers
    ax.annotate("", xy=(5, 6.0), xytext=(5, 5.3),
                 arrowprops=dict(arrowstyle="<->", color=DARK, lw=1.5))
    ax.text(5.6, 5.65, "REST API\nWebSocket", fontsize=6.5, ha="left", color=GRAY)

    ax.annotate("", xy=(5, 3.1), xytext=(5, 2.3),
                 arrowprops=dict(arrowstyle="<->", color=DARK, lw=1.5))
    ax.text(5.6, 2.7, "HTTP / WS\nXiaoZhi Protocol", fontsize=6.5, ha="left", color=GRAY)

    fig.savefig(os.path.join(OUT, "architecture.png"))
    plt.close(fig)
    print("  -> architecture.png")


# ══════════════════════════════════════════════════════════════
# 3. UML CLASS DIAGRAM
# ══════════════════════════════════════════════════════════════
def draw_uml():
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.set_xlim(0, 13)
    ax.set_ylim(-0.5, 10.5)
    ax.axis("off")
    fig.suptitle("Fig 3.2 — UML Class Diagram", fontsize=13, fontweight="bold", y=0.97)

    def draw_class(x, y, w, h, name, attrs, methods, color=BLUE):
        # Title bar
        rect_t = FancyBboxPatch((x, y + h - 0.55), w, 0.55,
                                boxstyle="round,pad=0.05", facecolor=LIGHT_BLUE, edgecolor=color, linewidth=1.2)
        ax.add_patch(rect_t)
        ax.text(x + w/2, y + h - 0.27, name, ha="center", va="center",
                fontsize=8, fontweight="bold", color=DARK)
        # Attrs
        attr_h = len(attrs) * 0.24 + 0.12
        rect_a = plt.Rectangle((x, y + h - 0.55 - attr_h), w, attr_h,
                               facecolor="white", edgecolor=color, linewidth=1)
        ax.add_patch(rect_a)
        for i, a in enumerate(attrs):
            ax.text(x + 0.1, y + h - 0.72 - i * 0.24, f"- {a}", fontsize=6.5, color=DARK, family="monospace")
        # Methods
        meth_h = len(methods) * 0.24 + 0.12
        rect_m = plt.Rectangle((x, y + h - 0.55 - attr_h - meth_h), w, meth_h,
                               facecolor="#fafafa", edgecolor=color, linewidth=1)
        ax.add_patch(rect_m)
        for i, m in enumerate(methods):
            ax.text(x + 0.1, y + h - 0.64 - attr_h - 0.06 - i * 0.24, f"+ {m}",
                    fontsize=6.5, color=DARK, family="monospace")

    # ── Top row: Main orchestration classes ──
    draw_class(0.3, 6, 3, 3.2,
               "VoiceAssistantPipeline",
               ["asr_engine", "tts_engine", "llm_engine", "translator", "config"],
               ["process_audio()", "process_text()", "get_metrics()"])

    draw_class(3.8, 6, 3, 3.2,
               "AgentOrchestrator",
               ["state: AgentState", "graph: StateGraph", "llm: QwenLLM", "intent_type"],
               ["setup()", "classify_intent()", "route_to_agent()", "run()"])

    # ── Top-right: Data models ──
    draw_class(7.3, 7.2, 2.3, 2.8,
               "Conversation",
               ["id", "session_id", "language", "asr_time_ms", "llm_time_ms", "messages[]"],
               ["__post_init__()"], color=TEAL)

    draw_class(10, 7.2, 2.2, 2.8,
               "Message",
               ["id", "conversation_id", "role", "content", "language", "timestamp"],
               ["__post_init__()"], color=TEAL)

    draw_class(7.3, 5, 2.3, 1.8,
               "Task",
               ["id", "title", "status", "created_at", "source_input"],
               ["__post_init__()"], color=TEAL)

    draw_class(10, 5, 2.2, 1.8,
               "SystemMetric",
               ["id", "component", "metric_name", "value", "timestamp"],
               ["__post_init__()"], color=TEAL)

    # ── Bottom row: Component classes ──
    draw_class(0.2, 0.5, 2.5, 2.8,
               "WhisperASR",
               ["model", "model_size", "device", "LANGUAGES"],
               ["load_model()", "transcribe()", "detect_language()"])

    draw_class(3.1, 0.5, 2.5, 2.8,
               "TTSEngine",
               ["backends[]", "default_backend", "cache"],
               ["synthesize()", "compare()", "load_backend()"])

    draw_class(6.0, 0.5, 2.5, 2.8,
               "Translator",
               ["model", "tokenizer", "device", "src/tgt_lang"],
               ["translate()", "detect_lang()", "load_model()"])

    draw_class(8.9, 0.5, 2.5, 2.8,
               "QwenLLM",
               ["model", "tokenizer", "model_size", "device"],
               ["generate()", "chat()", "load_model()"])

    # ── "Database Models" label ──
    ax.text(9.75, 10.15, "Database Models", ha="center", va="center",
            fontsize=8, fontstyle="italic", color=TEAL,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#e8f5e9", edgecolor=TEAL, alpha=0.5))

    # ── Relationship arrows ──
    # Pipeline uses bottom-row components
    ax.annotate("", xy=(1.5, 6), xytext=(1.5, 3.3),
                 arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.2))
    ax.text(1.7, 4.5, "uses", fontsize=7, color=GRAY, fontstyle="italic")

    # Orchestrator uses LLM
    ax.annotate("", xy=(5.3, 6), xytext=(10.1, 3.3),
                 arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1, linestyle="dashed"))

    # Dashed line between bottom components
    ax.plot([2.7, 3.1], [1.9, 1.9], color=GRAY, lw=0.7, linestyle="dotted")
    ax.plot([5.6, 6.0], [1.9, 1.9], color=GRAY, lw=0.7, linestyle="dotted")
    ax.plot([8.5, 8.9], [1.9, 1.9], color=GRAY, lw=0.7, linestyle="dotted")

    # Conversation -> Message
    ax.annotate("", xy=(10, 8.6), xytext=(9.6, 8.6),
                 arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1))
    ax.text(9.8, 8.85, "1..*", fontsize=6, color=TEAL, ha="center")

    fig.savefig(os.path.join(OUT, "uml_class.png"))
    plt.close(fig)
    print("  -> uml_class.png")


# ══════════════════════════════════════════════════════════════
# 4. USE-CASE DIAGRAM
# ══════════════════════════════════════════════════════════════
def draw_usecase():
    fig, ax = plt.subplots(figsize=(9, 6.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_title("Fig 3.3 — Use-Case Diagram", fontsize=12, fontweight="bold", pad=12)

    # System boundary
    rect = FancyBboxPatch((3.2, 0.5), 5.8, 8,
                          boxstyle="round,pad=0.15", facecolor="#fafafa", edgecolor=BLUE, linewidth=2, linestyle="--")
    ax.add_patch(rect)
    ax.text(6.1, 8.2, "Voice Assistant System", ha="center", fontsize=11, fontweight="bold", color=BLUE)

    # Actors
    def draw_actor(x, y, label):
        ax.plot(x, y + 0.3, "o", markersize=10, color=DARK, markerfacecolor="white", markeredgewidth=1.5)
        ax.plot([x, x], [y + 0.15, y - 0.15], color=DARK, lw=1.5)
        ax.plot([x - 0.25, x + 0.25], [y + 0.05, y + 0.05], color=DARK, lw=1.5)
        ax.plot([x - 0.2, x], [y - 0.4, y - 0.15], color=DARK, lw=1.5)
        ax.plot([x + 0.2, x], [y - 0.4, y - 0.15], color=DARK, lw=1.5)
        ax.text(x, y - 0.6, label, ha="center", fontsize=8, fontweight="bold", color=DARK)

    draw_actor(1.5, 7, "User")
    draw_actor(1.5, 3.5, "Admin")
    draw_actor(10.5, 5, "Edge\nDevice")

    # Use cases
    def draw_uc(x, y, label, color=LIGHT_BLUE):
        ellipse = mpatches.Ellipse((x, y), 3.2, 0.8, facecolor=color, edgecolor=BLUE, linewidth=1)
        ax.add_patch(ellipse)
        ax.text(x, y, label, ha="center", va="center", fontsize=7, color=DARK)

    ucs = [
        (5.8, 7.8, "Speak Voice Command"),
        (5.8, 7.0, "Get Response in Native Language"),
        (5.8, 6.2, "Set Reminders / Tasks"),
        (5.8, 5.4, "Ask Information Questions"),
        (5.8, 4.5, "Monitor Dashboard"),
        (5.8, 3.7, "View Conversation Logs"),
        (5.8, 2.9, "Check System Health"),
        (5.8, 2.1, "Capture Audio / Wake Word"),
        (5.8, 1.3, "Send Audio / Play Response"),
    ]
    for x, y, label in ucs:
        draw_uc(x, y, label)

    # User connections
    for y in [7.8, 7.0, 6.2, 5.4]:
        ax.plot([1.8, 4.2], [7 + 0.05, y], color=GRAY, lw=0.8)
    # Admin connections
    for y in [4.5, 3.7, 2.9]:
        ax.plot([1.8, 4.2], [3.5, y], color=GRAY, lw=0.8)
    # Device connections
    for y in [2.1, 1.3]:
        ax.plot([10.2, 7.4], [5, y], color=GRAY, lw=0.8)

    fig.savefig(os.path.join(OUT, "usecase.png"))
    plt.close(fig)
    print("  -> usecase.png")


# ══════════════════════════════════════════════════════════════
# 5. BURNDOWN CHART
# ══════════════════════════════════════════════════════════════
def draw_burndown():
    fig, ax = plt.subplots(figsize=(7.5, 4))

    sprints = ["Start", "Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4", "Sprint 5", "Sprint 6"]
    ideal = [230, 191.7, 153.3, 115, 76.7, 38.3, 0]
    actual = [230, 188, 150, 110, 67, 37, 0]

    ax.plot(sprints, ideal, "b--o", linewidth=1.5, markersize=6, label="Ideal", color=BLUE)
    ax.plot(sprints, actual, "r-s", linewidth=2, markersize=6, label="Actual", color=RED)

    ax.fill_between(sprints, actual, alpha=0.08, color=RED)
    ax.set_ylabel("Remaining Hours")
    ax.set_xlabel("Sprint")
    ax.set_title("Fig 4.1 — Sprint Burndown Chart (230 Total Hours)", fontsize=12, fontweight="bold")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 250)
    ax.grid(True, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.savefig(os.path.join(OUT, "burndown.png"))
    plt.close(fig)
    print("  -> burndown.png")


# ══════════════════════════════════════════════════════════════
# 6. LANGUAGE SUPPORT PIE CHART
# ══════════════════════════════════════════════════════════════
def draw_languages():
    fig, ax = plt.subplots(figsize=(6, 4))

    languages = ["Malayalam", "Hindi", "Tamil", "Telugu", "Bengali",
                 "Marathi", "Gujarati", "Kannada", "English", "Others"]
    sizes = [25, 18, 12, 10, 8, 7, 5, 5, 6, 4]
    colors = [BLUE, RED, GREEN, ORANGE, PURPLE, TEAL, "#e67e22", "#2980b9", GRAY, "#bdc3c7"]
    explode = [0.05, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    wedges, texts, autotexts = ax.pie(sizes, labels=languages, autopct="%1.0f%%",
                                       colors=colors, explode=explode, startangle=140,
                                       textprops={"fontsize": 7.5})
    for t in autotexts:
        t.set_fontsize(6.5)
        t.set_color("white")
        t.set_fontweight("bold")

    ax.set_title("Fig 5.1 — Supported Language Distribution", fontsize=11, fontweight="bold")
    fig.savefig(os.path.join(OUT, "languages.png"))
    plt.close(fig)
    print("  -> languages.png")


# ══════════════════════════════════════════════════════════════
# 7. LATENCY BREAKDOWN BAR CHART
# ══════════════════════════════════════════════════════════════
def draw_latency():
    fig, ax = plt.subplots(figsize=(7, 3.5))

    components = ["ASR\n(Whisper)", "Translation\n(IndicTrans2)", "LLM\n(Qwen 2.5)", "TTS\n(MMS-TTS)"]
    gpu_times = [120, 45, 350, 180]
    cpu_times = [380, 95, 1200, 520]

    x = np.arange(len(components))
    w = 0.32
    bars1 = ax.bar(x - w/2, gpu_times, w, label="GPU (CUDA)", color=BLUE, edgecolor="white")
    bars2 = ax.bar(x + w/2, cpu_times, w, label="CPU Only", color=ORANGE, edgecolor="white")

    ax.set_ylabel("Latency (ms)")
    ax.set_title("Fig 5.2 — Component Latency Breakdown (GPU vs CPU)", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(components, fontsize=9)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f"{int(bar.get_height())}ms", ha="center", fontsize=7, color=BLUE)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f"{int(bar.get_height())}ms", ha="center", fontsize=7, color=ORANGE)

    fig.savefig(os.path.join(OUT, "latency.png"))
    plt.close(fig)
    print("  -> latency.png")


# ══════════════════════════════════════════════════════════════
# 8. MODEL MEMORY FOOTPRINT
# ══════════════════════════════════════════════════════════════
def draw_memory():
    fig, ax = plt.subplots(figsize=(7, 3.5))

    models = ["Qwen 0.6B\n(FP32)", "Qwen 0.6B\n(Q8_0)", "Qwen 1.7B\n(FP32)", "Qwen 1.7B\n(Q8_0)",
              "IndicTrans2\n(dist)", "Whisper\n(tiny)", "MMS-TTS"]
    memory = [2400, 300, 6800, 850, 50, 75, 300]
    colors_list = [PURPLE, GREEN, PURPLE, GREEN, BLUE, ORANGE, BLUE]

    bars = ax.barh(models, memory, color=colors_list, edgecolor="white", height=0.6)
    ax.set_xlabel("Memory (MB)")
    ax.set_title("Fig 5.3 — Model Memory Footprint", fontsize=11, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar, val in zip(bars, memory):
        label = f"{val} MB" if val < 1000 else f"{val/1000:.1f} GB"
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                label, va="center", fontsize=7.5, color=DARK)

    fig.savefig(os.path.join(OUT, "memory.png"))
    plt.close(fig)
    print("  -> memory.png")


# ══════════════════════════════════════════════════════════════
# RUN ALL
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating figures...")
    draw_pipeline()
    draw_architecture()
    draw_uml()
    draw_usecase()
    draw_burndown()
    draw_languages()
    draw_latency()
    draw_memory()
    print("Done! All figures saved to report_assets/")
