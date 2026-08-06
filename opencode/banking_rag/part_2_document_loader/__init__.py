"""
Part 2: Document Loader Module
Handles loading documents from various formats (TXT, PDF, DOCX)
"""

from .document_loader import (
    DocumentMetadata,
    BaseDocumentLoader,
    TextDocumentLoader,
    PDFDocumentLoader,
    DocxDocumentLoader,
    DocumentLoaderFactory,
    BulkDocumentLoader,
)

__all__ = [
    "DocumentMetadata",
    "BaseDocumentLoader",
    "TextDocumentLoader",
    "PDFDocumentLoader",
    "DocxDocumentLoader",
    "DocumentLoaderFactory",
    "BulkDocumentLoader",
]
