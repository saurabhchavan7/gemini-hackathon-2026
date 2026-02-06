#!/usr/bin/env python3
"""
List all available Gemini models from Google Generative AI API
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

import google.generativeai as genai

# Configure with API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not set in .env file")
    exit(1)

genai.configure(api_key=api_key)

print("=" * 80)
print("Available Gemini Models")
print("=" * 80)

try:
    # List all available models
    models = genai.list_models()
    
    flash_models = []
    pro_models = []
    other_models = []
    
    for model in models:
        model_name = model.name
        display_name = model.display_name
        
        # Parse the actual model ID
        # Format: "models/gemini-2.0-flash-exp"
        if "flash" in model_name.lower():
            flash_models.append((model_name, display_name))
        elif "pro" in model_name.lower():
            pro_models.append((model_name, display_name))
        else:
            other_models.append((model_name, display_name))
    
    print("\n📱 FLASH MODELS (Fast & Efficient):")
    print("-" * 80)
    for name, display in flash_models:
        print(f"  • {name:45} | {display}")
    
    print("\n🚀 PRO MODELS (Advanced):")
    print("-" * 80)
    for name, display in pro_models:
        print(f"  • {name:45} | {display}")
    
    if other_models:
        print("\n📚 OTHER MODELS:")
        print("-" * 80)
        for name, display in other_models:
            print(f"  • {name:45} | {display}")
    
    print("\n" + "=" * 80)
    print(f"Total models available: {len(flash_models) + len(pro_models) + len(other_models)}")
    print("=" * 80)
    
except Exception as e:
    print(f"Error listing models: {e}")
    import traceback
    traceback.print_exc()
