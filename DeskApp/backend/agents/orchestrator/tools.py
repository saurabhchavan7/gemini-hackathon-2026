"""
LifeOS - Orchestrator Tools
These functions are called by Agent 3 when it detects actionable intents
"""
from typing import Dict
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from services.firestore_service import FirestoreService
from services.google_calendar_service import GoogleCalendarService
from services.google_tasks_service import GoogleTasksService

def add_to_shopping_list(user_id: str, item_name: str, price: float = 0.0) -> Dict:
    """
    Adds a detected product to the user's Firestore shopping list.
    Creates a document in users/{userId}/shopping_lists collection
    """
    try:
        db = FirestoreService()
        
        item_data = {
            "item_name": item_name,
            "price": price,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator"
        }
        
        doc_ref = db._get_user_ref(user_id).collection("shopping_lists").document()
        doc_ref.set(item_data)
        
        print(f"[TOOL] Added {item_name} to shopping list for user {user_id}")
        return {
            "status": "success", 
            "message": f"Added {item_name} to your shopping list",
            "item_id": doc_ref.id
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to add to shopping list: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def create_calendar_event(
    user_id: str, 
    event_title: str, 
    start_time: str,
    end_time: str = None,
    description: str = None,
    location: str = None,
    user_timezone: str = "UTC"
) -> Dict:
    """
    Creates an event in Google Calendar AND saves to Firestore.
    Uses user's actual timezone.
    """
    try:
        calendar_service = GoogleCalendarService(user_id)
        
        conflict_check = calendar_service.check_conflicts(start_time, end_time)
        
        if conflict_check['status'] == 'conflict':
            print(f"[WARNING] Scheduling conflict: {conflict_check['message']}")
        
        result = calendar_service.create_event(
            title=event_title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            user_timezone=user_timezone
        )
        
        if result['status'] == 'success':
            print(f"[TOOL] Created calendar event '{event_title}' in timezone {user_timezone}")
            return {
                "status": "success",
                "message": f"Event '{event_title}' added to Google Calendar",
                "google_link": result['google_link'],
                "event_id": result['firestore_id']
            }
        else:
            return result
        
    except Exception as e:
        print(f"[ERROR] Failed to create calendar event: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def create_task(
    user_id: str,
    task_title: str,
    notes: str = None,
    due_date: str = None
) -> Dict:
    """
    Creates a task in Google Tasks AND saves to Firestore.
    Use this for actionable items without specific times.
    """
    try:
        tasks_service = GoogleTasksService(user_id)
        
        result = tasks_service.create_task(
            title=task_title,
            notes=notes,
            due_date=due_date
        )
        
        if result['status'] == 'success':
            print(f"[TOOL] Created task '{task_title}' in Google Tasks")
            return {
                "status": "success",
                "message": f"Task '{task_title}' added to Google Tasks",
                "task_id": result['firestore_id']
            }
        else:
            return result
        
    except Exception as e:
        print(f"[ERROR] Failed to create task: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def create_note(user_id: str, title: str, content: str) -> Dict:
    """
    Creates a note for reference items.
    Creates a document in users/{userId}/notes collection
    """
    try:
        db = FirestoreService()
        
        note_data = {
            "title": title,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
            "source": "agent_orchestrator",
            "tags": []
        }
        
        doc_ref = db._get_user_ref(user_id).collection("notes").document()
        doc_ref.set(note_data)
        
        print(f"[TOOL] Created note '{title}' for user {user_id}")
        return {
            "status": "success",
            "message": f"Note '{title}' created",
            "note_id": doc_ref.id
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to create note: {e}")
        return {
            "status": "error",
            "message": str(e)
        }