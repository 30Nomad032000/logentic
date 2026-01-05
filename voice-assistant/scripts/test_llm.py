#!/usr/bin/env python3
"""
Qwen LLM Test Script
Test conversational AI with Qwen 2.5.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm import QwenLLM


def main():
    print("=" * 60)
    print("Qwen 2.5 LLM Test")
    print("=" * 60)

    # Initialize with 1.5B model (good balance of speed/quality)
    print("\n📌 Loading Qwen 2.5-1.5B-Instruct...")
    llm = QwenLLM(model_size="1.5b", device="cuda")

    # Test conversations
    test_inputs = [
        "Hello! How are you today?",
        "What's the weather usually like in Kerala?",
        "Can you help me set a reminder?",
        "Tell me a short joke.",
    ]

    print("\n" + "-" * 40)
    print("Testing Conversations")
    print("-" * 40)

    for user_input in test_inputs:
        print(f"\n👤 User: {user_input}")
        response = llm.chat(user_input)
        print(f"🤖 Assistant: {response.content}")
        print(f"   ⏱️  {response.generation_time_ms:.1f}ms | {response.tokens_used} tokens")

    # Test conversation memory
    print("\n" + "-" * 40)
    print("Testing Conversation Memory")
    print("-" * 40)

    llm.clear_history()

    print("\n👤 User: My name is Ebin.")
    response = llm.chat("My name is Ebin.")
    print(f"🤖 Assistant: {response.content}")

    print("\n👤 User: What's my name?")
    response = llm.chat("What's my name?")
    print(f"🤖 Assistant: {response.content}")

    # Interactive mode
    print("\n" + "=" * 60)
    print("Interactive Mode (type 'quit' to exit)")
    print("=" * 60)

    llm.clear_history()

    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                break
            if not user_input:
                continue

            response = llm.chat(user_input)
            print(f"🤖 Assistant: {response.content}")
            print(f"   ⏱️  {response.generation_time_ms:.1f}ms")

        except KeyboardInterrupt:
            break

    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()
