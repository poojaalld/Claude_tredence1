"""
Retriever Module for Banking RAG Assistant
Handles retrieving relevant chunks from indexed embeddings
"""

from typing import List, Dict, Optional, Any, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


@dataclass
class RetrievedChunk:
    """A retrieved chunk with similarity score"""
    chunk_id: str
    content: str
    source: str
    similarity_score: float
    chunk_index: int
    metadata: Dict[str, Any]


class BaseRetriever(ABC):
    """Abstract base class for retrievers"""
    
    def __init__(self, logger=None):
        """Initialize retriever"""
        self.logger = logger
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for query
        
        Args:
            query: Query string
            top_k: Number of chunks to retrieve
            
        Returns:
            List of RetrievedChunk objects
        """
        pass
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class VectorRetriever(BaseRetriever):
    """Retriever using vector similarity search"""
    
    def __init__(self, index_manager, embedding_generator, 
                 similarity_threshold: float = 0.5, logger=None):
        """
        Initialize vector retriever
        
        Args:
            index_manager: IndexManager instance (Part 5)
            embedding_generator: EmbeddingGenerator instance (Part 4)
            similarity_threshold: Minimum similarity score
            logger: Logger instance
        """
        super().__init__(logger)
        self.index_manager = index_manager
        self.embedding_generator = embedding_generator
        self.similarity_threshold = similarity_threshold
        
        self._log("VectorRetriever initialized", "debug")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Retrieve chunks using vector similarity"""
        start_time = time.time()
        
        self._log(f"Retrieving top {top_k} chunks for query", "debug")
        
        # Generate query embedding
        query_embedding = self.embedding_generator.embed([query])[0]
        
        # Search in index
        search_results = self.index_manager.search(query_embedding, top_k)
        
        # Filter by similarity threshold and convert to RetrievedChunk objects
        retrieved_chunks = []
        for result in search_results:
            if result['similarity'] >= self.similarity_threshold:
                metadata = result['metadata']
                chunk = RetrievedChunk(
                    chunk_id=result['id'],
                    content=metadata.get('content', ''),
                    source=metadata.get('source', 'unknown'),
                    similarity_score=result['similarity'],
                    chunk_index=metadata.get('chunk_index', 0),
                    metadata=metadata
                )
                retrieved_chunks.append(chunk)
        
        processing_time = time.time() - start_time
        self._log(
            f"Retrieved {len(retrieved_chunks)} chunks in {processing_time:.3f}s",
            "debug"
        )
        
        return retrieved_chunks


class HybridRetriever(BaseRetriever):
    """Hybrid retriever combining multiple strategies"""
    
    def __init__(self, vector_retriever, logger=None):
        """
        Initialize hybrid retriever
        
        Args:
            vector_retriever: VectorRetriever instance
            logger: Logger instance
        """
        super().__init__(logger)
        self.vector_retriever = vector_retriever
        
        self._log("HybridRetriever initialized", "debug")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Retrieve using hybrid strategy"""
        # For now, use vector retrieval as primary method
        # In future, could combine with BM25, semantic similarity, etc.
        
        self._log(f"Hybrid retrieval for: {query}", "debug")
        
        chunks = self.vector_retriever.retrieve(query, top_k)
        
        # Re-rank by relevance (could add additional scoring here)
        chunks_sorted = sorted(
            chunks,
            key=lambda x: x.similarity_score,
            reverse=True
        )
        
        return chunks_sorted[:top_k]


class ContextualRetriever(BaseRetriever):
    """Retriever with contextual window expansion"""
    
    def __init__(self, vector_retriever, context_window: int = 2, logger=None):
        """
        Initialize contextual retriever
        
        Args:
            vector_retriever: VectorRetriever instance
            context_window: Number of adjacent chunks to include
            logger: Logger instance
        """
        super().__init__(logger)
        self.vector_retriever = vector_retriever
        self.context_window = context_window
        
        self._log(f"ContextualRetriever initialized with window={context_window}", "debug")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Retrieve chunks with contextual expansion"""
        # Get primary chunks
        primary_chunks = self.vector_retriever.retrieve(query, top_k)
        
        # Could expand with context here
        # For MVP, just return the primary chunks
        
        return primary_chunks


class RankedRetriever(BaseRetriever):
    """Retriever with advanced ranking and filtering"""
    
    def __init__(self, vector_retriever, logger=None):
        """
        Initialize ranked retriever
        
        Args:
            vector_retriever: VectorRetriever instance
            logger: Logger instance
        """
        super().__init__(logger)
        self.vector_retriever = vector_retriever
        
        self._log("RankedRetriever initialized", "debug")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Retrieve with advanced ranking"""
        # Get chunks
        chunks = self.vector_retriever.retrieve(query, top_k * 2)
        
        # Apply ranking criteria
        ranked_chunks = self._rank_chunks(chunks, query)
        
        return ranked_chunks[:top_k]
    
    def _rank_chunks(self, chunks: List[RetrievedChunk], 
                    query: str) -> List[RetrievedChunk]:
        """Apply ranking to chunks"""
        # Primary ranking by similarity score
        chunks_sorted = sorted(
            chunks,
            key=lambda x: x.similarity_score,
            reverse=True
        )
        
        return chunks_sorted


class RetrieverFactory:
    """Factory for creating retrievers"""
    
    def __init__(self, index_manager, embedding_generator, logger=None):
        """Initialize factory"""
        self.index_manager = index_manager
        self.embedding_generator = embedding_generator
        self.logger = logger
    
    def create_vector_retriever(self, 
                              similarity_threshold: float = 0.5) -> VectorRetriever:
        """Create vector retriever"""
        return VectorRetriever(
            self.index_manager,
            self.embedding_generator,
            similarity_threshold,
            logger=self.logger
        )
    
    def create_hybrid_retriever(self) -> HybridRetriever:
        """Create hybrid retriever"""
        vector_retriever = self.create_vector_retriever()
        return HybridRetriever(vector_retriever, logger=self.logger)
    
    def create_contextual_retriever(self, 
                                  context_window: int = 2) -> ContextualRetriever:
        """Create contextual retriever"""
        vector_retriever = self.create_vector_retriever()
        return ContextualRetriever(vector_retriever, context_window, logger=self.logger)
    
    def create_ranked_retriever(self) -> RankedRetriever:
        """Create ranked retriever"""
        vector_retriever = self.create_vector_retriever()
        return RankedRetriever(vector_retriever, logger=self.logger)


class RetrievalPipeline:
    """Complete retrieval pipeline"""
    
    def __init__(self, retriever: BaseRetriever, logger=None):
        """
        Initialize retrieval pipeline
        
        Args:
            retriever: Retriever instance
            logger: Logger instance
        """
        self.retriever = retriever
        self.logger = logger
        self.retrieval_history = []
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """
        Execute retrieval pipeline
        
        Args:
            query: Query string
            top_k: Number of chunks to retrieve
            
        Returns:
            List of RetrievedChunk objects
        """
        self._log(f"Executing retrieval pipeline for: {query}", "info")
        
        start_time = time.time()
        
        # Execute retrieval
        chunks = self.retriever.retrieve(query, top_k)
        
        processing_time = time.time() - start_time
        
        # Log to history
        retrieval_result = {
            'query': query,
            'top_k': top_k,
            'results': len(chunks),
            'processing_time': processing_time,
            'chunks': [
                {
                    'id': c.chunk_id,
                    'similarity': c.similarity_score,
                    'source': c.source
                }
                for c in chunks
            ]
        }
        self.retrieval_history.append(retrieval_result)
        
        self._log(
            f"Retrieved {len(chunks)} chunks in {processing_time:.3f}s",
            "info"
        )
        
        return chunks
    
    def format_context(self, chunks: List[RetrievedChunk]) -> str:
        """
        Format retrieved chunks as context string
        
        Args:
            chunks: List of RetrievedChunk objects
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source: {chunk.source} - Chunk {chunk.chunk_index}] "
                f"(Similarity: {chunk.similarity_score:.3f})\n"
                f"{chunk.content}"
            )
        
        return "\n\n".join(context_parts)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        if not self.retrieval_history:
            return {'retrievals': 0}
        
        total_time = sum(r['processing_time'] for r in self.retrieval_history)
        avg_time = total_time / len(self.retrieval_history)
        
        return {
            'total_retrievals': len(self.retrieval_history),
            'total_time': total_time,
            'average_time': avg_time,
            'total_chunks_retrieved': sum(r['results'] for r in self.retrieval_history)
        }
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class QueryProcessor:
    """Process queries before retrieval"""
    
    def __init__(self, logger=None):
        """Initialize query processor"""
        self.logger = logger
    
    def process(self, query: str) -> str:
        """
        Process query
        
        Args:
            query: Raw query string
            
        Returns:
            Processed query string
        """
        # Clean query
        processed = query.strip()
        
        # Normalize whitespace
        processed = ' '.join(processed.split())
        
        self._log(f"Processed query: {processed}", "debug")
        
        return processed
    
    def extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        # Simple keyword extraction
        keywords = query.lower().split()
        
        # Filter common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'is', 'are', 'what', 'how', 'why', 'when', 'where'}
        keywords = [w for w in keywords if w not in stopwords and len(w) > 2]
        
        return keywords
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)
