"""
LifeOS Backend - Phase 2A
API with SQLite storage + Gemini Vision Analysis
"""

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import uuid
import sqlite3
import json

from models.database import init_database, get_connection
from agents.capture_agent import process_capture  # Import the new agent

app = FastAPI()

# Enable CORS for Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage path for screenshots
CAPTURES_DIR = "./captures"
os.makedirs(CAPTURES_DIR, exist_ok=True)

# Initialize database on startup
init_database()


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
    Receive a capture from Electron app:
    1. Save screenshot file
    2. Analyze with Gemini Vision
    3. Store to database
    """
    try:
        # Generate unique ID
        item_id = str(uuid.uuid4())[:8]
        
        # Save screenshot file
        filename = f"{item_id}.png"
        filepath = os.path.join(CAPTURES_DIR, filename)
        
        contents = await screenshot.read()
        with open(filepath, "wb") as f:
            f.write(contents)
        
        print(f"📸 Screenshot saved: {item_id}")
        
        # PHASE 2A: Analyze with Gemini
        print(f"🔍 Analyzing with Gemini...")
        analysis = process_capture(item_id, filepath)
        
        # Save to database
        conn = get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO items (
                id, screenshot_path, app_name, window_title, url, timestamp,
                extracted_text, content_type, title, entities, deadline, deadline_text,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id,
            filepath,
            app_name,
            window_title,
            url if url else None,
            timestamp or now,
            analysis.get("extracted_text", ""),
            analysis.get("content_type", "unknown"),
            analysis.get("title", ""),
            analysis.get("entities", ""),
            analysis.get("deadline"),
            analysis.get("deadline_text", ""),
            now,
            now
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Capture complete: {item_id}")
        print(f"   Content Type: {analysis.get('content_type')}")
        print(f"   Title: {analysis.get('title')[:50]}")
        
        return {
            "success": True,
            "item_id": item_id,
            "content_type": analysis.get("content_type"),
            "title": analysis.get("title"),
            "deadline": analysis.get("deadline"),
            "message": "Capture analyzed and saved"
        }
        
    except Exception as e:
        print(f"❌ Capture error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/items")
def get_items(limit: int = 50):
    """Get recent captures"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM items 
        WHERE is_archived = 0
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"items": items, "total": len(items)}


@app.get("/api/items/{item_id}")
def get_item(item_id: str):
    """Get a specific capture"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return {"error": "Item not found"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LifeOS Backend with Gemini Analysis...")
    print("💡 API running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)