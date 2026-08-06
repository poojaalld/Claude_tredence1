"""
Test module for document loader
Tests loading of various document formats
"""

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent))

from document_loader import (
    DocumentMetadata,
    TextDocumentLoader,
    DocumentLoaderFactory,
    BulkDocumentLoader,
)

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document


class TestDocumentMetadata:
    """Test suite for DocumentMetadata"""
    
    def test_metadata_creation(self):
        """Test creating document metadata"""
        metadata = DocumentMetadata(
            source="/path/to/file.txt",
            file_type=".txt",
            file_size=1024,
            loaded_at="2024-01-01T12:00:00"
        )
        
        assert metadata.source == "/path/to/file.txt"
        assert metadata.file_type == ".txt"
        assert metadata.file_size == 1024
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary"""
        metadata = DocumentMetadata(
            source="/path/to/file.txt",
            file_type=".txt",
            file_size=1024,
            loaded_at="2024-01-01T12:00:00",
            title="Test Document"
        )
        
        meta_dict = metadata.to_dict()
        assert isinstance(meta_dict, dict)
        assert meta_dict['source'] == "/path/to/file.txt"
        assert meta_dict['title'] == "Test Document"
    
    def test_metadata_optional_fields(self):
        """Test metadata with optional fields"""
        metadata = DocumentMetadata(
            source="/path/to/file.pdf",
            file_type=".pdf",
            file_size=2048,
            loaded_at="2024-01-01T12:00:00",
            num_pages=5,
            author="John Doe"
        )
        
        assert metadata.num_pages == 5
        assert metadata.author == "John Doe"


class TestTextDocumentLoader:
    """Test suite for TextDocumentLoader"""
    
    def test_can_load_text_file(self):
        """Test that loader can load text files"""
        loader = TextDocumentLoader()
        assert loader.can_load("document.txt") is True
    
    def test_cannot_load_other_formats(self):
        """Test that loader cannot load non-text files"""
        loader = TextDocumentLoader()
        assert loader.can_load("document.pdf") is False
        assert loader.can_load("document.docx") is False
    
    def test_load_text_file(self):
        """Test loading a text file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content.\nLine 2.")
            temp_file = f.name
        
        try:
            loader = TextDocumentLoader()
            documents = loader.load(temp_file)
            
            assert len(documents) == 1
            assert "test content" in documents[0].page_content
            assert documents[0].metadata['file_type'] == '.txt'
        finally:
            Path(temp_file).unlink()
    
    def test_load_empty_text_file(self):
        """Test loading an empty text file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name
        
        try:
            loader = TextDocumentLoader()
            documents = loader.load(temp_file)
            
            assert len(documents) == 1
            assert documents[0].page_content == ""
        finally:
            Path(temp_file).unlink()
    
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist"""
        loader = TextDocumentLoader()
        
        with pytest.raises(Exception):
            loader.load("/nonexistent/path/file.txt")


class TestDocumentLoaderFactory:
    """Test suite for DocumentLoaderFactory"""
    
    def test_factory_creation(self):
        """Test creating a factory"""
        factory = DocumentLoaderFactory()
        assert factory is not None
        assert len(factory.loaders) > 0
    
    def test_get_text_loader(self):
        """Test getting loader for text file"""
        factory = DocumentLoaderFactory()
        loader = factory.get_loader("document.txt")
        
        assert loader is not None
        assert isinstance(loader, TextDocumentLoader)
    
    def test_get_pdf_loader(self):
        """Test getting loader for PDF file"""
        factory = DocumentLoaderFactory()
        loader = factory.get_loader("document.pdf")
        
        # PDF loader might not be available if pypdf is not installed
        # but the factory should still be created
        if loader is not None:
            assert loader.can_load("document.pdf")
        else:
            # This is acceptable if pypdf is not installed
            assert True
    
    def test_no_loader_for_unsupported_format(self):
        """Test that factory returns None for unsupported formats"""
        factory = DocumentLoaderFactory()
        loader = factory.get_loader("document.xyz")
        
        assert loader is None
    
    def test_load_with_factory(self):
        """Test loading a document using factory"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Factory test content")
            temp_file = f.name
        
        try:
            factory = DocumentLoaderFactory()
            documents = factory.load(temp_file)
            
            assert len(documents) > 0
            assert "Factory test" in documents[0].page_content
        finally:
            Path(temp_file).unlink()
    
    def test_load_unsupported_file_raises_error(self):
        """Test that loading unsupported format raises ValueError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            temp_file = f.name
        
        try:
            factory = DocumentLoaderFactory()
            with pytest.raises(ValueError):
                factory.load(temp_file)
        finally:
            Path(temp_file).unlink()


class TestBulkDocumentLoader:
    """Test suite for BulkDocumentLoader"""
    
    def test_bulk_loader_creation(self):
        """Test creating a bulk loader"""
        loader = BulkDocumentLoader()
        assert loader is not None
        assert loader.loaded_documents == []
        assert loader.failed_files == []
    
    def test_load_files_list(self):
        """Test loading a list of files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = Path(temp_dir) / "file1.txt"
            file2 = Path(temp_dir) / "file2.txt"
            
            file1.write_text("Content 1")
            file2.write_text("Content 2")
            
            loader = BulkDocumentLoader()
            documents = loader.load_files([str(file1), str(file2)])
            
            assert len(documents) >= 2
    
    def test_load_from_directory(self):
        """Test loading all files from a directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = Path(temp_dir) / "doc1.txt"
            file2 = Path(temp_dir) / "doc2.txt"
            
            file1.write_text("Document 1")
            file2.write_text("Document 2")
            
            loader = BulkDocumentLoader()
            documents = loader.load_from_directory(temp_dir, recursive=False)
            
            assert len(documents) >= 2
    
    def test_load_from_directory_recursive(self):
        """Test recursive directory loading"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directories
            subdir = Path(temp_dir) / "subdir"
            subdir.mkdir()
            
            file1 = Path(temp_dir) / "doc1.txt"
            file2 = subdir / "doc2.txt"
            
            file1.write_text("Document 1")
            file2.write_text("Document 2")
            
            loader = BulkDocumentLoader()
            documents = loader.load_from_directory(temp_dir, recursive=True)
            
            assert len(documents) >= 2
    
    def test_load_from_nonexistent_directory(self):
        """Test loading from non-existent directory raises error"""
        loader = BulkDocumentLoader()
        
        with pytest.raises(ValueError):
            loader.load_from_directory("/nonexistent/path")
    
    def test_get_statistics(self):
        """Test getting loading statistics"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "doc1.txt"
            file1.write_text("Test content")
            
            loader = BulkDocumentLoader()
            loader.load_files([str(file1)])
            
            stats = loader.get_statistics()
            
            assert 'total_documents' in stats
            assert 'total_pages' in stats
            assert 'total_size_bytes' in stats
            assert 'failed_count' in stats
            assert 'success_rate' in stats
    
    def test_load_with_extension_filter(self):
        """Test loading with file extension filter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "doc1.txt"
            file2 = Path(temp_dir) / "doc2.txt"
            
            file1.write_text("Text 1")
            file2.write_text("Text 2")
            
            loader = BulkDocumentLoader()
            documents = loader.load_from_directory(
                temp_dir,
                recursive=False,
                extensions=['.txt']
            )
            
            assert len(documents) >= 2
    
    def test_failed_files_tracking(self):
        """Test that failed files are tracked"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "doc1.txt"
            file1.write_text("Valid content")
            
            loader = BulkDocumentLoader()
            documents = loader.load_files([str(file1)])
            
            # After loading valid file
            assert len(loader.failed_files) == 0


class TestDocumentContent:
    """Test suite for document content and metadata"""
    
    def test_document_metadata_structure(self):
        """Test that loaded documents have proper metadata structure"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document")
            temp_file = f.name
        
        try:
            loader = TextDocumentLoader()
            documents = loader.load(temp_file)
            
            doc = documents[0]
            assert hasattr(doc, 'page_content')
            assert hasattr(doc, 'metadata')
            assert isinstance(doc.metadata, dict)
            assert 'source' in doc.metadata
            assert 'file_type' in doc.metadata
        finally:
            Path(temp_file).unlink()
    
    def test_multiple_document_pages(self):
        """Test metadata for multi-page documents"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            content = "Page 1\n" + "=" * 50 + "\nPage 2"
            f.write(content)
            temp_file = f.name
        
        try:
            loader = TextDocumentLoader()
            documents = loader.load(temp_file)
            
            assert len(documents) == 1
            doc = documents[0]
            assert "Page 1" in doc.page_content
            assert "Page 2" in doc.page_content
        finally:
            Path(temp_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
