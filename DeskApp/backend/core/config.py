"""
LifeOS - Global Configuration
Purpose: Centralizes all environment variables and constants
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the absolute path to the .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # Infrastructure & GCP Settings
    PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "gemini-hackathon-2026-484903")
    LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    
    # Gemini Model Versions
    PERCEPTION_MODEL: str = "gemini-2.5-flash"
    COGNITION_MODEL: str = "gemini-2.5-flash"
    ORCHESTRATOR_MODEL: str = "gemini-2.5-flash"
    RESEARCH_MODEL: str = "gemini-2.5-flash"
    
    # Firestore Collection Names
    COLLECTION_CAPTURES: str = "captures"
    COLLECTION_MEMORIES: str = "memories"
    COLLECTION_ACTIONS: str = "actions"
    COLLECTION_GRAPH: str = "graph_edges"
    COLLECTION_CALENDAR_EVENTS: str = "google_calendar_events"
    COLLECTION_TASKS: str = "google_tasks"
    COLLECTION_SHOPPING: str = "shopping_lists"
    COLLECTION_NOTES: str = "notes"

    # API Keys & Secrets
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-fallback-secret-here")
    
    # Google OAuth Settings (For Desktop App Login)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3001/auth/callback")
    
    # Google OAuth Settings (For API Access)
    GOOGLE_CREDENTIALS_FILE: str = "google_credentials.json"
    GOOGLE_TOKENS_DIR: str = "tokens"

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=str(env_path),
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()

# Debug print to confirm loading
if not settings.GOOGLE_API_KEY:
    print(f"[ERROR] API Key missing in: {env_path}")
else:
    print(f"[CONFIG] API Key loaded (starts with: {settings.GOOGLE_API_KEY[:5]}...)")