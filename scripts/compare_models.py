#!/usr/bin/env python3
"""Compare live API models with example models in gateway.py."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.gateway import LLMGateway


async def main() -> None:
    """Query APIs and compare with example models."""
    print("Querying provider APIs and comparing with examples...\n")

    gateway = LLMGateway()
    provider_info = await gateway.get_provider_info()

    print("=" * 80)
    print("MODEL COMPARISON: Live API vs Example Models")
    print("=" * 80)
    print()

    for provider, info in sorted(provider_info.items()):
        print(f"\n{'=' * 80}")
        print(f"PROVIDER: {provider.upper()}")
        print(f"{'=' * 80}")
        print(f"Type: {info['type']}")
        print(f"Source: {info['source']}")
        if "server_url" in info:
            print(f"Server: {info['server_url']}")

        # Get example models for comparison
        example_models = gateway._get_example_models(provider)
        live_models = info["available_models"]

        print(f"\nLive Models ({len(live_models)}):")
        for model in live_models[:15]:  # Show first 15
            marker = "✓" if model in example_models else "✗"
            print(f"  {marker} {model}")
        if len(live_models) > 15:
            print(f"  ... and {len(live_models) - 15} more")

        print(f"\nExample Models ({len(example_models)}):")
        for model in example_models:
            marker = "✓" if model in live_models else "✗"
            status = "IN LIVE" if model in live_models else "NOT IN LIVE"
            print(f"  {marker} {model} ({status})")

        # Calculate differences
        only_in_live = set(live_models) - set(example_models)
        only_in_examples = set(example_models) - set(live_models)
        in_both = set(live_models) & set(example_models)

        print("\nSTATISTICS:")
        print(f"  - In both: {len(in_both)}")
        print(f"  - Only in live: {len(only_in_live)}")
        print(f"  - Only in examples: {len(only_in_examples)}")

        if only_in_examples:
            print("\n  ⚠️  EXAMPLES NOT IN LIVE API:")
            for model in sorted(only_in_examples)[:5]:
                print(f"      - {model}")

        if info["source"] == "live_query" and only_in_live:
            print("\n  ℹ️  NEW MODELS IN LIVE (not in examples):")
            for model in sorted(only_in_live)[:5]:
                print(f"      - {model}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nProviders with live_query:")
    for provider, info in provider_info.items():
        if info["source"] == "live_query":
            print(f"  ✓ {provider} ({info['type']})")

    print("\nProviders using examples (API query failed or not implemented):")
    for provider, info in provider_info.items():
        if info["source"] == "examples":
            print(f"  ✗ {provider} ({info['type']})")


if __name__ == "__main__":
    asyncio.run(main())
