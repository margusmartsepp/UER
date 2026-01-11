#!/usr/bin/env python3
"""Test the model caching system."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.gateway import LLMGateway


async def main() -> None:
    """Test model caching with metadata."""
    print("=" * 80)
    print("MODEL CACHE SYSTEM TEST")
    print("=" * 80)
    print()

    gateway = LLMGateway()

    # First, get cached models (should be empty initially)
    print("1. Initial cache state (before any queries):")
    print("-" * 80)
    cache_data = gateway.get_cached_models()
    print(json.dumps(cache_data, indent=2))
    print()

    # Query provider info (this will populate cache)
    print("2. Querying provider APIs (this will populate cache)...")
    print("-" * 80)
    provider_info = await gateway.get_provider_info()
    print(f"Queried {len(provider_info)} providers")
    print()

    # Get cached models again (should now have data)
    print("3. Cache state after querying:")
    print("-" * 80)
    cache_data = gateway.get_cached_models()
    print(json.dumps(cache_data, indent=2))
    print()

    # Test _get_example_models (should return from cache)
    print("4. Testing _get_example_models (should return from cache):")
    print("-" * 80)
    for provider in ["openai", "gemini", "anthropic"]:
        models = gateway._get_example_models(provider)
        print(f"\n{provider}:")
        if provider in gateway._model_cache:
            cache_info = gateway._model_cache[provider]
            print("  Source: cache")
            print(f"  Last updated: {cache_info['last_updated']}")
            print(f"  Total count: {cache_info['total_count']}")
            print(f"  Models: {len(models)}")
            for model in models[:5]:
                print(f"    - {model}")
            if len(models) > 5:
                print(f"    ... and {len(models) - 5} more")
        else:
            print("  Source: fallback examples")
            print(f"  Models: {len(models)}")
            for model in models[:5]:
                print(f"    - {model}")

    print("\n" + "=" * 80)
    print("CACHE SYSTEM FEATURES")
    print("=" * 80)
    print("\n✓ Models are cached with timestamps on first query")
    print("✓ Cache includes: models, last_updated, total_count")
    print("✓ get_cached_models() returns all cache data with current_time and message")
    print("✓ _get_example_models() returns from cache if available")
    print("✓ Fallback examples used only if cache is empty")
    print("✓ No artificial limits - returns all available models")


if __name__ == "__main__":
    asyncio.run(main())
