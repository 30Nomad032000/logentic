#!/bin/bash
# ClawGo (OpenClaw Pi Node) Setup Script
# Downloads and configures ClawGo for the voice assistant

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_DIR/config/clawgo"

echo "=== ClawGo Setup for Voice Assistant ==="
echo ""

# Step 1: Check for Ollama
echo "[1/4] Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "  ✓ Ollama found: $(ollama --version 2>/dev/null || echo 'installed')"
else
    echo "  ✗ Ollama not found."
    echo "  Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Or visit: https://ollama.com/download"
    echo ""
    read -p "Continue without Ollama? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Pull Qwen3 model for local inference
echo ""
echo "[2/4] Setting up local LLM (Qwen3 via Ollama)..."
if command -v ollama &> /dev/null; then
    echo "  Pulling qwen3:1.7b model (this may take a few minutes)..."
    ollama pull qwen3:1.7b || echo "  Warning: Failed to pull model. Ensure Ollama is running."
    echo "  ✓ Model ready"
else
    echo "  Skipping (Ollama not available)"
fi

# Step 3: Create workspace
echo ""
echo "[3/4] Creating ClawGo workspace..."
mkdir -p "$CONFIG_DIR"

# Create config if it doesn't exist
if [ ! -f "$CONFIG_DIR/openclaw.json" ]; then
    cat > "$CONFIG_DIR/openclaw.json" << 'CONFIGEOF'
{
  "gateway": {
    "url": "http://localhost:11434",
    "provider": "ollama"
  },
  "model": {
    "name": "qwen3:1.7b",
    "provider": "ollama",
    "options": {
      "temperature": 0.7,
      "num_predict": 256,
      "top_p": 0.9
    }
  },
  "voice": {
    "input_device": "default",
    "output_device": "default",
    "sample_rate": 16000,
    "vad_enabled": true
  },
  "workspace": {
    "soul_file": "SOUL.md",
    "tools_file": "TOOLS.md"
  }
}
CONFIGEOF
    echo "  ✓ Created openclaw.json"
fi

if [ ! -f "$CONFIG_DIR/SOUL.md" ]; then
    cat > "$CONFIG_DIR/SOUL.md" << 'SOULEOF'
# Voice Assistant Personality

You are a multilingual voice assistant designed for Indian language speakers.

## Core Traits
- Helpful and friendly
- Concise responses (1-3 sentences for voice)
- Culturally aware of Indian context
- Patient with language switches

## Languages
You primarily assist in Malayalam, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Punjabi, and English.

## Response Style
- Keep answers brief and suitable for spoken delivery
- Use simple, clear language
- Be warm and conversational
- When unsure, ask for clarification
SOULEOF
    echo "  ✓ Created SOUL.md"
fi

if [ ! -f "$CONFIG_DIR/TOOLS.md" ]; then
    cat > "$CONFIG_DIR/TOOLS.md" << 'TOOLSEOF'
# Available Tools

## Information
- Answer general knowledge questions
- Provide weather information
- Look up facts and data

## Tasks
- Set reminders and alarms
- Create simple to-do items
- Schedule basic events

## Conversation
- General chat and small talk
- Language translation assistance
- Cultural context and explanations
TOOLSEOF
    echo "  ✓ Created TOOLS.md"
fi

echo "  ✓ Workspace ready at: $CONFIG_DIR"

# Step 4: Verify setup
echo ""
echo "[4/4] Verifying setup..."
echo "  Config dir: $CONFIG_DIR"
echo "  Files:"
ls -la "$CONFIG_DIR/" 2>/dev/null | grep -E "\.json|\.md" | while read line; do
    echo "    $line"
done

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Ensure Ollama is running: ollama serve"
echo "  2. Start the voice assistant: uvicorn src.api.main:app --reload"
echo "  3. ClawGo agent will connect to Ollama automatically"
echo ""
