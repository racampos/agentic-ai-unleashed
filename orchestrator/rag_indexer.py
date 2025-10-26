"""
RAG Indexing Pipeline

Loads lab documentation, chunks it, generates embeddings, and builds FAISS index.
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import faiss
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config.nim_config import get_embedding_client, get_embedding_config


class LabDocumentIndexer:
    """
    Indexes lab documentation for RAG retrieval.

    Pipeline:
    1. Load markdown files from data/labs/
    2. Chunk documents with overlap
    3. Generate embeddings using Embed NIM
    4. Build FAISS index
    5. Save index and metadata
    """

    def __init__(
        self,
        labs_dir: str = "data/labs",
        index_dir: str = "data/faiss_index",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        embedding_dim: int = 1024,  # nv-embedqa-e5-v5 dimension
    ):
        self.labs_dir = Path(labs_dir)
        self.index_dir = Path(index_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_dim = embedding_dim

        # Create index directory if needed
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedding client
        self.embedding_client = get_embedding_client()
        self.embedding_config = get_embedding_config()

        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
        )

    def load_lab_documents(self) -> List[Document]:
        """
        Load all markdown files from labs directory.

        Returns:
            List of LangChain Document objects with metadata
        """
        documents = []

        for md_file in self.labs_dir.glob("*.md"):
            print(f"Loading: {md_file.name}")

            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract lab metadata from filename and content
            lab_id = md_file.stem

            # Try to extract lab title from first heading
            title = lab_id
            for line in content.split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            doc = Document(
                page_content=content,
                metadata={
                    "source": str(md_file),
                    "lab_id": lab_id,
                    "title": title,
                    "filename": md_file.name,
                }
            )
            documents.append(doc)

        print(f"Loaded {len(documents)} lab documents")
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks with overlap.

        Args:
            documents: List of full lab documents

        Returns:
            List of chunked documents with preserved metadata
        """
        print(f"Chunking documents (chunk_size={self.chunk_size}, overlap={self.chunk_overlap})...")

        chunks = []
        for doc in documents:
            doc_chunks = self.text_splitter.split_documents([doc])

            # Add chunk index to metadata
            for i, chunk in enumerate(doc_chunks):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["total_chunks"] = len(doc_chunks)
                chunks.append(chunk)

        print(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks

    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a list of texts using Embed NIM.

        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process per API call

        Returns:
            NumPy array of embeddings (shape: [len(texts), embedding_dim])
        """
        print(f"Generating embeddings for {len(texts)} chunks...")

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"  Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

            response = self.embedding_client.embeddings.create(
                model=self.embedding_config["model"],
                input=batch,
                extra_body={"input_type": "passage"}  # "passage" for documents being indexed
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        embeddings_array = np.array(all_embeddings, dtype=np.float32)
        print(f"Generated embeddings: shape={embeddings_array.shape}")

        return embeddings_array

    def build_faiss_index(self, embeddings: np.ndarray) -> faiss.IndexFlatL2:
        """
        Build FAISS index from embeddings.

        Args:
            embeddings: NumPy array of embeddings

        Returns:
            FAISS index ready for similarity search
        """
        print(f"Building FAISS index...")

        # Use simple L2 (Euclidean distance) index
        # For production, consider IndexIVFFlat or IndexHNSWFlat for large datasets
        index = faiss.IndexFlatL2(self.embedding_dim)
        index.add(embeddings)

        print(f"FAISS index built: {index.ntotal} vectors")
        return index

    def save_index(
        self,
        index: faiss.IndexFlatL2,
        chunks: List[Document],
        index_name: str = "labs_index"
    ):
        """
        Save FAISS index and document metadata to disk.

        Args:
            index: FAISS index to save
            chunks: List of document chunks (for metadata)
            index_name: Base name for saved files
        """
        index_path = self.index_dir / f"{index_name}.faiss"
        metadata_path = self.index_dir / f"{index_name}_metadata.pkl"

        # Save FAISS index
        print(f"Saving FAISS index to: {index_path}")
        faiss.write_index(index, str(index_path))

        # Save metadata (chunks without embeddings)
        metadata = [
            {
                "content": chunk.page_content,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ]

        print(f"Saving metadata to: {metadata_path}")
        with open(metadata_path, "wb") as f:
            pickle.dump(metadata, f)

        print(f"✓ Index saved successfully")
        print(f"  - FAISS index: {index_path}")
        print(f"  - Metadata: {metadata_path}")

    def build_index(self, index_name: str = "labs_index"):
        """
        Complete indexing pipeline: load → chunk → embed → index → save.

        Args:
            index_name: Name for the saved index files
        """
        print("=" * 60)
        print("RAG INDEXING PIPELINE")
        print("=" * 60)

        # Step 1: Load documents
        documents = self.load_lab_documents()
        if not documents:
            raise ValueError(f"No markdown files found in {self.labs_dir}")

        # Step 2: Chunk documents
        chunks = self.chunk_documents(documents)

        # Step 3: Generate embeddings
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.generate_embeddings(texts)

        # Step 4: Build FAISS index
        index = self.build_faiss_index(embeddings)

        # Step 5: Save index and metadata
        self.save_index(index, chunks, index_name)

        print("=" * 60)
        print("INDEXING COMPLETE")
        print("=" * 60)

        return index, chunks


def main():
    """Run the indexing pipeline."""
    indexer = LabDocumentIndexer()
    indexer.build_index()


if __name__ == "__main__":
    main()
