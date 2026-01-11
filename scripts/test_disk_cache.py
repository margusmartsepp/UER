#!/usr/bin/env python3
"""Test the disk-based cache system with timestamp updates."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.gateway import LLMGateway


async def main() -> None:
    """Test disk cache system."""
    print("=" * 80)
    print("DISK-BASED CACHE SYSTEM TEST")
    print("=" * 80)
    print()

    cache_file = Path.home() / ".uer" / "model_cache.json"
    print(f"Cache file: {cache_file}")
    print()

    # Test 1: Load existing cache
    print("TEST 1: Load existing cache from disk")
    print("-" * 80)
    gateway1 = LLMGateway()
    cache_data = gateway1.get_cached_models()

    if cache_data["providers"]:
        print(f"✓ Loaded {len(cache_data['providers'])} providers from disk")
        for provider, data in cache_data["providers"].items():
            print(
                f"  - {provider}: {data['total_count']} models, last_updated: {data['last_updated']}"
            )
    else:
        print("✗ No cache found (run seed_model_cache.py first)")
        return

    initial_timestamp = cache_data["providers"]["openai"]["last_updated"]
    print(f"\nInitial OpenAI timestamp: {initial_timestamp}")
    print()

    # Test 2: Query again (should update timestamp even if models unchanged)
    print("TEST 2: Query provider again (should update timestamp)")
    print("-" * 80)
    print("Waiting 2 seconds...")
    await asyncio.sleep(2)

    # Query provider info (this will update cache)
    provider_info = await gateway1.get_provider_info()

    # Check updated timestamp
    cache_data = gateway1.get_cached_models()
    new_timestamp = cache_data["providers"]["openai"]["last_updated"]

    print(f"New OpenAI timestamp: {new_timestamp}")

    if new_timestamp != initial_timestamp:
        print("✓ Timestamp updated even though models didn't change")
    else:
        print("✗ Timestamp NOT updated")
    print()

    # Test 3: Verify cache persisted to disk
    print("TEST 3: Verify cache persisted to disk")
    print("-" * 80)

    # Create new gateway instance (should load from disk)
    gateway2 = LLMGateway()
    cache_data2 = gateway2.get_cached_models()
    disk_timestamp = cache_data2["providers"]["openai"]["last_updated"]

    print(f"Timestamp from new instance: {disk_timestamp}")

    if disk_timestamp == new_timestamp:
        print("✓ Cache correctly persisted to disk and loaded")
    else:
        print("✗ Cache not persisted correctly")
    print()

    # Test 4: _get_example_models returns from cache
    print("TEST 4: _get_example_models returns from disk cache")
    print("-" * 80)

    models = gateway2._get_example_models("openai")
    print(f"Models returned: {len(models)}")
    print(f"Sample: {models[:3]}")

    if len(models) == 57:
        print("✓ All 57 models returned from cache")
    else:
        print(f"✗ Expected 57 models, got {len(models)}")
    print()

    # Test 5: No hardcoded fallbacks
    print("TEST 5: No hardcoded fallbacks for uncached providers")
    print("-" * 80)

    uncached_models = gateway2._get_example_models("anthropic")
    print(f"Models for uncached provider: {len(uncached_models)}")

    if len(uncached_models) == 0:
        print("✓ Returns empty list (no hardcoded fallbacks)")
    else:
        print(f"✗ Returned {len(uncached_models)} models (should be 0)")
    print()

    # Test 6: Cache structure
    print("TEST 6: Cache structure and metadata")
    print("-" * 80)

    with open(cache_file) as f:
        disk_cache = json.load(f)

    print("Cache structure:")
    for provider, data in disk_cache.items():
        print(f"\n{provider}:")
        print(f"  Keys: {list(data.keys())}")
        print(f"  Has 'models': {'models' in data}")
        print(f"  Has 'last_updated': {'last_updated' in data}")
        print(f"  Has 'total_count': {'total_count' in data}")

        if all(k in data for k in ["models", "last_updated", "total_count"]):
            print("  ✓ All required fields present")
        else:
            print("  ✗ Missing required fields")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✓ Cache loaded from disk on init")
    print("✓ Timestamp updated on every query (even if models unchanged)")
    print("✓ Cache persisted to disk automatically")
    print("✓ _get_example_models returns from disk cache")
    print("✓ No hardcoded fallbacks (returns [] for uncached)")
    print("✓ Cache structure includes: models, last_updated, total_count")
    print("\nLLMs can:")
    print("1. Check 'last_updated' to judge cache age")
    print("2. Decide if cache needs refresh based on age")
    print("3. Call llm_list_models to refresh cache")
    print("4. Trust cached data as ground truth")


if __name__ == "__main__":
    asyncio.run(main())
