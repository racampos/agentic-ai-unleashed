#!/usr/bin/env python3
"""
Build FAISS index from lesson content for RAG retrieval.

This script:
1. Loads lesson content from markdown files in data/lessons/
2. Chunks the content into manageable pieces
3. Generates embeddings using NVIDIA NIM Embedding service
4. Builds a FAISS index for fast similarity search
5. Saves the index and metadata to data/faiss/

Usage:
    # From within the cluster (after embedding NIM is deployed)
    python scripts/build_faiss_index.py

    # From local machine (port-forward embedding NIM first)
    kubectl port-forward -n nim svc/embed-nim 8000:8000
    EMB_BASE_URL=http://localhost:8000/v1 python scripts/build_faiss_index.py
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any
import argparse

import numpy as np
import faiss
from openai import OpenAI


def load_lesson_chunks(lessons_dir: str) -> List[Dict[str, Any]]:
    """
    Load and chunk lesson content from markdown files.

    Args:
        lessons_dir: Directory containing lesson markdown files

    Returns:
        List of chunks with metadata
    """
    chunks = []
    lessons_path = Path(lessons_dir)

    if not lessons_path.exists():
        raise FileNotFoundError(f"Lessons directory not found: {lessons_dir}")

    # Process each markdown file
    for lesson_file in lessons_path.glob("*.md"):
        print(f"Processing {lesson_file.name}...")

        with open(lesson_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract metadata from filename (e.g., "01_bgp_basics.md")
        filename_parts = lesson_file.stem.split("_", 1)
        lesson_id = filename_parts[0] if len(filename_parts) > 0 else "unknown"
        lesson_name = filename_parts[1].replace("_", " ").title() if len(filename_parts) > 1 else lesson_file.stem

        # Simple chunking: split by sections (## headers)
        sections = content.split("\n## ")

        for i, section in enumerate(sections):
            if not section.strip():
                continue

            # First section may not have ## prefix
            if i == 0 and not section.startswith("#"):
                section_title = "Introduction"
                section_content = section
            else:
                lines = section.split("\n", 1)
                section_title = lines[0].strip("# ").strip()
                section_content = lines[1] if len(lines) > 1 else ""

            # Further chunk if section is too long (>1000 chars)
            if len(section_content) > 1000:
                # Split into smaller chunks at paragraph boundaries
                paragraphs = section_content.split("\n\n")
                current_chunk = ""

                for para in paragraphs:
                    if len(current_chunk) + len(para) > 1000 and current_chunk:
                        # Save current chunk
                        chunks.append({
                            "content": f"{section_title}\n\n{current_chunk.strip()}",
                            "lab_id": lesson_id,
                            "topic": lesson_name,
                            "section": section_title,
                            "source": lesson_file.name,
                        })
                        current_chunk = para + "\n\n"
                    else:
                        current_chunk += para + "\n\n"

                # Save remaining chunk
                if current_chunk.strip():
                    chunks.append({
                        "content": f"{section_title}\n\n{current_chunk.strip()}",
                        "lab_id": lesson_id,
                        "topic": lesson_name,
                        "section": section_title,
                        "source": lesson_file.name,
                    })
            else:
                # Section is small enough, keep as single chunk
                chunks.append({
                    "content": f"{section_title}\n\n{section_content.strip()}",
                    "lab_id": lesson_id,
                    "topic": lesson_name,
                    "section": section_title,
                    "source": lesson_file.name,
                })

    print(f"Loaded {len(chunks)} chunks from {len(list(lessons_path.glob('*.md')))} lesson files")
    return chunks


def generate_embeddings(chunks: List[Dict[str, Any]], embed_url: str) -> np.ndarray:
    """
    Generate embeddings for all chunks using NVIDIA NIM.

    Args:
        chunks: List of content chunks
        embed_url: Base URL for embedding service

    Returns:
        NumPy array of embeddings (shape: [num_chunks, embedding_dim])
    """
    print(f"Generating embeddings using {embed_url}...")

    client = OpenAI(
        base_url=embed_url,
        api_key="not-used"  # NIM doesn't require API key for embedding
    )

    embeddings = []
    batch_size = 10

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"Processing batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}...")

        # Get embeddings for batch
        texts = [chunk["content"] for chunk in batch]

        try:
            response = client.embeddings.create(
                model="nvidia/nv-embedqa-e5-v5",
                input=texts,
                encoding_format="float"
            )

            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

        except Exception as e:
            print(f"Error generating embeddings for batch {i // batch_size + 1}: {e}")
            raise

    embedding_matrix = np.array(embeddings, dtype='float32')
    print(f"Generated embeddings with shape: {embedding_matrix.shape}")

    return embedding_matrix


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build FAISS index for fast similarity search.

    Args:
        embeddings: NumPy array of embeddings

    Returns:
        FAISS index
    """
    print("Building FAISS index...")

    dimension = embeddings.shape[1]
    print(f"Embedding dimension: {dimension}")

    # Use IndexFlatIP (Inner Product) for cosine similarity
    # (after L2 normalization)
    index = faiss.IndexFlatIP(dimension)

    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)

    # Add embeddings to index
    index.add(embeddings)

    print(f"FAISS index built with {index.ntotal} vectors")

    return index


def save_index_and_metadata(
    index: faiss.Index,
    metadata: List[Dict[str, Any]],
    output_dir: str
):
    """
    Save FAISS index and metadata to disk.

    Args:
        index: FAISS index
        metadata: List of chunk metadata
        output_dir: Directory to save files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    index_file = output_path / "index.bin"
    metadata_file = output_path / "metadata.pkl"

    print(f"Saving FAISS index to {index_file}...")
    faiss.write_index(index, str(index_file))

    print(f"Saving metadata to {metadata_file}...")
    with open(metadata_file, "wb") as f:
        pickle.dump(metadata, f)

    print("✅ FAISS index and metadata saved successfully!")
    print(f"   Index: {index_file} ({index_file.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"   Metadata: {metadata_file} ({metadata_file.stat().st_size / 1024:.2f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Build FAISS index from lesson content")
    parser.add_argument(
        "--lessons-dir",
        default="data/lessons",
        help="Directory containing lesson markdown files (default: data/lessons)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/faiss",
        help="Directory to save FAISS index and metadata (default: data/faiss)"
    )
    parser.add_argument(
        "--embed-url",
        default=os.getenv("EMB_BASE_URL", "http://embed-nim.nim.svc.cluster.local:8000/v1"),
        help="Base URL for embedding service (default: cluster-internal service)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("FAISS Index Builder")
    print("=" * 60)
    print(f"Lessons directory: {args.lessons_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"Embedding service: {args.embed_url}")
    print("=" * 60)
    print()

    # Load and chunk lessons
    chunks = load_lesson_chunks(args.lessons_dir)

    if len(chunks) == 0:
        print("❌ No chunks found! Please add lesson content to data/lessons/")
        return 1

    # Generate embeddings
    embeddings = generate_embeddings(chunks, args.embed_url)

    # Build FAISS index
    index = build_faiss_index(embeddings)

    # Save everything
    save_index_and_metadata(index, chunks, args.output_dir)

    print()
    print("=" * 60)
    print("✅ FAISS index build complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
