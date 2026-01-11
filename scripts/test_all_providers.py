#!/usr/bin/env python3
"""Test that all providers can query and cache models."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.gateway import LLMGateway


async def main() -> None:
    """Test all provider model queries."""
    print("=" * 80)
    print("ALL PROVIDERS MODEL QUERY TEST")
    print("=" * 80)
    print()

    gateway = LLMGateway()

    print("Configured providers:")
    for provider in gateway.available_providers:
        print(f"  - {provider}")
    print()

    print("=" * 80)
    print("QUERYING PROVIDER APIs")
    print("=" * 80)
    print()

    # Get provider info (this will query all APIs)
    provider_info = await gateway.get_provider_info()

    for provider, info in sorted(provider_info.items()):
        print(f"\n{provider.upper()}")
        print("-" * 80)
        print(f"Type: {info['type']}")
        print(f"Source: {info['source']}")
        print(f"Models: {len(info['available_models'])}")

        if info["source"] == "live_query":
            print("✓ Successfully queried API and cached models")
            if info["available_models"]:
                print(f"Sample models:")
                for model in info["available_models"][:3]:
                    print(f"  - {model}")
        else:
            print("⚠ Using fallback examples (API query failed or no API key)")

    print("\n" + "=" * 80)
    print("CACHE STATUS")
    print("=" * 80)
    print()

    cache_data = gateway.get_cached_models()
    print(f"Cache file: {gateway._cache_file}")
    print(f"Providers cached: {len(cache_data['providers'])}")
    print()

    for provider, data in sorted(cache_data["providers"].items()):
        print(f"{provider}:")
        print(f"  Models: {data['total_count']}")
        print(f"  Last updated: {data['last_updated']}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    live_query_count = sum(
        1 for info in provider_info.values() if info["source"] == "live_query"
    )
    total_providers = len(provider_info)

    print(f"Total providers: {total_providers}")
    print(f"Live query success: {live_query_count}/{total_providers}")
    print(f"Cached providers: {len(cache_data['providers'])}")

    if live_query_count == total_providers:
        print("\n✓ All providers successfully queried and cached!")
    else:
        print(
            f"\n⚠ {total_providers - live_query_count} provider(s) using fallback examples"
        )
        print("  (This is expected if API keys are not configured)")


if __name__ == "__main__":
    asyncio.run(main())
