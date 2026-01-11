#!/usr/bin/env python3
"""Seed the model cache by querying all configured provider APIs.

This script queries provider APIs and populates ~/.uer/model_cache.json
with actual available models and timestamps.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.gateway import LLMGateway


async def main() -> None:
    """Seed model cache from provider APIs."""
    print("=" * 80)
    print("SEEDING MODEL CACHE FROM PROVIDER APIs")
    print("=" * 80)
    print()

    gateway = LLMGateway()

    print(f"Cache file: {gateway._cache_file}")
    print()

    # Check initial cache state
    print("Initial cache state:")
    print("-" * 80)
    if gateway._cache_file.exists():
        print("✓ Cache file exists")
        cache_data = gateway.get_cached_models()
        print(f"  Providers cached: {len(cache_data['providers'])}")
        for provider, data in cache_data["providers"].items():
            print(
                f"    - {provider}: {data['total_count']} models, last updated: {data['last_updated']}"
            )
    else:
        print("✗ Cache file does not exist yet")
    print()

    # Query all providers (this will populate and save cache)
    print("Querying provider APIs...")
    print("-" * 80)
    provider_info = await gateway.get_provider_info()

    for provider, info in sorted(provider_info.items()):
        if info["source"] == "live_query":
            print(f"✓ {provider}: {len(info['available_models'])} models (live query)")
        else:
            print(f"✗ {provider}: using examples (no API query)")
    print()

    # Show final cache state
    print("Final cache state:")
    print("-" * 80)
    cache_data = gateway.get_cached_models()
    print(f"Cache file: {gateway._cache_file}")
    print(f"Providers cached: {len(cache_data['providers'])}")
    print()

    for provider, data in sorted(cache_data["providers"].items()):
        print(f"{provider}:")
        print(f"  Models: {data['total_count']}")
        print(f"  Last updated: {data['last_updated']}")
        print("  Sample models:")
        for model in data["models"][:3]:
            print(f"    - {model}")
        print()

    print("=" * 80)
    print("CACHE SEEDED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nCache saved to: {gateway._cache_file}")
    print("\nLLMs can now:")
    print("1. Check cache age via 'last_updated' timestamp")
    print("2. Decide if cache needs refresh based on age")
    print("3. Use llm_list_models to refresh cache")
    print("4. Trust cached data as ground truth")


if __name__ == "__main__":
    asyncio.run(main())
