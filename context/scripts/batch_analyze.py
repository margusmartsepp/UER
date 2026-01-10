#!/usr/bin/env python3
"""
Batch PDF Analysis for Hackathon Papers

Processes all papers in the papers directory and generates structured outputs.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from pdf_analyzer import PDFAnalyzer

# Paper metadata and priorities
PAPERS = {
    "sharma_2024_sycophancy.pdf": {
        "track": ["Track 1", "Track 3"],
        "priority": "high",
        "size": "1.4MB",
        "topic": "Sycophancy in Language Models",
    },
    "park_2024_ai_deception.pdf": {
        "track": ["Foundation"],
        "priority": "high",
        "size": "5.6MB",
        "topic": "AI Deception Survey",
    },
    "li_2024_wmdp_benchmark.pdf": {
        "track": ["Track 1"],
        "priority": "medium",
        "size": "900KB",
        "topic": "WMDP Benchmark - Measurement Framework",
    },
    "vanderweij_2024_sandbagging.pdf": {
        "track": ["Track 1"],
        "priority": "medium",
        "size": "1.6MB",
        "topic": "Strategic Underperformance Detection",
    },
    "tice_2024_noise_injection_replacement.pdf": {
        "track": ["Track 1"],
        "priority": "medium",
        "size": "2.1MB",
        "topic": "Noise Injection for Sandbagging Detection",
    },
    "openai_2025_monitoring_reasoning.pdf": {
        "track": ["Track 3"],
        "priority": "medium",
        "size": "4.0MB",
        "topic": "CoT Monitoring Mitigation",
    },
    "anthropic_2025_shortcuts_to_sabotage.pdf": {
        "track": ["Track 3"],
        "priority": "medium",
        "size": "3.8MB",
        "topic": "Emergent Misalignment",
    },
    "denison_2024_reward_hacking_generalization.pdf": {
        "track": ["Track 2"],
        "priority": "medium",
        "size": "9.2MB",
        "topic": "Reward Hacking Generalization",
        "use_rag": True,
    },
    "weng_2024_reward_hacking_blog.pdf": {
        "track": ["Track 2"],
        "priority": "medium",
        "size": "8.1MB",
        "topic": "Reward Hacking Survey",
        "use_rag": True,
    },
    "chen_2024_agentverse.pdf": {
        "track": ["Track 4"],
        "priority": "medium",
        "size": "4.5MB",
        "topic": "Multi-Agent Emergent Behavior",
    },
    "school_of_reward_hacks_2024.pdf": {
        "track": ["Track 4"],
        "priority": "medium",
        "size": "4.3MB",
        "topic": "Training-Induced Misalignment",
    },
    "stanford_2024_ai_index_report.pdf": {
        "track": ["Context"],
        "priority": "low",
        "size": "29MB",
        "topic": "AI Index Report - Safety Sections",
        "use_rag": True,
    },
}


def analyze_all_papers(papers_dir: str, output_dir: str):
    """Analyze all papers and generate structured outputs."""
    papers_path = Path(papers_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {"timestamp": datetime.now().isoformat(), "papers": {}}

    print("=" * 80)
    print("BATCH PDF ANALYSIS - HACKATHON PAPERS")
    print("=" * 80)
    print()

    for pdf_name, metadata in PAPERS.items():
        pdf_file = papers_path / pdf_name

        if not pdf_file.exists():
            print(f"⚠️  SKIPPED: {pdf_name} (not found)")
            continue

        print(f"\n{'=' * 80}")
        print(f"📄 {metadata['topic']}")
        print(f"   File: {pdf_name}")
        print(f"   Track: {', '.join(metadata['track'])}")
        print(f"   Priority: {metadata['priority'].upper()}")
        if metadata.get("use_rag"):
            print("   ⚡ Large file - RAG recommended")
        print(f"{'=' * 80}")

        try:
            analyzer = PDFAnalyzer(str(pdf_file))
            result = analyzer.analyze(str(output_path))

            # Add metadata to results
            results["papers"][pdf_name] = {
                "metadata": metadata,
                "analysis": {
                    "pages": result["metadata"]["pages"],
                    "word_count": result["stats"]["word_count"],
                    "chunk_count": result["stats"]["chunk_count"],
                },
                "status": "success",
            }

            print("\n✓ Analysis complete!")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            results["papers"][pdf_name] = {"metadata": metadata, "status": "error", "error": str(e)}

    # Save summary
    summary_file = output_path / "_analysis_summary.json"
    summary_file.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"\n{'=' * 80}")
    print("BATCH ANALYSIS COMPLETE")
    print(f"{'=' * 80}")
    print(f"\nSummary saved to: {summary_file}")
    print(
        f"\nProcessed {len([r for r in results['papers'].values() if r['status'] == 'success'])} papers successfully"
    )

    # Print statistics
    print("\n📊 STATISTICS:")
    total_words = sum(
        r["analysis"]["word_count"] for r in results["papers"].values() if r["status"] == "success"
    )
    total_chunks = sum(
        r["analysis"]["chunk_count"] for r in results["papers"].values() if r["status"] == "success"
    )
    print(f"   Total words: {total_words:,}")
    print(f"   Total chunks: {total_chunks:,}")

    # Papers requiring RAG
    rag_papers = [name for name, meta in PAPERS.items() if meta.get("use_rag")]
    print(f"\n⚡ Papers requiring RAG ({len(rag_papers)}):")
    for paper in rag_papers:
        print(f"   - {paper}")


def main():
    """CLI interface."""
    if len(sys.argv) < 3:
        print("Usage: python batch_analyze.py <papers_dir> <output_dir>")
        print("\nExample:")
        print("  python batch_analyze.py ../papers ../insights")
        sys.exit(1)

    papers_dir = sys.argv[1]
    output_dir = sys.argv[2]

    analyze_all_papers(papers_dir, output_dir)


if __name__ == "__main__":
    main()
