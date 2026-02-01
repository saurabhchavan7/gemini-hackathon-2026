"""
LifeOS Capture Agent - Phase 2A
Analyzes screenshots with Gemini 3 Vision
"""

import base64
import json
from datetime import datetime
from pathlib import Path
import os

from matplotlib.style import context
from dotenv import load_dotenv

load_dotenv()

# Using google.genai (newer SDK)
from google import genai
from google.genai import types

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def analyze_screenshot(screenshot_path: str) -> dict:
    """
    Analyze a screenshot with Gemini 3 Vision
    Returns: extracted text, content type, entities, topic, deadline
    """
    
    print(f"🔍 Analyzing screenshot: {screenshot_path}")
    
    # Read image file
    with open(screenshot_path, "rb") as f:
        image_bytes = f.read()
    
    # Create prompt
    prompt = """Analyze this screenshot and extract the following information. Return as JSON only, no other text.

{
  "extracted_text": "All readable text from the screenshot (OCR)",
  "content_type": "One of: job_posting, article, product, video, social_post, document, email, chat, code, other",
  "title": "Main topic/title of the content",
  "entities": {
    "companies": ["list of company names"],
    "people": ["names of people mentioned"],
    "dates": ["any dates mentioned"],
    "prices": ["any prices or monetary amounts"],
    "locations": ["cities, countries, or locations"]
  },
  "deadline": "If a deadline/expiration date exists: YYYY-MM-DD, else null",
  "deadline_text": "How the deadline was expressed (e.g., 'Expires tomorrow', 'Apply by Feb 20')",
  "confidence": {
    "content_type": 0.0-1.0,
    "deadline": 0.0-1.0
  }
}

Be thorough with OCR. Extract EVERYTHING you can read."""


    try:
        # Send to Gemini 3 Flash (faster for vision tasks)
        response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/png"
            )
    ]
)
        
        # Parse response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        print("RAW GEMINI RESPONSE:")
        print(response.text)
        analysis = json.loads(response_text)
        
        print(f"✅ Analysis complete:")
        print(f"   Content Type: {analysis.get('content_type')}")
        print(f"   Title: {analysis.get('title')[:60]}..." if len(analysis.get('title', '')) > 60 else f"   Title: {analysis.get('title')}")
        if analysis.get('deadline'):
            print(f"   Deadline: {analysis.get('deadline')}")
        
        return analysis
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"   Response: {response.text[:200]}")
        return {
            "extracted_text": "",
            "content_type": "error",
            "title": "Analysis failed",
            "entities": {},
            "deadline": None,
            "error": str(e)
        }
    
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return {
            "extracted_text": "",
            "content_type": "error",
            "title": "Analysis failed",
            "entities": {},
            "deadline": None,
            "error": str(e)
        }


def process_capture(item_id: str, screenshot_path: str, context: None) -> dict:
    """
    Full capture processing pipeline:
    1. Analyze with Gemini
    2. Return structured data for storage
    """
    
    analysis = analyze_screenshot(screenshot_path)
    
    # Flatten for database storage
    result = {
        "item_id": item_id,
        "extracted_text": analysis.get("extracted_text", ""),
        "content_type": analysis.get("content_type", "unknown"),
        "title": analysis.get("title", ""),
        "entities": json.dumps(analysis.get("entities", {})),
        "deadline": analysis.get("deadline"),
        "deadline_text": analysis.get("deadline_text", ""),
        "confidence": json.dumps(analysis.get("confidence", {}))
    }
    
    return result



# def transcribe_audio(audio_path: str) -> str | None:
#     try:
#         if not audio_path or not os.path.exists(audio_path):
#             return None

#         with open(audio_path, "rb") as f:
#             audio_bytes = f.read()

#         response = client.models.generate_content(
#             model="gemini-3-flash-preview",
#             contents=[
#                 genai.types.Part.from_bytes(
#                     data=audio_bytes,
#                     mime_type="audio/webm"
#                 )
#             ]
#         )

#         transcript = response.text.strip()
#         return transcript if transcript else None

#     except Exception as e:
#         print("❌ Gemini audio transcription failed:", e)
#         return None


def transcribe_audio(audio_path: str) -> str | None:
    """
    Transcribe audio file using Gemini 2.0 Flash.
    Optimized for high accuracy and minimal 'hallucination'.
    """
    try:
        if not audio_path or not os.path.exists(audio_path):
            print(f"⚠️ File not found: {audio_path}")
            return None

        print(f"🎤 Transcribing audio: {audio_path}")

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # System instructions ground the model better than user prompts
        instruction = "You are a professional transcriptionist. Transcribe the audio exactly as heard. Do not add commentary or descriptions."

        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/webm"
                ),
                "Transcribe this audio. If silent, return [inaudible]."
            ],
            config=types.GenerateContentConfig(
                system_instruction=instruction,
                temperature=0.0, # Ensures consistency and prevents 'creative' transcripts
                top_p=0.95,
            )
        )

        if not response.text:
            return None

        transcript = response.text.strip()
        
        # Log success (shortened preview)
        preview = (transcript[:100] + '..') if len(transcript) > 100 else transcript
        print(f"✅ Transcribed: {preview}")
        
        return transcript

    except Exception as e:
        print(f"❌ Gemini transcription error: {e}")
        return None
    
if __name__ == "__main__":
    # Test with most recent screenshot
    captures_dir = Path("./captures")
    
    if not captures_dir.exists():
        print("❌ No captures directory found")
        exit(1)
    
    screenshots = list(captures_dir.glob("*.png"))
    if not screenshots:
        print("❌ No screenshots found")
        exit(1)
    
    latest = max(screenshots, key=lambda p: p.stat().st_mtime)
    print(f"📸 Testing with: {latest.name}")
    
    analysis = analyze_screenshot(str(latest))
    print("\n🔍 Full Analysis:")
    print(json.dumps(analysis, indent=2))
