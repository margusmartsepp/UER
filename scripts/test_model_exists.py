#!/usr/bin/env python3
"""Test the check_model_exists method for grounding."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.gateway import LLMGateway


async def main() -> None:
    """Test model existence checking."""
    gateway = LLMGateway()

    test_models = [
        # Valid models
        "openai/gpt-4o",
        "openai/o3-mini",
        "openai/gpt-5.2",
        # Invalid models
        "openai/gpt-4o-mega",
        "openai/llama4-8b",
        # Invalid format
        "gpt-4o",
        # Unconfigured provider
        "anthropic/claude-3-5-sonnet-20241022",
    ]

    print("=" * 80)
    print("MODEL EXISTENCE CHECKER - Grounding Test")
    print("=" * 80)
    print()

    for model in test_models:
        print(f"\nChecking: {model}")
        print("-" * 80)

        result = await gateway.check_model_exists(model)

        if result["exists"]:
            print("✓ EXISTS")
            print(f"  Provider: {result['provider']} ({result['provider_type']})")
            print(f"  Source: {result['source']}")
            print(f"  Total models available: {result['available_models_count']}")
        else:
            print("✗ DOES NOT EXIST")
            if "error" in result:
                print(f"  Error: {result['error']}")
            if "suggestion" in result and result["suggestion"]:
                print(f"  Suggestion: Try {result['suggestion']}")
            if "available_providers" in result:
                print(f"  Available providers: {', '.join(result['available_providers'])}")

    print("\n" + "=" * 80)
    print("GROUNDING USE CASE")
    print("=" * 80)
    print("\nThis method can be used to:")
    print("1. Verify model names before making API calls")
    print("2. Ground LLM responses with actual available models")
    print("3. Provide suggestions when models don't exist")
    print("4. Distinguish between live_query (actual) vs examples (fallback)")


if __name__ == "__main__":
    asyncio.run(main())
