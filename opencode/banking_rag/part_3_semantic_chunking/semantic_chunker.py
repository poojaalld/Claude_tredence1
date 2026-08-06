"""
Semantic Chunking Module for Banking RAG Assistant
Splits documents into semantically meaningful chunks while preserving context
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    HYBRID = "hybrid"
    SEMANTIC = "semantic"


@dataclass
class ChunkMetadata:
    """Metadata for document chunks"""
    source: str
    chunk_index: int
    total_chunks: int
    start_char: int
    end_char: int
    chunk_size: int
    original_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'source': self.source,
            'chunk_index': self.chunk_index,
            'total_chunks': self.total_chunks,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'chunk_size': self.chunk_size,
            **self.original_metadata
        }


@dataclass
class Chunk:
    """A semantic chunk of text"""
    content: str
    metadata: ChunkMetadata
    
    def to_document(self) -> Document:
        """Convert to LangChain Document"""
        return Document(
            page_content=self.content,
            metadata=self.metadata.to_dict()
        )


class BaseChunker(ABC):
    """Abstract base class for chunking strategies"""
    
    def __init__(self, logger=None):
        """Initialize the chunker"""
        self.logger = logger
    
    @abstractmethod
    def chunk(self, document: Document) -> List[Chunk]:
        """
        Split document into chunks
        
        Args:
            document: LangChain Document to chunk
            
        Returns:
            List of Chunk objects
        """
        pass
    
    def _create_chunk_metadata(
        self,
        source: str,
        chunk_index: int,
        total_chunks: int,
        start_char: int,
        chunk_size: int,
        original_metadata: Dict[str, Any]
    ) -> ChunkMetadata:
        """Create chunk metadata"""
        return ChunkMetadata(
            source=source,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            start_char=start_char,
            end_char=start_char + chunk_size,
            chunk_size=chunk_size,
            original_metadata=original_metadata
        )
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)


class FixedSizeChunker(BaseChunker):
    """Chunks documents into fixed-size pieces with overlap"""
    
    def __init__(
        self,
        chunk_size: int = 1024,
        overlap: int = 200,
        logger=None
    ):
        """
        Initialize fixed-size chunker
        
        Args:
            chunk_size: Size of each chunk in characters
            overlap: Number of overlapping characters between chunks
            logger: Logger instance
        """
        super().__init__(logger)
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk size")
    
    def chunk(self, document: Document) -> List[Chunk]:
        """Split document into fixed-size chunks"""
        text = document.page_content
        chunks = []
        
        self._log(
            f"Chunking document with fixed size: {self.chunk_size}, "
            f"overlap: {self.overlap}",
            "debug"
        )
        
        start_idx = 0
        chunk_index = 0
        
        while start_idx < len(text):
            end_idx = min(start_idx + self.chunk_size, len(text))
            chunk_text = text[start_idx:end_idx]
            
            # Calculate total chunks (for metadata)
            total_chunks = (len(text) - 1) // (self.chunk_size - self.overlap) + 1
            
            metadata = self._create_chunk_metadata(
                source=document.metadata.get('source', 'unknown'),
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                start_char=start_idx,
                chunk_size=len(chunk_text),
                original_metadata=document.metadata
            )
            
            chunk = Chunk(content=chunk_text, metadata=metadata)
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start_idx += self.chunk_size - self.overlap
            chunk_index += 1
        
        self._log(f"Created {len(chunks)} fixed-size chunks", "debug")
        return chunks


class SentenceChunker(BaseChunker):
    """Chunks documents by sentences"""
    
    def __init__(
        self,
        min_chunk_size: int = 500,
        max_chunk_size: int = 2000,
        overlap_sentences: int = 1,
        logger=None
    ):
        """
        Initialize sentence-based chunker
        
        Args:
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters
            overlap_sentences: Number of sentences to overlap
            logger: Logger instance
        """
        super().__init__(logger)
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_sentences = overlap_sentences
    
    def _split_sentences(self, text: str) -> List[Tuple[str, int]]:
        """
        Split text into sentences with positions
        
        Returns:
            List of (sentence, start_position) tuples
        """
        # Pattern for sentence splitting
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$'
        
        sentences = []
        current_pos = 0
        
        # Split by sentence boundaries
        parts = re.split(sentence_pattern, text)
        
        for part in parts:
            if part.strip():
                sentences.append((part, current_pos))
                current_pos += len(part)
        
        return sentences
    
    def chunk(self, document: Document) -> List[Chunk]:
        """Split document into sentence-based chunks"""
        text = document.page_content
        sentences = self._split_sentences(text)
        
        if not sentences:
            # Fallback to fixed-size if no sentences found
            return FixedSizeChunker(logger=self.logger).chunk(document)
        
        chunks = []
        current_chunk = []
        current_size = 0
        overlap_buffer = []
        chunk_index = 0
        
        self._log(f"Chunking document by sentences: {len(sentences)} sentences", "debug")
        
        for sentence, pos in sentences:
            sentence_size = len(sentence)
            
            # If adding sentence would exceed max, save chunk
            if current_size + sentence_size > self.max_chunk_size and current_chunk:
                chunk_text = ''.join(current_chunk)
                
                # Get start position
                total_chunks = len(text) // self.max_chunk_size + 1
                
                metadata = self._create_chunk_metadata(
                    source=document.metadata.get('source', 'unknown'),
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    start_char=pos - current_size,
                    chunk_size=len(chunk_text),
                    original_metadata=document.metadata
                )
                
                chunk = Chunk(content=chunk_text, metadata=metadata)
                chunks.append(chunk)
                
                # Prepare for next chunk with overlap
                overlap_count = min(self.overlap_sentences, len(current_chunk))
                overlap_buffer = current_chunk[-overlap_count:] if overlap_count > 0 else []
                current_chunk = overlap_buffer
                current_size = sum(len(s) for s in overlap_buffer)
                chunk_index += 1
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = ''.join(current_chunk)
            total_chunks = chunk_index + 1
            
            metadata = self._create_chunk_metadata(
                source=document.metadata.get('source', 'unknown'),
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                start_char=len(text) - len(chunk_text),
                chunk_size=len(chunk_text),
                original_metadata=document.metadata
            )
            
            chunk = Chunk(content=chunk_text, metadata=metadata)
            chunks.append(chunk)
        
        self._log(f"Created {len(chunks)} sentence-based chunks", "debug")
        return chunks


class ParagraphChunker(BaseChunker):
    """Chunks documents by paragraphs"""
    
    def __init__(
        self,
        min_chunk_size: int = 500,
        max_chunk_size: int = 2000,
        overlap_paragraphs: int = 1,
        logger=None
    ):
        """
        Initialize paragraph-based chunker
        
        Args:
            min_chunk_size: Minimum chunk size
            max_chunk_size: Maximum chunk size
            overlap_paragraphs: Paragraphs to overlap
            logger: Logger instance
        """
        super().__init__(logger)
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_paragraphs = overlap_paragraphs
    
    def _split_paragraphs(self, text: str) -> List[Tuple[str, int]]:
        """Split text into paragraphs with positions"""
        paragraphs = []
        current_pos = 0
        
        # Split by double newlines or significant whitespace
        parts = re.split(r'\n\n+', text)
        
        for part in parts:
            if part.strip():
                paragraphs.append((part, current_pos))
                current_pos += len(part) + 2  # Account for newlines
        
        return paragraphs
    
    def chunk(self, document: Document) -> List[Chunk]:
        """Split document into paragraph-based chunks"""
        text = document.page_content
        paragraphs = self._split_paragraphs(text)
        
        if not paragraphs:
            # Fallback to fixed-size
            return FixedSizeChunker(logger=self.logger).chunk(document)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        self._log(f"Chunking document by paragraphs: {len(paragraphs)} paragraphs", "debug")
        
        for para, pos in paragraphs:
            para_size = len(para)
            
            # If exceeds max size, save chunk
            if current_size + para_size > self.max_chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                total_chunks = len(paragraphs) // max(1, (self.max_chunk_size // 500)) + 1
                
                metadata = self._create_chunk_metadata(
                    source=document.metadata.get('source', 'unknown'),
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    start_char=pos - current_size,
                    chunk_size=len(chunk_text),
                    original_metadata=document.metadata
                )
                
                chunk = Chunk(content=chunk_text, metadata=metadata)
                chunks.append(chunk)
                
                # Overlap
                overlap_count = min(self.overlap_paragraphs, len(current_chunk))
                current_chunk = current_chunk[-overlap_count:] if overlap_count > 0 else []
                current_size = sum(len(p) for p in current_chunk)
                chunk_index += 1
            
            current_chunk.append(para)
            current_size += para_size
        
        # Final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            total_chunks = chunk_index + 1
            
            metadata = self._create_chunk_metadata(
                source=document.metadata.get('source', 'unknown'),
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                start_char=len(text) - len(chunk_text),
                chunk_size=len(chunk_text),
                original_metadata=document.metadata
            )
            
            chunk = Chunk(content=chunk_text, metadata=metadata)
            chunks.append(chunk)
        
        self._log(f"Created {len(chunks)} paragraph-based chunks", "debug")
        return chunks


class HybridChunker(BaseChunker):
    """Hybrid chunker that uses sentences within size constraints"""
    
    def __init__(
        self,
        chunk_size: int = 1024,
        overlap: int = 200,
        logger=None
    ):
        """Initialize hybrid chunker"""
        super().__init__(logger)
        self.sentence_chunker = SentenceChunker(
            min_chunk_size=chunk_size // 2,
            max_chunk_size=chunk_size * 2,
            logger=logger
        )
    
    def chunk(self, document: Document) -> List[Chunk]:
        """Use hybrid approach"""
        # Try sentence-based first
        chunks = self.sentence_chunker.chunk(document)
        
        # Adjust chunks to respect chunk_size constraints
        adjusted_chunks = []
        for chunk in chunks:
            if len(chunk.content) <= self.sentence_chunker.max_chunk_size:
                adjusted_chunks.append(chunk)
            else:
                # Split large chunks with fixed size
                fixed_chunker = FixedSizeChunker(
                    chunk_size=self.sentence_chunker.max_chunk_size,
                    overlap=0,
                    logger=self.logger
                )
                # Create temporary document
                temp_doc = Document(
                    page_content=chunk.content,
                    metadata=chunk.metadata.to_dict()
                )
                sub_chunks = fixed_chunker.chunk(temp_doc)
                adjusted_chunks.extend(sub_chunks)
        
        self._log(f"Created {len(adjusted_chunks)} hybrid chunks", "debug")
        return adjusted_chunks


class SemanticChunker(BaseChunker):
    """
    Advanced semantic chunker that identifies semantic boundaries
    (sections, topics) in documents
    """
    
    def __init__(
        self,
        chunk_size: int = 1024,
        min_similarity: float = 0.7,
        logger=None
    ):
        """
        Initialize semantic chunker
        
        Args:
            chunk_size: Target chunk size
            min_similarity: Minimum similarity threshold
            logger: Logger instance
        """
        super().__init__(logger)
        self.chunk_size = chunk_size
        self.min_similarity = min_similarity
    
    def _detect_semantic_boundaries(self, text: str) -> List[int]:
        """
        Detect semantic boundaries (headers, section breaks)
        
        Returns:
            List of positions where semantic breaks occur
        """
        boundaries = [0]
        
        # Look for headers (lines with ALL CAPS or "===" underlines)
        lines = text.split('\n')
        current_pos = 0
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Header patterns
            if (line_stripped.isupper() and len(line_stripped) > 3 or
                i > 0 and '===' in line or '---' in line or
                line_stripped.startswith('#')):
                boundaries.append(current_pos)
            
            current_pos += len(line) + 1
        
        boundaries.append(len(text))
        return sorted(set(boundaries))
    
    def chunk(self, document: Document) -> List[Chunk]:
        """Split document by semantic boundaries"""
        text = document.page_content
        boundaries = self._detect_semantic_boundaries(text)
        
        chunks = []
        chunk_index = 0
        
        self._log(f"Detected {len(boundaries)} semantic boundaries", "debug")
        
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            section = text[start:end].strip()
            
            if not section:
                continue
            
            # Further split if section is too large
            if len(section) > self.chunk_size:
                fixed_chunker = FixedSizeChunker(
                    chunk_size=self.chunk_size,
                    overlap=int(self.chunk_size * 0.2),
                    logger=self.logger
                )
                temp_doc = Document(
                    page_content=section,
                    metadata=document.metadata
                )
                sub_chunks = fixed_chunker.chunk(temp_doc)
                chunks.extend(sub_chunks)
            else:
                metadata = self._create_chunk_metadata(
                    source=document.metadata.get('source', 'unknown'),
                    chunk_index=chunk_index,
                    total_chunks=len(boundaries) - 1,
                    start_char=start,
                    chunk_size=len(section),
                    original_metadata=document.metadata
                )
                
                chunk = Chunk(content=section, metadata=metadata)
                chunks.append(chunk)
                chunk_index += 1
        
        self._log(f"Created {len(chunks)} semantic chunks", "debug")
        return chunks


class ChunkerFactory:
    """Factory for creating appropriate chunkers"""
    
    def __init__(self, logger=None):
        """Initialize factory"""
        self.logger = logger
    
    def create(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.HYBRID,
        **kwargs
    ) -> BaseChunker:
        """
        Create a chunker
        
        Args:
            strategy: Chunking strategy to use
            **kwargs: Strategy-specific arguments
            
        Returns:
            Configured chunker instance
        """
        if strategy == ChunkingStrategy.FIXED_SIZE:
            return FixedSizeChunker(logger=self.logger, **kwargs)
        elif strategy == ChunkingStrategy.SENTENCE:
            return SentenceChunker(logger=self.logger, **kwargs)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return ParagraphChunker(logger=self.logger, **kwargs)
        elif strategy == ChunkingStrategy.HYBRID:
            return HybridChunker(logger=self.logger, **kwargs)
        elif strategy == ChunkingStrategy.SEMANTIC:
            return SemanticChunker(logger=self.logger, **kwargs)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")


class BulkChunker:
    """Process multiple documents with chunking"""
    
    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.HYBRID,
        logger=None,
        **chunker_kwargs
    ):
        """
        Initialize bulk chunker
        
        Args:
            strategy: Chunking strategy
            logger: Logger instance
            **chunker_kwargs: Strategy-specific arguments
        """
        self.logger = logger
        self.factory = ChunkerFactory(logger)
        self.chunker = self.factory.create(strategy, **chunker_kwargs)
        self.chunks_created = []
        self.failed_documents = []
    
    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """
        Chunk multiple documents
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        
        self._log(f"Chunking {len(documents)} documents", "info")
        
        for i, document in enumerate(documents):
            try:
                self._log(f"Chunking document {i+1}/{len(documents)}", "debug")
                chunks = self.chunker.chunk(document)
                all_chunks.extend(chunks)
                self.chunks_created.extend(chunks)
            except Exception as e:
                error_msg = f"Failed to chunk document {i+1}: {str(e)}"
                self._log(error_msg, "error")
                self.failed_documents.append((document, str(e)))
        
        self._log(
            f"Created {len(all_chunks)} chunks from {len(documents)} documents",
            "info"
        )
        
        return all_chunks
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get chunking statistics"""
        total_chunks = len(self.chunks_created)
        total_chars = sum(len(c.content) for c in self.chunks_created)
        avg_chunk_size = total_chars / total_chunks if total_chunks > 0 else 0
        
        return {
            'total_chunks': total_chunks,
            'total_characters': total_chars,
            'average_chunk_size': avg_chunk_size,
            'failed_documents': len(self.failed_documents),
        }
    
    def _log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.logger:
            getattr(self.logger, level)(message)
