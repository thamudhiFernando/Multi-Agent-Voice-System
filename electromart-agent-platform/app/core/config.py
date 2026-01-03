from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

#Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):

    """Application settings loaded from environment variables"""
    """used Pydantic BaseSettings for validation and type checking"""

    # Application Settings
    APP_NAME: str = "ElectroMart Multi-Agent System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2000

    # CrewAI Configuration
    CREWAI_TELEMETRY: bool = False
    ENABLE_ANALYTICS: bool = False

    # Vector Database Configuration
    CHROMA_PERSIST_DIRECTORY: str = str(BASE_DIR / "data"/ "chroma_db")
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Database Configuration
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/electromart.db"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Conversation Settings
    MAX_CONVERSATION_HISTORY: int = 10
    CONVERSATION_TIMEOUT_MINUTES: int = 30

    # Agent Configuration
    ORCHESTRATOR_TEMPERATURE: float = 0.3
    SUB_AGENT_TEMPERATURE: float = 0.7
    MAX_AGENT_ITERATIONS: int = 5

    # Voice Configuration
    VOICE_LANGUAGE: str = "en"
    VOICE_ACCENT: str = "com" #.com for US English

    # Sentiment Analysis
    ENABLE_SENTIMENT_ANALYSIS: bool = True
    NEGATIVE_SENTIMENT_THRESHOLD: float = -0.5

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = str(BASE_DIR / "logs" / "app.log")

    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # Data Paths
    PRODUCTS_DATA_PATH: str = str(BASE_DIR / "data" / "products.json")
    ORDERS_DATA_PATH: str = str(BASE_DIR / "data" / "orders.json")
    PROMOTIONS_DATA_PATH: str = str(BASE_DIR / "data" / "promotions.json")
    KNOWLEDGE_BASE_PATH: str = str(BASE_DIR / "data" / "knowledge_base.json")

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create a global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Dependency function to get instance of settings
    Its used FastAPI's Depends() for DI"""
    return settings