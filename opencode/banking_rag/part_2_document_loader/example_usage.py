"""
Example usage of the Document Loader with banking documents
"""

import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "part_1_environment"))

from document_loader import BulkDocumentLoader, DocumentLoaderFactory
from config import settings
from logger import log


def example_1_load_single_file():
    """Example 1: Load a single document"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Load Single Document")
    print("="*60)
    
    factory = DocumentLoaderFactory(logger=log)
    
    data_file = Path(__file__).parent.parent / "data" / "sample_banking_docs.txt"
    
    if not data_file.exists():
        print(f"Sample file not found: {data_file}")
        return
    
    try:
        documents = factory.load(str(data_file))
        print(f"\nSuccessfully loaded {len(documents)} document(s)")
        print(f"File: {data_file.name}")
        print(f"Content length: {len(documents[0].page_content)} characters")
        print(f"\nMetadata:")
        for key, value in documents[0].metadata.items():
            if key != "custom_metadata":
                print(f"  {key}: {value}")
        
        # Show first 200 characters of content
        content_preview = documents[0].page_content[:200]
        print(f"\nContent preview:\n{content_preview}...")
        
    except Exception as e:
        print(f"Error loading document: {e}")


def example_2_load_directory():
    """Example 2: Load all documents from a directory"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Load Directory with Filtering")
    print("="*60)
    
    loader = BulkDocumentLoader(logger=log)
    
    data_dir = Path(__file__).parent.parent / "data"
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return
    
    try:
        documents = loader.load_from_directory(
            str(data_dir),
            recursive=False,
            extensions=['.txt']
        )
        
        print(f"\nSuccessfully loaded {len(documents)} document(s)")
        print(f"Directory: {data_dir.name}")
        
        # Show statistics
        stats = loader.get_statistics()
        print(f"\nStatistics:")
        print(f"  Total documents: {stats['total_documents']}")
        print(f"  Total pages: {stats['total_pages']}")
        print(f"  Total size: {stats['total_size_bytes']:,} bytes")
        print(f"  Failed files: {stats['failed_count']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        
        # Show document summaries
        if documents:
            print(f"\nDocument Summaries:")
            for i, doc in enumerate(documents[:3], 1):  # Show first 3
                content = doc.page_content[:100].replace('\n', ' ')
                print(f"  {i}. {content}...")
        
    except Exception as e:
        print(f"Error loading directory: {e}")


def example_3_statistics():
    """Example 3: Get loading statistics"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Loading Statistics")
    print("="*60)
    
    loader = BulkDocumentLoader(logger=log)
    
    data_dir = Path(__file__).parent.parent / "data"
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return
    
    try:
        documents = loader.load_from_directory(
            str(data_dir),
            recursive=True,
            extensions=['.txt']
        )
        
        stats = loader.get_statistics()
        
        print("\nLoading Statistics Report:")
        print(f"  Total Documents Loaded: {stats['total_documents']}")
        print(f"  Total Pages: {stats['total_pages']}")
        print(f"  Total Size: {stats['total_size_bytes']:,} bytes "
              f"({stats['total_size_bytes']/1024:.2f} KB)")
        print(f"  Failed Files: {stats['failed_count']}")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        
        if loader.failed_files:
            print(f"\n  Failed Files:")
            for file_path, error in loader.failed_files:
                print(f"    - {file_path}: {error}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_4_metadata_extraction():
    """Example 4: Extract and display metadata"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Metadata Extraction")
    print("="*60)
    
    factory = DocumentLoaderFactory(logger=log)
    
    data_file = Path(__file__).parent.parent / "data" / "sample_banking_docs.txt"
    
    if not data_file.exists():
        print(f"Sample file not found: {data_file}")
        return
    
    try:
        documents = factory.load(str(data_file))
        doc = documents[0]
        
        print("\nExtracted Metadata:")
        print(f"  Source: {doc.metadata.get('source', 'N/A')}")
        print(f"  File Type: {doc.metadata.get('file_type', 'N/A')}")
        print(f"  File Size: {doc.metadata.get('file_size', 0):,} bytes")
        print(f"  Loaded At: {doc.metadata.get('loaded_at', 'N/A')}")
        print(f"  Modified Date: {doc.metadata.get('modified_date', 'N/A')}")
        
        print(f"\nContent Statistics:")
        print(f"  Characters: {len(doc.page_content):,}")
        print(f"  Words: {len(doc.page_content.split()):,}")
        print(f"  Lines: {len(doc.page_content.splitlines()):,}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_5_multiple_files():
    """Example 5: Load multiple specific files"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Load Multiple Files")
    print("="*60)
    
    loader = BulkDocumentLoader(logger=log)
    
    data_dir = Path(__file__).parent.parent / "data"
    file1 = data_dir / "sample_banking_docs.txt"
    
    if not file1.exists():
        print(f"Sample file not found: {file1}")
        return
    
    try:
        files_to_load = [str(file1)]
        documents = loader.load_files(files_to_load)
        
        print(f"\nSuccessfully loaded {len(documents)} document(s) from "
              f"{len(files_to_load)} file(s)")
        
        stats = loader.get_statistics()
        print(f"\nStatistics:")
        print(f"  Total documents: {stats['total_documents']}")
        print(f"  Total size: {stats['total_size_bytes']:,} bytes")
        print(f"  Failed: {stats['failed_count']}")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples"""
    print("\n")
    print("[" + "="*58 + "]")
    print("[" + " Banking RAG - Document Loader Examples ".center(58) + "]")
    print("[" + "="*58 + "]")
    
    try:
        example_1_load_single_file()
        example_2_load_directory()
        example_3_statistics()
        example_4_metadata_extraction()
        example_5_multiple_files()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
