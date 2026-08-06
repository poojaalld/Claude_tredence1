# Part 2: Document Loader

This module handles loading documents from various file formats and extracting their content with preserved metadata.

## Overview

The document loader module provides:
- Support for multiple file formats (TXT, PDF, DOCX)
- Automatic format detection and appropriate loader selection
- Metadata preservation (source, file type, size, dates, page numbers)
- Batch processing of multiple files and directories
- Comprehensive error handling and statistics
- Logging integration for tracking operations

## Supported Formats

### Text Files (.txt)
- Plain text documents
- UTF-8 encoding support
- No dependencies required

### PDF Files (.pdf)
- Requires: `pypdf` library
- Extracts text from each page
- Preserves page numbers in metadata
- Install: `pip install pypdf`

### DOCX Files (.docx)
- Microsoft Word documents
- Requires: `python-docx` library
- Extracts paragraphs and tables
- Install: `pip install python-docx`

## Classes

### DocumentMetadata
Dataclass for storing document metadata:
```python
@dataclass
class DocumentMetadata:
    source: str                    # File path
    file_type: str                 # File extension
    file_size: int                 # File size in bytes
    loaded_at: str                 # ISO format timestamp
    num_pages: Optional[int]       # Number of pages (PDF only)
    title: Optional[str]           # Document title
    author: Optional[str]          # Document author
    created_date: Optional[str]    # Creation date
    modified_date: Optional[str]   # Last modified date
    custom_metadata: Optional[Dict] # Additional metadata
```

### BaseDocumentLoader
Abstract base class for all loaders:
```python
class BaseDocumentLoader(ABC):
    def can_load(self, file_path) -> bool: ...
    def load(self, file_path) -> List[Document]: ...
```

### Loader Classes
- **TextDocumentLoader**: Loads .txt files
- **PDFDocumentLoader**: Loads .pdf files
- **DocxDocumentLoader**: Loads .docx files

### DocumentLoaderFactory
Factory pattern for automatic loader selection:
```python
factory = DocumentLoaderFactory()
docs = factory.load("path/to/document.txt")
```

Gracefully handles missing optional dependencies.

### BulkDocumentLoader
Batch processor for multiple documents:
```python
loader = BulkDocumentLoader()

# Load from directory
docs = loader.load_from_directory("./documents")

# Load specific files
docs = loader.load_files(["doc1.txt", "doc2.pdf"])

# Get statistics
stats = loader.get_statistics()
```

## Usage Examples

### Load Single File
```python
from part_2_document_loader import DocumentLoaderFactory

factory = DocumentLoaderFactory()
documents = factory.load("banking_document.txt")

for doc in documents:
    print(f"Source: {doc.metadata['source']}")
    print(f"Content length: {len(doc.page_content)}")
```

### Load from Directory
```python
from part_2_document_loader import BulkDocumentLoader

loader = BulkDocumentLoader()
documents = loader.load_from_directory(
    "./data/documents",
    recursive=True,
    extensions=['.txt', '.pdf']
)

print(f"Loaded {len(documents)} documents")
```

### Load Specific Files
```python
loader = BulkDocumentLoader()
documents = loader.load_files([
    "doc1.txt",
    "doc2.pdf",
    "doc3.docx"
])

stats = loader.get_statistics()
print(f"Total pages: {stats['total_pages']}")
print(f"Total size: {stats['total_size_bytes']} bytes")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

### With Logger
```python
from part_1_environment import log
from part_2_document_loader import BulkDocumentLoader

loader = BulkDocumentLoader(logger=log)
documents = loader.load_from_directory("./documents")
```

## Document Object Structure

LangChain Document structure:
```python
{
    "page_content": "...",  # The actual document text
    "metadata": {
        "source": "/path/to/file.txt",
        "file_type": ".txt",
        "file_size": 2048,
        "loaded_at": "2024-01-15T10:30:00.123456",
        "page_number": 1,          # PDF only
        "total_pages": 5,          # PDF only
        "modified_date": "2024-01-15T09:00:00"
    }
}
```

## Testing

Run the test suite:
```bash
pytest test_document_loader.py -v
```

Test coverage includes:
- Metadata creation and serialization
- Single file loading
- Directory loading (recursive and non-recursive)
- Multiple file loading
- Error handling
- Extension filtering
- Statistics calculation
- Failed file tracking

## Error Handling

### Missing Dependencies
If optional dependencies (pypdf, python-docx) are not installed:
- Factory will skip the loader and continue
- Warning messages are logged
- Text loader will always be available

### File Not Found
```python
try:
    docs = factory.load("nonexistent.txt")
except Exception as e:
    print(f"Error: {e}")
```

### Unsupported Format
```python
try:
    docs = factory.load("document.xyz")
except ValueError as e:
    print(f"Supported formats: .txt, .pdf, .docx")
```

## Integration with Part 1

The document loader integrates with Part 1's configuration and logging:

```python
from part_1_environment import settings, log
from part_2_document_loader import BulkDocumentLoader

loader = BulkDocumentLoader(logger=log)
docs = loader.load_from_directory(
    settings.data_dir / "raw_documents"
)
```

## Statistics

Get loading statistics from BulkDocumentLoader:

```python
stats = loader.get_statistics()
# {
#     'total_documents': 10,
#     'total_pages': 50,
#     'total_size_bytes': 102400,
#     'failed_count': 1,
#     'success_rate': 90.0
# }
```

## Known Limitations

1. **PDF**: Requires text to be extractable from PDF. Scanned image PDFs won't work.
2. **DOCX**: Extracts only text from paragraphs and tables. Shapes, images, and comments are ignored.
3. **Encoding**: Assumes UTF-8 encoding for text files.

## Performance Notes

- Large files: Consider batch processing with appropriate memory management
- Directory loading: Can be slow with many files; use extension filtering
- Metadata: Automatically preserved for all documents

## Next Steps

After document loading, proceed to:
- Part 3: Semantic Chunking - Split documents into semantic chunks
- Part 4: Embeddings - Generate embeddings for chunks
- Part 5: Indexing - Create vector indexes

## Files

- `document_loader.py` - Main implementation
- `__init__.py` - Module exports
- `test_document_loader.py` - Test suite
- `README.md` - This file

## Test Results

```
24 passed, 7 warnings
Success Rate: 100%

Tests cover:
- Metadata creation and conversion
- Text file loading
- Format detection
- Batch operations
- Error handling
- Statistics generation
- File filtering
```

## Future Enhancements

Potential additions:
- Support for HTML, Markdown, and XML files
- OCR support for scanned PDFs
- Document chunking at the loader level
- Parallel processing for large batches
- Document validation and verification
- Content preview and summarization
