"""
Embedding Generation Module for Banking RAG Assistant
Handles embedding generation using OpenAI and Voyage AI APIs
"""

import os
import json
from typing import List, Dict, Optional, Any, Union, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
from datetime import datetime

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document


@dataclass
class EmbeddingMetadata:
    """Metadata for embeddings"""
    model: str
    dimension: int
    created_at: str
    tokens_used: int = 0
    cost_estimate: float = 0.0
    processing_time: float = 0.0
    api_provider: str = "unknown"


@dataclass
class EmbeddedChunk:
    """A chunk with embedding vector"""
    chunk_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding_metadata: Optional[EmbeddingMetadata] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'embedding': self.embedding,
            'metadata': self.metadata,
            'embedding_metadata': (
                vars(self.embedding_metadata) 
                if self.embedding_metadata else None
            )
        }


class BaseEmbeddingModel(ABC):
    """Abstract base class for embedding models"""
    
    def __init__(self, logger=None):
        """Initialize embedding model"""
        self.logger = logger
        self.model_name = "unknown"
        self.embedding_dim = 0
        self.tokens_used = 0
        self.cost_estimate = 0.0
    
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    def embed_chunk(self, chunk_id: str, content: str, metadata: Dict[str, Any]) -> EmbeddedChunk:
        """
        Embed a single chunk
        
        Args:
            chunk_id: Unique chunk identifier
            content: Chunk text content
            metadata: Chunk metadata
            
        Returns:
            EmbeddedChunk object
        """
        start_time = time.time()
        
        self._log(f"Embedding chunk: {chunk_id}", "debug")
        
        embeddings = self.embed([content])
        embedding = embeddings[0] if embeddings else []
        
        processing_time = time.time() - start_time
        
        embedding_meta = EmbeddingMetadata(
            model=self.model_name,
            dimension=self.embedding_dim,
            created_at=datetime.now().isoformat(),
            tokens_used=self._estimate_tokens(content),
            processing_time=processing_time,
            api_provider=self._get_provider()
        )
        
        return EmbeddedChunk(
            chunk_id=chunk_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            embedding_metadata=embedding_meta
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        return len(text.split()) // 4 + 1  # Rough estimate: ~4 chars per token
    
    def _get_provider(self) -> str:
        """Get API provider name"""
        return "unknown"
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class OpenAIEmbedding(BaseEmbeddingModel):
    """OpenAI Embedding API wrapper"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small", logger=None):
        """
        Initialize OpenAI embedding
        
        Args:
            api_key: OpenAI API key
            model: Model name
            logger: Logger instance
        """
        super().__init__(logger)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model
        self.embedding_dim = self._get_embedding_dim(model)
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and not found in environment")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self._log("OpenAI client initialized", "debug")
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
    
    def _get_embedding_dim(self, model: str) -> int:
        """Get embedding dimension for model"""
        dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dims.get(model, 1536)
    
    def _get_provider(self) -> str:
        """Get API provider name"""
        return "openai"
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI API
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        try:
            self._log(f"Requesting {len(texts)} embeddings from OpenAI", "debug")
            
            response = self.client.embeddings.create(
                input=texts,
                model=self.model_name
            )
            
            embeddings = [item.embedding for item in response.data]
            self.tokens_used += response.usage.total_tokens
            
            self._log(f"Generated {len(embeddings)} embeddings", "debug")
            
            return embeddings
            
        except Exception as e:
            self._log(f"Error generating embeddings: {str(e)}", "error")
            raise


class VoyageAIEmbedding(BaseEmbeddingModel):
    """Voyage AI Embedding API wrapper"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "voyage-3", logger=None):
        """
        Initialize Voyage AI embedding
        
        Args:
            api_key: Voyage AI API key
            model: Model name
            logger: Logger instance
        """
        super().__init__(logger)
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        self.model_name = model
        self.embedding_dim = self._get_embedding_dim(model)
        
        if not self.api_key:
            raise ValueError("Voyage AI API key not provided and not found in environment")
        
        try:
            import voyageai
            voyageai.api_key = self.api_key
            self.client = voyageai
            self._log("Voyage AI client initialized", "debug")
        except ImportError:
            raise ImportError("voyageai package not installed. Install with: pip install voyage-ai")
    
    def _get_embedding_dim(self, model: str) -> int:
        """Get embedding dimension for model"""
        dims = {
            "voyage-3": 1024,
            "voyage-3-lite": 512,
            "voyage-large-2": 1536,
            "voyage-large-2-instruct": 1536,
        }
        return dims.get(model, 1024)
    
    def _get_provider(self) -> str:
        """Get API provider name"""
        return "voyageai"
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Voyage AI API
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        try:
            self._log(f"Requesting {len(texts)} embeddings from Voyage AI", "debug")
            
            response = self.client.get_embedding(
                texts,
                model=self.model_name
            )
            
            embeddings = response
            
            self._log(f"Generated {len(embeddings)} embeddings", "debug")
            
            return embeddings
            
        except Exception as e:
            self._log(f"Error generating embeddings: {str(e)}", "error")
            raise


class MockEmbedding(BaseEmbeddingModel):
    """Mock embedding for testing (generates random vectors)"""
    
    def __init__(self, embedding_dim: int = 1536, logger=None):
        """
        Initialize mock embedding
        
        Args:
            embedding_dim: Embedding dimension
            logger: Logger instance
        """
        super().__init__(logger)
        self.model_name = "mock-embedding"
        self.embedding_dim = embedding_dim
        self._log(f"Mock embedding initialized with dim={embedding_dim}", "debug")
    
    def _get_provider(self) -> str:
        """Get API provider name"""
        return "mock"
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate mock embeddings
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of random embeddings
        """
        import random
        
        embeddings = []
        for text in texts:
            # Create deterministic embedding based on text hash
            seed = hash(text) % 2**32
            random.seed(seed)
            embedding = [random.random() for _ in range(self.embedding_dim)]
            embeddings.append(embedding)
        
        self._log(f"Generated {len(embeddings)} mock embeddings", "debug")
        return embeddings


class EmbeddingCache:
    """Cache for embeddings to avoid duplicate API calls"""
    
    def __init__(self, cache_file: Optional[str] = None, logger=None):
        """
        Initialize embedding cache
        
        Args:
            cache_file: Optional file path to persist cache
            logger: Logger instance
        """
        self.cache = {}
        self.cache_file = cache_file
        self.logger = logger
        
        if cache_file and os.path.exists(cache_file):
            self._load_cache()
    
    def get(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        text_hash = str(hash(text))
        return self.cache.get(text_hash)
    
    def set(self, text: str, embedding: List[float]) -> None:
        """Store embedding in cache"""
        text_hash = str(hash(text))
        self.cache[text_hash] = embedding
    
    def save(self) -> None:
        """Save cache to file"""
        if self.cache_file:
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump(self.cache, f)
                self._log(f"Cache saved to {self.cache_file}", "debug")
            except Exception as e:
                self._log(f"Error saving cache: {str(e)}", "error")
    
    def _load_cache(self) -> None:
        """Load cache from file"""
        try:
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
            self._log(f"Cache loaded from {self.cache_file}", "debug")
        except Exception as e:
            self._log(f"Error loading cache: {str(e)}", "error")
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class EmbeddingGenerator:
    """Main embedding generator with batching and caching"""
    
    def __init__(
        self,
        model_type: str = "openai",
        model_name: str = "text-embedding-3-small",
        batch_size: int = 100,
        use_cache: bool = True,
        cache_file: Optional[str] = None,
        logger=None
    ):
        """
        Initialize embedding generator
        
        Args:
            model_type: Type of embedding model (openai, voyage, mock)
            model_name: Specific model name
            batch_size: Batch size for processing
            use_cache: Whether to use caching
            cache_file: Cache file path
            logger: Logger instance
        """
        self.logger = logger
        self.batch_size = batch_size
        self.model_type = model_type
        
        # Initialize model
        if model_type == "openai":
            self.model = OpenAIEmbedding(model=model_name, logger=logger)
        elif model_type == "voyage":
            self.model = VoyageAIEmbedding(model=model_name, logger=logger)
        elif model_type == "mock":
            self.model = MockEmbedding(logger=logger)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Initialize cache
        self.cache = EmbeddingCache(cache_file=cache_file, logger=logger) if use_cache else None
        
        self.embedded_chunks = []
        self.failed_chunks = []
        
        self._log(f"EmbeddingGenerator initialized with {model_type}", "info")
    
    def embed_chunks(self, chunks: List[Any]) -> List[EmbeddedChunk]:
        """
        Embed a list of chunks
        
        Args:
            chunks: List of Chunk objects (from Part 3)
            
        Returns:
            List of EmbeddedChunk objects
        """
        self._log(f"Starting to embed {len(chunks)} chunks", "info")
        
        all_embedded = []
        
        # Process in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size
            
            self._log(f"Processing batch {batch_num}/{total_batches}", "debug")
            
            for chunk in batch:
                try:
                    # Generate chunk ID
                    chunk_id = f"{chunk.metadata.source}_{chunk.metadata.chunk_index}"
                    
                    # Check cache
                    cached_embedding = None
                    if self.cache:
                        cached_embedding = self.cache.get(chunk.content)
                    
                    if cached_embedding:
                        self._log(f"Using cached embedding for {chunk_id}", "debug")
                        embedded_chunk = EmbeddedChunk(
                            chunk_id=chunk_id,
                            content=chunk.content,
                            embedding=cached_embedding,
                            metadata=chunk.metadata.to_dict()
                        )
                    else:
                        # Generate new embedding
                        embedded_chunk = self.model.embed_chunk(
                            chunk_id=chunk_id,
                            content=chunk.content,
                            metadata=chunk.metadata.to_dict()
                        )
                        
                        # Cache the embedding
                        if self.cache:
                            self.cache.set(chunk.content, embedded_chunk.embedding)
                    
                    all_embedded.append(embedded_chunk)
                    self.embedded_chunks.append(embedded_chunk)
                    
                except Exception as e:
                    error_msg = f"Failed to embed chunk: {str(e)}"
                    self._log(error_msg, "error")
                    self.failed_chunks.append((chunk, str(e)))
        
        # Save cache if used
        if self.cache:
            self.cache.save()
        
        self._log(
            f"Embedding complete: {len(all_embedded)} successful, "
            f"{len(self.failed_chunks)} failed",
            "info"
        )
        
        return all_embedded
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get embedding statistics"""
        return {
            'total_embeddings': len(self.embedded_chunks),
            'failed_count': len(self.failed_chunks),
            'model': self.model.model_name,
            'embedding_dim': self.model.embedding_dim,
            'tokens_used': self.model.tokens_used,
            'api_provider': self.model._get_provider()
        }
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class BatchEmbeddingProcessor:
    """Process embeddings from documents with progress tracking"""
    
    def __init__(
        self,
        model_type: str = "openai",
        batch_size: int = 100,
        logger=None
    ):
        """
        Initialize batch processor
        
        Args:
            model_type: Type of embedding model
            batch_size: Batch size
            logger: Logger instance
        """
        self.logger = logger
        self.generator = EmbeddingGenerator(
            model_type=model_type,
            batch_size=batch_size,
            logger=logger
        )
    
    def process_chunks(self, chunks: List[Any]) -> List[EmbeddedChunk]:
        """
        Process chunks with progress tracking
        
        Args:
            chunks: List of chunks
            
        Returns:
            List of embedded chunks
        """
        return self.generator.embed_chunks(chunks)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics"""
        return self.generator.get_statistics()
