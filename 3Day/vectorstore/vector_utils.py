from embeddings.voyage_embedder import VoyageEmbedder


embedder = VoyageEmbedder()


def embed_query(query):

    return embedder.embed_text(query)