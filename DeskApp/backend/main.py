"""
LifeOS Backend - Phase 2A
API with SQLite storage + Gemini Vision Analysis
"""
import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from auth import google_oauth, jwt_manager
from models import user
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

class LoginRequest(BaseModel):
    """Request body for login endpoint"""
    code: str  # Authorization code from OAuth callback


class LoginResponse(BaseModel):
    """Response from login endpoint"""
    token: str  # JWT token
    user: dict  # User information


@app.post("/auth/google/login")
async def google_login(request: LoginRequest):
    """
    Handle Google OAuth login
    
    Flow:
    1. Receive authorization code from frontend
    2. Exchange code for tokens with Google
    3. Verify ID token and extract user info
    4. Create/update user in database
    5. Generate JWT token
    6. Return JWT + user info to frontend
    
    Frontend will store JWT and use it for authenticated requests
    """
    
    try:
        print(f"\n🔐 Login request received")
        
        # Step 1: Exchange authorization code for tokens with Google
        user_info = google_oauth.authenticate_user(request.code)
        
        # Step 2: Create or update user in database
        user_data = user.create_or_update_user(
            user_id=user_info["user_id"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info["picture"]
        )
        
        # Step 3: Generate JWT token for this user
        jwt_token = jwt_manager.create_jwt_token(
            user_id=user_data["user_id"],
            email=user_data["email"]
        )
        
        # Step 4: Return JWT + user info
        response = {
            "token": jwt_token,
            "user": {
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "name": user_data["name"],
                "picture": user_data["picture"]
            }
        }
        
        print(f"✅ Login successful: {user_data['email']}\n")
        
        return response
        
    except Exception as e:
        print(f"❌ Login failed: {e}\n")
        raise HTTPException(
            status_code=400,
            detail=f"Login failed: {str(e)}"
        )


@app.get("/api/user/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current authenticated user information
    
    Protected endpoint - requires valid JWT token in Authorization header
    
    Header format: Authorization: Bearer <jwt_token>
    
    Returns user profile data from database
    """
    
    try:
        print(f"\n👤 User info request received")
        
        # Step 1: Extract JWT token from Authorization header
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Authorization header missing"
            )
        
        # Authorization header format: "Bearer <token>"
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format"
            )
        
        token = authorization.replace("Bearer ", "")
        
        # Step 2: Verify JWT token and extract user_id
        try:
            payload = jwt_manager.verify_jwt_token(token)
            user_id = payload["user_id"]
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid or expired token: {str(e)}"
            )
        
        # Step 3: Get user from database
        user_data = user.get_user(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Step 4: Return user info
        print(f"✅ User info retrieved: {user_data['email']}\n")
        
        return {
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data["picture"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to get user: {e}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user information: {str(e)}"
        )


@app.get("/health")
def health_check():
    """
    Health check endpoint
    Returns API status
    """
    return {
        "status": "healthy",
        "service": "LifeOS Backend",
        "version": "1.0.0"
    }


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