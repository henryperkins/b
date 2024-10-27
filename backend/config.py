from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # Vector store settings
    VECTOR_STORE_TYPE: str = "faiss"  # or "chroma"
    FAISS_INDEX_PATH: str = "data/faiss_index"
    CHROMA_PERSIST_DIR: str = "data/chroma_db"
    
    # Embedding model settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    EMBEDDING_DEVICE: str = "cpu"
    
    # RAG settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MIN_SIMILARITY_SCORE: float = 0.7
    
    # Additional settings
    GOOGLE_API_KEY: str
    MAX_HISTORY_LENGTH: int = 10
    TEMPERATURE: float = 0.7
    MAX_OUTPUT_TOKENS: int = 2048

    class Config:
        env_file = ".env"

settings = Settings()