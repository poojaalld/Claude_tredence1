"""
FAISS Vector Store

This module provides a reusable wrapper around Facebook AI Similarity Search
(FAISS) for storing and retrieving document embeddings.

Author : Your Name
Project: Enterprise Banking RAG Assistant
"""

from __future__ import annotations

import os
import pickle
from typing import List, Dict, Any

import faiss
import numpy as np


class FAISSVectorStore:
    """
    Wrapper class for FAISS IndexFlatIP (Cosine Similarity)

    Attributes
    ----------
    dimension : int
        Embedding dimension.

    index : faiss.Index
        FAISS vector index.

    metadata : List[Dict]
        Metadata corresponding to every vector.
    """

    def __init__(self, dimension: int):

        self.dimension = dimension

        # Inner Product Index
        # (works as cosine after normalization)

        self.index = faiss.IndexFlatIP(dimension)

        self.metadata: List[Dict[str, Any]] = []

    ##################################################################
    # Utility
    ##################################################################

    @staticmethod
    def normalize(vector: np.ndarray) -> np.ndarray:
        """
        Normalize vectors for cosine similarity.
        """

        norm = np.linalg.norm(vector, axis=1, keepdims=True)

        return vector / norm

    ##################################################################
    # Build Index
    ##################################################################

    def build(self, embedded_chunks: List[Dict]) -> None:
        """
        Build FAISS index from embedded chunks.

        Parameters
        ----------
        embedded_chunks : List[Dict]
        """

        if len(embedded_chunks) == 0:
            raise ValueError("No embedded chunks found.")

        vectors = np.array(

            [chunk["embedding"] for chunk in embedded_chunks],

            dtype=np.float32

        )

        vectors = self.normalize(vectors)

        self.index.add(vectors)

        self.metadata = embedded_chunks

        print(f"Indexed {self.index.ntotal} vectors.")

    ##################################################################
    # Save
    ##################################################################

    def save(

        self,

        index_path: str,

        metadata_path: str

    ) -> None:

        os.makedirs(

            os.path.dirname(index_path),

            exist_ok=True

        )

        faiss.write_index(

            self.index,

            index_path

        )

        with open(

            metadata_path,

            "wb"

        ) as file:

            pickle.dump(

                self.metadata,

                file

            )

        print("FAISS index saved successfully.")

    ##################################################################
    # Load
    ##################################################################

    def load(

        self,

        index_path: str,

        metadata_path: str

    ) -> None:

        if not os.path.exists(index_path):
            raise FileNotFoundError(index_path)

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(metadata_path)

        self.index = faiss.read_index(index_path)

        with open(

            metadata_path,

            "rb"

        ) as file:

            self.metadata = pickle.load(file)

        print(

            f"Loaded {self.index.ntotal} vectors."

        )

    ##################################################################
    # Search
    ##################################################################

    def search(

        self,

        query_embedding: List[float],

        top_k: int = 5

    ) -> List[Dict]:

        vector = np.array(

            [query_embedding],

            dtype=np.float32

        )

        vector = self.normalize(vector)

        scores, indices = self.index.search(

            vector,

            top_k

        )

        results = []

        for score, idx in zip(

            scores[0],

            indices[0]

        ):

            if idx == -1:
                continue

            item = self.metadata[idx].copy()

            item["score"] = float(score)

            results.append(item)

        return results

    ##################################################################
    # Statistics
    ##################################################################

    def statistics(self):

        print()

        print("---------------")

        print("FAISS Statistics")

        print("---------------")

        print(f"Dimension : {self.dimension}")

        print(f"Vectors   : {self.index.ntotal}")

        print(f"Metadata  : {len(self.metadata)}")

        print()

    ##################################################################
    # Add New Document
    ##################################################################

    def add(

        self,

        embedding: List[float],

        metadata: Dict

    ):

        vector = np.array(

            [embedding],

            dtype=np.float32

        )

        vector = self.normalize(vector)

        self.index.add(vector)

        self.metadata.append(metadata)

    ##################################################################
    # Delete
    ##################################################################

    def clear(self):

        self.index.reset()

        self.metadata = []

        print("Index cleared.")