import os
from dotenv import load_dotenv

# Force Python to read the hidden .env file into memory
load_dotenv(os.path.join(os.getcwd(), '.env'))
load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI BI Copilot"
    API_V1_STR: str = "/api/v1"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
    
    # Allow all origins for development and deployment connectivity
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

# Instantiate for the application
settings = Settings()
