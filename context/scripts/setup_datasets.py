#!/usr/bin/env python3
"""
Setup script to download priority datasets for UER manipulation testing.

Usage:
    python setup_datasets.py [--all] [--wmdp] [--wildchat] [--eval-harness]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run shell command and return output."""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True


def download_wmdp(datasets_dir):
    """Download WMDP Benchmark."""
    print("\n=== Downloading WMDP Benchmark ===")
    wmdp_dir = datasets_dir / "wmdp"

    if wmdp_dir.exists():
        print("WMDP already exists. Skipping.")
        return True

    # Clone repo
    if not run_command(
        "git clone https://github.com/centerforaisafety/wmdp.git",
        cwd=datasets_dir
    ):
        return False

    # Install package
    print("Installing WMDP package...")
    if not run_command("pip install -e .", cwd=wmdp_dir):
        return False

    print("✓ WMDP Benchmark ready")
    return True


def download_wildchat_sample(datasets_dir):
    """Download WildChat sample (10k conversations)."""
    print("\n=== Downloading WildChat Sample ===")
    wildchat_dir = datasets_dir / "wildchat"
    wildchat_dir.mkdir(exist_ok=True)

    # Create download script
    download_script = wildchat_dir / "download.py"
    download_script.write_text("""
from datasets import load_dataset
import json

print("Loading WildChat dataset (this may take a few minutes)...")
dataset = load_dataset("allenai/WildChat", split="train", streaming=True)

print("Saving first 10,000 conversations...")
conversations = []
for i, conv in enumerate(dataset):
    if i >= 10000:
        break
    conversations.append(conv)
    if (i + 1) % 1000 == 0:
        print(f"  {i + 1} conversations loaded...")

with open("wildchat_sample_10k.json", "w") as f:
    json.dump(conversations, f, indent=2)

print(f"✓ Saved {len(conversations)} conversations to wildchat_sample_10k.json")
""")

    # Install datasets library
    print("Installing Hugging Face datasets...")
    if not run_command("pip install datasets"):
        return False

    # Run download
    print("Downloading conversations (this takes ~5 minutes)...")
    if not run_command(f"python {download_script}", cwd=wildchat_dir):
        return False

    print("✓ WildChat sample ready")
    return True


def download_eval_harness(datasets_dir):
    """Download lm-evaluation-harness."""
    print("\n=== Downloading lm-evaluation-harness ===")
    harness_dir = datasets_dir / "lm-evaluation-harness"

    if harness_dir.exists():
        print("lm-evaluation-harness already exists. Skipping.")
        return True

    # Clone repo
    if not run_command(
        "git clone https://github.com/EleutherAI/lm-evaluation-harness.git",
        cwd=datasets_dir
    ):
        return False

    # Install package
    print("Installing lm-evaluation-harness...")
    if not run_command("pip install -e .", cwd=harness_dir):
        return False

    print("✓ lm-evaluation-harness ready")
    return True


def download_school_of_reward_hacks(datasets_dir):
    """Download School of Reward Hacks dataset."""
    print("\n=== Downloading School of Reward Hacks ===")
    sorh_dir = datasets_dir / "school-of-reward-hacks"

    if sorh_dir.exists():
        print("School of Reward Hacks already exists. Skipping.")
        return True

    # Clone repo
    if not run_command(
        "git clone https://github.com/aypan17/reward-hacking.git school-of-reward-hacks",
        cwd=datasets_dir
    ):
        return False

    print("✓ School of Reward Hacks ready")
    return True


def main():
    parser = argparse.ArgumentParser(description="Download datasets for UER")
    parser.add_argument("--all", action="store_true", help="Download all datasets")
    parser.add_argument("--wmdp", action="store_true", help="Download WMDP Benchmark")
    parser.add_argument("--wildchat", action="store_true", help="Download WildChat sample")
    parser.add_argument("--eval-harness", action="store_true", help="Download lm-evaluation-harness")
    parser.add_argument("--sorh", action="store_true", help="Download School of Reward Hacks")

    args = parser.parse_args()

    # Default to priority datasets if no flags
    if not any([args.all, args.wmdp, args.wildchat, args.eval_harness, args.sorh]):
        print("No datasets specified. Downloading priority datasets (WMDP + eval-harness)...")
        args.wmdp = True
        args.eval_harness = True

    # Get datasets directory
    script_dir = Path(__file__).parent
    datasets_dir = script_dir.parent / "datasets"
    datasets_dir.mkdir(exist_ok=True)

    print(f"Datasets will be saved to: {datasets_dir.absolute()}")

    # Download selected datasets
    success = True

    if args.all or args.wmdp:
        success = download_wmdp(datasets_dir) and success

    if args.all or args.wildchat:
        success = download_wildchat_sample(datasets_dir) and success

    if args.all or args.eval_harness:
        success = download_eval_harness(datasets_dir) and success

    if args.all or args.sorh:
        success = download_school_of_reward_hacks(datasets_dir) and success

    if success:
        print("\n" + "="*50)
        print("✓ All requested datasets downloaded successfully!")
        print("="*50)
        print(f"\nDatasets location: {datasets_dir.absolute()}")
        print("\nNext steps:")
        print("  1. Run test scripts: python test_wmdp.py")
        print("  2. See usage examples: cat ../datasets/README.md")
    else:
        print("\n✗ Some datasets failed to download. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
