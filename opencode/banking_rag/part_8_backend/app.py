"""
FastAPI Backend for Banking RAG Assistant
Provides REST API endpoints for RAG pipeline
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
from datetime import datetime


# Request/Response models
class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    top_k: int = 5
    max_tokens: int = 2048


class ChunkInfo(BaseModel):
    """Retrieved chunk info"""
    chunk_id: str
    similarity_score: float
    source: str


class QueryResponse(BaseModel):
    """Query response model"""
    query: str
    response: str
    sources: List[str]
    chunks_retrieved: int
    confidence: float
    processing_time: float
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str


class StatsResponse(BaseModel):
    """Statistics response"""
    total_queries: int
    average_processing_time: float
    total_chunks_retrieved: int
    average_confidence: float


# Initialize FastAPI app
app = FastAPI(
    title="Banking RAG Assistant API",
    description="REST API for banking RAG system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables (in production, use dependency injection)
rag_pipeline = None
logger = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on startup"""
    global rag_pipeline, logger
    
    try:
        from part_1_environment import log, settings
        logger = log
        
        logger.info("Starting Banking RAG API...")
        
        # Load components
        from part_4_embeddings import EmbeddingGenerator
        from part_5_indexing import IndexManager
        from part_6_retriever import RetrieverFactory, RetrievalPipeline
        from part_7_rag_pipeline import RAGPipeline
        
        # Initialize embedding generator
        embedding_gen = EmbeddingGenerator(
            model_type="mock",  # Use mock for demo
            logger=logger
        )
        
        # Initialize index manager
        index_mgr = IndexManager(
            index_type="faiss",
            embedding_dim=1536,
            logger=logger
        )
        
        # Initialize retriever factory
        retriever_factory = RetrieverFactory(
            index_mgr,
            embedding_gen,
            logger=logger
        )
        vector_retriever = retriever_factory.create_vector_retriever()
        
        # Initialize retrieval pipeline
        retrieval_pipeline = RetrievalPipeline(vector_retriever, logger=logger)
        
        # Initialize RAG pipeline
        rag_pipeline = RAGPipeline(
            retrieval_pipeline,
            embedding_gen,
            logger=logger
        )
        
        logger.info("Banking RAG API initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing RAG pipeline: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if logger:
        logger.info("Banking RAG API shutting down")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query through the RAG pipeline
    
    Args:
        request: QueryRequest with query and parameters
        
    Returns:
        QueryResponse with answer and metadata
    """
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    try:
        if logger:
            logger.info(f"Processing query: {request.query}")
        
        # Process through RAG pipeline
        response = rag_pipeline.process_query(
            request.query,
            top_k=request.top_k,
            max_tokens=request.max_tokens
        )
        
        return QueryResponse(
            query=response.query,
            response=response.response,
            sources=response.sources,
            chunks_retrieved=response.retrieval_count,
            confidence=response.confidence,
            processing_time=response.processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        if logger:
            logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get RAG pipeline statistics"""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    try:
        stats = rag_pipeline.get_statistics()
        
        return StatsResponse(
            total_queries=stats.get('total_queries', 0),
            average_processing_time=stats.get('average_processing_time', 0),
            total_chunks_retrieved=stats.get('total_chunks_retrieved', 0),
            average_confidence=stats.get('average_confidence', 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/docs-redirect")
async def redirect_docs():
    """Redirect to API documentation"""
    return {"message": "Go to /docs for interactive API documentation"}


def main():
    """Run the API server"""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
