import json

from faiss_store import FAISSVectorStore


with open("embeddings.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

dimension = len(chunks[0]["embedding"])

store = FAISSVectorStore(dimension)

store.build(chunks)

store.statistics()

store.save(
    "vectorstore/indexes/faiss.index",
    "vectorstore/indexes/metadata.pkl"
)