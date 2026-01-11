#!/usr/bin/env python3
"""Check what the top 10 sorted models are."""

import asyncio
import os

import httpx


async def main() -> None:
    """Query OpenAI API and show top 10 after sorting."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            data = response.json()

            # Filter for chat models
            models = [
                m["id"]
                for m in data.get("data", [])
                if "gpt" in m["id"].lower() or "o1" in m["id"].lower() or "o3" in m["id"].lower()
            ]

            print(f"Total filtered models: {len(models)}\n")

            # Sort reverse alphabetically (what the code does)
            sorted_models = sorted(models, reverse=True)

            print("Top 10 after sorted(models, reverse=True)[:10]:")
            print("=" * 80)
            for i, model in enumerate(sorted_models[:10], 1):
                print(f"{i:2}. {model}")

            print("\n" + "=" * 80)
            print("Where is gpt-4o?")
            print("=" * 80)
            gpt4o_index = sorted_models.index("gpt-4o") if "gpt-4o" in sorted_models else -1
            if gpt4o_index >= 0:
                print(f"gpt-4o is at position {gpt4o_index + 1} (not in top 10!)")
                print("\nModels around gpt-4o:")
                for i in range(max(0, gpt4o_index - 2), min(len(sorted_models), gpt4o_index + 3)):
                    marker = ">>>" if i == gpt4o_index else "   "
                    print(f"{marker} {i+1:2}. {sorted_models[i]}")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
