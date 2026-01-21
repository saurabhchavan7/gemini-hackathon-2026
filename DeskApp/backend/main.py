"""
LifeOS Backend - Phase 1D
Simple API to receive and store captures from Electron app
"""

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import uuid
import json

app = FastAPI()

# Enable CORS for Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage paths
CAPTURES_DIR = "./captures"
METADATA_FILE = "./captures/metadata.json"

# Ensure captures directory exists
os.makedirs(CAPTURES_DIR, exist_ok=True)

# Load or create metadata store
def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {"items": []}

def save_metadata(data):
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.get("/")
def root():
    return {"status": "LifeOS Backend Running"}


@app.post("/api/capture")
async def capture_screenshot(
    screenshot: UploadFile = File(...),
    app_name: str = Form("Unknown"),
    window_title: str = Form("Unknown"),
    url: str = Form(""),
    timestamp: str = Form("")
):
    """
    Receive a capture from the Electron app
    
    Expects multipart form data with:
    - screenshot: PNG file
    - app_name: string
    - window_title: string  
    - url: string (optional)
    - timestamp: string
    """
    try:
        # Generate unique ID
        item_id = str(uuid.uuid4())[:8]
        
        # Save screenshot
        filename = f"{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(CAPTURES_DIR, filename)
        
        # Read and save the uploaded file
        contents = await screenshot.read()
        with open(filepath, "wb") as f:
            f.write(contents)
        
        # Create metadata entry
        item = {
            "id": item_id,
            "screenshot_path": filepath,
            "app_name": app_name,
            "window_title": window_title,
            "url": url if url else None,
            "timestamp": timestamp or datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            # Placeholders for AI processing (Phase 2)
            "content_type": None,
            "extracted_text": None,
            "entities": [],
            "intent": None,
            "tags": [],
            "urgency": None,
        }
        
        # Save to metadata
        metadata = load_metadata()
        metadata["items"].append(item)
        save_metadata(metadata)
        
        print(f"✅ Capture saved: {item_id}")
        print(f"   App: {app_name}")
        print(f"   Title: {window_title[:50]}{'...' if len(window_title) > 50 else ''}")
        print(f"   URL: {url or 'N/A'}")
        
        return {
            "success": True,
            "item_id": item_id,
            "message": "Capture saved successfully"
        }
        
    except Exception as e:
        print(f"❌ Capture error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/items")
def get_items(limit: int = 50):
    """Get recent captures"""
    metadata = load_metadata()
    items = metadata.get("items", [])
    return {
        "items": items[-limit:][::-1],  # Most recent first
        "total": len(items)
    }


@app.get("/api/items/{item_id}")
def get_item(item_id: str):
    """Get a specific capture"""
    metadata = load_metadata()
    for item in metadata["items"]:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LifeOS Backend...")
    print("📡 API running at http://localhost:8000")
    print("📖 Docs at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)