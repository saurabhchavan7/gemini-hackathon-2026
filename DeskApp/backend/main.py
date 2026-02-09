"""
LifeOS Backend - Phase 3 (Agentic Integration)
Updated: 3-Layer Universal Classification System
"""
import os
import sys
import uuid
import json
import asyncio
import io
from datetime import datetime, timezone
from google.cloud import firestore
from typing import Optional

# 1. Standard FastAPI imports
from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google import genai

# 2. Existing Auth and Local Database logic
from auth import google_oauth, jwt_manager
from models import user
from models.database import init_database, get_connection
import google.generativeai as genai

# 3. Agentic Architecture Imports
from agents.perception.capture_agent import PerceptionAgent
from agents.cognition.intent_agent import IntentAgent
from agents.orchestrator.planning_agent import PlanningAgent
from agents.research_agent import ResearchAgent
from services.firestore_service import FirestoreService
from services.storage_service import StorageService
from models.capture import Capture, CaptureMetadata
from models.memory import Memory
from core.event_bus import bus
from core.config import settings  # ADDED: Was missing, needed for /api/inbox
from agents.proactive_agent import ProactiveAgent
from agents.synthesis_agent import SynthesisAgent
from agents.graph_agent import GraphAgent
from agents.resource_finder_agent import ResourceFinderAgent

from services.embedding_service import EmbeddingService
from services.vector_search_service import VectorSearchService
from services.rag_service import RAGService
from services.clustering_service import ClusteringService
from datetime import datetime
import pytz
from services.notification_service import NotificationService

notification_service = NotificationService()

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
embedding_service = EmbeddingService()
vector_search_service = VectorSearchService()
rag_service = RAGService()


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



# ============================================
# STEP 2: ADD EMAIL INTELLIGENCE ENDPOINTS
# Add these endpoints BEFORE the if __name__ == "__main__" section
# ============================================

# Email Intelligence Endpoints
@app.post("/api/email-intelligence/check")
async def check_emails_scheduled(authorization: str = Header(None)):
    """
    Scheduled endpoint for Cloud Scheduler
    Checks emails for all users (or specific user if authorized)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from agents.email_assistant_agent import EmailAssistantAgent
        from services.token_service import TokenService
        
        token_service = TokenService()
        has_gmail = await token_service.check_gmail_connected(user_id)
        
        if not has_gmail:
            return {
                "status": "skip",
                "message": "User has not connected Gmail",
                "user_id": user_id
            }
        
        agent = EmailAssistantAgent(user_id=user_id)
        result = await agent.process_yesterdays_emails(max_emails=20)
        
        return {
            "status": "success",
            "user_id": user_id,
            "result": result
        }
        
    except Exception as e:
        print(f"[ERROR] Scheduled email check failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "user_id": user_id
        }


@app.post("/api/email-intelligence/manual")
async def check_emails_manual(authorization: str = Header(None)):
    """Manual trigger for email checking by user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from agents.email_assistant_agent import EmailAssistantAgent
        from services.token_service import TokenService
        
        token_service = TokenService()
        has_gmail = await token_service.check_gmail_connected(user_id)
        
        if not has_gmail:
            raise HTTPException(
                status_code=403,
                detail="Gmail not connected. Please log out and log in again to grant Gmail access."
            )
        
        agent = EmailAssistantAgent(user_id=user_id)
        result = await agent.process_yesterdays_emails(max_emails=20)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Manual email check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/email-intelligence/status")
async def get_email_status(authorization: str = Header(None)):
    """Check if user has Gmail connected"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        from services.token_service import TokenService
        
        token_service = TokenService()
        has_gmail = await token_service.check_gmail_connected(user_id)
        
        return {
            "success": True,
            "gmail_connected": has_gmail,
            "user_id": user_id
        }
        
    except Exception as e:
        print(f"[ERROR] Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/email-intelligence/drafts")
async def get_email_drafts(
    limit: int = Query(20, ge=1, le=100),
    status: str = Query("pending"),
    authorization: str = Header(None)
):
    """Get AI-generated email drafts for user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        from google.cloud import firestore as firestore_module
        
        query = db._get_user_ref(user_id).collection("email_drafts")
        
        if status:
            query = query.where("status", "==", status)
        
        docs = query.order_by("created_at", direction=firestore_module.Query.DESCENDING).limit(limit).stream()
        
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
        print(f"[ERROR] Failed to fetch drafts: {e}")
        raise HTTPException(status_code=500, detail=str(e))



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
    screenshot_file: Optional[UploadFile] = File(None),  # NOW OPTIONAL
    audio_file: Optional[UploadFile] = File(None),
    app_name: str = Form("Unknown"),
    window_title: str = Form("Unknown"),
    url: str = Form(""),
    timestamp: str = Form(""),
    text_note: Optional[str] = Form(None),
    timezone: str = Form("UTC"),
    authorization: str = Header(None)
):
    """
    Multi-Agent Capture Pipeline - Accepts File Uploads and stores in GCS
    
    Supports:
    - Screenshot only
    - Audio only
    - Text note only
    - Any combination of the above
    
    Flow:
    1. Receive inputs (at least one required)
    2. Upload to GCS (if files present)
    3. Agent 1: Perception (OCR + Audio)
    4. Agent 2: Classification
    5. Save to Firestore with GCS paths
    6. Embed to Vector Search
    7. Trigger background agents
    """
    
    # Auth Check
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]

    # Validate at least one input is provided
    if not screenshot_file and not audio_file and not text_note:
        raise HTTPException(
            status_code=400, 
            detail="At least one of: screenshot, audio, or text note must be provided"
        )

    # Initialize services
    perception = PerceptionAgent()
    cognition = IntentAgent()
    db = FirestoreService()
    storage = StorageService()
    
    capture_id = str(uuid.uuid4())
    
    try:
        # Determine capture type
        if screenshot_file and audio_file:
            capture_type = "multi-modal"
        elif screenshot_file:
            capture_type = "screenshot"
        elif audio_file:
            capture_type = "audio"
        else:
            capture_type = "text_note"
        
        # Read uploaded files (if present)
        screenshot_bytes = None
        screenshot_size = 0
        if screenshot_file:
            screenshot_bytes = await screenshot_file.read()
            screenshot_size = len(screenshot_bytes)
        
        audio_bytes = None
        audio_size = 0
        if audio_file:
            audio_bytes = await audio_file.read()
            audio_size = len(audio_bytes)
        
        print(f"[CAPTURE] Created capture: {capture_id}")
        print(f"[CAPTURE] Type: {capture_type}")
        if screenshot_bytes:
            print(f"[CAPTURE] Screenshot: {screenshot_size} bytes")
        if audio_bytes:
            print(f"[CAPTURE] Audio: {audio_size} bytes")
        if text_note:
            print(f"[CAPTURE] Text note: {len(text_note)} characters")
        
        # Upload screenshot to GCS (if present)
        screenshot_gcs_path = None
        screenshot_upload_result = None
        if screenshot_bytes:
            screenshot_gcs_path = f"users/{user_id}/captures/{capture_id}.png"
            screenshot_upload_result = storage.upload_file_bytes(screenshot_bytes, screenshot_gcs_path)
            print(f"[CAPTURE] Screenshot uploaded to GCS: {screenshot_gcs_path}")
        
        # Upload audio to GCS (if present)
        audio_gcs_path = None
        audio_upload_result = None
        if audio_bytes:
            audio_gcs_path = f"users/{user_id}/captures/{capture_id}.webm"
            audio_upload_result = storage.upload_file_bytes(audio_bytes, audio_gcs_path)
            print(f"[CAPTURE] Audio uploaded to GCS: {audio_gcs_path}")
        
        # Create comprehensive capture record with GCS paths
        comprehensive_capture = CaptureRecord(
            capture_id=capture_id,  # CORRECT FIELD NAME
            user_id=user_id,
            capture_type=capture_type,
            input=RawInput(
                screenshot_path=screenshot_upload_result.get('path') if screenshot_upload_result else None,
                audio_path=audio_upload_result.get('path') if audio_upload_result else None,
                text_note=text_note,
                context=CaptureContext(
                    app_name=app_name,
                    window_title=window_title,
                    url=url or None,
                    platform="windows",
                    timezone=timezone if timezone else "UTC"
                ),
                screenshot_size_bytes=screenshot_size if screenshot_size > 0 else None,
                audio_duration_seconds=None
            )
        )

        
        comprehensive_capture.timeline.capture_received = datetime.utcnow()

        # AGENT 1: Perception
        comprehensive_capture.timeline.perception_started = datetime.utcnow()
        print("[Agent 1] Perception analyzing...")
        
        perception_start = datetime.utcnow()
        raw_result = await perception.process(
            screenshot_bytes=screenshot_bytes, 
            audio_bytes=audio_bytes
        )
        perception_end = datetime.utcnow()
        
        comprehensive_capture.perception.ocr_text = raw_result.ocr_text
        comprehensive_capture.perception.audio_transcript = raw_result.audio_transcript or ""
        comprehensive_capture.perception.visual_description = raw_result.visual_description
        comprehensive_capture.perception.combined_content = f"{raw_result.ocr_text}\n{raw_result.audio_transcript or ''}\n{text_note or ''}"
        comprehensive_capture.perception.processing_time_ms = int((perception_end - perception_start).total_seconds() * 1000)
        comprehensive_capture.perception.started_at = perception_start
        comprehensive_capture.perception.completed_at = perception_end
        
        comprehensive_capture.timeline.perception_completed = perception_end
        print(f"[Agent 1] Completed in {comprehensive_capture.perception.processing_time_ms}ms")

        # AGENT 2: Classification
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
        
        print(f"[CLASSIFICATION] Domain: {classification.domain}")
        print(f"[CLASSIFICATION] Context Type: {classification.context_type}")
        print(f"[CLASSIFICATION] Primary Intent: {classification.primary_intent}")
        print(f"[CLASSIFICATION] Total Actions: {len(classification.actions)}")

        # Save to Firestore
        comprehensive_capture.timeline.firestore_save_started = datetime.utcnow()
        await db.save_comprehensive_capture(comprehensive_capture)
        
        # Create legacy format capture for backward compatibility
        capture_doc = Capture(
            capture_id=capture_id,  #  CORRECT FIELD NAME
            user_id=user_id,
            capture_type=capture_type,
            screenshot_path=screenshot_upload_result.get('path') if screenshot_upload_result else None,
            audio_path=audio_upload_result.get('path') if audio_upload_result else None,
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
            capture_id=capture_id,  #  UNIFIED FIELD
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

        # Embed to vector search
        try:
            print("[VECTOR] Embedding capture for semantic search...")
            
            combined_for_embedding = f"""
            Title: {classification.overall_summary}
            Domain: {classification.domain}
            Content: {raw_result.ocr_text}
            Audio: {raw_result.audio_transcript or ''}
            Notes: {text_note or ''}
            """
            
            embedding_error, vector_error = embedding_service.embed_and_upload_capture(
                capture_id=capture_id,
                user_id=user_id,
                combined_text=combined_for_embedding,
                # metadata={
                #     'domain': classification.domain,
                #     'timestamp': datetime.now(timezone.utc).isoformat()
                # }
                

                metadata={
                    'domain': classification.domain,
                    'timestamp': datetime.utcnow().isoformat()  # ✅ WORKS
                }
            )
            
            if embedding_error or vector_error:
                print(f"[VECTOR] Warning: Vector upload failed")
            else:
                print(f"[VECTOR] Capture embedded successfully")
                
        except Exception as e:
            print(f"[VECTOR] Non-critical error: {e}")
        
        comprehensive_capture.timeline.firestore_save_completed = datetime.utcnow()
        comprehensive_capture.memory_id = capture_id
        
        print(f"[FIRESTORE] Saved comprehensive + legacy formats: {capture_id}")

        # Emit event to background agents
        user_timezone = capture_doc.context.timezone if capture_doc.context.timezone else "UTC"
        
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

        comprehensive_capture.status = "processing"
        await db.update_comprehensive_capture(comprehensive_capture)

        return {
            "success": True,
            "capture_id": capture_id,
            "capture_type": capture_type,
            "summary": classification.overall_summary,
            "domain": classification.domain,
            "context_type": classification.context_type,
            "primary_intent": classification.primary_intent,
            "total_actions": len(classification.actions),
            "actions": [
                {"intent": a.intent, "summary": a.summary[:100]}
                for a in classification.actions
            ],
            "gcs_paths": {
                "screenshot": screenshot_upload_result.get('path') if screenshot_upload_result else None,
                "audio": audio_upload_result.get('path') if audio_upload_result else None
            },
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
    limit: int = 100,
    filter_intent: str = Query(None),
    filter_domain: str = Query(None),
    authorization: str = Header(None)
):
    """
    Retrieves user's captured memories with screenshots
    Returns enriched data with screenshot URLs from GCS
    """
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    print(f"[API] Inbox request for user: {user_id}")
    
    try:
        db = FirestoreService()
        
        # Get memories from Firestore
        docs = (
            db._get_user_ref(user_id)
            .collection(settings.COLLECTION_MEMORIES)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        
        memories = []
        for doc in docs:
            memory_data = doc.to_dict()
            memory_data['id'] = doc.id
            
            # Filter by intent (if specified)
            if filter_intent and memory_data.get('intent') != filter_intent:
                continue
            
            # Filter by domain (if specified)
            if filter_domain and memory_data.get('domain') != filter_domain:
                continue
            
            # Get comprehensive capture to fetch screenshot URL
            capture_ref = memory_data.get('capture_ref')
            if capture_ref:
                try:
                    comp_doc = (
                        db._get_user_ref(user_id)
                        .collection("comprehensive_captures")
                        .document(capture_ref)
                        .get()
                    )
                    
                    if comp_doc.exists:
                        comp_data = comp_doc.to_dict()
                        input_data = comp_data.get('input', {})
                        
                        # Add screenshot URL to memory
                        screenshot_path = input_data.get('screenshot_path')
                        if screenshot_path:
                            # Build GCS public URL
                            bucket_name = os.getenv('GCS_BUCKET', 'rag-gcs-bucket')
                            memory_data['screenshot_url'] = f"https://storage.googleapis.com/{bucket_name}/{screenshot_path}"
                        
                        # Add window context
                        context = input_data.get('context', {})
                        memory_data['source_app'] = context.get('app_name', 'Unknown')
                        memory_data['window_title'] = context.get('window_title', '')
                        memory_data['url'] = context.get('url')
                        
                except Exception as e:
                    print(f"[WARNING] Could not fetch comprehensive capture for {capture_ref}: {e}")
            
            memories.append(memory_data)
        
        print(f"[API] Returning {len(memories)} memories")
        
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
# def public_gcs_url(bucket: str, object_path: str) -> str:
#     return f"https://storage.googleapis.com/{bucket}/{object_path}"

# @app.get("/api/capture/{capture_id}/full")
# async def get_full_capture(
#     capture_id: str,
#     authorization: str = Header(None)
# ):
#     """
#     Retrieves complete comprehensive capture with all agent results
#     PLUS proxy URLs for GCS files (no signing needed)
#     """
    
#     if not authorization or not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Unauthorized")
    
#     token = authorization.replace("Bearer ", "")
#     payload = jwt_manager.verify_jwt_token(token)
#     user_id = payload["user_id"]
    
#     try:
#         db = FirestoreService()
#         capture_data = await db.get_comprehensive_capture(user_id, capture_id)
        
#         if not capture_data:
#             raise HTTPException(status_code=404, detail="Capture not found")
        
#         # Generate proxy URLs for GCS files (instead of signed URLs)
#         if capture_data.get('input'):
#             input_data = capture_data['input']
            
#             # Screenshot - Convert GCS path to proxy URL
#             if input_data:
#                 storage = StorageService()
            
#             # Screenshot - Generate signed URL
#             if input_data.get('screenshot_path'):
#                 screenshot_path = input_data['screenshot_path']
#                 try:
#                     signed_url = storage.generate_signed_url(screenshot_path, expiration=3600)
#                     input_data['screenshot_signed_url'] = signed_url
#                     input_data['screenshot_url'] = signed_url
#                     print(f"[API] Generated signed URL for screenshot: {screenshot_path}")
#                 except Exception as e:
#                     print(f"[ERROR] Failed to generate screenshot signed URL: {e}")
            
            
#             # Audio - Generate signed URL
#             if input_data.get('audio_path'):
#                 audio_path = input_data['audio_path']
#                 try:
#                     signed_url = storage.generate_signed_url(audio_path, expiration=3600)
#                     input_data['audio_signed_url'] = signed_url
#                     input_data['audio_url'] = signed_url
#                     print(f"[API] Generated signed URL for audio: {audio_path}")
#                 except Exception as e:
#                     print(f"[ERROR] Failed to generate audio signed URL: {e}")
        
#             # Handle attached files
#             if capture_data.get('attached_files'):
#                 storage = StorageService()
#                 for file in capture_data['attached_files']:
#                     if file.get('gcs_path'):
#                         try:
#                             signed_url = storage.generate_signed_url(file['gcs_path'], expiration=3600)
#                             file['signed_url'] = signed_url
#                             file['url'] = signed_url
#                             print(f"[API] Generated signed URL for file: {file['gcs_path']}")
#                         except Exception as e:
#                             print(f"[ERROR] Failed to generate file signed URL: {e}")

        
#         timeline = capture_data.get("timeline", {})
#         agents_completed = {
#             "perception": bool(timeline.get("perception_completed")),
#             "classification": bool(timeline.get("classification_completed")),
#             "execution": bool(timeline.get("execution_completed")),
#             "research": bool(timeline.get("research_completed")),
#             "proactive": bool(timeline.get("proactive_completed")),
#             "resources": bool(timeline.get("resources_completed"))
#         }
        
#         response = {
#             "success": True,
#             "capture": capture_data,
#             "metadata": {
#                 "capture_id": capture_id,
#                 "user_id": user_id,
#                 "status": capture_data.get("status"),
#                 "domain": capture_data.get("classification", {}).get("domain"),
#                 "total_actions": capture_data.get("classification", {}).get("total_actions", 0),
#                 "agents_completed": agents_completed,
#                 "has_errors": len(capture_data.get("errors", [])) > 0
#             }
#         }
        
#         print(f"[API] Retrieved full capture {capture_id} with proxy URLs")
#         return response
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"[ERROR] get_full_capture failed: {e}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


def public_gcs_url(bucket: str, object_path: str) -> str:
    return f"https://storage.googleapis.com/{bucket}/{object_path}"


@app.get("/api/capture/{capture_id}/full")
async def get_full_capture(
    capture_id: str,
    authorization: str = Header(None)
):
    """
    Retrieves complete comprehensive capture with all agent results
    PLUS PUBLIC URLs for GCS files (NO signing)
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

        # -------------------------------
        # PUBLIC GCS URL GENERATION
        # -------------------------------
        bucket = "rag-gcs-bucket"

        if capture_data.get("input"):
            input_data = capture_data["input"]

            # Screenshot
            if input_data.get("screenshot_path"):
                screenshot_path = input_data["screenshot_path"]
                public_url = public_gcs_url(bucket, screenshot_path)
                input_data["screenshot_url"] = public_url
                print(f"[API] Using public URL for screenshot: {public_url}")

            # Audio
            if input_data.get("audio_path"):
                audio_path = input_data["audio_path"]
                public_url = public_gcs_url(bucket, audio_path)
                input_data["audio_url"] = public_url
                print(f"[API] Using public URL for audio: {public_url}")

        # Attached files
        if capture_data.get("attached_files"):
            for file in capture_data["attached_files"]:
                if file.get("gcs_path"):
                    public_url = public_gcs_url(bucket, file["gcs_path"])
                    file["url"] = public_url
                    print(f"[API] Using public URL for file: {public_url}")

        # -------------------------------
        # Agent completion metadata
        # -------------------------------
        timeline = capture_data.get("timeline", {})
        agents_completed = {
            "perception": bool(timeline.get("perception_completed")),
            "classification": bool(timeline.get("classification_completed")),
            "execution": bool(timeline.get("execution_completed")),
            "research": bool(timeline.get("research_completed")),
            "proactive": bool(timeline.get("proactive_completed")),
            "resources": bool(timeline.get("resources_completed")),
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
                "has_errors": len(capture_data.get("errors", [])) > 0,
            },
        }

        print(f"[API] Retrieved full capture {capture_id} with PUBLIC GCS URLs")
        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] get_full_capture failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/capture/{capture_id}/full")
async def get_full_capture_v2(
    capture_id: str,
    authorization: str = Header(None)
):
    """
    V2 ENHANCED: Get comprehensive capture with ALL subcollections
    Uses unified capture_id linkage strategy
    """
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt_manager.verify_jwt_token(token)
        user_id = payload["user_id"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    try:
        db = FirestoreService()
        
        print(f"[API V2] Fetching enhanced capture: {capture_id}")
        
        # Use new V2 fetch method with unified capture_id linkage
        capture_data = await db.get_enhanced_capture_data_v2(user_id, capture_id)
        
        if not capture_data:
            raise HTTPException(status_code=404, detail="Capture not found")
        
        # Generate public GCS URLs
        bucket = os.getenv('GCS_BUCKET', 'rag-gcs-bucket')
        
        if capture_data.get('input'):
            input_data = capture_data['input']
            
            # Screenshot
            if input_data.get('screenshot_path'):
                screenshot_path = input_data['screenshot_path']
                public_url = f"https://storage.googleapis.com/{bucket}/{screenshot_path}"
                input_data['screenshot_signed_url'] = public_url
                input_data['screenshot_url'] = public_url
                print(f"[API V2] Using public URL for screenshot")
            
            # Audio
            if input_data.get('audio_path'):
                audio_path = input_data['audio_path']
                public_url = f"https://storage.googleapis.com/{bucket}/{audio_path}"
                input_data['audio_signed_url'] = public_url
                input_data['audio_url'] = public_url
                print(f"[API V2] Using public URL for audio")
        
        # Build enhanced metadata
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
            "version": "v2",
            "capture": capture_data,
            "metadata": {
                "capture_id": capture_id,
                "user_id": user_id,
                "status": capture_data.get("status"),
                "domain": capture_data.get("classification", {}).get("domain"),
                "total_actions": capture_data.get("execution", {}).get("total_actions", 0),
                "agents_completed": agents_completed,
                "has_errors": len(capture_data.get("errors", [])) > 0,
                "has_research": capture_data.get('research', {}).get('has_data', False),
                "has_resources": capture_data.get('resources', {}).get('has_data', False),
                "research_sources_count": capture_data.get('research', {}).get('sources_count', 0),
                "resources_count": capture_data.get('resources', {}).get('resources_count', 0)
            }
        }
        
        print(f"[API V2] Enhanced capture ready with unified linkage")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] get_full_capture_v2 failed: {e}")
        import traceback
        traceback.print_exc()
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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
    limit: int = 100,
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


# ============================================
# FILE UPLOAD ENDPOINT
# ============================================



@app.post("/api/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    capture_id: Optional[str] = Form(None),
    authorization: str = Header(None)
):
    """
    Upload a PDF or DOCX file, store in GCS, embed, and save to Firestore + Vector Search
    """
    # Auth Check
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt_manager.verify_jwt_token(token)
        user_id = payload["user_id"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    # Validation
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.pdf', '.docx'):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx files are allowed")

    contents = await file.read()
    size = len(contents)
    MAX_BYTES = 50 * 1024 * 1024
    if size > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    # Upload to GCS
    try:
        from services.storage_service import StorageService
        storage = StorageService()
        dest_path = f"users/{user_id}/files/{str(uuid.uuid4())}{ext}"
        upload_result = storage.upload_file_bytes(contents, dest_path)
        print(f"[UPLOAD] File uploaded to GCS: {dest_path}")
    except Exception as e:
        print(f"[UPLOAD] GCS upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    # Save basic metadata to Firestore
    db = FirestoreService()
    file_meta = {
        'name': filename,
        'gcs_path': upload_result.get('path'),
        'gcs_bucket': upload_result.get('bucket'),
        'gcs_url': upload_result.get('public_url'),
        'size_bytes': size,
        'file_type': file.content_type,
        'capture_id': capture_id,
        'uploaded_at': datetime.utcnow().isoformat()
    }
    
    try:
        file_doc_id = await db.save_user_file(user_id, file_meta)
        print(f"[UPLOAD] Basic metadata saved to Firestore: {file_doc_id}")
    except Exception as e:
        print(f"[UPLOAD] Firestore save failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file metadata: {str(e)}")

    # Parse and chunk file
    import tempfile
    from services.file_parser import FileParser
    
    parsed = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        print(f"[UPLOAD] Parsing file...")
        parsed = FileParser.parse_and_chunk(tmp_path)
        os.remove(tmp_path)
        
        print(f"[UPLOAD]  Parsed: {len(parsed['chunks'])} chunks")
        print(f"[UPLOAD] Title: {parsed['title']}")
        print(f"[UPLOAD] Domain: {parsed['domain']}")
        
    except Exception as e:
        print(f"[UPLOAD] File parsing failed: {e}")
        import traceback
        traceback.print_exc()

    # Save enhanced metadata + embed to vector search
    embedding_error = None
    vector_error = None
    
    if parsed:
        try:
            # Save enhanced metadata to Firestore
            enhanced_meta = {
                'file_name': parsed['file_name'],
                'upload_date': parsed['upload_date'],
                'title': parsed['title'],
                'summary': parsed['summary'],
                'domain': parsed['domain'],
                'chunks': parsed['chunks'],
                'text': parsed['text'],
                'gcs_path': upload_result.get('path'),
                'gcs_bucket': upload_result.get('bucket'),
                'gcs_url': upload_result.get('public_url'),
                'size_bytes': size,
                'file_type': file.content_type,
                'capture_id': capture_id,
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
            await db.save_file_metadata(user_id, file_doc_id, enhanced_meta)
            print(f"[UPLOAD]  Enhanced metadata saved")
            
            # Embed and upload to vector search
            print(f"[UPLOAD] Generating embeddings and uploading to vector search...")
            
            embedding_error, vector_error = embedding_service.embed_and_upload_document(
                chunks=parsed['chunks'],
                file_doc_id=file_doc_id,
                user_id=user_id,
                metadata={
                    'domain': parsed['domain'],
                    'title': parsed['title'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            if embedding_error:
                print(f"[UPLOAD]  Embedding error: {embedding_error}")
            elif vector_error:
                print(f"[UPLOAD]  Vector upload error: {vector_error}")
            else:
                print(f"[UPLOAD]  Successfully uploaded to vector search!")
            
        except Exception as e:
            print(f"[UPLOAD] Enhanced processing failed: {e}")
            import traceback
            traceback.print_exc()

# Embed to vector search
    if parsed:
        try:
            print(f"[UPLOAD] Embedding to vector search...")
            
            embedding_error, vector_error = embedding_service.embed_and_upload_document(
                chunks=parsed['chunks'],
                file_doc_id=file_doc_id,
                user_id=user_id,
                metadata={
                    'domain': parsed['domain'],
                    'title': parsed['title'],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            if embedding_error or vector_error:
                print(f"[UPLOAD] Warning: Vector upload failed")
                print(f"[UPLOAD] Embedding error: {embedding_error}")
                print(f"[UPLOAD] Vector error: {vector_error}")
            else:
                print(f"[UPLOAD] Successfully embedded to vector search")
                
        except Exception as e:
            print(f"[UPLOAD] Non-critical error embedding: {e}")
            embedding_error = str(e)
    
    return {
        "success": True,
        "file_id": file_doc_id,
        "meta": enhanced_meta if parsed else file_meta,
        "embedding_error": embedding_error,
        "vector_error": vector_error,
        "vector_search_ready": (embedding_error is None and vector_error is None)
    }

# ============================================
# NEW ENDPOINT: CHATBOT SEMANTIC SEARCH
# ============================================

@app.post("/api/search")
async def semantic_search(
    query: str = Form(...),
    num_results: int = Form(10),
    filter_type: Optional[str] = Form(None),
    filter_domain: Optional[str] = Form(None),
    authorization: str = Header(None)
):
    """
    Semantic search across user's captures and documents using Vector Search
    
    Args:
        query: Natural language search query
        num_results: Number of results to return (default: 10)
        filter_type: Optional filter - "capture" or "document"
        filter_domain: Optional domain filter (e.g., "money_finance")
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        print(f"[SEARCH API] User {user_id} searching: '{query}'")
        
        results = vector_search_service.search(
            query=query,
            user_id=user_id,
            num_results=num_results,
            filter_type=filter_type,
            filter_domain=filter_domain
        )
        
        db = FirestoreService()
        enriched_results = []
        
        for result in results:
            source_id = result['source_id']
            item_type = result['type']
            
            try:
                if item_type == "capture":
                    doc = db._get_user_ref(user_id).collection("memories").document(source_id).get()
                else:
                    doc = db._get_user_ref(user_id).collection("files").document(source_id).get()
                
                if doc.exists:
                    item_data = doc.to_dict()
                    item_data['id'] = doc.id
                    item_data['_similarity_score'] = 1 - result['distance']
                    item_data['_vector_distance'] = result['distance']
                    enriched_results.append(item_data)
            except Exception as e:
                print(f"[SEARCH API] Warning: Could not fetch {source_id}: {e}")
                continue
        
        print(f"[SEARCH API] Returning {len(enriched_results)} enriched results")
        
        return {
            "success": True,
            "query": query,
            "total_results": len(enriched_results),
            "filters": {
                "type": filter_type,
                "domain": filter_domain
            },
            "results": enriched_results
        }
        
    except Exception as e:
        print(f"[SEARCH API] Search failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask")
async def ask_question(
    question: str = Form(...),
    filter_domain: Optional[str] = Form(None),
    authorization: str = Header(None)
):
    """RAG endpoint - Returns AI-generated answer with sources"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        result = rag_service.answer_question(
            query=question,
            user_id=user_id,
            num_results=5,
            filter_domain=filter_domain
        )
        
        return {
            "success": True,
            "question": question,
            "answer": result['answer'],
            "sources": result['sources'],
            "confidence": result['confidence']
        }
        
    except Exception as e:
        print(f"[API] Ask question failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/inbox/{capture_id}/ask")
async def ask_about_capture(
    capture_id: str,
    question: str = Form(...),
    authorization: str = Header(None)
):
    """Ask Gemini a question about a specific capture"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        print(f"[ASK API] Question about capture {capture_id}: '{question}'")
        
        # Get the specific capture
        db = FirestoreService()
        memory_doc = db._get_user_ref(user_id).collection(settings.COLLECTION_MEMORIES).document(capture_id).get()
        
        if not memory_doc.exists:
            raise HTTPException(status_code=404, detail="Capture not found")
        
        memory_data = memory_doc.to_dict()
        
        # Build context from this specific capture
        context = f"""Title: {memory_data.get('title', 'Untitled')}
Summary: {memory_data.get('one_line_summary', '')}
Full Content: {memory_data.get('full_transcript', '')}
Domain: {memory_data.get('domain', 'unknown')}
Intent: {memory_data.get('intent', 'unknown')}
Tags: {', '.join(memory_data.get('tags', []))}"""
        
        # Generate answer using Gemini
        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""You are an intelligent assistant helping users find information about their captured items.

CAPTURED ITEM:
• Title: {memory_data.get('title', 'Untitled')}
• Summary: {memory_data.get('one_line_summary', '')}
• Content: {memory_data.get('full_transcript', '')}
• Domain: {memory_data.get('domain', 'unknown')}
• Intent: {memory_data.get('intent', 'unknown')}
• Tags: {', '.join(memory_data.get('tags', []))}

QUESTION: {question}

INSTRUCTIONS:
1. Answer based on the captured content and your knowledge
2. Provide a BRIEF, well-formatted response (2-4 sentences max)
3. Use citations: [From Capture], [General Knowledge]
4. Format cleanly with sections (ANSWER, DETAILS, NOTES)
5. NO EMOJIS - Professional formatting only

FORMAT:
ANSWER:
[Direct answer]

DETAILS:
• [Key detail 1] [Citation]
• [Key detail 2] [Citation]

NOTES:
[Additional context if needed]

Response:"""
        
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        print(f"[ASK API] Answer generated: {answer[:100]}...")
        
        return {
            "success": True,
            "question": question,
            "answer": answer,
            "capture_id": capture_id,
            "capture_title": memory_data.get('title', 'Untitled')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ASK API] Failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/ask/no-auth")
async def ask_no_auth(
    question: str = Form(...),
    filter_domain: Optional[str] = Form(None)
):
    """Test endpoint - REMOVE BEFORE PRODUCTION"""
    user_id = "113314724333098866443"
    
    try:
        result = rag_service.answer_question(
            query=question,
            user_id=user_id,
            filter_domain=filter_domain
        )
        
        return {
            "success": True,
            "question": question,
            "answer": result['answer'],
            "sources": result['sources']
        }
    except Exception as e:
        print(f"[API] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/google/login")
async def google_login(request: LoginRequest):
    """Handle Google OAuth login and save tokens"""
    try:
        print("[AUTH] Login request received")
        
        user_info = google_oauth.authenticate_user(request.code)
        
        # Save to SQLite (existing)
        user_data = user.create_or_update_user(
            user_id=user_info["user_id"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info["picture"]
        )
        
        # CRITICAL: Also save to Firestore
        db = FirestoreService()
        user_doc_ref = db._get_user_ref(user_data["user_id"])
        user_doc_ref.set({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data["picture"],
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat()
        }, merge=True)
        
        print(f"[AUTH] User saved to Firestore: {user_data['email']}")
        
        # Save Google OAuth tokens to Firestore
        tokens_saved = await google_oauth.save_tokens_to_firestore(
            user_id=user_data["user_id"],
            tokens={
                "access_token": user_info.get("access_token"),
                "refresh_token": user_info.get("refresh_token"),
                "expires_in": 3600
            }
        )
        
        if tokens_saved:
            print(f"[AUTH] Google tokens saved to Firestore")
        else:
            print(f"[WARNING] Failed to save Google tokens")
        
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

# ============================================
# MASTER SCHEDULER ENDPOINT (ALL USERS)
# ============================================

@app.post("/api/email-intelligence/check-all")
async def check_emails_all_users():
    """Master scheduler endpoint - checks ALL users"""
    
    print("[MASTER SCHEDULER] Starting check for all users")
    
    try:
        from services.token_service import TokenService
        from agents.email_assistant_agent import EmailAssistantAgent
        
        db = FirestoreService()
        token_service = TokenService()
        
        # Get all users
        users_ref = db.db.collection("users").stream()
        
        all_users = []
        users_with_tokens = []
        
        for user_doc in users_ref:
            user_id = user_doc.id
            all_users.append(user_id)
            print(f"[MASTER SCHEDULER] Found user: {user_id}")
            
            # Check if user has Gmail tokens
            token_doc = db._get_user_ref(user_id).collection("google_tokens").document("gmail").get()
            
            if token_doc.exists:
                token_data = token_doc.to_dict()
                if token_data.get("access_token") and token_data.get("refresh_token"):
                    users_with_tokens.append(user_id)
                    print(f"[MASTER SCHEDULER] ✓ User {user_id} has Gmail tokens")
        
        print(f"[MASTER SCHEDULER] Total users: {len(all_users)}, With Gmail: {len(users_with_tokens)}")
        
        # Process each user
        results = []
        for user_id in users_with_tokens:
            try:
                print(f"[MASTER SCHEDULER] Processing user: {user_id}")
                
                agent = EmailAssistantAgent(user_id=user_id)
                result = await agent.process_yesterdays_emails(max_emails=20)
                
                results.append({
                    "user_id": user_id,
                    "status": "success",
                    "drafts_created": result.get('drafts_created', 0)
                })
                
                print(f"[MASTER SCHEDULER] ✓ User {user_id}: {result.get('drafts_created', 0)} drafts")
                
            except Exception as e:
                print(f"[ERROR] Failed for user {user_id}: {e}")
                results.append({"user_id": user_id, "status": "error", "error": str(e)})
        
        return {
            "status": "success",
            "total_users": len(all_users),
            "users_with_gmail": len(users_with_tokens),
            "users_processed": len(results),
            "results": results
        }
        
    except Exception as e:
        print(f"[ERROR] Master scheduler failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
@app.get("/api/collections")
async def get_collections(authorization: str = Header(None)):
    """Get smart collections based on 12 life domains"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        print(f"[API] Collections request for user: {user_id}")
        
        db = FirestoreService()
        
        # Get all memories
        all_memories = []
        docs = db._get_user_ref(user_id).collection(settings.COLLECTION_MEMORIES).stream()
        for doc in docs:
            memory_data = doc.to_dict()
            memory_data['id'] = doc.id
            all_memories.append(memory_data)
        
        print(f"[API] Found {len(all_memories)} total memories")
        
        # Define 12 collections
        collections_config = [
            {
                "id": "work_career",
                "name": "Work & Career",
                "description": "Job postings, meetings, tasks, and professional growth",
                "icon": "Briefcase",
                "domain": "work_career"
            },
            {
                "id": "education_learning",
                "name": "Education & Learning",
                "description": "Courses, tutorials, research, and study materials",
                "icon": "GraduationCap",
                "domain": "education_learning"
            },
            {
                "id": "money_finance",
                "name": "Money & Finance",
                "description": "Bills, payments, subscriptions, and investments",
                "icon": "DollarSign",
                "domain": "money_finance"
            },
            {
                "id": "home_daily_life",
                "name": "Home & Daily Life",
                "description": "Groceries, repairs, utilities, and household tasks",
                "icon": "Home",
                "domain": "home_daily_life"
            },
            {
                "id": "health_wellbeing",
                "name": "Health & Wellness",
                "description": "Doctor appointments, fitness, and medical records",
                "icon": "Heart",
                "domain": "health_wellbeing"
            },
            {
                "id": "family_relationships",
                "name": "Family & Relationships",
                "description": "Family events, birthdays, and personal connections",
                "icon": "Users",
                "domain": "family_relationships"
            },
            {
                "id": "travel_movement",
                "name": "Travel & Movement",
                "description": "Flights, hotels, itineraries, and travel plans",
                "icon": "Plane",
                "domain": "travel_movement"
            },
            {
                "id": "shopping_consumption",
                "name": "Shopping",
                "description": "Products, wishlists, and purchase decisions",
                "icon": "ShoppingCart",
                "domain": "shopping_consumption"
            },
            {
                "id": "entertainment_leisure",
                "name": "Entertainment",
                "description": "Movies, shows, games, and leisure activities",
                "icon": "Film",
                "domain": "entertainment_leisure"
            },
            {
                "id": "social_community",
                "name": "Social & Community",
                "description": "Social posts, news, and community engagement",
                "icon": "MessageCircle",
                "domain": "social_community"
            },
            {
                "id": "admin_documents",
                "name": "Documents & Admin",
                "description": "IDs, forms, legal documents, and official papers",
                "icon": "FileText",
                "domain": "admin_documents"
            },
            {
                "id": "ideas_thoughts",
                "name": "Ideas & Thoughts",
                "description": "Personal notes, brainstorms, and creative ideas",
                "icon": "Lightbulb",
                "domain": "ideas_thoughts"
            }
        ]
        
        # Build collections matching SmartCollection type
        collections = []
        for idx, config in enumerate(collections_config):
            domain_memories = [m for m in all_memories if m.get('domain') == config['domain']]
            
            if len(domain_memories) > 0:  # Only include collections with items
                collections.append({
                    "id": config['id'],
                    "name": config['name'],
                    "description": config['description'],
                    "icon": config['icon'],
                    "filter": {
                        "domains": [config['domain']]  # Filter by domain
                    },
                    "captureIds": [m['id'] for m in domain_memories],
                    "order": idx
                })
        
        print(f"[API] Returning {len(collections)} non-empty collections")
        
        return {
            "success": True,
            "collections": collections,
            "total": len(collections)
        }
        
    except Exception as e:
        print(f"[ERROR] Collections fetch failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    

# Initialize at top with other services
clustering_service = ClusteringService()

@app.get("/api/synthesis/clusters")
async def get_theme_clusters(
    num_clusters: int = Query(4, ge=2, le=8),
    authorization: str = Header(None)
):
    """Generate AI-powered theme clusters from user's memories"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        print(f"[SYNTHESIS] Generating theme clusters for user: {user_id}")
        
        db = FirestoreService()
        
        # Get all memories
        memories_query = (
            db._get_user_ref(user_id)
            .collection(settings.COLLECTION_MEMORIES)
            .limit(100)
            .stream()
        )
        
        memories = []
        for doc in memories_query:
            memory_data = doc.to_dict()
            memory_data['id'] = doc.id
            memories.append(memory_data)
        
        print(f"[SYNTHESIS] Found {len(memories)} memories")
        
        if len(memories) < 2:
            return {
                "success": True,
                "clusters": [],
                "total": 0,
                "message": "Not enough captures yet. Capture more items to discover themes!"
            }
        
        # Generate clusters using AI
        clusters = clustering_service.generate_clusters(
            memories=memories,
            num_clusters=num_clusters
        )
        
        print(f"[SYNTHESIS] Returning {len(clusters)} clusters")
        
        return {
            "success": True,
            "clusters": clusters,
            "total": len(clusters)
        }
        
    except Exception as e:
        print(f"[ERROR] Clustering failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/api/notifications/proactive")
async def get_proactive_notifications(authorization: str = Header(None)):
    """Get AI-powered proactive notifications"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        notifications = notification_service.get_proactive_notifications(user_id)
        
        return {
            "success": True,
            "notifications": notifications,
            "count": len(notifications)
        }
        
    except Exception as e:
        print(f"[API] Proactive notifications failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    


@app.get("/api/debug/firestore-schema")
async def debug_firestore_schema(authorization: str = Header(None)):
    """Debug endpoint - See actual Firestore structure"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    payload = jwt_manager.verify_jwt_token(token)
    user_id = payload["user_id"]
    
    try:
        db = FirestoreService()
        
        schema = {
            "collections": {}
        }
        
        # Check each collection
        collections = [
            'memories',
            'comprehensive_captures',
            'captures',
            'notes',
            'research_results',
            'shopping_lists',
            'task_resources'
        ]
        
        for coll_name in collections:
            try:
                coll_ref = db._get_user_ref(user_id).collection(coll_name)
                docs = list(coll_ref.limit(2).stream())
                
                if len(docs) > 0:
                    # Get first document
                    first_doc = docs[0].to_dict()
                    
                    # Recursively get structure
                    schema["collections"][coll_name] = {
                        "count": len(docs),
                        "sample_id": docs[0].id,
                        "structure": get_schema_structure(first_doc)
                    }
                else:
                    schema["collections"][coll_name] = {"count": 0}
                    
            except Exception as e:
                schema["collections"][coll_name] = {"error": str(e)}
        
        return schema
        
    except Exception as e:
        return {"error": str(e)}


def get_schema_structure(obj, depth=0, max_depth=3):
    """Recursively get structure of nested dict"""
    
    if depth > max_depth:
        return "..."
    
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(value, dict):
                result[key] = get_schema_structure(value, depth + 1, max_depth)
            elif isinstance(value, list):
                if len(value) > 0:
                    result[key] = [get_schema_structure(value[0], depth + 1, max_depth)]
                else:
                    result[key] = []
            else:
                result[key] = f"<{type(value).__name__}>"
        return result
    elif isinstance(obj, list):
        if len(obj) > 0:
            return [get_schema_structure(obj[0], depth + 1, max_depth)]
        return []
    else:
        return f"<{type(obj).__name__}>"
    
@app.get("/api/debug/schema-all")
async def debug_schema_all():
    """Debug endpoint - Get schema for ALL collections (REMOVE IN PRODUCTION!)"""
    
    # Hardcode your user ID for testing
    user_id = "104141873915987258012"
    
    try:
        db = FirestoreService()
        user_ref = db._get_user_ref(user_id)
        
        schema = {}
        
        # List of all possible collections
        collections = [
            'comprehensive_captures',
            'memories',
            'captures',
            'notes',
            'research_results',
            'shopping_lists',
            'task_resources',
            'learning_items'
        ]
        
        for coll_name in collections:
            try:
                coll_ref = user_ref.collection(coll_name)
                docs = list(coll_ref.limit(1).stream())
                
                if len(docs) == 0:
                    schema[coll_name] = {"status": "empty", "count": 0}
                    continue
                
                doc = docs[0]
                data = doc.to_dict()
                
                # Get field names and types
                field_info = {}
                for key, value in data.items():
                    if isinstance(value, dict):
                        field_info[key] = {
                            "type": "dict",
                            "keys": list(value.keys())[:10]  # First 10 keys
                        }
                    elif isinstance(value, list):
                        field_info[key] = {
                            "type": "list",
                            "length": len(value),
                            "sample": value[0] if len(value) > 0 else None
                        }
                    else:
                        field_info[key] = {
                            "type": type(value).__name__,
                            "sample": str(value)[:100] if isinstance(value, str) else value
                        }
                
                schema[coll_name] = {
                    "status": "found",
                    "document_id": doc.id,
                    "field_count": len(data),
                    "fields": field_info,
                    "full_sample": data  # Complete first document
                }
                
            except Exception as e:
                schema[coll_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "user_id": user_id,
            "collections": schema
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    

@app.get("/api/storage/download")
async def get_signed_url(
    path: str = Query(..., description="GCS file path"),
    authorization: str = Header(None)
):
    """
    Generate a signed URL for a GCS file
    Allows temporary access to private storage files
    """
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt_manager.verify_jwt_token(token)
        user_id = payload["user_id"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    try:
        from services.storage_service import StorageService
        storage = StorageService()
        
        # Generate signed URL (valid for 1 hour)
        signed_url = storage.generate_signed_url(path, expiration=3600)
        
        print(f"[STORAGE] Generated signed URL for: {path}")
        
        # Redirect to signed URL
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=signed_url)
        
    except Exception as e:
        print(f"[ERROR] Failed to generate signed URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/storage/file/{user_id}/{folder}/{filename}")
async def proxy_gcs_file(
    user_id: str,
    folder: str,
    filename: str,
    authorization: str = Header(None)
):
    """
    Proxy GCS files through backend
    No signed URLs needed - backend has access
    """
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt_manager.verify_jwt_token(token)
        request_user_id = payload["user_id"]
        
        # Security: Only allow users to access their own files
        if user_id != request_user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    try:
        from services.storage_service import StorageService
        storage = StorageService()
        
        # Construct GCS path
        gcs_path = f"users/{user_id}/{folder}/{filename}"
        
        # Download file from GCS
        blob = storage.bucket.blob(gcs_path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file content
        file_bytes = blob.download_as_bytes()
        
        # Determine content type
        content_type = blob.content_type or "application/octet-stream"
        
        print(f"[STORAGE PROXY] Serving file: {gcs_path}")
        
        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to proxy file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

# if __name__ == "__main__":
#     import uvicorn
#     print("[STARTUP] LifeOS Multi-Agent System v2.0")
#     print("[STARTUP] 3-Layer Universal Classification System")
#     print("[STARTUP] Domains: 12 | Context Types: 19 | Intents: 14")
#     print("[STARTUP] API running athttps://lifeos-backend-1056690364460.us-central1.run.app")
#     port = int(os.getenv("PORT", "3001"))
#     uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    import uvicorn
    print("[STARTUP] LifeOS Multi-Agent System v2.0")
    print("[STARTUP] 3-Layer Universal Classification System")
    print("[STARTUP] Domains: 12 | Context Types: 19 | Intents: 14")
    
    # Dynamic port and host info
    port = int(os.getenv("PORT", "8000"))  # Changed default to 8000
    host = "0.0.0.0"
    
    # Determine environment
    env = os.getenv("ENV", "local")
    if env == "cloud":
        print(f"[STARTUP] API running on Cloud Run (port {port})")
    else:
        print(f"[STARTUP] API running locally at http://localhost:{port}")
    
    uvicorn.run(app, host=host, port=port)