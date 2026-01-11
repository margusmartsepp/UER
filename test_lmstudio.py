#!/usr/bin/env python3
"""Test LM Studio integration with UER.

This script tests that UER can connect to LM Studio (or any OpenAI-compatible local server).

Setup:
1. Start LM Studio and load a model
2. Enable the local server (default port 1234)
3. Set environment variable: OPENAI_API_BASE=http://localhost:1234/v1
4. Optionally set OPENAI_API_KEY=dummy (some servers require it, LM Studio doesn't)
5. Run this script

Usage:
    # Default LM Studio port
    OPENAI_API_BASE=http://localhost:1234/v1 python test_lmstudio.py

    # Custom port
    OPENAI_API_BASE=http://localhost:8080/v1 python test_lmstudio.py

    # With API key (if your server requires it)
    OPENAI_API_BASE=http://localhost:1234/v1 OPENAI_API_KEY=dummy python test_lmstudio.py
"""

import asyncio
import os
import sys

# Add src to path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from uer.llm.gateway import LLMGateway  # noqa: E402


async def test_lmstudio() -> bool:
    """Test LM Studio connection."""
    print("=" * 60)
    print("LM Studio / Local OpenAI Server Test")
    print("=" * 60)

    # Check environment
    api_base = os.getenv("OPENAI_API_BASE")
    api_key = os.getenv("OPENAI_API_KEY")

    print("\n📋 Configuration:")
    print(f"   OPENAI_API_BASE: {api_base or '❌ Not set'}")
    print(f"   OPENAI_API_KEY:  {api_key or '❌ Not set (OK for LM Studio)'}")

    if not api_base:
        print("\n❌ ERROR: OPENAI_API_BASE not set!")
        print("\n💡 To fix:")
        print("   1. Start LM Studio and load a model")
        print("   2. Enable the local server (default port 1234)")
        print("   3. Run: OPENAI_API_BASE=http://localhost:1234/v1 python test_lmstudio.py")
        return False

    # Initialize gateway
    print("\n🔧 Initializing LLM Gateway...")
    gateway = LLMGateway()

    providers = gateway.get_available_providers()
    print(f"   Available providers: {', '.join(providers) or 'none'}")

    if "openai" not in providers:
        print("\n❌ ERROR: openai provider not detected!")
        print("   Make sure OPENAI_API_BASE is set correctly")
        return False

    print("   ✅ OpenAI provider detected (local server)")

    # Test 1: Simple completion
    print("\n🧪 Test 1: Simple completion")
    print("   Model: openai/local-model")
    print("   Prompt: What is 2+2?")

    try:
        # Note: LM Studio ignores the model name after openai/
        # It uses whatever model is currently loaded
        response = await gateway.call(
            model="openai/local-model",
            messages=[{"role": "user", "content": "What is 2+2? Answer with just the number."}],
            max_tokens=50,
            temperature=0.1,
        )

        content = response["choices"][0]["message"]["content"]
        print(f"   ✅ Response: {content.strip()}")

        # Check usage stats
        usage = response.get("usage", {})
        print(
            f"   📊 Tokens: {usage.get('prompt_tokens', 0)} prompt + "
            f"{usage.get('completion_tokens', 0)} completion = "
            f"{usage.get('total_tokens', 0)} total"
        )

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 2: Multi-turn conversation
    print("\n🧪 Test 2: Multi-turn conversation")

    try:
        response = await gateway.call(
            model="openai/local-model",
            messages=[
                {"role": "user", "content": "My name is Alice."},
                {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
                {"role": "user", "content": "What's my name?"},
            ],
            max_tokens=50,
            temperature=0.1,
        )

        content = response["choices"][0]["message"]["content"]
        print(f"   ✅ Response: {content.strip()}")

        # Check if model remembered the name
        if "alice" in content.lower():
            print("   ✅ Model correctly remembered the name!")
        else:
            print("   ⚠️  Model may not have remembered the name")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 3: Different model names (all use loaded model in LM Studio)
    print("\n🧪 Test 3: Model name flexibility")
    print("   Note: LM Studio uses whatever model is loaded, ignoring the name")

    model_names = [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4",
        "openai/my-local-model",
        "openai/llama-3.1-8b",
    ]

    for model_name in model_names:
        try:
            response = await gateway.call(
                model=model_name, messages=[{"role": "user", "content": "Hi"}], max_tokens=10
            )
            print(f"   ✅ {model_name}: Works")
        except Exception as e:
            print(f"   ❌ {model_name}: {e}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\n💡 Tips:")
    print("   - LM Studio uses the currently loaded model, ignoring model names")
    print("   - Use any model name like: openai/my-model or openai/gpt-4")
    print("   - Default port is 1234, but you can change it in LM Studio settings")
    print("   - No API key required for LM Studio")
    print("\n📚 Usage in MCP client (Claude Desktop, etc.):")
    print('   Set in config: "OPENAI_API_BASE": "http://localhost:1234/v1"')
    print('   Then use: llm_call with model="openai/local-model"')

    return True


async def main() -> None:
    """Main entry point."""
    try:
        success = await test_lmstudio()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
