"""
LifeOS Backend - Phase 3 (Agentic Integration)
Updated: 3-Layer Universal Classification System
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
from core.config import settings  # ADDED: Was missing, needed for /api/inbox
from agents.proactive_agent import ProactiveAgent
from agents.synthesis_agent import SynthesisAgent
from agents.graph_agent import GraphAgent
from agents.resource_finder_agent import ResourceFinderAgent


from models.capture import (
    CaptureRecord, 
    RawInput, 
    CaptureContext,
    PerceptionResult as ComprehensivePerceptionResult,
    ClassificationResult as ComprehensiveClassificationResult,
    ExtractedAction,
    ExecutionResult,
    ExecutedAction,
    ProcessingTimeline
)
from datetime import datetime
import uuid

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
bus.subscribe("intent_analyzed", orchestrator.process, priority=1)
bus.subscribe("intent_analyzed", researcher.process, priority=2)
bus.subscribe("intent_analyzed", proactive.process, priority=3)
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
# UTILITY ENDPOINTS
# ============================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LifeOS Backend",
        "version": "2.0.0",  # Updated version
        "classification": "3-layer-universal"
    }


@app.get("/")
def root():
    """Root endpoint"""
    return {"status": "LifeOS Backend Running", "classification_system": "3-layer"}


# ============================================
# WEBSOCKET: REAL-TIME TRANSCRIPTION
# ============================================

@app.websocket("/ws/transcribe")
async def ws_transcribe(websocket: WebSocket, token: str = Query(default="")):
    """WebSocket endpoint for real-time transcription"""
    await websocket.accept()
    
    from google import genai
    
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


# ============================================
# MAIN CAPTURE PIPELINE (3-LAYER CLASSIFICATION)
# ============================================



# ============================================
# MAIN CAPTURE PIPELINE (COMPREHENSIVE)
# ============================================

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
    """
    Multi-Agent Capture Pipeline with Comprehensive Metadata Tracking
    
    Flow:
    1. Create CaptureRecord (empty classification)
    2. Agent 1: Perception
    3. Agent 2: Classification (populates classification field)
    4. Save comprehensive + legacy formats
    5. Trigger background agents
    """
    
    # Auth Check
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]

    # Initialize Agents & DB
    perception = PerceptionAgent()
    cognition = IntentAgent()
    db = FirestoreService()
    
    capture_id = str(uuid.uuid4())
    
    # Get file sizes
    screenshot_size = os.path.getsize(screenshot_path) if os.path.exists(screenshot_path) else 0
    audio_size = os.path.getsize(audio_path) if audio_path and os.path.exists(audio_path) else 0
    
    # ========================================
    # STEP 1: CREATE COMPREHENSIVE CAPTURE RECORD
    # Classification is empty - will populate after Agent 2
    # ========================================
    comprehensive_capture = CaptureRecord(
        id=capture_id,
        user_id=user_id,
        capture_type="multi-modal" if audio_path else "screenshot",
        input=RawInput(
            screenshot_path=screenshot_path,
            audio_path=audio_path,
            text_note=text_note,
            context=CaptureContext(
                app_name=app_name,
                window_title=window_title,
                url=url or None,
                platform="windows",
                timezone=timezone if timezone else "UTC"
            ),
            screenshot_size_bytes=screenshot_size,
            audio_duration_seconds=None
        )
    )
    
    # Set timeline start
    comprehensive_capture.timeline.capture_received = datetime.utcnow()
    
    print(f"[CAPTURE] Created comprehensive capture record: {capture_id}")
    print(f"[CAPTURE] Screenshot: {screenshot_size} bytes")

    try:
        # Read Files
        with open(screenshot_path, "rb") as f:
            screenshot_bytes = f.read()
        
        audio_bytes = None
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

        # ========================================
        # STEP 2: AGENT 1 - PERCEPTION
        # ========================================
        comprehensive_capture.timeline.perception_started = datetime.utcnow()
        print("[Agent 1] Perception analyzing...")
        
        perception_start = datetime.utcnow()
        raw_result = await perception.process(
            screenshot_bytes=screenshot_bytes, 
            audio_bytes=audio_bytes
        )
        perception_end = datetime.utcnow()
        
        # Update perception in capture
        comprehensive_capture.perception.ocr_text = raw_result.ocr_text
        comprehensive_capture.perception.audio_transcript = raw_result.audio_transcript or ""
        comprehensive_capture.perception.visual_description = raw_result.visual_description
        comprehensive_capture.perception.combined_content = f"{raw_result.ocr_text}\n{raw_result.audio_transcript or ''}\n{text_note or ''}"
        comprehensive_capture.perception.processing_time_ms = int((perception_end - perception_start).total_seconds() * 1000)
        comprehensive_capture.perception.started_at = perception_start
        comprehensive_capture.perception.completed_at = perception_end
        
        comprehensive_capture.timeline.perception_completed = perception_end
        print(f"[Agent 1] Completed in {comprehensive_capture.perception.processing_time_ms}ms")

        # ========================================
        # STEP 3: AGENT 2 - CLASSIFICATION
        # ========================================
        comprehensive_capture.timeline.classification_started = datetime.utcnow()
        print("[Agent 2] Multi-Action Classification...")
        
        combined_context = comprehensive_capture.perception.combined_content
        
        classification_start = datetime.utcnow()
        classification = await cognition.process(text_content=combined_context)
        classification_end = datetime.utcnow()

        # Map actions
        extracted_actions = []
        for action in classification.actions:
            extracted_actions.append(ExtractedAction(
                intent=action.intent,
                summary=action.summary,
                priority=action.priority,
                due_date=action.due_date,
                event_time=action.event_time,
                event_end_time=action.event_end_time,
                attendee_emails=action.attendee_emails,
                attendee_names=action.attendee_names,
                send_invite=action.send_invite,
                amount=action.amount,
                location=action.location,
                notes=action.notes,
                tags=action.tags,
                source_phrase=action.source_phrase
            ))
        
        # POPULATE classification (was empty before)
        comprehensive_capture.classification.domain = classification.domain
        comprehensive_capture.classification.domain_confidence = 0.9
        comprehensive_capture.classification.context_type = classification.context_type
        comprehensive_capture.classification.primary_intent = classification.primary_intent
        comprehensive_capture.classification.overall_summary = classification.overall_summary
        comprehensive_capture.classification.actions = extracted_actions
        comprehensive_capture.classification.total_actions = len(extracted_actions)
        comprehensive_capture.classification.classification_reasoning = classification.classification_reasoning
        comprehensive_capture.classification.processing_time_ms = int((classification_end - classification_start).total_seconds() * 1000)
        comprehensive_capture.classification.started_at = classification_start
        comprehensive_capture.classification.completed_at = classification_end
        
        comprehensive_capture.timeline.classification_completed = classification_end
        
        # Log
        print(f"[CLASSIFICATION] Domain: {classification.domain}")
        print(f"[CLASSIFICATION] Context Type: {classification.context_type}")
        print(f"[CLASSIFICATION] Primary Intent: {classification.primary_intent}")
        print(f"[CLASSIFICATION] Total Actions: {len(classification.actions)}")

        # ========================================
        # STEP 4: SAVE TO FIRESTORE
        # ========================================
        comprehensive_capture.timeline.firestore_save_started = datetime.utcnow()
        
        # Save comprehensive capture
        await db.save_comprehensive_capture(comprehensive_capture)
        
        # BACKWARD COMPATIBILITY: Also save old formats
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

        primary_action = classification.actions[0] if classification.actions else None
        
        memory_doc = Memory(
            id=capture_id,
            capture_ref=capture_id,
            user_id=user_id,
            title=classification.overall_summary,
            one_line_summary=classification.overall_summary,
            full_transcript=raw_result.ocr_text,
            domain=classification.domain,
            context_type=classification.context_type,
            intent=classification.primary_intent,
            category=None,
            priority=primary_action.priority if primary_action else 3,
            tags=primary_action.tags if primary_action else [],
            actionable_items=[a.summary for a in classification.actions],
            task_context=primary_action.notes if primary_action else "",
            attendee_emails=primary_action.attendee_emails if primary_action else []
        )

        await db.save_capture(capture_doc)
        await db.save_memory(memory_doc)
        
        comprehensive_capture.timeline.firestore_save_completed = datetime.utcnow()
        comprehensive_capture.memory_id = capture_id
        
        print(f"[FIRESTORE] Saved comprehensive + legacy formats: {capture_id}")

        # ========================================
        # STEP 5: EMIT EVENT TO BACKGROUND AGENTS
        # ========================================
        user_timezone = capture_doc.context.timezone if capture_doc.context.timezone else "UTC"
        
        print(f"[EVENT BUS] Emitting intent_analyzed event")

        # Convert actions to dict
        actions_data = []
        for action in classification.actions:
            actions_data.append({
                "intent": action.intent,
                "summary": action.summary,
                "priority": action.priority,
                "due_date": action.due_date,
                "event_time": action.event_time,
                "event_end_time": action.event_end_time,
                "attendee_emails": action.attendee_emails,
                "attendee_names": action.attendee_names,
                "send_invite": action.send_invite,
                "amount": action.amount,
                "location": action.location,
                "notes": action.notes,
                "tags": action.tags
            })

        event_data = {
            "domain": classification.domain,
            "context_type": classification.context_type,
            "primary_intent": classification.primary_intent,
            "actions": actions_data,
            "overall_summary": classification.overall_summary,
            "intent": classification.primary_intent,
            "summary": classification.overall_summary,
            "user_id": user_id,
            "capture_id": capture_id,
            "full_context": combined_context,
            "user_timezone": user_timezone
        }
        
        asyncio.create_task(bus.emit("intent_analyzed", event_data))

        # ========================================
        # STEP 6: UPDATE STATUS & RETURN
        # ========================================
        comprehensive_capture.status = "processing"
        await db.update_comprehensive_capture(comprehensive_capture)

        return {
            "success": True,
            "capture_id": capture_id,
            "summary": classification.overall_summary,
            "domain": classification.domain,
            "context_type": classification.context_type,
            "primary_intent": classification.primary_intent,
            "total_actions": len(classification.actions),
            "actions": [
                {"intent": a.intent, "summary": a.summary[:100]}
                for a in classification.actions
            ],
            "processing_time_ms": {
                "perception": comprehensive_capture.perception.processing_time_ms,
                "classification": comprehensive_capture.classification.processing_time_ms,
                "total": comprehensive_capture.perception.processing_time_ms + 
                        comprehensive_capture.classification.processing_time_ms
            },
            "full_capture_url": f"/api/capture/{capture_id}/full"
        }

    except Exception as e:
        print(f"[ERROR] Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        
        comprehensive_capture.mark_failed(str(e))
        try:
            await db.update_comprehensive_capture(comprehensive_capture)
        except:
            pass
        
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SYNTHESIS AGENT (MANUAL TRIGGER)
# ============================================

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
        
        # TODO: Implement db.get_memory() for real data
        memories = [
            {
                "title": "Tokyo Travel Research",
                "one_line_summary": "Found great hotel in Shibuya",
                "domain": "travel_movement",
                "tags": ["japan", "tokyo", "hotel"]
            },
            {
                "title": "Restaurant Recommendations",
                "one_line_summary": "Top ramen spots in Tokyo",
                "domain": "travel_movement",
                "tags": ["japan", "food", "ramen"]
            }
        ]
        
        result = await synthesis_agent.synthesize_memories(memories)
        return result
        
    except Exception as e:
        print(f"[ERROR] Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DATA RETRIEVAL ENDPOINTS
# ============================================

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


@app.get("/api/inbox")
async def get_inbox(
    limit: int = 50,
    filter_intent: str = Query(None),
    filter_domain: str = Query(None),  # NEW: Filter by domain
    authorization: str = Header(None)
):
    """Retrieves user's captured memories with AI insights (3-Layer Classification)"""
    
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
            
            # Filter by intent (if specified)
            if filter_intent and memory_data.get('intent') != filter_intent:
                continue
            
            # Filter by domain (NEW - if specified)
            if filter_domain and memory_data.get('domain') != filter_domain:
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


# ============================================
# COMPREHENSIVE CAPTURE ENDPOINTS
# ============================================

@app.get("/api/capture/{capture_id}/full")
async def get_full_capture(
    capture_id: str,
    authorization: str = Header(None)
):
    """
    Retrieves complete comprehensive capture with all agent results
    
    Returns full audit trail with:
    - Raw input, Perception results, Classification results
    - Execution results, Research, Proactive tips, Resources
    - Complete timeline, Processing statistics
    """
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        capture_data = await db.get_comprehensive_capture(user_id, capture_id)
        
        if not capture_data:
            raise HTTPException(status_code=404, detail="Capture not found")
        
        timeline = capture_data.get("timeline", {})
        agents_completed = {
            "perception": bool(timeline.get("perception_completed")),
            "classification": bool(timeline.get("classification_completed")),
            "execution": bool(timeline.get("execution_completed")),
            "research": bool(timeline.get("research_completed")),
            "proactive": bool(timeline.get("proactive_completed")),
            "resources": bool(timeline.get("resources_completed"))
        }
        
        response = {
            "success": True,
            "capture": capture_data,
            "metadata": {
                "capture_id": capture_id,
                "user_id": user_id,
                "status": capture_data.get("status"),
                "domain": capture_data.get("classification", {}).get("domain"),
                "total_actions": capture_data.get("classification", {}).get("total_actions", 0),
                "agents_completed": agents_completed,
                "has_errors": len(capture_data.get("errors", [])) > 0
            }
        }
        
        print(f"[API] Retrieved full capture {capture_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] get_full_capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/captures/recent")
async def get_recent_captures(
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    authorization: str = Header(None)
):
    """Get recent comprehensive captures with optional status filter"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        captures = await db.list_comprehensive_captures(
            user_id=user_id,
            limit=limit,
            status=status
        )
        
        # Add summary to each
        for capture in captures:
            classification = capture.get("classification", {})
            timeline = capture.get("timeline", {})
            
            capture["_summary"] = {
                "domain": classification.get("domain"),
                "primary_intent": classification.get("primary_intent"),
                "total_actions": classification.get("total_actions", 0),
                "summary": classification.get("overall_summary", "")[:100],
                "processing_time_ms": timeline.get("total_processing_time_ms", 0),
                "status": capture.get("status")
            }
        
        return {
            "success": True,
            "captures": captures,
            "total": len(captures),
            "filters": {"limit": limit, "status": status}
        }
        
    except Exception as e:
        print(f"[ERROR] get_recent_captures failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/captures/statistics")
async def get_captures_statistics(authorization: str = Header(None)):
    """Get statistics about user's captures - total, success rate, avg time, etc."""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        stats = await db.get_capture_statistics(user_id)
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        print(f"[ERROR] get_captures_statistics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/capture/{capture_id}/timeline")
async def get_capture_timeline(
    capture_id: str,
    authorization: str = Header(None)
):
    """Get just the timeline for a capture - useful for progress tracking"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        capture_data = await db.get_comprehensive_capture(user_id, capture_id)
        
        if not capture_data:
            raise HTTPException(status_code=404, detail="Capture not found")
        
        timeline = capture_data.get("timeline", {})
        
        return {
            "success": True,
            "capture_id": capture_id,
            "timeline": timeline,
            "status": capture_data.get("status")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] get_capture_timeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/captures/recent")
async def get_recent_captures(
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    authorization: str = Header(None)
):
    """
    Get recent comprehensive captures
    
    Query params:
    - limit: Number to return (1-100)
    - status: Filter by status (processing, completed, failed)
    """
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        captures = await db.list_comprehensive_captures(
            user_id=user_id,
            limit=limit,
            status=status
        )
        
        # Add summary metadata to each capture
        for capture in captures:
            classification = capture.get("classification", {})
            timeline = capture.get("timeline", {})
            
            capture["_summary"] = {
                "domain": classification.get("domain"),
                "primary_intent": classification.get("primary_intent"),
                "total_actions": classification.get("total_actions", 0),
                "summary": classification.get("overall_summary", "")[:100],
                "processing_time_ms": timeline.get("total_processing_time_ms", 0),
                "status": capture.get("status")
            }
        
        return {
            "success": True,
            "captures": captures,
            "total": len(captures),
            "filters": {
                "limit": limit,
                "status": status
            }
        }
        
    except Exception as e:
        print(f"[ERROR] get_recent_captures failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/captures/statistics")
async def get_captures_statistics(authorization: str = Header(None)):
    """
    Get statistics about user's captures
    - Total captures
    - Success rate
    - Average processing time
    - Breakdown by status
    - Breakdown by domain
    """
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        stats = await db.get_capture_statistics(user_id)
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        print(f"[ERROR] get_captures_statistics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/capture/{capture_id}/timeline")
async def get_capture_timeline(
    capture_id: str,
    authorization: str = Header(None)
):
    """
    Get just the timeline for a capture
    Useful for progress tracking
    """
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        capture_data = await db.get_comprehensive_capture(user_id, capture_id)
        
        if not capture_data:
            raise HTTPException(status_code=404, detail="Capture not found")
        
        timeline = capture_data.get("timeline", {})
        
        return {
            "success": True,
            "capture_id": capture_id,
            "timeline": timeline,
            "status": capture_data.get("status")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] get_capture_timeline failed: {e}")
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
# KNOWLEDGE GRAPH ENDPOINTS
# ============================================

graph_agent = GraphAgent()

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


# ============================================
# DOMAIN-SPECIFIC ENDPOINTS (3-Layer System)
# ============================================

# ------------------------------------------
# FINANCIAL (money_finance domain)
# ------------------------------------------

@app.get("/api/financial")
async def get_financial_items(
    limit: int = 50,
    status: str = Query(None),
    category: str = Query(None),
    authorization: str = Header(None)
):
    """Get user's financial items (bills, payments, subscriptions)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        query = db._get_user_ref(user_id).collection("financial_items")
        
        if status:
            query = query.where("status", "==", status)
        if category:
            query = query.where("category", "==", category)
        
        docs = query.order_by("created_at", direction=firestore_module.Query.DESCENDING).limit(limit).stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items, "total": len(items), "domain": "money_finance"}
        
    except Exception as e:
        print(f"[ERROR] Financial items fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/financial/{item_id}/pay")
async def mark_bill_paid(
    item_id: str,
    authorization: str = Header(None)
):
    """Mark a bill as paid"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        doc_ref = db._get_user_ref(user_id).collection("financial_items").document(item_id)
        doc_ref.update({
            "status": "paid",
            "paid_at": datetime.utcnow().isoformat()
        })
        
        return {"success": True, "message": "Bill marked as paid", "item_id": item_id}
        
    except Exception as e:
        print(f"[ERROR] Mark bill paid failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# HEALTH (health_wellbeing domain)
# ------------------------------------------

@app.get("/api/health")
async def get_health_items(
    limit: int = 50,
    item_type: str = Query(None),
    status: str = Query(None),
    authorization: str = Header(None)
):
    """Get user's health items (appointments, medications, records)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        query = db._get_user_ref(user_id).collection("health_items")
        
        if item_type:
            query = query.where("item_type", "==", item_type)
        if status:
            query = query.where("status", "==", status)
        
        docs = query.order_by("created_at", direction=firestore_module.Query.DESCENDING).limit(limit).stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items, "total": len(items), "domain": "health_wellbeing"}
        
    except Exception as e:
        print(f"[ERROR] Health items fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/health/{item_id}/complete")
async def mark_health_item_complete(
    item_id: str,
    authorization: str = Header(None)
):
    """Mark a health item (appointment) as completed"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        doc_ref = db._get_user_ref(user_id).collection("health_items").document(item_id)
        doc_ref.update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        })
        
        return {"success": True, "message": "Health item marked as completed", "item_id": item_id}
        
    except Exception as e:
        print(f"[ERROR] Mark health complete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# TRAVEL (travel_movement domain)
# ------------------------------------------

@app.get("/api/travel")
async def get_travel_items(
    limit: int = 50,
    item_type: str = Query(None),
    status: str = Query("upcoming"),
    authorization: str = Header(None)
):
    """Get user's travel items (bookings, itineraries)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        query = db._get_user_ref(user_id).collection("travel_items")
        
        if item_type:
            query = query.where("item_type", "==", item_type)
        if status:
            query = query.where("status", "==", status)
        
        docs = query.order_by("created_at", direction=firestore_module.Query.DESCENDING).limit(limit).stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items, "total": len(items), "domain": "travel_movement"}
        
    except Exception as e:
        print(f"[ERROR] Travel items fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/travel/{item_id}")
async def get_travel_item(
    item_id: str,
    authorization: str = Header(None)
):
    """Get a single travel item"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        doc = db._get_user_ref(user_id).collection("travel_items").document(item_id).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Travel item not found")
        
        item_data = doc.to_dict()
        item_data['id'] = doc.id
        
        return {"success": True, "item": item_data}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Travel item fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# FAMILY (family_relationships domain)
# ------------------------------------------

@app.get("/api/family")
async def get_family_items(
    limit: int = 50,
    event_type: str = Query(None),
    authorization: str = Header(None)
):
    """Get user's family items (events, birthdays, school)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        query = db._get_user_ref(user_id).collection("family_items")
        
        if event_type:
            query = query.where("event_type", "==", event_type)
        
        docs = query.order_by("created_at", direction=firestore_module.Query.DESCENDING).limit(limit).stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items, "total": len(items), "domain": "family_relationships"}
        
    except Exception as e:
        print(f"[ERROR] Family items fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/family/{item_id}")
async def get_family_item(
    item_id: str,
    authorization: str = Header(None)
):
    """Get a single family item"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        doc = db._get_user_ref(user_id).collection("family_items").document(item_id).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Family item not found")
        
        item_data = doc.to_dict()
        item_data['id'] = doc.id
        
        return {"success": True, "item": item_data}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Family item fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# WATCHLIST (entertainment_leisure domain)
# ------------------------------------------

@app.get("/api/watchlist")
async def get_watchlist(
    limit: int = 50,
    media_type: str = Query(None),
    status: str = Query("to_watch"),
    authorization: str = Header(None)
):
    """Get user's watchlist (movies, shows, books)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        query = db._get_user_ref(user_id).collection("media_items")
        
        if media_type:
            query = query.where("media_type", "==", media_type)
        if status:
            query = query.where("status", "==", status)
        
        docs = query.order_by("created_at", direction=firestore_module.Query.DESCENDING).limit(limit).stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items, "total": len(items), "domain": "entertainment_leisure"}
        
    except Exception as e:
        print(f"[ERROR] Watchlist fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/watchlist/{item_id}/watched")
async def mark_as_watched(
    item_id: str,
    authorization: str = Header(None)
):
    """Mark a media item as watched"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        doc_ref = db._get_user_ref(user_id).collection("media_items").document(item_id)
        doc_ref.update({
            "status": "watched",
            "watched_at": datetime.utcnow().isoformat()
        })
        
        return {"success": True, "message": "Marked as watched", "item_id": item_id}
        
    except Exception as e:
        print(f"[ERROR] Mark watched failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# LEARNING (education_learning domain)
# ------------------------------------------

@app.get("/api/learning")
async def get_learning_items(
    limit: int = 50,
    item_type: str = Query(None),
    status: str = Query("active"),
    authorization: str = Header(None)
):
    """Get user's learning items (courses, assignments, topics)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        query = db._get_user_ref(user_id).collection("learning_items")
        
        if item_type:
            query = query.where("item_type", "==", item_type)
        if status:
            query = query.where("status", "==", status)
        
        docs = query.order_by("created_at", direction=firestore_module.Query.DESCENDING).limit(limit).stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items, "total": len(items), "domain": "education_learning"}
        
    except Exception as e:
        print(f"[ERROR] Learning items fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/{item_id}/complete")
async def mark_learning_complete(
    item_id: str,
    authorization: str = Header(None)
):
    """Mark a learning item as completed"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        doc_ref = db._get_user_ref(user_id).collection("learning_items").document(item_id)
        doc_ref.update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        })
        
        return {"success": True, "message": "Learning item marked as completed", "item_id": item_id}
        
    except Exception as e:
        print(f"[ERROR] Mark learning complete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# DOCUMENTS (admin_documents domain)
# ------------------------------------------

@app.get("/api/documents")
async def get_document_items(
    limit: int = 50,
    doc_type: str = Query(None),
    authorization: str = Header(None)
):
    """Get user's document items (IDs, forms, legal docs)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        query = db._get_user_ref(user_id).collection("document_items")
        
        if doc_type:
            query = query.where("doc_type", "==", doc_type)
        
        docs = query.order_by("created_at", direction=firestore_module.Query.DESCENDING).limit(limit).stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items, "total": len(items), "domain": "admin_documents"}
        
    except Exception as e:
        print(f"[ERROR] Document items fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{item_id}")
async def get_document_item(
    item_id: str,
    authorization: str = Header(None)
):
    """Get a single document item"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        doc = db._get_user_ref(user_id).collection("document_items").document(item_id).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        item_data = doc.to_dict()
        item_data['id'] = doc.id
        
        return {"success": True, "item": item_data}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Document fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# GENERIC DOMAIN ACCESS
# ------------------------------------------

@app.get("/api/domain/{domain}")
async def get_items_by_domain(
    domain: str,
    limit: int = 50,
    authorization: str = Header(None)
):
    """Generic endpoint to get items from any domain collection"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    # Validate domain
    valid_domains = [
        "work_career", "education_learning", "money_finance", "home_daily_life",
        "health_wellbeing", "family_relationships", "travel_movement",
        "shopping_consumption", "entertainment_leisure", "social_community",
        "admin_documents", "ideas_thoughts"
    ]
    
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {valid_domains}")
    
    try:
        db = FirestoreService()
        items = await db.get_items_by_domain(user_id, domain, limit)
        
        return {"success": True, "items": items, "total": len(items), "domain": domain}
        
    except Exception as e:
        print(f"[ERROR] Domain items fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memories/domain/{domain}")
async def get_memories_by_domain(
    domain: str,
    limit: int = 50,
    authorization: str = Header(None)
):
    """Get memories filtered by domain"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        memories = await db.get_user_memories(user_id, limit=limit, domain=domain)
        
        return {"success": True, "memories": memories, "total": len(memories), "domain": domain}
        
    except Exception as e:
        print(f"[ERROR] Memories by domain fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# DASHBOARD ENDPOINTS
# ------------------------------------------

@app.get("/api/dashboard/counts")
async def get_dashboard_counts(authorization: str = Header(None)):
    """Get item counts for each domain (for dashboard)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        counts = await db.get_domain_counts(user_id)
        
        return {"success": True, "counts": counts}
        
    except Exception as e:
        print(f"[ERROR] Dashboard counts fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/recent")
async def get_dashboard_recent(
    limit: int = 10,
    authorization: str = Header(None)
):
    """Get most recent items across all domains"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        items = await db.get_recent_across_domains(user_id, limit=limit)
        
        return {"success": True, "items": items, "total": len(items)}
        
    except Exception as e:
        print(f"[ERROR] Dashboard recent fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# HOME ITEMS (home_daily_life domain)
# ------------------------------------------

@app.get("/api/home")
async def get_home_items(
    limit: int = 50,
    item_type: str = Query(None),
    authorization: str = Header(None)
):
    """Get user's home items (chores, repairs, groceries)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        query = db._get_user_ref(user_id).collection("home_items")
        
        if item_type:
            query = query.where("item_type", "==", item_type)
        
        docs = query.order_by("created_at", direction=firestore_module.Query.DESCENDING).limit(limit).stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items, "total": len(items), "domain": "home_daily_life"}
        
    except Exception as e:
        print(f"[ERROR] Home items fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# SOCIAL ITEMS (social_community domain)
# ------------------------------------------

@app.get("/api/social")
async def get_social_items(
    limit: int = 50,
    authorization: str = Header(None)
):
    """Get user's social items (posts, discussions, news)"""
    
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
            .collection("social_items")
            .order_by("created_at", direction=firestore_module.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return {"success": True, "items": items, "total": len(items), "domain": "social_community"}
        
    except Exception as e:
        print(f"[ERROR] Social items fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------
# NOTES/IDEAS (ideas_thoughts domain)
# ------------------------------------------

@app.get("/api/notes")
async def get_notes(
    limit: int = 50,
    domain: str = Query(None),
    authorization: str = Header(None)
):
    """Get user's notes with optional domain filter"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        notes = await db.get_notes(user_id, limit=limit, domain=domain)
        
        return {"success": True, "items": notes, "total": len(notes)}
        
    except Exception as e:
        print(f"[ERROR] Notes fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STARTUP
# ============================================

if __name__ == "__main__":
    import uvicorn
    print("[STARTUP] LifeOS Multi-Agent System v2.0")
    print("[STARTUP] 3-Layer Universal Classification System")
    print("[STARTUP] Domains: 12 | Context Types: 19 | Intents: 14")
    print("[STARTUP] API running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)