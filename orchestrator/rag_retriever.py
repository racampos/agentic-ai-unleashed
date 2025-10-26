"""
RAG Retrieval System

Queries FAISS index to retrieve relevant documentation chunks.
"""

import pickle
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import faiss

from config.nim_config import get_embedding_client, get_embedding_config


class LabDocumentRetriever:
    """
    Retrieves relevant lab documentation chunks using FAISS similarity search.

    Usage:
        retriever = LabDocumentRetriever()
        results = retriever.retrieve("How do I configure an IP address?", k=3)
    """

    def __init__(
        self,
        index_dir: str = "data/faiss_index",
        index_name: str = "labs_index",
    ):
        self.index_dir = Path(index_dir)
        self.index_name = index_name

        # Load FAISS index
        index_path = self.index_dir / f"{index_name}.faiss"
        metadata_path = self.index_dir / f"{index_name}_metadata.pkl"

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}\n"
                f"Run rag_indexer.py first to build the index."
            )

        print(f"Loading FAISS index from: {index_path}")
        self.index = faiss.read_index(str(index_path))

        print(f"Loading metadata from: {metadata_path}")
        with open(metadata_path, "rb") as f:
            self.metadata = pickle.load(f)

        print(f"✓ Loaded index with {self.index.ntotal} vectors")

        # Initialize embedding client for query embedding
        self.embedding_client = get_embedding_client()
        self.embedding_config = get_embedding_config()

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query string.

        Args:
            query: User's question or search query

        Returns:
            NumPy array of embedding (shape: [1, embedding_dim])
        """
        response = self.embedding_client.embeddings.create(
            model=self.embedding_config["model"],
            input=[query],
            extra_body={"input_type": "query"}  # "query" for search queries
        )

        embedding = np.array([response.data[0].embedding], dtype=np.float32)
        return embedding

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter_lab: str = None
    ) -> List[Dict]:
        """
        Retrieve top-k most relevant document chunks for a query.

        Args:
            query: User's question or search query
            k: Number of results to return
            filter_lab: Optional lab_id to filter results (e.g., "01-basic-routing")

        Returns:
            List of dictionaries with keys:
                - content: The document chunk text
                - metadata: Lab metadata (source, lab_id, title, chunk_index)
                - score: Similarity score (lower is better for L2 distance)
        """
        # Generate query embedding
        query_embedding = self.embed_query(query)

        # Search FAISS index
        distances, indices = self.index.search(query_embedding, k * 2)  # Get extra for filtering

        # Retrieve metadata for results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue

            chunk_metadata = self.metadata[idx]

            # Apply lab filter if specified
            if filter_lab and chunk_metadata["metadata"]["lab_id"] != filter_lab:
                continue

            results.append({
                "content": chunk_metadata["content"],
                "metadata": chunk_metadata["metadata"],
                "score": float(distance),
            })

            # Stop once we have k results
            if len(results) >= k:
                break

        return results

    def retrieve_with_context(
        self,
        query: str,
        k: int = 3,
        filter_lab: str = None,
        context_window: int = 1
    ) -> List[Dict]:
        """
        Retrieve results with surrounding context chunks.

        Args:
            query: User's question
            k: Number of primary results
            filter_lab: Optional lab filter
            context_window: Number of chunks before/after to include

        Returns:
            List of result dictionaries with expanded context
        """
        # Get primary results
        results = self.retrieve(query, k, filter_lab)

        # TODO: Implement context expansion by fetching adjacent chunks
        # This would require storing chunk ordering in metadata
        # For now, just return primary results

        return results

    def retrieve_by_lab(self, lab_id: str, max_results: int = 10) -> List[Dict]:
        """
        Retrieve all chunks from a specific lab.

        Args:
            lab_id: Lab identifier (e.g., "01-basic-routing")
            max_results: Maximum chunks to return

        Returns:
            List of all chunks from that lab
        """
        results = []

        for idx, chunk_metadata in enumerate(self.metadata):
            if chunk_metadata["metadata"]["lab_id"] == lab_id:
                results.append({
                    "content": chunk_metadata["content"],
                    "metadata": chunk_metadata["metadata"],
                    "score": 0.0,  # Not based on similarity
                })

            if len(results) >= max_results:
                break

        return results

    def get_lab_list(self) -> List[Dict[str, str]]:
        """
        Get list of all indexed labs.

        Returns:
            List of dicts with lab_id and title
        """
        labs = {}

        for chunk_metadata in self.metadata:
            lab_id = chunk_metadata["metadata"]["lab_id"]
            title = chunk_metadata["metadata"]["title"]

            if lab_id not in labs:
                labs[lab_id] = title

        return [{"lab_id": lab_id, "title": title} for lab_id, title in labs.items()]


def main():
    """Test the retriever with sample queries."""
    retriever = LabDocumentRetriever()

    print("\n" + "=" * 60)
    print("Testing RAG Retriever")
    print("=" * 60)

    # Test query 1
    print("\nQuery 1: How do I configure an IP address on a router?")
    results = retriever.retrieve("How do I configure an IP address on a router?", k=3)

    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} (score: {result['score']:.4f}) ---")
        print(f"Lab: {result['metadata']['title']}")
        print(f"Source: {result['metadata']['filename']}")
        print(f"Content preview: {result['content'][:200]}...")

    # Test query 2
    print("\n" + "=" * 60)
    print("\nQuery 2: What is a static route?")
    results = retriever.retrieve("What is a static route?", k=3)

    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} (score: {result['score']:.4f}) ---")
        print(f"Lab: {result['metadata']['title']}")
        print(f"Content preview: {result['content'][:200]}...")

    # List all labs
    print("\n" + "=" * 60)
    print("\nAll indexed labs:")
    labs = retriever.get_lab_list()
    for lab in labs:
        print(f"  - {lab['lab_id']}: {lab['title']}")


if __name__ == "__main__":
    main()
