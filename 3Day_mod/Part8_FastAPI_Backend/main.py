"""
FastAPI backend for the Banking KB RAG Assistant.

Exposes Part 7's answer_question() over HTTP so Part 9's Streamlit frontend
(or any other client) never needs direct access to the embedding provider,
vector store, or Claude credentials -- only this service does.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8000
    # or: python main.py
"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Part6_Retriever"))
sys.path.insert(0, str(PROJECT_ROOT / "Part7_Claude_RAG_Pipeline"))

from rag_pipeline import answer_question
from retriever import warm_up
from shared import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the FAISS index once at startup: fails fast on a missing/corrupt
    # index instead of on a user's first request, and the first real query
    # doesn't pay the disk-read cost.
    warm_up()
    yield


app = FastAPI(
    title="Banking KB RAG Assistant",
    description=(
        "Answers questions about the Enterprise Digital Banking Platform "
        "from its internal documentation (BRD, SRS, HLD/LLD, ADRs, security "
        "guidelines, and more), with citations back to source documents."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The user's question.")
    top_k: int | None = Field(
        None, gt=0, description="Number of chunks to retrieve; defaults to shared/config.py's TOP_K."
    )


class Source(BaseModel):
    number: int
    source_file: str
    heading_path: str
    score: float


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[Source]


class HealthResponse(BaseModel):
    status: str
    vector_store: str
    embedding_provider: str
    claude_model: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        vector_store=config.VECTOR_STORE,
        embedding_provider=config.EMBEDDING_PROVIDER,
        claude_model=config.CLAUDE_MODEL,
    )


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    try:
        result = answer_question(request.query, top_k=request.top_k)
    except RuntimeError as exc:
        # e.g. a missing ANTHROPIC_API_KEY / embedding key -- a server
        # configuration problem, not something the caller can fix by
        # changing their request.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return QueryResponse(**result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.FASTAPI_HOST, port=config.FASTAPI_PORT)
