#!/usr/bin/env python3
"""
PDF Analysis Tool for Hackathon Papers

Extracts text from PDFs, chunks content, and prepares for analysis.
Can be used standalone or integrated with UER's storage system.
"""

import json
import sys
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Install with: pip install PyPDF2")
    sys.exit(1)


class PDFAnalyzer:
    """Analyze PDF papers and extract structured content."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

    def extract_text(self) -> str:
        """Extract all text from PDF."""
        text = []
        with open(self.pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text.append(page.extract_text())
        return "\n\n".join(text)

    def extract_metadata(self) -> dict:
        """Extract PDF metadata."""
        with open(self.pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            metadata = reader.metadata
            return {
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
                "pages": len(reader.pages),
                "file_size": self.pdf_path.stat().st_size,
                "file_name": self.pdf_path.name,
            }

    def chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> list[dict]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Full text to chunk
            chunk_size: Target characters per chunk
            overlap: Overlap between chunks

        Returns:
            List of chunks with metadata
        """
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind(".")
                last_newline = chunk_text.rfind("\n\n")
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.7:  # At least 70% of chunk size
                    end = start + break_point + 1
                    chunk_text = text[start:end]

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": chunk_text.strip(),
                    "start_char": start,
                    "end_char": end,
                    "length": len(chunk_text),
                }
            )

            chunk_id += 1
            start = end - overlap

        return chunks

    def analyze(self, output_dir: str | None = None) -> dict:
        """
        Full analysis: extract text, metadata, and chunks.

        Args:
            output_dir: Optional directory to save outputs

        Returns:
            Analysis results dictionary
        """
        print(f"Analyzing: {self.pdf_path.name}")

        # Extract metadata
        metadata = self.extract_metadata()
        print(f"  Pages: {metadata['pages']}, Size: {metadata['file_size'] / 1024 / 1024:.1f}MB")

        # Extract text
        print("  Extracting text...")
        text = self.extract_text()
        word_count = len(text.split())
        print(f"  Extracted {word_count:,} words")

        # Chunk text
        print("  Chunking text...")
        chunks = self.chunk_text(text)
        print(f"  Created {len(chunks)} chunks")

        result = {
            "metadata": metadata,
            "text": text,
            "chunks": chunks,
            "stats": {
                "word_count": word_count,
                "char_count": len(text),
                "chunk_count": len(chunks),
            },
        }

        # Save outputs if requested
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            base_name = self.pdf_path.stem

            # Save full text
            text_file = output_path / f"{base_name}_text.txt"
            text_file.write_text(text, encoding="utf-8")
            print(f"  Saved text: {text_file}")

            # Save chunks
            chunks_file = output_path / f"{base_name}_chunks.json"
            chunks_file.write_text(json.dumps(chunks, indent=2), encoding="utf-8")
            print(f"  Saved chunks: {chunks_file}")

            # Save metadata
            meta_file = output_path / f"{base_name}_metadata.json"
            meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            print(f"  Saved metadata: {meta_file}")

        return result


def main():
    """CLI interface for PDF analysis."""
    if len(sys.argv) < 2:
        print("Usage: python pdf_analyzer.py <pdf_path> [output_dir]")
        print("\nExample:")
        print("  python pdf_analyzer.py ../papers/sharma_2024_sycophancy.pdf ../insights/")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    analyzer = PDFAnalyzer(pdf_path)
    result = analyzer.analyze(output_dir)

    print("\n✓ Analysis complete!")
    print(f"  Words: {result['stats']['word_count']:,}")
    print(f"  Chunks: {result['stats']['chunk_count']}")


if __name__ == "__main__":
    main()
