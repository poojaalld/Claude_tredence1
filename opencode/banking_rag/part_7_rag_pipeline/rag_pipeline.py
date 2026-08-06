"""
RAG Pipeline Module for Banking RAG Assistant
Orchestrates retrieval and generation using Claude
"""

from typing import List, Dict, Optional, Any
import time
from dataclasses import dataclass

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document


@dataclass
class RAGResponse:
    """Response from RAG pipeline"""
    query: str
    response: str
    sources: List[str]
    context: str
    processing_time: float
    retrieval_count: int
    model: str
    confidence: float = 0.0


class RAGPromptBuilder:
    """Builds prompts for RAG"""
    
    def __init__(self, logger=None):
        """Initialize prompt builder"""
        self.logger = logger
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for Claude"""
        return """You are a helpful banking assistant powered by a knowledge base. 
Your role is to answer questions about banking products, services, and policies using the provided context.

Guidelines:
1. Answer based on the provided context
2. Be accurate and factual
3. If information isn't in the context, say you don't have that information
4. Be friendly and professional
5. Keep responses concise but informative"""
    
    def build_prompt(self, query: str, context: str) -> str:
        """
        Build prompt with context
        
        Args:
            query: User query
            context: Retrieved context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""Context from banking knowledge base:
{context}

User Question: {query}

Please answer the question based on the context provided above."""
        
        return prompt
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class ClaudeGenerator:
    """Generate responses using Anthropic Claude"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 model: str = "claude-3-sonnet-20240229", logger=None):
        """
        Initialize Claude generator
        
        Args:
            api_key: Anthropic API key
            model: Model name
            logger: Logger instance
        """
        self.logger = logger
        self.model = model
        
        import os
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("Anthropic API key not provided")
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            self._log("Claude client initialized", "debug")
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )
    
    def generate(self, system_prompt: str, user_prompt: str, 
                max_tokens: int = 2048) -> str:
        """
        Generate response from Claude
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response
        """
        try:
            self._log(f"Generating response with {self.model}", "debug")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response = message.content[0].text
            
            self._log(f"Generated response ({len(response)} chars)", "debug")
            
            return response
            
        except Exception as e:
            self._log(f"Error generating response: {str(e)}", "error")
            raise
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class RAGPipeline:
    """Complete RAG pipeline"""
    
    def __init__(self, 
                 retrieval_pipeline,
                 embedding_generator,
                 logger=None):
        """
        Initialize RAG pipeline
        
        Args:
            retrieval_pipeline: RetrievalPipeline instance (Part 6)
            embedding_generator: EmbeddingGenerator instance (Part 4)
            logger: Logger instance
        """
        self.retrieval_pipeline = retrieval_pipeline
        self.embedding_generator = embedding_generator
        self.logger = logger
        
        # Initialize generators
        self.prompt_builder = RAGPromptBuilder(logger)
        self.claude_generator = ClaudeGenerator(logger=logger)
        
        self.query_history = []
        
        self._log("RAG Pipeline initialized", "info")
    
    def process_query(self, query: str, top_k: int = 5, 
                     max_tokens: int = 2048) -> RAGResponse:
        """
        Process query through complete RAG pipeline
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            max_tokens: Max tokens in response
            
        Returns:
            RAGResponse object
        """
        start_time = time.time()
        
        self._log(f"Processing query: {query}", "info")
        
        try:
            # Step 1: Retrieve relevant context
            retrieved_chunks = self.retrieval_pipeline.retrieve(query, top_k)
            
            if not retrieved_chunks:
                self._log("No relevant chunks found", "warning")
                return RAGResponse(
                    query=query,
                    response="I don't have relevant information in my knowledge base to answer this question.",
                    sources=[],
                    context="",
                    processing_time=time.time() - start_time,
                    retrieval_count=0,
                    model=self.claude_generator.model
                )
            
            # Step 2: Format context
            context = self.retrieval_pipeline.format_context(retrieved_chunks)
            
            # Step 3: Build prompt
            user_prompt = self.prompt_builder.build_prompt(query, context)
            
            # Step 4: Generate response
            response = self.claude_generator.generate(
                system_prompt=self.prompt_builder.system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens
            )
            
            # Step 5: Extract sources
            sources = list(set(chunk.source for chunk in retrieved_chunks))
            
            # Calculate confidence based on similarity scores
            confidence = (
                sum(chunk.similarity_score for chunk in retrieved_chunks) / 
                len(retrieved_chunks)
                if retrieved_chunks else 0.0
            )
            
            processing_time = time.time() - start_time
            
            # Create response object
            rag_response = RAGResponse(
                query=query,
                response=response,
                sources=sources,
                context=context,
                processing_time=processing_time,
                retrieval_count=len(retrieved_chunks),
                model=self.claude_generator.model,
                confidence=confidence
            )
            
            # Store in history
            self.query_history.append({
                'query': query,
                'response': response,
                'sources': sources,
                'processing_time': processing_time,
                'retrieval_count': len(retrieved_chunks),
                'confidence': confidence
            })
            
            self._log(
                f"Query processed in {processing_time:.3f}s. "
                f"Retrieved {len(retrieved_chunks)} chunks from {len(sources)} sources.",
                "info"
            )
            
            return rag_response
            
        except Exception as e:
            self._log(f"Error processing query: {str(e)}", "error")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        if not self.query_history:
            return {'queries': 0}
        
        total_time = sum(q['processing_time'] for q in self.query_history)
        avg_time = total_time / len(self.query_history)
        total_retrieved = sum(q['retrieval_count'] for q in self.query_history)
        avg_confidence = (
            sum(q['confidence'] for q in self.query_history) / 
            len(self.query_history)
        )
        
        return {
            'total_queries': len(self.query_history),
            'total_processing_time': total_time,
            'average_processing_time': avg_time,
            'total_chunks_retrieved': total_retrieved,
            'average_chunks_per_query': total_retrieved / len(self.query_history),
            'average_confidence': avg_confidence
        }
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class ConversationalRAG:
    """Conversational RAG with history"""
    
    def __init__(self, rag_pipeline: RAGPipeline, logger=None):
        """
        Initialize conversational RAG
        
        Args:
            rag_pipeline: RAGPipeline instance
            logger: Logger instance
        """
        self.rag_pipeline = rag_pipeline
        self.logger = logger
        self.conversation_history = []
    
    def chat(self, user_message: str, top_k: int = 5) -> RAGResponse:
        """
        Chat with RAG pipeline
        
        Args:
            user_message: User message
            top_k: Number of chunks to retrieve
            
        Returns:
            RAGResponse object
        """
        self._log(f"User: {user_message}", "debug")
        
        # Process through RAG pipeline
        response = self.rag_pipeline.process_query(user_message, top_k)
        
        # Store in conversation history
        self.conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': response.response,
            'sources': response.sources,
            'confidence': response.confidence
        })
        
        self._log(f"Assistant: {response.response[:100]}...", "debug")
        
        return response
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def reset_history(self) -> None:
        """Reset conversation history"""
        self.conversation_history = []
        self._log("Conversation history reset", "debug")
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class ResponseFormatter:
    """Format RAG responses for display"""
    
    @staticmethod
    def format_response(rag_response: RAGResponse) -> str:
        """
        Format RAG response for display
        
        Args:
            rag_response: RAGResponse object
            
        Returns:
            Formatted string
        """
        output = []
        output.append("=" * 60)
        output.append("Banking Assistant Response")
        output.append("=" * 60)
        output.append("")
        output.append(f"Question: {rag_response.query}")
        output.append("")
        output.append("Answer:")
        output.append(rag_response.response)
        output.append("")
        output.append("-" * 60)
        output.append(f"Sources: {', '.join(rag_response.sources)}")
        output.append(f"Confidence: {rag_response.confidence:.2%}")
        output.append(f"Processing Time: {rag_response.processing_time:.3f}s")
        output.append(f"Retrieved Chunks: {rag_response.retrieval_count}")
        output.append("=" * 60)
        
        return "\n".join(output)
    
    @staticmethod
    def format_context(rag_response: RAGResponse) -> str:
        """
        Format context for display
        
        Args:
            rag_response: RAGResponse object
            
        Returns:
            Formatted context
        """
        return rag_response.context
