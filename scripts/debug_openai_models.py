#!/usr/bin/env python3
"""Debug script to see raw OpenAI models API response."""

import asyncio
import os

import httpx


async def main() -> None:
    """Query OpenAI API and show raw response."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return

    print("Querying OpenAI /v1/models endpoint...\n")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            data = response.json()

            print(f"Total models: {len(data.get('data', []))}\n")

            # Show all models
            print("ALL MODELS:")
            print("=" * 80)
            for model in data.get("data", []):
                model_id = model.get("id", "")
                owned_by = model.get("owned_by", "")
                print(f"  {model_id:50} (owned by: {owned_by})")

            print("\n" + "=" * 80)
            print("FILTERED MODELS (gpt, o1, o3 in name):")
            print("=" * 80)
            filtered = [
                m["id"]
                for m in data.get("data", [])
                if "gpt" in m["id"].lower() or "o1" in m["id"].lower() or "o3" in m["id"].lower()
            ]
            for model_id in sorted(filtered, reverse=True):
                print(f"  {model_id}")

            print(f"\nFiltered count: {len(filtered)}")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
