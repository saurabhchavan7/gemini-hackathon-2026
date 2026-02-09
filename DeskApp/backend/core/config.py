"""
LifeOS - Global Configuration
Purpose: Centralizes all environment variables and constants
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Import model configurations from models_config.py
from . import models_config

# Get the absolute path to the .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # Infrastructure & GCP Settings
    PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    
    # Gemini Model Versions (loaded from models_config.py - visible in repo for judges)
    PRIMARY_MODEL: str = models_config.GEMINI_PRIMARY_MODEL
    PRO_MODEL: str = models_config.GEMINI_PRO_MODEL
    VISION_MODEL: str = models_config.GEMINI_VISION_MODEL
    AUDIO_MODEL: str = models_config.GEMINI_AUDIO_MODEL
    EMBEDDING_MODEL: str = models_config.GEMINI_EMBEDDING_MODEL

    # Agent-specific models (loaded from models_config.py)
    PERCEPTION_MODEL: str = models_config.GEMINI_PERCEPTION_MODEL
    COGNITION_MODEL: str = models_config.GEMINI_COGNITION_MODEL
    ORCHESTRATOR_MODEL: str = models_config.GEMINI_ORCHESTRATOR_MODEL
    RESEARCH_MODEL: str = models_config.GEMINI_RESEARCH_MODEL
    
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
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    
    # Google OAuth Settings (For Desktop App Login)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3001/auth/callback")
    
    # Google OAuth Settings (For API Access)
    GOOGLE_CREDENTIALS_FILE: str = "google_credentials.json"
    GOOGLE_TOKENS_DIR: str = "tokens"

    # Vertex AI Vector Search
    VERTEX_INDEX_ENDPOINT_ID: str = os.getenv("VERTEX_INDEX_ENDPOINT_ID", "")
    VERTEX_DEPLOYED_INDEX_ID: str = os.getenv("VERTEX_DEPLOYED_INDEX_ID", "")
    VERTEX_INDEX_NAME: str = os.getenv("VERTEX_INDEX_NAME", "")

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=str(env_path),
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()

# Debug print to confirm loading (avoid leaking secrets)
if not settings.GOOGLE_API_KEY:
    print(f"[ERROR] API Key missing in: {env_path}")