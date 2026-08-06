"""
Setup script for Banking RAG Assistant
Initializes the project structure and dependencies
"""

import os
import sys
import subprocess
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def setup_project():
    """Initialize the project"""
    
    print("=" * 60)
    print("Banking RAG Assistant - Project Setup")
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Create .env from .env.example if it doesn't exist
    env_file = project_root / ".env"
    env_example = project_root / "part_1_environment" / ".env.example"
    
    print("\n1. Setting up environment file...")
    if not env_file.exists():
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("   [OK] Created .env from .env.example")
            print("   [WARN] Please edit .env and add your API keys!")
        else:
            print("   [ERROR] .env.example not found")
    else:
        print("   [OK] .env already exists")
    
    # Create data directories
    print("\n2. Creating data directories...")
    data_dirs = [
        project_root / "data" / "raw_documents",
        project_root / "data" / "processed_chunks",
        project_root / "data" / "embeddings",
        project_root / "logs",
    ]
    
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"   [OK] Created {dir_path.relative_to(project_root)}")
    
    # Install dependencies
    print("\n3. Installing dependencies...")
    requirements = project_root / "part_1_environment" / "requirements.txt"
    if requirements.exists():
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements)
            ])
            print("   [OK] Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("   [ERROR] Failed to install dependencies")
            return False
    else:
        print("   [ERROR] requirements.txt not found")
        return False
    
    # Run tests
    print("\n4. Running configuration tests...")
    test_file = project_root / "part_1_environment" / "test_config.py"
    if test_file.exists():
        try:
            os.chdir(project_root / "part_1_environment")
            subprocess.check_call([
                sys.executable, "-m", "pytest", "test_config.py", "-v"
            ])
            print("   [OK] All tests passed!")
        except subprocess.CalledProcessError:
            print("   [WARN] Some tests failed (this might be expected)")
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Start Part 2: Document Loader")
    print("\nFor more information, see part_1_environment/README.md")
    
    return True


if __name__ == "__main__":
    success = setup_project()
    sys.exit(0 if success else 1)
