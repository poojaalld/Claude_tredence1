"""
Test module for embedding generation
Tests embedding generation, caching, and batch processing
"""

import pytest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "part_3_semantic_chunking"))

from embedding_generator import (
    EmbeddingMetadata,
    EmbeddedChunk,
    MockEmbedding,
    EmbeddingCache,
    EmbeddingGenerator,
    BatchEmbeddingProcessor,
)

from semantic_chunker import Chunk, ChunkMetadata

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document


class TestEmbeddingMetadata:
    """Test EmbeddingMetadata class"""
    
    def test_metadata_creation(self):
        """Test creating embedding metadata"""
        metadata = EmbeddingMetadata(
            model="text-embedding-3-small",
            dimension=1536,
            created_at="2024-01-15T10:30:00"
        )
        
        assert metadata.model == "text-embedding-3-small"
        assert metadata.dimension == 1536
        assert metadata.tokens_used == 0


class TestEmbeddedChunk:
    """Test EmbeddedChunk class"""
    
    def test_embedded_chunk_creation(self):
        """Test creating an embedded chunk"""
        embedding = [0.1] * 1536
        chunk = EmbeddedChunk(
            chunk_id="test_0",
            content="Test content",
            embedding=embedding,
            metadata={"source": "test.txt"}
        )
        
        assert chunk.chunk_id == "test_0"
        assert chunk.content == "Test content"
        assert len(chunk.embedding) == 1536
    
    def test_embedded_chunk_to_dict(self):
        """Test converting embedded chunk to dictionary"""
        embedding = [0.1] * 1536
        chunk = EmbeddedChunk(
            chunk_id="test_0",
            content="Test content",
            embedding=embedding
        )
        
        chunk_dict = chunk.to_dict()
        assert isinstance(chunk_dict, dict)
        assert chunk_dict['chunk_id'] == "test_0"
        assert len(chunk_dict['embedding']) == 1536


class TestMockEmbedding:
    """Test MockEmbedding class"""
    
    def test_creation(self):
        """Test creating mock embedding"""
        embedding = MockEmbedding(embedding_dim=768)
        assert embedding.model_name == "mock-embedding"
        assert embedding.embedding_dim == 768
    
    def test_embed_texts(self):
        """Test embedding texts"""
        embedding = MockEmbedding(embedding_dim=512)
        texts = ["Hello world", "Test content", "Another text"]
        
        embeddings = embedding.embed(texts)
        
        assert len(embeddings) == len(texts)
        assert all(len(e) == 512 for e in embeddings)
    
    def test_deterministic_embeddings(self):
        """Test that same text produces same embedding"""
        embedding = MockEmbedding(embedding_dim=256)
        
        text = "Test deterministic embedding"
        embedding1 = embedding.embed([text])[0]
        embedding2 = embedding.embed([text])[0]
        
        assert embedding1 == embedding2
    
    def test_embed_chunk(self):
        """Test embedding a single chunk"""
        embedding = MockEmbedding()
        metadata = ChunkMetadata(
            source="test.txt",
            chunk_index=0,
            total_chunks=1,
            start_char=0,
            end_char=100,
            chunk_size=100
        )
        
        embedded = embedding.embed_chunk(
            chunk_id="test_0",
            content="Test content",
            metadata=metadata.to_dict()
        )
        
        assert embedded.chunk_id == "test_0"
        assert len(embedded.embedding) > 0
        assert embedded.embedding_metadata is not None


class TestEmbeddingCache:
    """Test EmbeddingCache class"""
    
    def test_cache_creation(self):
        """Test creating cache"""
        cache = EmbeddingCache()
        assert cache.cache == {}
    
    def test_cache_get_set(self):
        """Test caching embeddings"""
        cache = EmbeddingCache()
        text = "Test text"
        embedding = [0.1] * 1536
        
        cache.set(text, embedding)
        retrieved = cache.get(text)
        
        assert retrieved == embedding
    
    def test_cache_persistence(self):
        """Test saving and loading cache"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            cache_file = f.name
        
        try:
            # Create and populate cache
            cache1 = EmbeddingCache(cache_file=cache_file)
            text = "Persist this text"
            embedding = [0.2] * 1536
            cache1.set(text, embedding)
            cache1.save()
            
            # Verify file was created
            assert Path(cache_file).exists()
            
            # Load cache in new instance
            cache2 = EmbeddingCache(cache_file=cache_file)
            
            # Same text should have same hash and be retrievable
            retrieved = cache2.get(text)
            assert retrieved == embedding
        finally:
            Path(cache_file).unlink(missing_ok=True)
    
    def test_cache_miss(self):
        """Test cache miss"""
        cache = EmbeddingCache()
        result = cache.get("nonexistent text")
        
        assert result is None


class TestEmbeddingGenerator:
    """Test EmbeddingGenerator class"""
    
    def test_creation(self):
        """Test creating embedding generator"""
        generator = EmbeddingGenerator(model_type="mock")
        assert generator.model is not None
        assert generator.batch_size == 100
    
    def test_embed_chunks(self):
        """Test embedding chunks"""
        # Create mock chunks
        chunks = []
        for i in range(3):
            metadata = ChunkMetadata(
                source="test.txt",
                chunk_index=i,
                total_chunks=3,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                chunk_size=100
            )
            chunk = Chunk(
                content=f"Test content {i}",
                metadata=metadata
            )
            chunks.append(chunk)
        
        generator = EmbeddingGenerator(model_type="mock")
        embedded = generator.embed_chunks(chunks)
        
        assert len(embedded) == len(chunks)
        assert all(isinstance(e, EmbeddedChunk) for e in embedded)
        assert all(len(e.embedding) > 0 for e in embedded)
    
    def test_embedding_statistics(self):
        """Test getting statistics"""
        chunks = []
        for i in range(2):
            metadata = ChunkMetadata(
                source="test.txt",
                chunk_index=i,
                total_chunks=2,
                start_char=i * 50,
                end_char=(i + 1) * 50,
                chunk_size=50
            )
            chunk = Chunk(content=f"Test {i}", metadata=metadata)
            chunks.append(chunk)
        
        generator = EmbeddingGenerator(model_type="mock")
        embedded = generator.embed_chunks(chunks)
        
        stats = generator.get_statistics()
        assert stats['total_embeddings'] == len(embedded)
        assert stats['api_provider'] == "mock"
        assert stats['embedding_dim'] > 0
    
    def test_cache_integration(self):
        """Test cache integration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            cache_file = f.name
        
        try:
            # Create chunks
            chunks = []
            metadata = ChunkMetadata(
                source="test.txt",
                chunk_index=0,
                total_chunks=1,
                start_char=0,
                end_char=50,
                chunk_size=50
            )
            chunk = Chunk(content="Test cache", metadata=metadata)
            chunks.append(chunk)
            
            # First embedding
            gen1 = EmbeddingGenerator(
                model_type="mock",
                cache_file=cache_file,
                use_cache=True
            )
            embedded1 = gen1.embed_chunks(chunks)
            
            # Second embedding should use cache
            gen2 = EmbeddingGenerator(
                model_type="mock",
                cache_file=cache_file,
                use_cache=True
            )
            embedded2 = gen2.embed_chunks(chunks)
            
            assert embedded1[0].embedding == embedded2[0].embedding
        finally:
            Path(cache_file).unlink(missing_ok=True)


class TestBatchEmbeddingProcessor:
    """Test BatchEmbeddingProcessor class"""
    
    def test_creation(self):
        """Test creating batch processor"""
        processor = BatchEmbeddingProcessor(model_type="mock")
        assert processor.generator is not None
    
    def test_process_chunks(self):
        """Test processing chunks"""
        chunks = []
        for i in range(5):
            metadata = ChunkMetadata(
                source="test.txt",
                chunk_index=i,
                total_chunks=5,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                chunk_size=100
            )
            chunk = Chunk(content=f"Content {i}", metadata=metadata)
            chunks.append(chunk)
        
        processor = BatchEmbeddingProcessor(model_type="mock", batch_size=2)
        embedded = processor.process_chunks(chunks)
        
        assert len(embedded) == len(chunks)
    
    def test_statistics(self):
        """Test getting statistics"""
        chunks = []
        metadata = ChunkMetadata(
            source="test.txt",
            chunk_index=0,
            total_chunks=1,
            start_char=0,
            end_char=50,
            chunk_size=50
        )
        chunk = Chunk(content="Test", metadata=metadata)
        chunks.append(chunk)
        
        processor = BatchEmbeddingProcessor(model_type="mock")
        embedded = processor.process_chunks(chunks)
        
        stats = processor.get_statistics()
        assert stats['total_embeddings'] == 1


class TestEmbeddingQuality:
    """Test embedding quality metrics"""
    
    def test_embedding_dimensions(self):
        """Test embedding dimension consistency"""
        generator = EmbeddingGenerator(model_type="mock")
        
        chunks = []
        for i in range(3):
            metadata = ChunkMetadata(
                source="test.txt",
                chunk_index=i,
                total_chunks=3,
                start_char=0,
                end_char=50,
                chunk_size=50
            )
            chunk = Chunk(content=f"Text {i}", metadata=metadata)
            chunks.append(chunk)
        
        embedded = generator.embed_chunks(chunks)
        
        dims = [len(e.embedding) for e in embedded]
        assert len(set(dims)) == 1  # All embeddings have same dimension
    
    def test_embedding_not_empty(self):
        """Test that embeddings are generated"""
        generator = EmbeddingGenerator(model_type="mock")
        
        metadata = ChunkMetadata(
            source="test.txt",
            chunk_index=0,
            total_chunks=1,
            start_char=0,
            end_char=50,
            chunk_size=50
        )
        chunk = Chunk(content="Test content", metadata=metadata)
        
        embedded = generator.embed_chunks([chunk])
        
        assert len(embedded) == 1
        assert len(embedded[0].embedding) > 0
        assert all(isinstance(x, float) for x in embedded[0].embedding)
    
    def test_metadata_preservation(self):
        """Test that metadata is preserved in embeddings"""
        generator = EmbeddingGenerator(model_type="mock")
        
        metadata = ChunkMetadata(
            source="test.txt",
            chunk_index=2,
            total_chunks=5,
            start_char=100,
            end_char=200,
            chunk_size=100
        )
        chunk = Chunk(content="Test", metadata=metadata)
        
        embedded = generator.embed_chunks([chunk])
        
        assert embedded[0].metadata['source'] == "test.txt"
        assert embedded[0].metadata['chunk_index'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
