"""
Test module for vector indexing
Tests FAISS and PostgreSQL indexing
"""

import pytest
import sys
import tempfile
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "part_4_embeddings"))

from vector_indexing import (
    IndexMetadata,
    FAISSVectorIndex,
    VectorIndexFactory,
    IndexManager,
)

from embedding_generator import EmbeddedChunk


class TestIndexMetadata:
    """Test IndexMetadata class"""
    
    def test_metadata_creation(self):
        """Test creating index metadata"""
        metadata = IndexMetadata(
            index_type="faiss",
            created_at="2024-01-15T10:30:00",
            total_vectors=100,
            vector_dimension=1536
        )
        
        assert metadata.index_type == "faiss"
        assert metadata.total_vectors == 100
        assert metadata.vector_dimension == 1536


class TestFAISSVectorIndex:
    """Test FAISS vector index"""
    
    def test_creation(self):
        """Test creating FAISS index"""
        try:
            index = FAISSVectorIndex(embedding_dim=1536)
            assert index.embedding_dim == 1536
            assert len(index.vector_ids) == 0
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_add_vectors(self):
        """Test adding vectors"""
        try:
            index = FAISSVectorIndex(embedding_dim=512)
            
            vectors = [
                [0.1] * 512,
                [0.2] * 512,
                [0.3] * 512
            ]
            ids = ["vec_0", "vec_1", "vec_2"]
            metadata = [
                {"source": "doc1.txt", "chunk": 0},
                {"source": "doc1.txt", "chunk": 1},
                {"source": "doc2.txt", "chunk": 0}
            ]
            
            index.add_vectors(vectors, ids, metadata)
            
            assert len(index.vector_ids) == 3
            assert index.vector_ids == ids
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_search(self):
        """Test searching vectors"""
        try:
            index = FAISSVectorIndex(embedding_dim=256)
            
            # Add vectors
            vectors = [
                [0.1] * 256,
                [0.1001] * 256,  # Similar to first
                [0.9] * 256       # Different
            ]
            ids = ["vec_0", "vec_1", "vec_2"]
            metadata = [{"id": i} for i in range(3)]
            
            index.add_vectors(vectors, ids, metadata)
            
            # Search with query similar to first vector
            query = [0.1005] * 256
            results = index.search(query, top_k=2)
            
            assert len(results) == 2
            assert results[0][1] > 0  # Similarity score
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_get_metadata(self):
        """Test retrieving metadata"""
        try:
            index = FAISSVectorIndex(embedding_dim=128)
            
            vectors = [[0.5] * 128]
            ids = ["test_vec"]
            metadata = [{"test": "data"}]
            
            index.add_vectors(vectors, ids, metadata)
            
            retrieved_meta = index.get_metadata("test_vec")
            assert retrieved_meta == {"test": "data"}
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_save_load(self):
        """Test saving and loading index"""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create and save
                index1 = FAISSVectorIndex(embedding_dim=64)
                vectors = [[0.5] * 64, [0.6] * 64]
                ids = ["v1", "v2"]
                metadata = [{"id": 1}, {"id": 2}]
                
                index1.add_vectors(vectors, ids, metadata)
                index1.save(tmpdir)
                
                # Load in new instance
                index2 = FAISSVectorIndex(embedding_dim=64)
                index2.load(tmpdir)
                
                assert index2.vector_ids == ids
                assert index2.get_metadata("v1") == {"id": 1}
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_statistics(self):
        """Test getting statistics"""
        try:
            index = FAISSVectorIndex(embedding_dim=1536)
            
            vectors = [[0.1] * 1536 for _ in range(5)]
            ids = [f"vec_{i}" for i in range(5)]
            metadata = [{"idx": i} for i in range(5)]
            
            index.add_vectors(vectors, ids, metadata)
            
            stats = index.get_statistics()
            assert stats['total_vectors'] == 5
            assert stats['embedding_dimension'] == 1536
        except ImportError:
            pytest.skip("FAISS not installed")


class TestVectorIndexFactory:
    """Test VectorIndexFactory"""
    
    def test_factory_creation(self):
        """Test creating factory"""
        factory = VectorIndexFactory()
        assert factory is not None
    
    def test_create_faiss_index(self):
        """Test creating FAISS index via factory"""
        try:
            factory = VectorIndexFactory()
            index = factory.create_faiss_index(embedding_dim=1024)
            
            assert isinstance(index, FAISSVectorIndex)
            assert index.embedding_dim == 1024
        except ImportError:
            pytest.skip("FAISS not installed")


class TestIndexManager:
    """Test IndexManager"""
    
    def test_creation(self):
        """Test creating index manager"""
        try:
            manager = IndexManager(index_type="faiss", embedding_dim=1536)
            assert manager.index_type == "faiss"
            assert manager.embedding_dim == 1536
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_add_embedded_chunks(self):
        """Test adding embedded chunks"""
        try:
            manager = IndexManager(index_type="faiss", embedding_dim=512)
            
            # Create embedded chunks
            chunks = []
            for i in range(3):
                chunk = EmbeddedChunk(
                    chunk_id=f"chunk_{i}",
                    content=f"Test content {i}",
                    embedding=[0.1 * (i + 1)] * 512,
                    metadata={"source": "test.txt", "idx": i}
                )
                chunks.append(chunk)
            
            manager.add_embedded_chunks(chunks)
            
            stats = manager.get_statistics()
            assert stats['total_vectors'] == 3
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_search(self):
        """Test searching"""
        try:
            manager = IndexManager(index_type="faiss", embedding_dim=256)
            
            # Add chunks
            chunks = []
            for i in range(3):
                chunk = EmbeddedChunk(
                    chunk_id=f"chunk_{i}",
                    content=f"Content {i}",
                    embedding=[0.1] * 256 if i == 0 else [0.9] * 256,
                    metadata={"idx": i}
                )
                chunks.append(chunk)
            
            manager.add_embedded_chunks(chunks)
            
            # Search
            query_embedding = [0.1] * 256
            results = manager.search(query_embedding, top_k=2)
            
            assert len(results) <= 2
            assert all('similarity' in r for r in results)
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_save_load_index(self):
        """Test saving and loading index"""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create and save
                manager1 = IndexManager(index_type="faiss", embedding_dim=64)
                
                chunks = []
                for i in range(2):
                    chunk = EmbeddedChunk(
                        chunk_id=f"chunk_{i}",
                        content=f"Content {i}",
                        embedding=[0.5] * 64,
                        metadata={"id": i}
                    )
                    chunks.append(chunk)
                
                manager1.add_embedded_chunks(chunks)
                manager1.save_index(tmpdir)
                
                # Load in new instance
                manager2 = IndexManager(index_type="faiss", embedding_dim=64)
                manager2.load_index(tmpdir)
                
                stats = manager2.get_statistics()
                assert stats['total_vectors'] == 2
        except ImportError:
            pytest.skip("FAISS not installed")


class TestIndexIntegration:
    """Integration tests for indexing"""
    
    def test_full_workflow(self):
        """Test complete indexing workflow"""
        try:
            # Initialize manager
            manager = IndexManager(index_type="faiss", embedding_dim=768)
            
            # Create embedded chunks
            chunks = []
            for i in range(5):
                chunk = EmbeddedChunk(
                    chunk_id=f"banking_chunk_{i}",
                    content=f"Banking topic {i}",
                    embedding=[0.1 * (i + 1)] * 768,
                    metadata={
                        "source": f"banking_doc_{i % 2}.txt",
                        "chunk_idx": i,
                        "topic": "banking"
                    }
                )
                chunks.append(chunk)
            
            # Add chunks
            manager.add_embedded_chunks(chunks)
            
            # Get statistics
            stats = manager.get_statistics()
            assert stats['total_vectors'] == 5
            
            # Search
            results = manager.search([0.15] * 768, top_k=3)
            assert len(results) <= 3
            
            # Verify metadata
            for result in results:
                assert 'id' in result
                assert 'similarity' in result
                assert 'metadata' in result
        except ImportError:
            pytest.skip("FAISS not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
