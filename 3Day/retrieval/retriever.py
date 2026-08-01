"""
Retriever Module

Responsible for:

1. Query Embedding
2. Vector Search
3. Returning Relevant Chunks
"""

from embeddings.voyage_embedder import VoyageEmbedder
from vectorstore.faiss_store import FAISSVectorStore


class Retriever:

    def __init__(

            self,

            index_path,

            metadata_path,

            embedding_dimension

    ):

        self.embedder = VoyageEmbedder()

        self.store = FAISSVectorStore(

            embedding_dimension

        )

        self.store.load(

            index_path,

            metadata_path

        )

    ##########################################################

    def retrieve(

            self,

            question,

            top_k=5

    ):

        query_embedding = self.embedder.embed_text(

            question

        )

        results = self.store.search(

            query_embedding,

            top_k

        )

        return results