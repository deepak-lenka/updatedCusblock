import os
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Curiosity Blocks API"
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(default=os.getenv("OPENAI_API_KEY", ""))
    
    # Exa API settings
    EXA_API_KEY: str = Field(default=os.getenv("EXA_API_KEY", ""))
    EXA_BASE_URL: str = "https://api.exa.ai/search"
    
    # LLM settings
    DEFAULT_MODEL: str = "gpt-3.5-turbo-16k"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 4000
    
    # Memory settings
    MEMORY_TOKEN_LIMIT: int = 3000
    MAX_HISTORY: int = 10
    
    # Data directory
    DATA_DIR: str = Field(default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings object
settings = Settings()
