"""
LifeOS Backend - Phase 3 (Agentic Integration)
"""
import os
import sys
import uuid
import json
import asyncio
from datetime import datetime
from typing import Optional

# 1. Standard FastAPI imports
from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

# 2. Existing Auth and Local Database logic
from auth import google_oauth, jwt_manager
from models import user
from models.database import init_database, get_connection

# 3. Agentic Architecture Imports
from agents.perception.capture_agent import PerceptionAgent
from agents.cognition.intent_agent import IntentAgent
from agents.orchestrator.planning_agent import PlanningAgent
from agents.research_agent import ResearchAgent
from services.firestore_service import FirestoreService
from models.capture import Capture, CaptureMetadata
from models.memory import Memory
from core.event_bus import bus
from agents.proactive_agent import ProactiveAgent
from agents.synthesis_agent import SynthesisAgent
from agents.graph_agent import GraphAgent
from agents.resource_finder_agent import ResourceFinderAgent

# Initialize FastAPI
app = FastAPI()

# Enable CORS for Electron
app.add_middleware(
 CORSMiddleware,
 allow_origins=[
 "http://localhost:3000",
 "http://127.0.0.1:3000",
 ],
 allow_credentials=True,
 allow_methods=["*"],
 allow_headers=["*"],
)
# Storage path for screenshots
CAPTURES_DIR = "./captures"
os.makedirs(CAPTURES_DIR, exist_ok=True)

# Initialize database on startup for Auth/User tables
init_database()

# Initialize Agents AFTER all imports
orchestrator = PlanningAgent()
researcher = ResearchAgent()
proactive = ProactiveAgent()
resource_finder = ResourceFinderAgent() 

# Subscribe Agents to the Event Bus
# Subscribe with priorities
bus.subscribe("intent_analyzed", orchestrator.process, priority=1) # Runs first
bus.subscribe("intent_analyzed", researcher.process, priority=2)
bus.subscribe("intent_analyzed", proactive.process, priority=3) # Runs last
bus.subscribe("intent_analyzed", resource_finder.process, priority=4)

# ============================================
# AUTH ENDPOINTS
# ============================================

class LoginRequest(BaseModel):
 """Request body for login endpoint"""
 code: str

class LoginResponse(BaseModel):
 """Response from login endpoint"""
 token: str
 user: dict

@app.post("/auth/google/login")
async def google_login(request: LoginRequest):
    """Handle Google OAuth login"""
    try:
        print("[AUTH] Login request received")
        
        user_info = google_oauth.authenticate_user(request.code)
        user_data = user.create_or_update_user(
            user_id=user_info["user_id"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info["picture"]
        )
        
        jwt_token = jwt_manager.create_jwt_token(
            user_id=user_data["user_id"],
            email=user_data["email"]
        )
        
        response = {
            "token": jwt_token,
            "user": {
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "name": user_data["name"],
                "picture": user_data["picture"]
            }
        }
        
        print(f"[AUTH] Login successful: {user_data['email']}")
        return response
        
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")

@app.get("/api/user/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current authenticated user information"""
    try:
        print("[API] User info request received")
        
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = authorization.replace("Bearer ", "")
        
        try:
            payload = jwt_manager.verify_jwt_token(token)
            user_id = payload["user_id"]
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
        
        user_data = user.get_user(user_id)
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        print(f"[API] User info retrieved: {user_data['email']}")
        
        return {
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data["picture"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user information: {str(e)}")
# ============================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LifeOS Backend",
        "version": "1.0.0"
    }


@app.get("/")
def root():
    """Root endpoint"""
    return {"status": "LifeOS Backend Running"}


@app.websocket("/ws/transcribe")
async def ws_transcribe(websocket: WebSocket, token: str = Query(default="")):
    """WebSocket endpoint for real-time transcription"""
    await websocket.accept()
    
    from google import genai
    from core.config import settings


    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
 
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
                    data = await websocket.receive_bytes()
                    await live_session.send_realtime_input(
                        audio={"data": data, "mime_type": "audio/pcm;rate=16000"}
                    )

            async def forward_text():
                while True:
                    turn = live_session.receive()
                    async for resp in turn:
                        text_out = None
                        if getattr(resp, "server_content", None) and getattr(resp.server_content, "model_turn", None):
                            parts = resp.server_content.model_turn.parts or []
                            for p in parts:
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
async def handle_capture(
    screenshot_path: str = Form(...),
    app_name: str = Form("Unknown"),
    window_title: str = Form("Unknown"),
    url: str = Form(""),
    timestamp: str = Form(""),
    text_note: str = Form(None),
    audio_path: str = Form(None),
    timezone: str = Form("UTC"),
    authorization: str = Header(None)
):
    """Multi-Agent Capture Pipeline"""
    
    # Auth Check
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]

    # Setup Agents
    perception = PerceptionAgent()
    cognition = IntentAgent()
    db = FirestoreService()

    try:
        # Read Files
        with open(screenshot_path, "rb") as f:
            screenshot_bytes = f.read()
        
        audio_bytes = None
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

        # AGENT 1: Perception
        print("[Agent 1] Perception analyzing...")
        raw_result = await perception.process(
            screenshot_bytes=screenshot_bytes, 
            audio_bytes=audio_bytes
        )

        # AGENT 2: Cognition
        print("[Agent 2] Cognition determining intent...")
        combined_context = f"{raw_result.ocr_text}\nTranscript: {raw_result.audio_transcript}\nNote: {text_note}"
        intent_result = await cognition.process(text_content=combined_context)

        # Save to Firestore
        capture_id = str(uuid.uuid4())
        capture_doc = Capture(
            id=capture_id,
            user_id=user_id,
            capture_type="multi-modal" if audio_path else "screenshot",
            screenshot_path=screenshot_path,
            audio_path=audio_path,
            context=CaptureMetadata(
                app_name=app_name,
                window_title=window_title,
                url=url,
                platform="windows",
                timezone=timezone if timezone else "UTC"
            )
        )

        memory_doc = Memory(
            id=capture_id,
            capture_ref=capture_id,
            user_id=user_id,
            title=intent_result.one_line_summary,
            one_line_summary=intent_result.one_line_summary,
            full_transcript=raw_result.ocr_text,
            category=intent_result.category,
            intent=intent_result.intent,
            tags=intent_result.tags
        )

        await db.save_capture(capture_doc)
        await db.save_memory(memory_doc)

        # Emit event to background agents
        user_timezone = capture_doc.context.timezone if capture_doc.context.timezone else "UTC"
        
        print(f"[CAPTURE] Emitting event for intent: {intent_result.intent}")
        print(f"[CAPTURE] User timezone: {user_timezone}")

        event_data = {
            "intent": intent_result.intent,
            "summary": intent_result.one_line_summary,
            "user_id": user_id,
            "full_context": combined_context,
            "tags": intent_result.tags,
            "priority": intent_result.priority,
            "actionable_items": intent_result.actionable_items,
            "user_timezone": user_timezone
        }
        
        asyncio.create_task(bus.emit("intent_analyzed", event_data))

        return {
            "success": True, 
            "item_id": capture_id, 
            "summary": intent_result.one_line_summary,
            "intent": intent_result.intent
        }

    except Exception as e:
        print(f"[ERROR] Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 
# Initialize synthesis agent (manual trigger only)
synthesis_agent = SynthesisAgent()

@app.post("/api/synthesize")
async def synthesize_memories(
    memory_ids: list[str] = Form(...),
    authorization: str = Header(None)
):
    """Manually trigger synthesis of multiple memories"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        # Mock data for testing (implement db.get_memory later)
        memories = [
            {
                "title": "Tokyo Travel Research",
                "one_line_summary": "Found great hotel in Shibuya",
                "category": "Travel",
                "tags": ["japan", "tokyo", "hotel"]
            },
            {
                "title": "Restaurant Recommendations",
                "one_line_summary": "Top ramen spots in Tokyo",
                "category": "Travel", 
                "tags": ["japan", "food", "ramen"]
            }
        ]
        
        result = await synthesis_agent.synthesize_memories(memories)
        return result
        
    except Exception as e:
        print(f"[ERROR] Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/items")
def get_items(limit: int = 50, authorization: str = Header(None)):
    """Get recent captures from Firestore"""
    if not authorization:
        return {"items": []}
    
    token = authorization.replace("Bearer ", "")
    user_id = jwt_manager.verify_jwt_token(token)["user_id"]
    
    return {"items": [], "total": 0}


@app.get("/api/items/{item_id}")
def get_item(item_id: str):
    """Get a specific capture"""
    return {"error": "Not implemented yet"}


@app.post("/api/graph/analyze")
async def analyze_knowledge_graph(authorization: str = Header(None)):
    """Manually trigger graph analysis"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        memories = await db.get_user_memories(user_id, limit=20)
        
        if len(memories) < 2:
            return {
                "status": "skip",
                "message": "Need at least 2 memories to analyze"
            }
        
        connections = await graph_agent.process_batch(memories)
        
        for conn in connections:
            await db.save_graph_edge(user_id, conn)
        
        return {
            "status": "success",
            "memories_analyzed": len(memories),
            "connections_found": len(connections),
            "connections": connections
        }
        
    except Exception as e:
        print(f"[ERROR] Graph analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph")
async def get_knowledge_graph(authorization: str = Header(None)):
    """Retrieve the user's knowledge graph"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        memories = await db.get_user_memories(user_id, limit=50)
        edges = await db.get_user_graph(user_id)
        
        return {
            "nodes": memories,
            "edges": edges,
            "summary": {
                "total_memories": len(memories),
                "total_connections": len(edges)
            }
        }
        
    except Exception as e:
        print(f"[ERROR] Graph retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inbox")
async def get_inbox(
    limit: int = 50,
    filter_intent: str = Query(None),
    authorization: str = Header(None)
):
    """Retrieves user's captured memories with AI insights"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        docs = db._get_user_ref(user_id).collection(settings.COLLECTION_MEMORIES).limit(limit).stream()
        
        memories = []
        for doc in docs:
            memory_data = doc.to_dict()
            memory_data['id'] = doc.id
            
            if filter_intent and memory_data.get('intent') != filter_intent:
                continue
            
            memories.append(memory_data)
        
        return {
            "success": True,
            "memories": memories,
            "total": len(memories)
        }
        
    except Exception as e:
        print(f"[ERROR] Inbox fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shopping-list")
async def get_shopping_list(authorization: str = Header(None)):
    """Get user's shopping list items"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        docs = db._get_user_ref(user_id).collection("shopping_lists").where("status", "==", "pending").stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items}
        
    except Exception as e:
        print(f"[ERROR] Shopping list fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar")
async def get_calendar_events(authorization: str = Header(None)):
    """Get user's calendar events"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        docs = db._get_user_ref(user_id).collection("calendar_events").where("status", "==", "scheduled").stream()
        
        events = []
        for doc in docs:
            event_data = doc.to_dict()
            event_data['id'] = doc.id
            events.append(event_data)
        
        return {"success": True, "events": events}
        
    except Exception as e:
        print(f"[ERROR] Calendar fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# GOOGLE INTEGRATIONS ENDPOINTS
# ============================================

@app.get("/api/google/calendar/events")
async def get_google_calendar_events(
    max_results: int = 20,
    authorization: str = Header(None)
):
    """Get user's Google Calendar events"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from services.google_calendar_service import GoogleCalendarService
        calendar_service = GoogleCalendarService(user_id)
        
        result = calendar_service.list_upcoming_events(max_results=max_results)
        
        if result['status'] == 'success':
            return {
                "success": True,
                "events": result['events'],
                "total": len(result['events'])
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Failed to fetch events'))
        
    except Exception as e:
        print(f"[ERROR] Calendar events fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/google/tasks")
async def get_google_tasks(
    max_results: int = 20,
    authorization: str = Header(None)
):
    """Get user's Google Tasks"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from services.google_tasks_service import GoogleTasksService
        tasks_service = GoogleTasksService(user_id)
        
        result = tasks_service.list_tasks(max_results=max_results)
        
        if result['status'] == 'success':
            return {
                "success": True,
                "tasks": result['tasks'],
                "total": len(result['tasks'])
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Failed to fetch tasks'))
        
    except Exception as e:
        print(f"[ERROR] Tasks fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/google/tasks/{task_id}/complete")
async def complete_google_task(
    task_id: str,
    authorization: str = Header(None)
):
    """Mark a Google Task as completed"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from services.google_tasks_service import GoogleTasksService
        tasks_service = GoogleTasksService(user_id)
        
        result = tasks_service.complete_task(task_id)
        
        if result['status'] == 'success':
            return {
                "success": True,
                "message": result['message']
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Failed to complete task'))
        
    except Exception as e:
        print(f"[ERROR] Task completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/google/sync-status")
async def get_google_sync_status(authorization: str = Header(None)):
    """Check if user has authenticated with Google APIs"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from services.google_auth_service import GoogleAuthService
        auth_service = GoogleAuthService(user_id)
        
        is_authenticated = auth_service.is_authenticated()
        
        return {
            "success": True,
            "authenticated": is_authenticated,
            "services": {
                "calendar": is_authenticated,
                "tasks": is_authenticated,
                "gmail": is_authenticated
            }
        }
        
    except Exception as e:
        print(f"[ERROR] Sync status check failed: {e}")
        return {
            "success": True,
            "authenticated": False,
            "services": {
                "calendar": False,
                "tasks": False,
                "gmail": False
            }
        }


@app.post("/api/google/authenticate")
async def authenticate_google(authorization: str = Header(None)):
    """Trigger Google OAuth flow for the user"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from services.google_auth_service import GoogleAuthService
        auth_service = GoogleAuthService(user_id)
        
        if auth_service.is_authenticated():
            return {
                "success": True,
                "message": "Already authenticated with Google",
                "authenticated": True
            }
        
        creds = auth_service.get_credentials()
        
        if creds and creds.valid:
            return {
                "success": True,
                "message": "Successfully authenticated with Google",
                "authenticated": True
            }
        else:
            raise HTTPException(status_code=500, detail="Authentication failed")
        
    except Exception as e:
        print(f"[ERROR] Google authentication failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/google/auth-url")
async def get_google_auth_url(authorization: str = Header(None)):
    """Get Google OAuth URL for first-time setup"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from services.google_auth_service import GoogleAuthService
        auth_service = GoogleAuthService(user_id)
        
        if auth_service.is_authenticated():
            return {
                "success": True,
                "authenticated": True,
                "message": "Already authenticated with Google"
            }
        
        auth_url = auth_service.get_auth_url()
        
        return {
            "success": True,
            "authenticated": False,
            "auth_url": auth_url,
            "message": "Visit the auth_url to grant permissions"
        }
        
    except Exception as e:
        print(f"[ERROR] Auth URL generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AGENT 8: RESOURCE FINDER ENDPOINTS
# ============================================

@app.get("/api/resources")
async def get_task_resources(
    limit: int = 20,
    authorization: str = Header(None)
):
    """Get learning resources found by Agent 8"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        resources = await db.get_task_resources(user_id, limit=limit)
        
        return {
            "success": True,
            "resources": resources,
            "total": len(resources)
        }
        
    except Exception as e:
        print(f"[ERROR] Resources fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/resources/{resource_id}/feedback")
async def submit_resource_feedback(
    resource_id: str,
    helpful: bool = Form(...),
    used_resources: list = Form([]),
    rating: int = Form(None),
    authorization: str = Header(None)
):
    """User feedback on resources"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        feedback = {
            "helpful": helpful,
            "used_resources": used_resources,
            "rating": rating,
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        await db.update_resource_feedback(user_id, resource_id, feedback)
        
        return {
            "success": True,
            "message": "Feedback recorded"
        }
        
    except Exception as e:
        print(f"[ERROR] Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AGENT 9: EMAIL ASSISTANT ENDPOINTS  
# ============================================

@app.post("/api/test-email-check")
async def test_email_assistant(authorization: str = Header(None)):
    """Manually trigger email intelligence check"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from agents.email_assistant_agent import EmailAssistantAgent
        
        email_agent = EmailAssistantAgent()
        email_agent.user_id = user_id
        
        result = await email_agent.process_yesterdays_emails(max_emails=20)
        return result
        
    except Exception as e:
        print(f"[ERROR] Email check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/email-drafts")
async def get_email_drafts(
    limit: int = 20,
    authorization: str = Header(None)
):
    """Get AI-generated email drafts"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        docs = (
            db._get_user_ref(user_id)
            .collection("email_drafts")
            .where("status", "==", "pending")
            .order_by("created_at", direction=firestore_module.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        
        drafts = []
        for doc in docs:
            draft_data = doc.to_dict()
            draft_data['id'] = doc.id
            drafts.append(draft_data)
        
        return {
            "success": True,
            "drafts": drafts,
            "total": len(drafts)
        }
        
    except Exception as e:
        print(f"[ERROR] Email drafts fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 

if __name__ == "__main__":
    import uvicorn
    print("[STARTUP] Starting LifeOS Multi-Agent System")
    print("[STARTUP] API running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)