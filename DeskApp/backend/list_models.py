"""
List all available Gemini models
"""

from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("📋 Available Models:\n")

for model in client.models.list():
    print(f"  - {model.name}")
