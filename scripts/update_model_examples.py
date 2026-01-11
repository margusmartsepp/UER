#!/usr/bin/env python3
"""Query actual models from provider APIs and update gateway examples.

This script queries live APIs to get actual available models and updates
the example models in gateway.py with grounded, real data.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.gateway import LLMGateway


async def main() -> None:
    """Query APIs and display actual available models."""
    print("Querying provider APIs for actual available models...\n")

    gateway = LLMGateway()
    provider_info = await gateway.get_provider_info()

    print("=" * 80)
    print("ACTUAL AVAILABLE MODELS (from live API queries)")
    print("=" * 80)
    print()

    for provider, info in provider_info.items():
        print(f"## {provider.upper()}")
        print(f"   Type: {info['type']}")
        print(f"   Source: {info['source']}")
        if "server_url" in info:
            print(f"   Server: {info['server_url']}")
        print(f"   Models ({len(info['available_models'])}):")
        for model in info["available_models"][:10]:  # Show first 10
            print(f"      - {model}")
        if len(info["available_models"]) > 10:
            print(f"      ... and {len(info['available_models']) - 10} more")
        print()

    print("=" * 80)
    print("\nTo update gateway.py examples:")
    print("1. Review the models above marked as 'live_query'")
    print("2. Manually update _get_example_models() in src/uer/llm/gateway.py")
    print("3. Only use models that came from live_query, not examples")
    print("4. Keep examples conservative - only well-known, stable models")
    print("\nNOTE: This script shows what's actually available right now.")
    print("Examples should be updated based on this grounded data.")


if __name__ == "__main__":
    asyncio.run(main())
