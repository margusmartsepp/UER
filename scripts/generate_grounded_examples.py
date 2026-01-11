#!/usr/bin/env python3
"""Generate grounded example models from actual API queries.

This script queries all configured provider APIs and generates a grounded
examples dictionary with timestamps and metadata.
"""

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uer.llm.gateway import LLMGateway


async def main() -> None:
    """Query APIs and generate grounded examples."""
    print("Querying provider APIs to generate grounded examples...\n")

    gateway = LLMGateway()
    provider_info = await gateway.get_provider_info()

    # Prepare grounded examples
    grounded_examples = {
        "_metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "note": (
                "These examples were generated from actual API queries. "
                "Your knowledge cutoff may be older than this data. "
                "Use the current timestamp and generated_at to assess freshness. "
                "This is a cached view and may become deprecated - always prefer "
                "querying llm_list_models or check_model_exists for live data."
            ),
        }
    }

    print("=" * 80)
    print("GROUNDED EXAMPLES FROM LIVE API QUERIES")
    print("=" * 80)
    print(f"Generated at: {grounded_examples['_metadata']['generated_at']}")
    print()

    for provider, info in sorted(provider_info.items()):
        if info["source"] == "live_query":
            # Use live query data
            models = info["available_models"][:10]  # Top 10 for examples
            grounded_examples[provider] = {
                "models": models,
                "source": "live_query",
                "queried_at": grounded_examples["_metadata"]["generated_at"],
                "total_available": len(info["available_models"]),
            }

            print(f"✓ {provider.upper()} (live_query)")
            print(f"  Total available: {len(info['available_models'])}")
            print("  Top 10 for examples:")
            for model in models:
                print(f"    - {model}")
            print()
        else:
            print(f"✗ {provider.upper()} (using fallback examples - no live query)")
            print()

    # Generate Python code for _get_example_models
    print("=" * 80)
    print("GENERATED CODE FOR _get_example_models()")
    print("=" * 80)
    print()
    print("```python")
    print("def _get_example_models(self, provider: str) -> list[str]:")
    print('    """Get example model names for a provider.')
    print("    ")
    print("    These examples are grounded in actual API queries.")
    print(f"    Generated at: {grounded_examples['_metadata']['generated_at']}")
    print("    ")
    print("    IMPORTANT: This is a cached view and may be deprecated.")
    print("    Always prefer querying llm_list_models or check_model_exists for live data.")
    print("    ")
    print("    Args:")
    print("        provider: Provider name (e.g., 'openai', 'anthropic')")
    print("    ")
    print("    Returns:")
    print("        List of example model identifiers")
    print('    """')
    print("    # Grounded examples from live API queries")
    print(f"    # Generated: {grounded_examples['_metadata']['generated_at']}")
    print("    # Note: Your knowledge cutoff may be older than this data")
    print("    # This is a cached view - query llm_list_models for current data")
    print("    examples = {")

    for provider, data in sorted(grounded_examples.items()):
        if provider == "_metadata":
            continue
        print(f'        "{provider}": [')
        for model in data["models"]:
            print(f'            "{model}",')
        print(f'        ],  # {data["source"]}, {data["total_available"]} total')

    print("    }")
    print("    ")
    print('    return examples.get(provider, [f"{provider}/model-name"])')
    print("```")

    # Save to file
    output_file = Path(__file__).parent / "grounded_examples.json"
    with open(output_file, "w") as f:
        json.dump(grounded_examples, f, indent=2)

    print()
    print(f"\nSaved grounded examples to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
