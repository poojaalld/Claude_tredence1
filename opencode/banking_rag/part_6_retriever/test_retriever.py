"""
Test module for retriever
Tests retrieval strategies and ranking
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

sys.path.insert(0, str(Path(__file__).parent))

from retriever import (
    RetrievedChunk,
    VectorRetriever,
    HybridRetriever,
    ContextualRetriever,
    RankedRetriever,
    RetrieverFactory,
    RetrievalPipeline,
    QueryProcessor,
)


class TestRetrievedChunk:
    """Test RetrievedChunk class"""
    
    def test_creation(self):
        """Test creating retrieved chunk"""
        chunk = RetrievedChunk(
            chunk_id="test_0",
            content="Test content",
            source="test.txt",
            similarity_score=0.95,
            chunk_index=0,
            metadata={"key": "value"}
        )
        
        assert chunk.chunk_id == "test_0"
        assert chunk.similarity_score == 0.95
        assert chunk.source == "test.txt"


class TestVectorRetriever:
    """Test VectorRetriever"""
    
    def test_creation(self):
        """Test creating vector retriever"""
        mock_index = Mock()
        mock_embedding_gen = Mock()
        
        retriever = VectorRetriever(
            mock_index,
            mock_embedding_gen,
            similarity_threshold=0.5
        )
        
        assert retriever.similarity_threshold == 0.5
    
    def test_retrieve(self):
        """Test retrieval"""
        # Mock index manager
        mock_index = Mock()
        mock_index.search.return_value = [
            {
                'id': 'chunk_0',
                'similarity': 0.95,
                'metadata': {
                    'content': 'Test content',
                    'source': 'test.txt',
                    'chunk_index': 0
                }
            }
        ]
        
        # Mock embedding generator
        mock_embedding_gen = Mock()
        mock_embedding_gen.embed.return_value = [[0.1] * 1536]
        
        retriever = VectorRetriever(mock_index, mock_embedding_gen)
        results = retriever.retrieve("test query", top_k=5)
        
        assert len(results) == 1
        assert results[0].chunk_id == 'chunk_0'
        assert results[0].similarity_score == 0.95
    
    def test_threshold_filtering(self):
        """Test filtering by similarity threshold"""
        mock_index = Mock()
        mock_index.search.return_value = [
            {
                'id': 'chunk_0',
                'similarity': 0.9,
                'metadata': {'content': 'Good', 'source': 'test.txt', 'chunk_index': 0}
            },
            {
                'id': 'chunk_1',
                'similarity': 0.3,
                'metadata': {'content': 'Bad', 'source': 'test.txt', 'chunk_index': 1}
            }
        ]
        
        mock_embedding_gen = Mock()
        mock_embedding_gen.embed.return_value = [[0.1] * 1536]
        
        retriever = VectorRetriever(mock_index, mock_embedding_gen, similarity_threshold=0.5)
        results = retriever.retrieve("query", top_k=5)
        
        # Only chunk_0 should be returned (similarity > 0.5)
        assert len(results) == 1
        assert results[0].chunk_id == 'chunk_0'


class TestHybridRetriever:
    """Test HybridRetriever"""
    
    def test_creation(self):
        """Test creating hybrid retriever"""
        mock_vector = Mock()
        retriever = HybridRetriever(mock_vector)
        
        assert retriever.vector_retriever == mock_vector
    
    def test_retrieve(self):
        """Test hybrid retrieval"""
        # Mock vector retriever results
        mock_chunks = [
            RetrievedChunk("c0", "Content 0", "doc.txt", 0.95, 0, {}),
            RetrievedChunk("c1", "Content 1", "doc.txt", 0.80, 1, {}),
        ]
        
        mock_vector = Mock()
        mock_vector.retrieve.return_value = mock_chunks
        
        retriever = HybridRetriever(mock_vector)
        results = retriever.retrieve("query", top_k=2)
        
        assert len(results) == 2
        # Results should be sorted by similarity (descending)
        assert results[0].similarity_score >= results[1].similarity_score


class TestContextualRetriever:
    """Test ContextualRetriever"""
    
    def test_creation(self):
        """Test creating contextual retriever"""
        mock_vector = Mock()
        retriever = ContextualRetriever(mock_vector, context_window=3)
        
        assert retriever.context_window == 3
    
    def test_retrieve(self):
        """Test contextual retrieval"""
        mock_chunks = [
            RetrievedChunk("c0", "Content", "doc.txt", 0.95, 0, {})
        ]
        
        mock_vector = Mock()
        mock_vector.retrieve.return_value = mock_chunks
        
        retriever = ContextualRetriever(mock_vector)
        results = retriever.retrieve("query")
        
        assert len(results) == 1


class TestRankedRetriever:
    """Test RankedRetriever"""
    
    def test_creation(self):
        """Test creating ranked retriever"""
        mock_vector = Mock()
        retriever = RankedRetriever(mock_vector)
        
        assert retriever.vector_retriever == mock_vector
    
    def test_ranking(self):
        """Test chunk ranking"""
        mock_chunks = [
            RetrievedChunk("c2", "Content 2", "doc.txt", 0.7, 2, {}),
            RetrievedChunk("c0", "Content 0", "doc.txt", 0.95, 0, {}),
            RetrievedChunk("c1", "Content 1", "doc.txt", 0.85, 1, {}),
        ]
        
        mock_vector = Mock()
        mock_vector.retrieve.return_value = mock_chunks
        
        retriever = RankedRetriever(mock_vector)
        results = retriever.retrieve("query", top_k=3)
        
        # Results should be ranked by similarity
        assert results[0].similarity_score >= results[1].similarity_score


class TestRetrieverFactory:
    """Test RetrieverFactory"""
    
    def test_factory_creation(self):
        """Test creating factory"""
        mock_index = Mock()
        mock_embedding = Mock()
        
        factory = RetrieverFactory(mock_index, mock_embedding)
        assert factory.index_manager == mock_index
    
    def test_create_vector_retriever(self):
        """Test creating vector retriever"""
        mock_index = Mock()
        mock_embedding = Mock()
        
        factory = RetrieverFactory(mock_index, mock_embedding)
        retriever = factory.create_vector_retriever()
        
        assert isinstance(retriever, VectorRetriever)
    
    def test_create_hybrid_retriever(self):
        """Test creating hybrid retriever"""
        mock_index = Mock()
        mock_embedding = Mock()
        
        factory = RetrieverFactory(mock_index, mock_embedding)
        retriever = factory.create_hybrid_retriever()
        
        assert isinstance(retriever, HybridRetriever)
    
    def test_create_ranked_retriever(self):
        """Test creating ranked retriever"""
        mock_index = Mock()
        mock_embedding = Mock()
        
        factory = RetrieverFactory(mock_index, mock_embedding)
        retriever = factory.create_ranked_retriever()
        
        assert isinstance(retriever, RankedRetriever)


class TestRetrievalPipeline:
    """Test RetrievalPipeline"""
    
    def test_creation(self):
        """Test creating pipeline"""
        mock_retriever = Mock()
        pipeline = RetrievalPipeline(mock_retriever)
        
        assert pipeline.retriever == mock_retriever
    
    def test_retrieve(self):
        """Test pipeline retrieval"""
        mock_chunks = [
            RetrievedChunk("c0", "Content", "doc.txt", 0.95, 0, {})
        ]
        
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_chunks
        
        pipeline = RetrievalPipeline(mock_retriever)
        results = pipeline.retrieve("query")
        
        assert len(results) == 1
        assert len(pipeline.retrieval_history) == 1
    
    def test_format_context(self):
        """Test context formatting"""
        chunks = [
            RetrievedChunk("c0", "Content 0", "doc.txt", 0.95, 0, {}),
            RetrievedChunk("c1", "Content 1", "doc.txt", 0.85, 1, {}),
        ]
        
        mock_retriever = Mock()
        pipeline = RetrievalPipeline(mock_retriever)
        
        context = pipeline.format_context(chunks)
        
        assert "Content 0" in context
        assert "Content 1" in context
        assert "doc.txt" in context
    
    def test_statistics(self):
        """Test statistics"""
        mock_chunks = [
            RetrievedChunk("c0", "Content", "doc.txt", 0.95, 0, {})
        ]
        
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_chunks
        
        pipeline = RetrievalPipeline(mock_retriever)
        pipeline.retrieve("query 1")
        pipeline.retrieve("query 2")
        
        stats = pipeline.get_statistics()
        
        assert stats['total_retrievals'] == 2
        assert stats['total_chunks_retrieved'] == 2


class TestQueryProcessor:
    """Test QueryProcessor"""
    
    def test_process(self):
        """Test query processing"""
        processor = QueryProcessor()
        
        query = "  How much is the  interest rate  "
        processed = processor.process(query)
        
        assert processed == "How much is the interest rate"
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        processor = QueryProcessor()
        
        query = "What is the interest rate for savings accounts"
        keywords = processor.extract_keywords(query)
        
        assert "interest" in keywords
        assert "rate" in keywords
        assert "savings" in keywords
        assert "what" not in keywords  # Stopword
        assert "the" not in keywords  # Stopword


class TestRetrieverIntegration:
    """Integration tests for retriever"""
    
    def test_full_retrieval_workflow(self):
        """Test complete retrieval workflow"""
        # Create mock chunks
        mock_chunks = [
            RetrievedChunk(
                chunk_id="banking_0",
                content="Account interest rates are 2.5% for savings accounts",
                source="banking_doc.txt",
                similarity_score=0.92,
                chunk_index=0,
                metadata={"topic": "interest"}
            ),
            RetrievedChunk(
                chunk_id="banking_1",
                content="Checking accounts have no interest",
                source="banking_doc.txt",
                similarity_score=0.85,
                chunk_index=1,
                metadata={"topic": "checking"}
            ),
        ]
        
        # Mock retriever
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_chunks
        
        # Create pipeline
        pipeline = RetrievalPipeline(mock_retriever)
        
        # Process query
        query_processor = QueryProcessor()
        processed_query = query_processor.process("What is interest rate")
        
        # Retrieve
        results = pipeline.retrieve(processed_query, top_k=5)
        
        # Format context
        context = pipeline.format_context(results)
        
        # Verify
        assert len(results) == 2
        assert "interest" in context
        assert "2.5%" in context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
