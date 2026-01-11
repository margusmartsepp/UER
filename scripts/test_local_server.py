#!/usr/bin/env python3
"""Test local OpenAI-compatible server routing (LM Studio, Ollama)."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.gateway import LLMGateway


async def test_local_server() -> None:
    """Test that local server calls are routed correctly."""
    print("=" * 80)
    print("LOCAL SERVER ROUTING TEST")
    print("=" * 80)
    print()

    # Check if OPENAI_API_BASE is set
    api_base = os.getenv("OPENAI_API_BASE")
    if not api_base:
        print("⚠ OPENAI_API_BASE not set")
        print("  To test local server routing, set:")
        print("  export OPENAI_API_BASE=http://localhost:1234/v1")
        print()
        return

    print(f"OPENAI_API_BASE: {api_base}")
    print()

    gateway = LLMGateway()

    # Get available models
    print("Querying available models...")
    provider_info = await gateway.get_provider_info()

    if "openai" not in provider_info:
        print("✗ OpenAI provider not detected")
        return

    info = provider_info["openai"]
    print(f"Provider type: {info['type']}")
    print(f"Source: {info['source']}")
    print(f"Available models: {len(info['available_models'])}")

    if info["type"] == "local" and "server_url" in info:
        print(f"Server URL: {info['server_url']}")
        print("✓ Local server detected")
    else:
        print("⚠ Not detected as local server")

    if not info["available_models"]:
        print("\n✗ No models available")
        print("  Make sure your local server (LM Studio, etc.) is running")
        return

    print("\nAvailable models:")
    for model in info["available_models"][:5]:
        print(f"  - {model}")

    # Test calling a model
    print("\n" + "=" * 80)
    print("TEST CALL")
    print("=" * 80)
    print()

    test_model = info["available_models"][0]
    print(f"Testing model: {test_model}")
    print(f"Request will be routed to: {api_base}")
    print()

    try:
        response = await gateway.call(
            model=test_model,
            messages=[{"role": "user", "content": "Say 'Hello from local server!'"}],
            max_tokens=50,
            temperature=0.7,
        )

        print("✓ Call successful!")
        print(f"\nResponse:")
        if "choices" in response and response["choices"]:
            content = response["choices"][0]["message"]["content"]
            print(f"  {content}")
        print(f"\nModel used: {response.get('model', 'unknown')}")
        print(f"Tokens: {response.get('usage', {})}")

    except Exception as e:
        print(f"✗ Call failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure your local server is running")
        print(f"2. Verify the server is accessible at: {api_base}")
        print("3. Check that the model is loaded in your local server")


async def test_configuration() -> None:
    """Test configuration display."""
    print("\n" + "=" * 80)
    print("CONFIGURATION")
    print("=" * 80)
    print()

    print("Environment variables:")
    print(f"  OPENAI_API_BASE: {os.getenv('OPENAI_API_BASE', 'not set')}")
    print(f"  OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
    print(f"  OLLAMA_API_BASE: {os.getenv('OLLAMA_API_BASE', 'not set (default: http://localhost:11434/v1)')}")
    print()

    print("How LiteLLM routing works:")
    print("1. If OPENAI_API_BASE is set:")
    print("   - LiteLLM will route openai/* calls to that URL")
    print("   - Example: openai/meta-llama-3.1-8b-instruct -> http://localhost:1234/v1")
    print()
    print("2. If OLLAMA_API_BASE is set:")
    print("   - LiteLLM will route ollama/* calls to that URL")
    print("   - Example: ollama/llama2 -> http://localhost:11434/v1")
    print()
    print("3. Without custom base URLs:")
    print("   - openai/* routes to api.openai.com (requires OPENAI_API_KEY)")
    print("   - ollama/* routes to localhost:11434 (default)")


async def main() -> None:
    """Run all tests."""
    await test_local_server()
    await test_configuration()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    api_base = os.getenv("OPENAI_API_BASE")
    if api_base:
        print(f"✓ Local server configured: {api_base}")
        print("✓ LiteLLM will route openai/* calls to your local server")
    else:
        print("⚠ No local server configured")
        print("  Set OPENAI_API_BASE to use LM Studio or other local servers")


if __name__ == "__main__":
    asyncio.run(main())
