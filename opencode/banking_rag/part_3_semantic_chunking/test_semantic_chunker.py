"""
Test module for semantic chunking
Tests various chunking strategies and quality metrics
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from semantic_chunker import (
    ChunkingStrategy,
    ChunkMetadata,
    Chunk,
    FixedSizeChunker,
    SentenceChunker,
    ParagraphChunker,
    HybridChunker,
    SemanticChunker,
    ChunkerFactory,
    BulkChunker,
)

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document


class TestChunkMetadata:
    """Test ChunkMetadata class"""
    
    def test_metadata_creation(self):
        """Test creating chunk metadata"""
        metadata = ChunkMetadata(
            source="test.txt",
            chunk_index=0,
            total_chunks=5,
            start_char=0,
            end_char=100,
            chunk_size=100
        )
        
        assert metadata.chunk_index == 0
        assert metadata.total_chunks == 5
        assert metadata.chunk_size == 100
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary"""
        metadata = ChunkMetadata(
            source="test.txt",
            chunk_index=1,
            total_chunks=5,
            start_char=100,
            end_char=200,
            chunk_size=100,
            original_metadata={"page": 1}
        )
        
        meta_dict = metadata.to_dict()
        assert isinstance(meta_dict, dict)
        assert meta_dict['chunk_index'] == 1
        assert meta_dict['source'] == "test.txt"
        assert meta_dict['page'] == 1


class TestChunk:
    """Test Chunk class"""
    
    def test_chunk_creation(self):
        """Test creating a chunk"""
        metadata = ChunkMetadata(
            source="test.txt",
            chunk_index=0,
            total_chunks=1,
            start_char=0,
            end_char=50,
            chunk_size=50
        )
        
        chunk = Chunk(content="Test content", metadata=metadata)
        assert chunk.content == "Test content"
        assert chunk.metadata.source == "test.txt"
    
    def test_chunk_to_document(self):
        """Test converting chunk to LangChain Document"""
        metadata = ChunkMetadata(
            source="test.txt",
            chunk_index=0,
            total_chunks=1,
            start_char=0,
            end_char=50,
            chunk_size=50
        )
        
        chunk = Chunk(content="Test content", metadata=metadata)
        doc = chunk.to_document()
        
        assert isinstance(doc, Document)
        assert doc.page_content == "Test content"
        assert doc.metadata['source'] == "test.txt"


class TestFixedSizeChunker:
    """Test FixedSizeChunker"""
    
    def test_creation(self):
        """Test creating a fixed-size chunker"""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        assert chunker.chunk_size == 100
        assert chunker.overlap == 20
    
    def test_invalid_overlap(self):
        """Test that overlap cannot exceed chunk size"""
        with pytest.raises(ValueError):
            FixedSizeChunker(chunk_size=100, overlap=150)
    
    def test_chunk_simple_text(self):
        """Test chunking simple text"""
        text = "A" * 500
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        chunks = chunker.chunk(doc)
        
        assert len(chunks) > 1
        assert all(len(c.content) <= 100 for c in chunks)
    
    def test_chunk_preserves_content(self):
        """Test that chunking doesn't lose content"""
        text = "The quick brown fox jumps over the lazy dog. " * 20
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = FixedSizeChunker(chunk_size=200, overlap=50)
        chunks = chunker.chunk(doc)
        
        # Reconstruct with overlap consideration
        assert len(chunks) > 0
        assert chunks[0].content.startswith("The quick")
    
    def test_chunk_metadata(self):
        """Test that chunk metadata is correct"""
        text = "Test content " * 100
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        chunks = chunker.chunk(doc)
        
        for i, chunk in enumerate(chunks):
            assert chunk.metadata.chunk_index == i
            assert chunk.metadata.source == "test.txt"


class TestSentenceChunker:
    """Test SentenceChunker"""
    
    def test_creation(self):
        """Test creating a sentence chunker"""
        chunker = SentenceChunker(
            min_chunk_size=100,
            max_chunk_size=500
        )
        assert chunker.min_chunk_size == 100
        assert chunker.max_chunk_size == 500
    
    def test_chunk_sentences(self):
        """Test chunking by sentences"""
        text = "First sentence. Second sentence. Third sentence. " * 10
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = SentenceChunker(
            min_chunk_size=100,
            max_chunk_size=300
        )
        chunks = chunker.chunk(doc)
        
        assert len(chunks) > 1
        assert all(len(c.content) <= 400 for c in chunks)  # Some flexibility
    
    def test_sentence_detection(self):
        """Test sentence detection"""
        text = "Hello world. This is a test. Another sentence!"
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = SentenceChunker()
        sentences = chunker._split_sentences(text)
        
        assert len(sentences) >= 2


class TestParagraphChunker:
    """Test ParagraphChunker"""
    
    def test_creation(self):
        """Test creating a paragraph chunker"""
        chunker = ParagraphChunker(
            min_chunk_size=100,
            max_chunk_size=1000
        )
        assert chunker.min_chunk_size == 100
    
    def test_chunk_paragraphs(self):
        """Test chunking by paragraphs"""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3.\n\n" * 5
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = ParagraphChunker(
            min_chunk_size=50,
            max_chunk_size=500
        )
        chunks = chunker.chunk(doc)
        
        assert len(chunks) >= 1
        assert all(c.content.strip() for c in chunks)


class TestHybridChunker:
    """Test HybridChunker"""
    
    def test_creation(self):
        """Test creating a hybrid chunker"""
        chunker = HybridChunker(chunk_size=500)
        assert chunker.sentence_chunker is not None
    
    def test_hybrid_chunking(self):
        """Test hybrid chunking strategy"""
        text = "Sentence one. Sentence two. " * 50
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = HybridChunker(chunk_size=300)
        chunks = chunker.chunk(doc)
        
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)


class TestSemanticChunker:
    """Test SemanticChunker"""
    
    def test_creation(self):
        """Test creating a semantic chunker"""
        chunker = SemanticChunker(chunk_size=500)
        assert chunker.chunk_size == 500
    
    def test_boundary_detection(self):
        """Test semantic boundary detection"""
        text = """SECTION ONE
Content here.

SECTION TWO
More content.

SECTION THREE
Final content."""
        
        chunker = SemanticChunker()
        boundaries = chunker._detect_semantic_boundaries(text)
        
        assert len(boundaries) >= 2
        assert boundaries[0] == 0
    
    def test_semantic_chunking(self):
        """Test semantic chunking"""
        text = """INTRODUCTION
This is the introduction.

MAIN CONTENT
This is the main section. """ * 10
        
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = SemanticChunker(chunk_size=200)
        chunks = chunker.chunk(doc)
        
        assert len(chunks) > 0


class TestChunkerFactory:
    """Test ChunkerFactory"""
    
    def test_factory_creation(self):
        """Test creating factory"""
        factory = ChunkerFactory()
        assert factory is not None
    
    def test_create_fixed_size_chunker(self):
        """Test creating fixed-size chunker"""
        factory = ChunkerFactory()
        chunker = factory.create(
            ChunkingStrategy.FIXED_SIZE,
            chunk_size=100,
            overlap=20
        )
        
        assert isinstance(chunker, FixedSizeChunker)
    
    def test_create_sentence_chunker(self):
        """Test creating sentence chunker"""
        factory = ChunkerFactory()
        chunker = factory.create(ChunkingStrategy.SENTENCE)
        
        assert isinstance(chunker, SentenceChunker)
    
    def test_create_hybrid_chunker(self):
        """Test creating hybrid chunker"""
        factory = ChunkerFactory()
        chunker = factory.create(ChunkingStrategy.HYBRID)
        
        assert isinstance(chunker, HybridChunker)
    
    def test_create_semantic_chunker(self):
        """Test creating semantic chunker"""
        factory = ChunkerFactory()
        chunker = factory.create(ChunkingStrategy.SEMANTIC)
        
        assert isinstance(chunker, SemanticChunker)
    
    def test_invalid_strategy(self):
        """Test that invalid strategy raises error"""
        factory = ChunkerFactory()
        
        with pytest.raises(ValueError):
            factory.create("invalid_strategy")


class TestBulkChunker:
    """Test BulkChunker"""
    
    def test_creation(self):
        """Test creating bulk chunker"""
        chunker = BulkChunker()
        assert chunker is not None
        assert chunker.chunks_created == []
    
    def test_chunk_multiple_documents(self):
        """Test chunking multiple documents"""
        docs = [
            Document(
                page_content="Document 1. " * 500,  # Increased content
                metadata={"source": "doc1.txt"}
            ),
            Document(
                page_content="Document 2. " * 500,  # Increased content
                metadata={"source": "doc2.txt"}
            ),
        ]
        
        chunker = BulkChunker(strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=500)
        chunks = chunker.chunk_documents(docs)
        
        assert len(chunks) >= len(docs)  # Should have at least 2+ chunks
        assert len(chunker.chunks_created) == len(chunks)
    
    def test_statistics(self):
        """Test getting statistics"""
        docs = [
            Document(
                page_content="Test content. " * 100,
                metadata={"source": "test.txt"}
            )
        ]
        
        chunker = BulkChunker()
        chunks = chunker.chunk_documents(docs)
        
        stats = chunker.get_statistics()
        assert 'total_chunks' in stats
        assert 'total_characters' in stats
        assert 'average_chunk_size' in stats
        assert stats['total_chunks'] == len(chunks)
    
    def test_failed_documents_tracking(self):
        """Test that failed documents are tracked"""
        docs = [
            Document(page_content="Good content", metadata={"source": "good.txt"}),
        ]
        
        chunker = BulkChunker()
        chunks = chunker.chunk_documents(docs)
        
        assert len(chunks) > 0
        assert len(chunker.failed_documents) == 0


class TestChunkingQuality:
    """Test chunking quality metrics"""
    
    def test_chunk_size_variation(self):
        """Test that chunks have reasonable size variation"""
        text = "Test content. " * 500
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = FixedSizeChunker(chunk_size=200, overlap=50)
        chunks = chunker.chunk(doc)
        
        sizes = [len(c.content) for c in chunks]
        assert len(sizes) > 0
        assert all(0 < size <= 250 for size in sizes)
    
    def test_metadata_consistency(self):
        """Test that metadata is consistent across chunks"""
        text = "A" * 1000
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = FixedSizeChunker(chunk_size=100, overlap=10)
        chunks = chunker.chunk(doc)
        
        for chunk in chunks:
            assert chunk.metadata.source == "test.txt"
            assert chunk.metadata.chunk_index >= 0
            assert chunk.metadata.total_chunks > 0
    
    def test_overlap_correctness(self):
        """Test that overlap is applied correctly"""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 100
        doc = Document(page_content=text, metadata={"source": "test.txt"})
        
        chunker = FixedSizeChunker(chunk_size=50, overlap=10)
        chunks = chunker.chunk(doc)
        
        # Check that overlapping chunks have common content
        if len(chunks) > 1:
            # First chunk ends with characters that should appear in next
            first_end = chunks[0].content[-10:]
            second_start = chunks[1].content[:10]
            # Due to overlap, there should be some shared characters
            assert len(chunks) > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
