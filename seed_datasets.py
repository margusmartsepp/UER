#!/usr/bin/env python3
"""
Seed datasets for UER hackathon project.

This script downloads all necessary datasets for manipulation detection:
- WMDP Benchmark (3,668 questions)
- WildChat (10k conversation sample)
- lm-evaluation-harness (evaluation framework)

Usage:
    uv run seed_datasets.py
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run command and return success status."""
    print(f"  Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"  [ERROR] {result.stderr}")
        if check:
            return False

    if result.stdout and result.stdout.strip():
        print(f"  {result.stdout.strip()}")
    return True


def setup_directories():
    """Create necessary directories."""
    print("\n[STEP 1/5] Setting up directories...")

    datasets_dir = Path("context/datasets")
    dirs_to_create = [
        datasets_dir / "wmdp_questions",
        datasets_dir / "wildchat",
        datasets_dir / "results",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")

    print("  [OK] Directories ready")
    return datasets_dir


def install_dependencies():
    """Install Python dependencies with uv."""
    print("\n[STEP 2/5] Installing dependencies with uv...")

    if not run_command("uv pip install datasets huggingface-hub"):
        return False

    print("  [OK] Dependencies installed")
    return True


def download_wmdp(datasets_dir):
    """Download WMDP benchmark."""
    print("\n[STEP 3/5] Downloading WMDP Benchmark...")

    wmdp_dir = datasets_dir / "wmdp_questions"

    try:
        from datasets import load_dataset
    except ImportError:
        print("  [ERROR] datasets library not found")
        return False

    subsets = ["wmdp-bio", "wmdp-chem", "wmdp-cyber"]
    total_questions = 0

    for subset in subsets:
        print(f"  Downloading {subset}...")
        try:
            dataset = load_dataset("cais/wmdp", subset, split="test")
            output_file = wmdp_dir / f"{subset}.json"
            dataset.to_json(output_file)
            total_questions += len(dataset)
            print(f"    Saved {len(dataset)} questions")
        except Exception as e:
            print(f"    [ERROR] {e}")
            return False

    print(f"  [OK] WMDP downloaded: {total_questions} total questions")
    return True


def download_wildchat(datasets_dir):
    """Download WildChat sample."""
    print("\n[STEP 4/5] Downloading WildChat sample (10k conversations)...")
    print("  This may take 5-10 minutes...")

    wildchat_dir = datasets_dir / "wildchat"
    output_file = wildchat_dir / "wildchat_sample_10k.json"

    try:
        from datasets import load_dataset

        print("  Loading dataset...")
        dataset = load_dataset("allenai/WildChat", split="train", streaming=True)

        conversations = []
        for i, conv in enumerate(dataset):
            if i >= 10000:
                break
            conversations.append(conv)
            if (i + 1) % 2000 == 0:
                print(f"    {i + 1}/10000 conversations...")

        print(f"  Saving to {output_file.name}...")

        def json_serializer(obj):
            """Custom JSON serializer for datetime objects."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, indent=2, default=json_serializer)

        size_mb = output_file.stat().st_size / 1024 / 1024
        print(f"  [OK] WildChat downloaded: {len(conversations)} conversations ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def clone_eval_harness(datasets_dir):
    """Clone lm-evaluation-harness repository."""
    print("\n[STEP 5/5] Cloning lm-evaluation-harness...")

    harness_dir = datasets_dir / "lm-evaluation-harness"

    if harness_dir.exists():
        print("  [SKIP] Already exists")
        return True

    if not run_command(
        "git clone https://github.com/EleutherAI/lm-evaluation-harness.git",
        cwd=datasets_dir
    ):
        return False

    print("  [OK] lm-evaluation-harness cloned")
    return True


def print_summary(datasets_dir):
    """Print summary of downloaded datasets."""
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)

    # Count WMDP files
    wmdp_files = list((datasets_dir / "wmdp_questions").glob("*.json"))
    print(f"\nWMDP Benchmark: {len(wmdp_files)} files")
    for f in wmdp_files:
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name}: {size_kb:.0f} KB")

    # Check WildChat
    wildchat_file = datasets_dir / "wildchat" / "wildchat_sample_10k.json"
    if wildchat_file.exists():
        size_mb = wildchat_file.stat().st_size / 1024 / 1024
        print(f"\nWildChat: {size_mb:.1f} MB")
    else:
        print("\nWildChat: [MISSING]")

    # Check eval harness
    harness_dir = datasets_dir / "lm-evaluation-harness"
    if harness_dir.exists():
        print(f"\nlm-evaluation-harness: installed")
    else:
        print(f"\nlm-evaluation-harness: [MISSING]")

    print("\n" + "="*60)
    print("Next steps:")
    print("  1. Test sandbagging:  cd context/scripts && python test_wmdp.py --limit 10")
    print("  2. Test sycophancy:   python test_sycophancy.py")
    print("="*60)


def main():
    """Main setup function."""
    print("="*60)
    print("UER Dataset Setup")
    print("="*60)

    # Run setup steps
    datasets_dir = setup_directories()

    if not install_dependencies():
        print("\n[FAILED] Dependency installation failed")
        sys.exit(1)

    if not download_wmdp(datasets_dir):
        print("\n[FAILED] WMDP download failed")
        sys.exit(1)

    if not download_wildchat(datasets_dir):
        print("\n[FAILED] WildChat download failed")
        sys.exit(1)

    if not clone_eval_harness(datasets_dir):
        print("\n[FAILED] eval-harness clone failed")
        sys.exit(1)

    # Print summary
    print_summary(datasets_dir)


if __name__ == "__main__":
    main()
