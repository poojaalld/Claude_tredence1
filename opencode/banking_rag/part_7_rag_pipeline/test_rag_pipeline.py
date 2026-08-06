"""
Test module for RAG pipeline
Tests retrieval-augmented generation
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "part_6_retriever"))

from rag_pipeline import (
    RAGResponse,
    RAGPromptBuilder,
    RAGPipeline,
    ConversationalRAG,
    ResponseFormatter,
)

from retriever import RetrievedChunk


class TestRAGResponse:
    """Test RAGResponse class"""
    
    def test_creation(self):
        """Test creating RAG response"""
        response = RAGResponse(
            query="What is interest rate?",
            response="The interest rate for savings accounts is 2.5%",
            sources=["banking.txt"],
            context="Context here",
            processing_time=0.5,
            retrieval_count=3,
            model="claude-3-sonnet",
            confidence=0.95
        )
        
        assert response.query == "What is interest rate?"
        assert response.confidence == 0.95
        assert response.model == "claude-3-sonnet"


class TestRAGPromptBuilder:
    """Test RAGPromptBuilder"""
    
    def test_creation(self):
        """Test creating prompt builder"""
        builder = RAGPromptBuilder()
        assert builder.system_prompt is not None
    
    def test_build_prompt(self):
        """Test prompt building"""
        builder = RAGPromptBuilder()
        
        query = "What is interest rate?"
        context = "Interest rates vary by account type"
        
        prompt = builder.build_prompt(query, context)
        
        assert query in prompt
        assert context in prompt
        assert "Question:" in prompt or "question:" in prompt.lower()


class TestRAGPipeline:
    """Test RAGPipeline"""
    
    def test_creation(self):
        """Test creating RAG pipeline"""
        mock_retrieval = Mock()
        mock_embedding = Mock()
        
        with patch('rag_pipeline.ClaudeGenerator'):
            pipeline = RAGPipeline(mock_retrieval, mock_embedding)
        
            assert pipeline.retrieval_pipeline == mock_retrieval
            assert pipeline.embedding_generator == mock_embedding
    
    def test_process_query_with_results(self):
        """Test processing query with results"""
        pytest.skip("Requires API key - tested in integration")
    
    def test_process_query_no_results(self):
        """Test processing query with no results"""
        pytest.skip("Requires API key - tested in integration")
    
    def test_statistics(self):
        """Test getting statistics"""
        pytest.skip("Requires API key - tested in integration")


class TestConversationalRAG:
    """Test ConversationalRAG"""
    
    def test_creation(self):
        """Test creating conversational RAG"""
        mock_pipeline = Mock()
        conv_rag = ConversationalRAG(mock_pipeline)
        
        assert conv_rag.rag_pipeline == mock_pipeline
    
    def test_chat(self):
        """Test chat interaction"""
        mock_response = RAGResponse(
            query="Hello",
            response="Hi there!",
            sources=["doc.txt"],
            context="Context",
            processing_time=0.1,
            retrieval_count=1,
            model="claude-3",
            confidence=0.9
        )
        
        mock_pipeline = Mock()
        mock_pipeline.process_query.return_value = mock_response
        
        conv_rag = ConversationalRAG(mock_pipeline)
        response = conv_rag.chat("Hello")
        
        assert response.response == "Hi there!"
        assert len(conv_rag.conversation_history) == 2  # user + assistant
    
    def test_conversation_history(self):
        """Test conversation history"""
        mock_response = RAGResponse(
            query="Q",
            response="A",
            sources=["doc.txt"],
            context="",
            processing_time=0.1,
            retrieval_count=1,
            model="claude-3",
            confidence=0.9
        )
        
        mock_pipeline = Mock()
        mock_pipeline.process_query.return_value = mock_response
        
        conv_rag = ConversationalRAG(mock_pipeline)
        conv_rag.chat("Question 1")
        conv_rag.chat("Question 2")
        
        history = conv_rag.get_conversation_history()
        
        assert len(history) == 4  # 2 Q&A pairs
    
    def test_reset_history(self):
        """Test resetting history"""
        mock_response = RAGResponse(
            "Q", "A", ["doc.txt"], "", 0.1, 1, "claude-3", 0.9
        )
        
        mock_pipeline = Mock()
        mock_pipeline.process_query.return_value = mock_response
        
        conv_rag = ConversationalRAG(mock_pipeline)
        conv_rag.chat("Question")
        
        assert len(conv_rag.conversation_history) == 2
        
        conv_rag.reset_history()
        
        assert len(conv_rag.conversation_history) == 0


class TestResponseFormatter:
    """Test ResponseFormatter"""
    
    def test_format_response(self):
        """Test formatting response"""
        response = RAGResponse(
            query="What is interest rate?",
            response="The rate is 2.5%",
            sources=["banking.txt"],
            context="Context",
            processing_time=0.5,
            retrieval_count=3,
            model="claude-3",
            confidence=0.95
        )
        
        formatted = ResponseFormatter.format_response(response)
        
        assert "Question:" in formatted
        assert "What is interest rate?" in formatted
        assert "The rate is 2.5%" in formatted
        assert "banking.txt" in formatted
        assert "95" in formatted  # Either 0.95 or 95%
    
    def test_format_context(self):
        """Test formatting context"""
        response = RAGResponse(
            "Q", "A", ["doc.txt"], "Test context", 0.1, 1, "claude-3", 0.9
        )
        
        context = ResponseFormatter.format_context(response)
        
        assert context == "Test context"


class TestRAGIntegration:
    """Integration tests for RAG"""
    
    def test_full_rag_workflow(self):
        """Test complete RAG workflow"""
        pytest.skip("Requires API key - full integration test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
