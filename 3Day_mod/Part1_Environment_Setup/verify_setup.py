"""
Environment verification script for the Banking KB RAG Assistant.

Run this after installing requirements.txt and creating shared/.env to
confirm the environment is ready before moving on to Part 2.

Usage:
    python verify_setup.py
"""
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_PACKAGES = [
    "dotenv",
    "docx",
    "tiktoken",
    "numpy",
    "sklearn",
    "openai",
    "voyageai",
    "faiss",
    "pgvector",
    "psycopg2",
    "sqlalchemy",
    "anthropic",
    "fastapi",
    "uvicorn",
    "pydantic",
    "streamlit",
    "requests",
    "pytest",
    "httpx",
]

CHECK_MARK = "[OK]"
CROSS_MARK = "[FAIL]"
WARN_MARK = "[WARN]"


def check_python_version() -> bool:
    ok = sys.version_info >= (3, 10)
    marker = CHECK_MARK if ok else CROSS_MARK
    print(f"{marker} Python version: {sys.version.split()[0]} (>= 3.10 required)")
    return ok


def check_packages() -> bool:
    print("\nChecking installed packages:")
    all_ok = True
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
            print(f"  {CHECK_MARK} {package}")
        except ImportError:
            print(f"  {CROSS_MARK} {package} -- not installed (pip install -r requirements.txt)")
            all_ok = False
    return all_ok


def check_env_file() -> bool:
    print("\nChecking configuration:")
    env_path = PROJECT_ROOT / "shared" / ".env"
    if not env_path.exists():
        print(f"  {CROSS_MARK} {env_path} not found -- copy shared/.env.example to shared/.env")
        return False
    print(f"  {CHECK_MARK} {env_path} found")

    try:
        from shared import config
    except Exception as exc:  # noqa: BLE001
        print(f"  {CROSS_MARK} Failed to import shared.config: {exc}")
        return False

    all_ok = True

    if config.EMBEDDING_PROVIDER == "openai" and not config.OPENAI_API_KEY:
        print(f"  {CROSS_MARK} EMBEDDING_PROVIDER=openai but OPENAI_API_KEY is empty")
        all_ok = False
    elif config.EMBEDDING_PROVIDER == "voyage" and not config.VOYAGE_API_KEY:
        print(f"  {CROSS_MARK} EMBEDDING_PROVIDER=voyage but VOYAGE_API_KEY is empty")
        all_ok = False
    else:
        print(f"  {CHECK_MARK} Embedding provider '{config.EMBEDDING_PROVIDER}' has an API key set")

    if not config.ANTHROPIC_API_KEY:
        print(f"  {WARN_MARK} ANTHROPIC_API_KEY is empty (needed later for Part 7 - Claude RAG pipeline)")
    else:
        print(f"  {CHECK_MARK} ANTHROPIC_API_KEY is set")

    if config.VECTOR_STORE == "pgvector" and not config.DATABASE_URL:
        print(f"  {CROSS_MARK} VECTOR_STORE=pgvector but DATABASE_URL is empty")
        all_ok = False
    else:
        print(f"  {CHECK_MARK} Vector store '{config.VECTOR_STORE}' is configured")

    return all_ok


def check_data_folder() -> bool:
    print("\nChecking knowledge base data:")
    data_dir = PROJECT_ROOT / "Data"
    if not data_dir.exists():
        print(f"  {CROSS_MARK} {data_dir} not found")
        return False

    docs = sorted(data_dir.glob("*.docx"))
    if not docs:
        print(f"  {CROSS_MARK} No .docx files found in {data_dir}")
        return False

    print(f"  {CHECK_MARK} {data_dir} found with {len(docs)} document(s):")
    for doc in docs:
        print(f"      - {doc.name}")
    return True


def check_storage_dirs() -> bool:
    print("\nChecking shared storage/log directories:")
    from shared import config

    all_ok = True
    for name, path in [("storage", config.STORAGE_DIR), ("logs", config.LOGS_DIR)]:
        if path.exists():
            print(f"  {CHECK_MARK} shared/{name} ready at {path}")
        else:
            print(f"  {CROSS_MARK} shared/{name} missing at {path}")
            all_ok = False
    return all_ok


def main() -> int:
    print("=" * 60)
    print("Banking KB RAG Assistant -- Environment Verification")
    print("=" * 60)

    results = [
        check_python_version(),
        check_packages(),
        check_env_file(),
        check_data_folder(),
        check_storage_dirs(),
    ]

    print("\n" + "=" * 60)
    if all(results):
        print(f"{CHECK_MARK} Environment is ready. Proceed to Part 2 (Document Loader).")
        return 0
    print(f"{CROSS_MARK} Environment is NOT ready. Fix the issues above and re-run this script.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
