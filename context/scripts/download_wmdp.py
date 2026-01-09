#!/usr/bin/env python3
"""
Download WMDP benchmark questions from Hugging Face.

Usage:
    python download_wmdp.py
"""

import json
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library not found.")
    print("Please install: pip install datasets")
    exit(1)


def download_wmdp():
    """Download WMDP benchmark from Hugging Face."""

    datasets_dir = Path(__file__).parent.parent / "datasets"
    wmdp_dir = datasets_dir / "wmdp_questions"
    wmdp_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Downloading WMDP Benchmark from Hugging Face")
    print("="*60)
    print(f"Saving to: {wmdp_dir.absolute()}\n")

    # Download each subset
    subsets = ["wmdp-bio", "wmdp-chem", "wmdp-cyber"]

    for subset in subsets:
        print(f"Downloading {subset}...")
        try:
            dataset = load_dataset("cais/wmdp", subset, split="test")

            # Save as JSON
            output_file = wmdp_dir / f"{subset}.json"
            dataset.to_json(output_file)

            print(f"  Saved {len(dataset)} questions to {output_file.name}")

        except Exception as e:
            print(f"  Error downloading {subset}: {e}")

    # Create summary
    print("\n" + "="*60)
    print("Download complete!")
    print("="*60)

    # Count total questions
    total = 0
    for subset_file in wmdp_dir.glob("*.json"):
        with open(subset_file) as f:
            data = json.load(f)
            total += len(data)
            print(f"  {subset_file.name}: {len(data)} questions")

    print(f"\nTotal: {total} questions")
    print(f"\nFiles saved in: {wmdp_dir.absolute()}")


if __name__ == "__main__":
    download_wmdp()
