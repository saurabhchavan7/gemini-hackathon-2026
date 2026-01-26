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
from agents.capture_agent import transcribe_audio

from fastapi import WebSocket, WebSocketDisconnect, Query
import asyncio
from google import genai

from models.database import init_database, get_connection
from agents.capture_agent import process_capture  # Import the new agent
from models.firestore_db import firestore_client

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


@app.websocket("/ws/transcribe")
async def ws_transcribe(websocket: WebSocket, token: str = Query(default="")):
    """
    Client sends binary PCM16 (16kHz mono) frames.
    Server streams to Gemini Live, returns partial transcripts as JSON text frames.
    """
    await websocket.accept()

    # TODO (optional): verify JWT token here (you already verify in HTTP routes).
    # For now keep it permissive during dev:
    # if not token: await websocket.close(code=4401); return

    client = genai.Client()

    MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
    CONFIG = {
        "response_modalities": ["TEXT"],
        "system_instruction": (
            "You are a transcription engine. "
            "Transcribe the user's speech verbatim. "
            "Return only transcript text, no extra commentary."
        ),
    }

    try:
        async with client.aio.live.connect(model=MODEL, config=CONFIG) as live_session:

            async def forward_audio():
                while True:
                    data = await websocket.receive_bytes()  # PCM16 bytes
                    # Gemini Live wants PCM audio
                    await live_session.send_realtime_input(
                        audio={"data": data, "mime_type": "audio/pcm;rate=16000"}
                    )

            async def forward_text():
                while True:
                    turn = live_session.receive()
                    async for resp in turn:
                        # Extract text parts (best-effort; message structure varies)
                        text_out = None
                        if getattr(resp, "server_content", None) and getattr(resp.server_content, "model_turn", None):
                            parts = resp.server_content.model_turn.parts or []
                            for p in parts:
                                # Some SDK builds provide p.text
                                if getattr(p, "text", None):
                                    text_out = (text_out or "") + p.text

                        if text_out:
                            await websocket.send_json({"type": "partial", "text": text_out})

            async with asyncio.TaskGroup() as tg:
                tg.create_task(forward_audio())
                tg.create_task(forward_text())

    except WebSocketDisconnect:
        return
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})
        await websocket.close()


@app.post("/api/capture")
async def capture_screenshot(
    screenshot_path: str = Form(...),
    app_name: str = Form("Unknown"),
    window_title: str = Form("Unknown"),
    url: str = Form(""),
    timestamp: str = Form(""),
    text_note: str = Form(None),  # Optional text annotation
    audio_note: UploadFile = File(None),  # Optional audio file
    audio_path: str = Form(None),
    authorization: str = Header(None),  # JWT token
    audio_transcript: str = Form(None),

):
    """
    Enhanced capture endpoint with multi-modal input
    """
    
    # 1. Verify JWT token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt_manager.verify_jwt_token(token)
        user_id = payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # 2. Generate capture ID (no file write)
    item_id = str(uuid.uuid4())[:8]

    # 2. Save screenshot
    # item_id = str(uuid.uuid4())[:8]
    # filename = f"{item_id}.png"
    # filepath = os.path.join(CAPTURES_DIR, filename)
    
    # contents = await screenshot.read()
    # with open(filepath, "wb") as f:
    #     f.write(contents)
    
    # 3. Save audio note if provided
    
    if audio_note:
        audio_filename = f"{item_id}_audio.webm"
        audio_path = os.path.join(CAPTURES_DIR, audio_filename)
        audio_contents = await audio_note.read()
        with open(audio_path, "wb") as f:
            f.write(audio_contents)
    
    # 4. Analyze with Gemini
    analysis_context = f"User note: {text_note}" if text_note else ""
    analysis = process_capture(item_id, screenshot_path, context=analysis_context)
    audio_transcript = None
    if audio_path:
        audio_transcript = transcribe_audio(audio_path)

    # # 5. Save to database (add user_id, text_note, audio_path)
    # conn = get_connection()
    # cursor = conn.cursor()
    
    # cursor.execute("""
    #     INSERT INTO items (
    #         id, user_id,
    #         screenshot_path,
    #         audio_path,
    #         text_note,
    #         audio_transcript,
    #         app_name, window_title, url, timestamp,
    #         extracted_text, content_type, title, entities, deadline,
    #         created_at, updated_at
    #     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    # """, (
    #     item_id,
    #     user_id,
    #     screenshot_path,
    #     audio_path,
    #     text_note,
    #     audio_transcript,
    #     app_name,
    #     window_title,
    #     url,
    #     timestamp,
    #     analysis["extracted_text"],
    #     analysis["content_type"],
    #     analysis["title"],
    #     json.dumps(analysis["entities"]),
    #     analysis["deadline"],
    #     datetime.now().isoformat(), datetime.now().isoformat()
    # ))
    
    # conn.commit()
    # conn.close()

    # 5. PREPARE DATA FOR FIRESTORE (No SQL query needed!)
    capture_data = {
        "item_id": item_id,
        "user_id": user_id,
        "screenshot_path": screenshot_path,
        "audio_path": audio_path,
        "text_note": text_note,
        "audio_transcript": audio_transcript,
        "app_name": app_name,
        "window_title": window_title,
        "url": url,
        "timestamp": timestamp,
        # Flatten analysis data directly
        "extracted_text": analysis.get("extracted_text"),
        "content_type": analysis.get("content_type"),
        "title": analysis.get("title"),
        "entities": analysis.get("entities"), # Pass as dict/list, not string
        "deadline": analysis.get("deadline"),
        "is_archived": False
    }

    # SAVE TO FIRESTORE
    firestore_client.save_capture(user_id, capture_data)

    print("audio_path:", audio_path)
    print("text_note:", text_note)  
    
    return {
        "success": True,
        "item_id": item_id,
        "message": "Capture saved to Cloud Firestore"
    }


# @app.get("/api/items")
# def get_items(limit: int = 50):
#     """Get recent captures"""
#     conn = get_connection()
#     conn.row_factory = sqlite3.Row
#     cursor = conn.cursor()
    
#     cursor.execute("""
#         SELECT * FROM items 
#         WHERE is_archived = 0
#         ORDER BY created_at DESC
#         LIMIT ?
#     """, (limit,))
    
#     items = [dict(row) for row in cursor.fetchall()]
#     conn.close()
    
#     return {"items": items, "total": len(items)}


@app.get("/api/items")
def get_items(limit: int = 50, authorization: str = Header(None)):
    # Verify User ID from token
    if not authorization: return {"items": []}
    token = authorization.replace("Bearer ", "")
    user_id = jwt_manager.verify_jwt_token(token)["user_id"]

    # Fetch from Firestore
    items = firestore_client.get_user_captures(user_id, limit)
    
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