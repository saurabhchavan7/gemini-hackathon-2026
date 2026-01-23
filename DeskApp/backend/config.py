"""
config.py

Purpose: Centralized configuration for backend environment variables

Contains:
- Google OAuth credentials (Client ID, Client Secret)
- JWT signing secret
- Gemini API key
- Backend URLs and settings

Usage:
- Import: from config import GOOGLE_CLIENT_ID, JWT_SECRET
- All sensitive values loaded from .env file
- Never commit .env to version control
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# GOOGLE OAUTH CONFIGURATION
# ============================================

# OAuth Client ID from GCP Console
# Get from: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# OAuth Client Secret from GCP Console
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# OAuth redirect URI (must match what's configured in GCP)
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/callback")

# ============================================
# JWT CONFIGURATION
# ============================================

# Secret key for signing JWT tokens
# Generate with: openssl rand -hex 32
JWT_SECRET = os.getenv("JWT_SECRET")

# JWT algorithm
JWT_ALGORITHM = "HS256"

# JWT expiration time (in days)
JWT_EXPIRATION_DAYS = 30

# ============================================
# GEMINI API CONFIGURATION
# ============================================

# Gemini API key from Google AI Studio
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ============================================
# DATABASE CONFIGURATION
# ============================================

# Database type: "sqlite" or "firestore"
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")

# SQLite database path
SQLITE_DB_PATH = "./data/lifeos.db"

# Firestore project ID (if using Firestore)
FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID")

# Service account key path (if using Firestore)
SERVICE_ACCOUNT_KEY_PATH = os.getenv("SERVICE_ACCOUNT_KEY_PATH")

# ============================================
# BACKEND SETTINGS
# ============================================

# Backend port
PORT = int(os.getenv("PORT", "8000"))

# CORS allowed origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Debug mode
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# ============================================
# VALIDATION
# ============================================

def validate_config():
    """
    Validate that all required environment variables are set
    Raises ValueError if any required variable is missing
    """
    required_vars = {
        "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
        "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET,
        "JWT_SECRET": JWT_SECRET,
        "GEMINI_API_KEY": GEMINI_API_KEY
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(
            f"❌ Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please set them in your .env file"
        )
    
    print("✅ Configuration loaded successfully")
    print(f"   Database: {DATABASE_TYPE}")
    print(f"   Debug Mode: {DEBUG}")

# Validate on import (optional - comment out if you want to defer validation)
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"\n⚠️  Configuration Warning: {e}\n")
