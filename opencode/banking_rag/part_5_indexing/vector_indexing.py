"""
Vector Indexing Module for Banking RAG Assistant
Handles vector indexing using FAISS and pgvector
"""

import os
import json
import pickle
from typing import List, Dict, Tuple, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document


@dataclass
class IndexMetadata:
    """Metadata for index"""
    index_type: str
    created_at: str
    total_vectors: int
    vector_dimension: int
    index_path: Optional[str] = None


class BaseVectorIndex(ABC):
    """Abstract base class for vector indices"""
    
    def __init__(self, embedding_dim: int, logger=None):
        """
        Initialize vector index
        
        Args:
            embedding_dim: Dimension of embeddings
            logger: Logger instance
        """
        self.embedding_dim = embedding_dim
        self.logger = logger
        self.vector_ids = []
        self.vectors = []
        self.metadata_store = {}
    
    @abstractmethod
    def add_vectors(self, vectors: List[List[float]], ids: List[str], 
                   metadata: List[Dict[str, Any]]) -> None:
        """
        Add vectors to index
        
        Args:
            vectors: List of embedding vectors
            ids: List of vector IDs
            metadata: List of metadata dictionaries
        """
        pass
    
    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of (id, similarity_score) tuples
        """
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """Save index to disk"""
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """Load index from disk"""
        pass
    
    def get_metadata(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a vector"""
        return self.metadata_store.get(vector_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            'total_vectors': len(self.vector_ids),
            'embedding_dimension': self.embedding_dim,
            'vector_ids': len(self.vector_ids)
        }
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class FAISSVectorIndex(BaseVectorIndex):
    """FAISS-based vector index for fast similarity search"""
    
    def __init__(self, embedding_dim: int, logger=None):
        """
        Initialize FAISS index
        
        Args:
            embedding_dim: Dimension of embeddings
            logger: Logger instance
        """
        super().__init__(embedding_dim, logger)
        self._check_dependencies()
        
        import faiss
        # Create an IndexFlatL2 index (Euclidean distance)
        self.faiss_index = faiss.IndexFlatL2(embedding_dim)
        self._log("FAISS index initialized", "debug")
    
    def _check_dependencies(self):
        """Check if FAISS is installed"""
        try:
            import faiss
        except ImportError:
            raise ImportError(
                "faiss-cpu is not installed. Install with: pip install faiss-cpu"
            )
    
    def add_vectors(self, vectors: List[List[float]], ids: List[str], 
                   metadata: List[Dict[str, Any]]) -> None:
        """Add vectors to FAISS index"""
        if not vectors:
            return
        
        self._log(f"Adding {len(vectors)} vectors to FAISS index", "debug")
        
        # Convert to numpy array
        vectors_array = np.array(vectors, dtype=np.float32)
        
        # Add to FAISS
        self.faiss_index.add(vectors_array)
        
        # Store metadata
        for vec_id, meta in zip(ids, metadata):
            self.vector_ids.append(vec_id)
            self.metadata_store[vec_id] = meta
            self.vectors.append(vectors)
        
        self._log(f"Total vectors in index: {len(self.vector_ids)}", "debug")
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar vectors in FAISS index"""
        self._log(f"Searching for top {top_k} similar vectors", "debug")
        
        # Convert query to numpy array
        query_array = np.array([query_vector], dtype=np.float32)
        
        # Search
        distances, indices = self.faiss_index.search(query_array, min(top_k, len(self.vector_ids)))
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.vector_ids):
                vector_id = self.vector_ids[idx]
                # Convert distance to similarity score (1 / (1 + distance))
                similarity = 1.0 / (1.0 + distance)
                results.append((vector_id, similarity))
        
        return results
    
    def save(self, path: str) -> None:
        """Save FAISS index to disk"""
        try:
            import faiss
            
            # Create directory if needed
            os.makedirs(path, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.faiss_index, os.path.join(path, "faiss_index.bin"))
            
            # Save metadata and IDs
            index_data = {
                'vector_ids': self.vector_ids,
                'metadata_store': self.metadata_store,
                'embedding_dim': self.embedding_dim
            }
            with open(os.path.join(path, "index_metadata.json"), 'w') as f:
                json.dump(index_data, f)
            
            self._log(f"Index saved to {path}", "info")
        except Exception as e:
            self._log(f"Error saving index: {str(e)}", "error")
            raise
    
    def load(self, path: str) -> None:
        """Load FAISS index from disk"""
        try:
            import faiss
            
            # Load FAISS index
            self.faiss_index = faiss.read_index(os.path.join(path, "faiss_index.bin"))
            
            # Load metadata and IDs
            with open(os.path.join(path, "index_metadata.json"), 'r') as f:
                index_data = json.load(f)
                self.vector_ids = index_data['vector_ids']
                self.metadata_store = index_data['metadata_store']
            
            self._log(f"Index loaded from {path}", "info")
        except Exception as e:
            self._log(f"Error loading index: {str(e)}", "error")
            raise


class PostgresVectorIndex(BaseVectorIndex):
    """PostgreSQL with pgvector for vector indexing"""
    
    def __init__(self, embedding_dim: int, connection_string: str, 
                 table_name: str = "embeddings", logger=None):
        """
        Initialize PostgreSQL vector index
        
        Args:
            embedding_dim: Dimension of embeddings
            connection_string: PostgreSQL connection string
            table_name: Table name for storing embeddings
            logger: Logger instance
        """
        super().__init__(embedding_dim, logger)
        self._check_dependencies()
        
        self.connection_string = connection_string
        self.table_name = table_name
        
        import psycopg2
        self.connection = psycopg2.connect(connection_string)
        self.cursor = self.connection.cursor()
        
        self._create_table()
        self._log("PostgreSQL vector index initialized", "debug")
    
    def _check_dependencies(self):
        """Check if psycopg2 is installed"""
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "psycopg2 is not installed. Install with: pip install psycopg2-binary"
            )
    
    def _create_table(self):
        """Create table for storing embeddings"""
        try:
            # Create pgvector extension if not exists
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            self.connection.commit()
            
            # Create table
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id TEXT PRIMARY KEY,
                content TEXT,
                embedding vector({self.embedding_dim}),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            
            # Create index for vector similarity
            index_name = f"{self.table_name}_embedding_idx"
            create_index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)"
            
            try:
                self.cursor.execute(create_index_sql)
                self.connection.commit()
            except:
                pass  # Index might already exist
            
            self._log("PostgreSQL table created/verified", "debug")
        except Exception as e:
            self._log(f"Error creating table: {str(e)}", "error")
            raise
    
    def add_vectors(self, vectors: List[List[float]], ids: List[str], 
                   metadata: List[Dict[str, Any]]) -> None:
        """Add vectors to PostgreSQL"""
        try:
            for vector, vec_id, meta in zip(vectors, ids, metadata):
                # Convert vector to string format for pgvector
                vector_str = "[" + ",".join(str(v) for v in vector) + "]"
                
                insert_sql = f"""
                INSERT INTO {self.table_name} (id, embedding, metadata)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata
                """
                
                self.cursor.execute(
                    insert_sql,
                    (vec_id, vector_str, json.dumps(meta))
                )
                
                self.vector_ids.append(vec_id)
                self.metadata_store[vec_id] = meta
            
            self.connection.commit()
            self._log(f"Added {len(vectors)} vectors to PostgreSQL", "debug")
        except Exception as e:
            self.connection.rollback()
            self._log(f"Error adding vectors: {str(e)}", "error")
            raise
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar vectors using PostgreSQL"""
        try:
            # Convert query to string format
            query_str = "[" + ",".join(str(v) for v in query_vector) + "]"
            
            search_sql = f"""
            SELECT id, 1 - (embedding <=> %s::vector) as similarity
            FROM {self.table_name}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """
            
            self.cursor.execute(search_sql, (query_str, query_str, top_k))
            results = [(row[0], row[1]) for row in self.cursor.fetchall()]
            
            self._log(f"Found {len(results)} similar vectors", "debug")
            return results
        except Exception as e:
            self._log(f"Error searching vectors: {str(e)}", "error")
            raise
    
    def save(self, path: str) -> None:
        """Save index metadata to disk"""
        try:
            os.makedirs(path, exist_ok=True)
            
            index_data = {
                'vector_ids': self.vector_ids,
                'table_name': self.table_name,
                'embedding_dim': self.embedding_dim,
                'index_type': 'postgres'
            }
            
            with open(os.path.join(path, "index_metadata.json"), 'w') as f:
                json.dump(index_data, f)
            
            self._log(f"Index metadata saved to {path}", "info")
        except Exception as e:
            self._log(f"Error saving index: {str(e)}", "error")
            raise
    
    def load(self, path: str) -> None:
        """Load index metadata from disk"""
        try:
            with open(os.path.join(path, "index_metadata.json"), 'r') as f:
                index_data = json.load(f)
                self.vector_ids = index_data['vector_ids']
            
            self._log(f"Index metadata loaded from {path}", "info")
        except Exception as e:
            self._log(f"Error loading index: {str(e)}", "error")
            raise
    
    def __del__(self):
        """Close PostgreSQL connection"""
        try:
            if hasattr(self, 'cursor'):
                self.cursor.close()
            if hasattr(self, 'connection'):
                self.connection.close()
        except:
            pass


class VectorIndexFactory:
    """Factory for creating vector indices"""
    
    def __init__(self, logger=None):
        """Initialize factory"""
        self.logger = logger
    
    def create_faiss_index(self, embedding_dim: int) -> FAISSVectorIndex:
        """Create FAISS index"""
        return FAISSVectorIndex(embedding_dim, logger=self.logger)
    
    def create_postgres_index(self, embedding_dim: int, connection_string: str,
                            table_name: str = "embeddings") -> PostgresVectorIndex:
        """Create PostgreSQL index"""
        return PostgresVectorIndex(
            embedding_dim,
            connection_string,
            table_name,
            logger=self.logger
        )


class IndexManager:
    """Manage vector indices and embeddings storage"""
    
    def __init__(self, index_type: str = "faiss", embedding_dim: int = 1536,
                 index_path: Optional[str] = None, logger=None):
        """
        Initialize index manager
        
        Args:
            index_type: Type of index (faiss or postgres)
            embedding_dim: Embedding dimension
            index_path: Path for index storage
            logger: Logger instance
        """
        self.logger = logger
        self.index_type = index_type
        self.embedding_dim = embedding_dim
        self.index_path = index_path
        
        factory = VectorIndexFactory(logger)
        
        if index_type == "faiss":
            self.index = factory.create_faiss_index(embedding_dim)
        elif index_type == "postgres":
            if not index_path:
                raise ValueError("PostgreSQL connection string required for postgres index")
            self.index = factory.create_postgres_index(embedding_dim, index_path)
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        self._log(f"IndexManager initialized with {index_type}", "info")
    
    def add_embedded_chunks(self, embedded_chunks: List[Any]) -> None:
        """
        Add embedded chunks to index
        
        Args:
            embedded_chunks: List of EmbeddedChunk objects (from Part 4)
        """
        vectors = [chunk.embedding for chunk in embedded_chunks]
        ids = [chunk.chunk_id for chunk in embedded_chunks]
        metadata = [chunk.metadata for chunk in embedded_chunks]
        
        self._log(f"Adding {len(vectors)} embedded chunks to index", "info")
        self.index.add_vectors(vectors, ids, metadata)
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar chunks
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            
        Returns:
            List of search results with metadata
        """
        results = self.index.search(query_embedding, top_k)
        
        search_results = []
        for vector_id, similarity in results:
            metadata = self.index.get_metadata(vector_id)
            search_results.append({
                'id': vector_id,
                'similarity': similarity,
                'metadata': metadata
            })
        
        return search_results
    
    def save_index(self, path: str) -> None:
        """Save index to disk"""
        self.index.save(path)
    
    def load_index(self, path: str) -> None:
        """Load index from disk"""
        self.index.load(path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics"""
        return self.index.get_statistics()
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)
