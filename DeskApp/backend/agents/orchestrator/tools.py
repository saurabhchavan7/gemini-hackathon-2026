"""
LifeOS - Orchestrator Tools (Expanded for 3-Layer Classification)
14 Intents × 12 Domains Support
ALL TOOLS NOW ACCEPT AND STORE capture_id
"""
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from services.firestore_service import FirestoreService
from services.google_calendar_service import GoogleCalendarService
from services.google_tasks_service import GoogleTasksService


# ============================================
# EXISTING TOOLS (Enhanced with capture_id)
# ============================================

def add_to_shopping_list(
    user_id: str, 
    item_name: str, 
    price: float = 0.0, 
    domain: str = "shopping_consumption",
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: buy
    Adds a product to shopping list
    """
    try:
        db = FirestoreService()
        
        item_data = {
            "item_name": item_name,
            "price": price,
            "status": "pending",
            "domain": domain,
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("shopping_lists").document()
        doc_ref.set(item_data)
        
        print(f"[TOOL] Added '{item_name}' to shopping list (capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Added {item_name} to shopping list", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] add_to_shopping_list failed: {e}")
        return {"status": "error", "message": str(e)}


async def create_calendar_event(
    user_id: str, 
    event_title: str, 
    start_time: str,
    end_time: str = None,
    description: str = None,
    location: str = None,
    user_timezone: str = "UTC",
    attendees: List[str] = None,
    send_invites: bool = False,
    domain: str = "work_career",
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: schedule
    Creates event in Google Calendar + Firestore
    """
    try:
        calendar_service = GoogleCalendarService(user_id)
        await calendar_service.initialize()
        
        result = calendar_service.create_event(
            title=event_title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            user_timezone=user_timezone,
            attendees=attendees,
            send_invites=send_invites,
            capture_id=capture_id
        )
        
        if result['status'] == 'success':
            attendee_info = f" with {len(attendees)} attendees" if attendees else ""
            print(f"[TOOL] Created calendar event '{event_title}'{attendee_info} (capture: {capture_id})")
            return {
                "status": "success",
                "message": f"Event '{event_title}' added to Google Calendar",
                "google_link": result.get('google_link'),
                "google_event_id": result.get('google_event_id'),
                "firestore_doc_id": result.get('firestore_doc_id'),
                "capture_id": capture_id,
                "domain": domain
            }
        return result
        
    except Exception as e:
        print(f"[ERROR] create_calendar_event failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


async def create_task(
    user_id: str,
    task_title: str,
    notes: str = None,
    due_date: str = None,
    domain: str = "work_career",
    priority: int = 3,
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: act
    Creates task in Google Tasks + Firestore
    """
    try:
        tasks_service = GoogleTasksService(user_id)
        await tasks_service.initialize()
        
        result = tasks_service.create_task(
            title=task_title,
            notes=notes,
            due_date=due_date,
            capture_id=capture_id
        )
        
        if result['status'] == 'success':
            print(f"[TOOL] Created task '{task_title}' (domain: {domain}, capture: {capture_id})")
            return {
                "status": "success",
                "message": f"Task '{task_title}' added to Google Tasks",
                "google_task_id": result.get('google_task_id'),
                "firestore_doc_id": result.get('firestore_doc_id'),
                "capture_id": capture_id,
                "domain": domain
            }
        return result
        
    except Exception as e:
        print(f"[ERROR] create_task failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def create_note(
    user_id: str, 
    title: str, 
    content: str, 
    domain: str = "ideas_thoughts",
    tags: List[str] = None,
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: remember, reference, archive
    Creates a note in Firestore
    """
    try:
        db = FirestoreService()
        
        note_data = {
            "title": title,
            "content": content,
            "domain": domain,
            "tags": tags or ["Note", "Ideas", "Thoughts"],
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("notes").document()
        doc_ref.set(note_data)
        
        print(f"[TOOL] Created note '{title}' (domain: {domain}, capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Note '{title}' created", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] create_note failed: {e}")
        return {"status": "error", "message": str(e)}


# ============================================
# NEW TOOLS FOR 3-LAYER SYSTEM (All with capture_id)
# ============================================

def add_to_bills(
    user_id: str,
    bill_name: str,
    amount: float = 0.0,
    due_date: str = None,
    category: str = "utilities",
    recurring: bool = False,
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: pay
    Domain: money_finance
    Adds a bill/payment to financial tracking
    """
    try:
        db = FirestoreService()
        
        bill_data = {
            "bill_name": bill_name,
            "amount": amount,
            "due_date": due_date,
            "category": category,
            "recurring": recurring,
            "status": "pending",
            "domain": "money_finance",
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("financial_items").document()
        doc_ref.set(bill_data)
        
        print(f"[TOOL] Added bill '{bill_name}' (${amount}, capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Bill '{bill_name}' added", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] add_to_bills failed: {e}")
        return {"status": "error", "message": str(e)}


async def create_health_item(
    user_id: str,
    title: str,
    item_type: str = "appointment",
    date_time: str = None,
    doctor: str = None,
    notes: str = None,
    add_to_calendar: bool = True,
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: schedule, track, remember
    Domain: health_wellbeing
    Creates health-related item (appointment, medication, etc.)
    """
    try:
        db = FirestoreService()
        
        health_data = {
            "title": title,
            "item_type": item_type,
            "date_time": date_time,
            "doctor": doctor,
            "notes": notes,
            "status": "scheduled" if item_type == "appointment" else "active",
            "domain": "health_wellbeing",
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("health_items").document()
        doc_ref.set(health_data)
        
        # Also create calendar event for appointments
        if add_to_calendar and date_time and item_type == "appointment":
            calendar_result = await create_calendar_event(
                user_id=user_id,
                event_title=f"Medical: {title}",
                start_time=date_time,
                description=f"Doctor: {doctor}\nNotes: {notes}" if doctor else notes,
                domain="health_wellbeing",
                capture_id=capture_id
            )
            print(f"[TOOL] Also added to calendar: {calendar_result.get('status')}")
        
        print(f"[TOOL] Created health item '{title}' (type: {item_type}, capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Health item '{title}' created", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] create_health_item failed: {e}")
        return {"status": "error", "message": str(e)}


def create_travel_item(
    user_id: str,
    title: str,
    item_type: str = "booking",
    date_time: str = None,
    location: str = None,
    confirmation: str = None,
    notes: str = None,
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: remember, schedule
    Domain: travel_movement
    Saves travel bookings, itineraries, etc.
    """
    try:
        db = FirestoreService()
        
        travel_data = {
            "title": title,
            "item_type": item_type,
            "date_time": date_time,
            "location": location,
            "confirmation_number": confirmation,
            "notes": notes,
            "status": "upcoming",
            "domain": "travel_movement",
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("travel_items").document()
        doc_ref.set(travel_data)
        
        print(f"[TOOL] Created travel item '{title}' (type: {item_type}, capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Travel item '{title}' saved", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] create_travel_item failed: {e}")
        return {"status": "error", "message": str(e)}


def add_to_watchlist(
    user_id: str,
    title: str,
    media_type: str = "movie",
    platform: str = None,
    notes: str = None,
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: remember
    Domain: entertainment_leisure
    Adds movie/show/book to watchlist
    """
    try:
        db = FirestoreService()
        
        media_data = {
            "title": title,
            "media_type": media_type,
            "platform": platform,
            "notes": notes,
            "status": "to_watch",
            "domain": "entertainment_leisure",
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("media_items").document()
        doc_ref.set(media_data)
        
        print(f"[TOOL] Added '{title}' to watchlist ({media_type}, capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"'{title}' added to watchlist", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] add_to_watchlist failed: {e}")
        return {"status": "error", "message": str(e)}


async def create_family_event(
    user_id: str,
    title: str,
    event_type: str = "event",
    date_time: str = None,
    person: str = None,
    notes: str = None,
    add_to_calendar: bool = True,
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: schedule, remember
    Domain: family_relationships
    Creates family-related event (birthday, school event, etc.)
    """
    try:
        db = FirestoreService()
        
        family_data = {
            "title": title,
            "event_type": event_type,
            "date_time": date_time,
            "related_person": person,
            "notes": notes,
            "status": "upcoming",
            "domain": "family_relationships",
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("family_items").document()
        doc_ref.set(family_data)
        
        # Add to calendar
        if add_to_calendar and date_time:
            calendar_result = await create_calendar_event(
                user_id=user_id,
                event_title=f"Family: {title}",
                start_time=date_time,
                description=f"Person: {person}\n{notes}" if person else notes,
                domain="family_relationships",
                capture_id=capture_id
            )
        
        print(f"[TOOL] Created family event '{title}' (capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Family event '{title}' created", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] create_family_event failed: {e}")
        return {"status": "error", "message": str(e)}


def create_tracker(
    user_id: str,
    title: str,
    tracker_type: str = "general",
    current_value: str = None,
    target_value: str = None,
    domain: str = "ideas_thoughts",
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: track
    Creates a tracking entry for monitoring over time
    """
    try:
        db = FirestoreService()
        
        # Determine collection based on domain
        collection_map = {
            "health_wellbeing": "health_items",
            "money_finance": "financial_items",
            "education_learning": "learning_items"
        }
        collection = collection_map.get(domain, "notes")
        
        tracker_data = {
            "title": title,
            "tracker_type": tracker_type,
            "current_value": current_value,
            "target_value": target_value,
            "domain": domain,
            "status": "tracking",
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection(collection).document()
        doc_ref.set(tracker_data)
        
        print(f"[TOOL] Created tracker '{title}' in {collection} (capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Tracker '{title}' created", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] create_tracker failed: {e}")
        return {"status": "error", "message": str(e)}


def create_comparison(
    user_id: str,
    title: str,
    options: List[str] = None,
    criteria: List[str] = None,
    notes: str = None,
    domain: str = "shopping_consumption",
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: compare
    Creates a comparison note for evaluating options
    """
    try:
        db = FirestoreService()
        
        comparison_data = {
            "title": f"Comparison: {title}",
            "options": options or [],
            "criteria": criteria or [],
            "notes": notes,
            "domain": domain,
            "item_type": "comparison",
            "status": "evaluating",
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("notes").document()
        doc_ref.set(comparison_data)
        
        print(f"[TOOL] Created comparison '{title}' (capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Comparison '{title}' created", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] create_comparison failed: {e}")
        return {"status": "error", "message": str(e)}


async def create_reminder(
    user_id: str,
    title: str,
    remind_date: str = None,
    notes: str = None,
    domain: str = "work_career",
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: follow_up
    Creates a follow-up reminder as a Google Task
    """
    try:
        result = await create_task(
            user_id=user_id,
            task_title=f"Follow up: {title}",
            notes=notes,
            due_date=remind_date,
            domain=domain,
            capture_id=capture_id
        )
        
        print(f"[TOOL] Created follow-up reminder '{title}' (capture: {capture_id})")
        return result
        
    except Exception as e:
        print(f"[ERROR] create_reminder failed: {e}")
        return {"status": "error", "message": str(e)}


async def create_waiting_item(
    user_id: str,
    title: str,
    waiting_for: str = None,
    expected_date: str = None,
    notes: str = None,
    domain: str = "work_career",
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: wait
    Creates a 'waiting for' item to track pending responses
    """
    try:
        task_notes = f"Waiting for: {waiting_for}\n{notes}" if waiting_for else notes
        
        result = await create_task(
            user_id=user_id,
            task_title=f"Waiting: {title}",
            notes=task_notes,
            due_date=expected_date,
            domain=domain,
            capture_id=capture_id
        )
        
        print(f"[TOOL] Created waiting item '{title}' (capture: {capture_id})")
        return result
        
    except Exception as e:
        print(f"[ERROR] create_waiting_item failed: {e}")
        return {"status": "error", "message": str(e)}


def archive_item(
    user_id: str,
    title: str,
    content: str,
    domain: str = "admin_documents",
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: archive
    Saves item for records with no action needed
    """
    try:
        result = create_note(
            user_id=user_id,
            title=f"[Archived] {title}",
            content=content,
            domain=domain,
            tags=["archived", "fyi"],
            capture_id=capture_id
        )
        
        print(f"[TOOL] Archived '{title}' (capture: {capture_id})")
        return result
        
    except Exception as e:
        print(f"[ERROR] archive_item failed: {e}")
        return {"status": "error", "message": str(e)}


async def save_document(
    user_id: str,
    title: str,
    doc_type: str = "general",
    content: str = None,
    expiry_date: str = None,
    notes: str = None,
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: remember, archive
    Domain: admin_documents
    Saves important documents (IDs, forms, etc.)
    """
    try:
        db = FirestoreService()
        
        doc_data = {
            "title": title,
            "doc_type": doc_type,
            "content": content,
            "expiry_date": expiry_date,
            "notes": notes,
            "status": "active",
            "domain": "admin_documents",
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("document_items").document()
        doc_ref.set(doc_data)
        
        # If has expiry, create reminder
        if expiry_date:
            await create_reminder(
                user_id=user_id,
                title=f"{title} expiring",
                remind_date=expiry_date,
                notes=f"Document '{title}' is expiring",
                domain="admin_documents",
                capture_id=capture_id
            )
        
        print(f"[TOOL] Saved document '{title}' (capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Document '{title}' saved", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] save_document failed: {e}")
        return {"status": "error", "message": str(e)}


async def create_learning_item(
    user_id: str,
    title: str,
    item_type: str = "topic",
    content: str = None,
    due_date: str = None,
    notes: str = None,
    capture_id: Optional[str] = None
) -> Dict:
    """
    Intent: learn, act
    Domain: education_learning
    Creates learning item (course, assignment, study topic)
    """
    try:
        db = FirestoreService()
        
        learning_data = {
            "title": title,
            "item_type": item_type,
            "content": content,
            "due_date": due_date,
            "notes": notes,
            "status": "active",
            "domain": "education_learning",
            "capture_id": capture_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("learning_items").document()
        doc_ref.set(learning_data)
        
        # If it's an assignment with due date, also create task
        if item_type == "assignment" and due_date:
            await create_task(
                user_id=user_id,
                task_title=title,
                notes=notes,
                due_date=due_date,
                domain="education_learning",
                capture_id=capture_id
            )
        
        print(f"[TOOL] Created learning item '{title}' (capture: {capture_id})")
        return {
            "status": "success", 
            "message": f"Learning item '{title}' created", 
            "firestore_doc_id": doc_ref.id,
            "capture_id": capture_id
        }
        
    except Exception as e:
        print(f"[ERROR] create_learning_item failed: {e}")
        return {"status": "error", "message": str(e)}


# ============================================
# TOOL REGISTRY (for Agent 3)
# ============================================

TOOL_REGISTRY = {
    # Action-oriented
    "act": create_task,
    "schedule": create_calendar_event,
    "pay": add_to_bills,
    "buy": add_to_shopping_list,
    
    # Information-oriented
    "remember": create_note,
    "learn": create_learning_item,
    "track": create_tracker,
    "reference": create_note,
    
    # Research-oriented
    "research": None,  # Handled by Research Agent via event bus
    "compare": create_comparison,
    
    # Follow-up oriented
    "follow_up": create_reminder,
    "wait": create_waiting_item,
    
    # Low priority
    "archive": archive_item,
    "ignore": None  # Skip - no action
}

# Domain-specific tool overrides
DOMAIN_TOOL_OVERRIDES = {
    ("health_wellbeing", "schedule"): create_health_item,
    ("health_wellbeing", "remember"): create_health_item,
    ("health_wellbeing", "track"): create_health_item,
    
    ("travel_movement", "remember"): create_travel_item,
    ("travel_movement", "schedule"): create_travel_item,
    
    ("family_relationships", "schedule"): create_family_event,
    ("family_relationships", "remember"): create_family_event,
    
    ("entertainment_leisure", "remember"): add_to_watchlist,
    ("entertainment_leisure", "buy"): add_to_watchlist,
    
    ("admin_documents", "remember"): save_document,
    ("admin_documents", "archive"): save_document,
    
    ("education_learning", "learn"): create_learning_item,
    ("education_learning", "act"): create_learning_item,
}


def get_tool_for_intent(domain: str, intent: str):
    """
    Returns the appropriate tool function based on domain + intent combination.
    Uses domain-specific overrides when available.
    """
    # Check for domain-specific override first
    override_key = (domain, intent)
    if override_key in DOMAIN_TOOL_OVERRIDES:
        return DOMAIN_TOOL_OVERRIDES[override_key]
    
    # Fall back to generic intent-based tool
    return TOOL_REGISTRY.get(intent)