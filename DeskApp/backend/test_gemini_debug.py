"""
Test Gemini 3 Vision - Debug version
"""

from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()

# Create client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def test_gemini_vision(image_path: str):
    """Test Gemini's ability to analyze a screenshot"""
    
    print(f"🧠 Testing Gemini Vision with: {image_path}")
    
    # Read image bytes
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    print(f"📦 Image size: {len(image_bytes)} bytes")
    
    # Simple prompt
    prompt = "What do you see in this screenshot? Describe it briefly."

    # Send to Gemini - simpler format
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            prompt,
            types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        ]
    )
    
    # Debug: print full response
    print("\n🔍 Full response object:")
    print(f"   response.text: {response.text}")
    print(f"   response.candidates: {response.candidates}")
    
    if response.candidates:
        for i, candidate in enumerate(response.candidates):
            print(f"   Candidate {i}: {candidate}")
    
    return response.text


if __name__ == "__main__":
    captures_dir = "./captures"
    screenshots = [f for f in os.listdir(captures_dir) if f.endswith('.png')]
    
    if not screenshots:
        print("❌ No screenshots found!")
        exit(1)
    
    latest = sorted(screenshots)[-1]
    image_path = os.path.join(captures_dir, latest)
    
    print(f"📸 Found screenshot: {latest}")
    test_gemini_vision(image_path)