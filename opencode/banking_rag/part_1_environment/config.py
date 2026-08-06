"""
Configuration module for Banking RAG Assistant
Handles environment variables and application settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Keys
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    voyage_api_key: str = Field(default="", alias="VOYAGE_API_KEY")
    
    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="banking_rag", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")
    
    # FAISS Configuration
    faiss_index_path: str = Field(default="./data/faiss_index", alias="FAISS_INDEX_PATH")
    
    # Application Configuration
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    
    # Streamlit Configuration
    streamlit_server_port: int = Field(default=8501, alias="STREAMLIT_SERVER_PORT")
    streamlit_server_headless: bool = Field(default=True, alias="STREAMLIT_SERVER_HEADLESS")
    
    # Model Configuration
    embedding_model: str = "voyage-3"
    chat_model: str = "claude-3-sonnet-20240229"
    temperature: float = 0.7
    max_tokens: int = 2048
    
    # Chunking Configuration
    chunk_size: int = 1024
    chunk_overlap: int = 200
    
    # RAG Configuration
    top_k_retrieval: int = 5
    similarity_threshold: float = 0.5
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path"""
        return Path(__file__).parent.parent / "data"


# Load settings
settings = Settings()
