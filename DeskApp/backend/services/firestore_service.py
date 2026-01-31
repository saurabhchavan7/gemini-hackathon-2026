"""
LifeOS - Firestore Service
Role: Manages hierarchical data storage in Google Cloud Firestore
"""
import os
from google.cloud import firestore
from core.config import settings
from models.capture import Capture
from models.memory import Memory
from models.action import Action
from typing import Optional, List

class FirestoreService:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID") or "gemini-hackathon-2026-484903"
        
        try:
            self.db = firestore.Client(project=self.project_id)
            print(f"[FIRESTORE] Initialized for project: {self.project_id}")
        except Exception as e:
            print(f"[ERROR] Firestore initialization failed: {e}")
            raise e

    def _get_user_ref(self, user_id: str):
        """Helper to get the root document for a user"""
        return self.db.collection("users").document(user_id)

    async def save_capture(self, capture: Capture) -> bool:
        """Saves a raw capture into the user's subcollection"""
        try:
            doc_ref = self._get_user_ref(capture.user_id).collection(settings.COLLECTION_CAPTURES).document(capture.id)
            doc_ref.set(capture.model_dump())
            print(f"[FIRESTORE] Capture {capture.id} saved")
            return True
        except Exception as e:
            print(f"[ERROR] save_capture failed: {e}")
            return False

    async def save_memory(self, memory: Memory) -> bool:
        """Saves a processed memory"""
        try:
            doc_ref = self._get_user_ref(memory.user_id).collection(settings.COLLECTION_MEMORIES).document(memory.id)
            doc_ref.set(memory.model_dump())
            print(f"[FIRESTORE] Memory {memory.id} archived")
            return True
        except Exception as e:
            print(f"[ERROR] save_memory failed: {e}")
            return False

    async def create_action(self, action: Action) -> bool:
        """Adds a new executable task to the user's action list"""
        try:
            doc_ref = self._get_user_ref(action.user_id).collection(settings.COLLECTION_ACTIONS).document(action.id)
            doc_ref.set(action.model_dump())
            return True
        except Exception as e:
            print(f"[ERROR] create_action failed: {e}")
            return False
    
    async def save_graph_edge(self, user_id: str, edge: dict) -> bool:
        """Saves a connection/edge in the knowledge graph"""
        try:
            edge_id = f"{edge['source_id']}__{edge['target_id']}"
            doc_ref = self._get_user_ref(user_id).collection(settings.COLLECTION_GRAPH).document(edge_id)
            doc_ref.set(edge)
            print(f"[FIRESTORE] Graph edge saved: {edge['relationship']}")
            return True
        except Exception as e:
            print(f"[ERROR] save_graph_edge failed: {e}")
            return False
    
    async def get_user_memories(self, user_id: str, limit: int = 20) -> list:
        """Retrieves recent memories for graph analysis"""
        try:
            docs = self._get_user_ref(user_id).collection(settings.COLLECTION_MEMORIES).limit(limit).stream()
            memories = []
            for doc in docs:
                memory_data = doc.to_dict()
                memory_data['id'] = doc.id
                memories.append(memory_data)
            return memories
        except Exception as e:
            print(f"[ERROR] get_user_memories failed: {e}")
            return []

    async def get_user_graph(self, user_id: str) -> list:
        """Retrieves all graph edges for a user"""
        try:
            docs = self._get_user_ref(user_id).collection(settings.COLLECTION_GRAPH).stream()
            edges = []
            for doc in docs:
                edge_data = doc.to_dict()
                edges.append(edge_data)
            return edges
        except Exception as e:
            print(f"[ERROR] get_user_graph failed: {e}")
            return []
    
    async def get_google_calendar_events(self, user_id: str, limit: int = 20) -> list:
        """Retrieves Google Calendar events from Firestore cache"""
        try:
            docs = (
                self._get_user_ref(user_id)
                .collection("google_calendar_events")
                .order_by("start_time", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                event_data['id'] = doc.id
                events.append(event_data)
            return events
        except Exception as e:
            print(f"[ERROR] get_google_calendar_events failed: {e}")
            return []

    async def get_google_tasks(self, user_id: str, limit: int = 20) -> list:
        """Retrieves Google Tasks from Firestore cache"""
        try:
            docs = (
                self._get_user_ref(user_id)
                .collection("google_tasks")
                .where("completed", "==", False)
                .limit(limit)
                .stream()
            )
            tasks = []
            for doc in docs:
                task_data = doc.to_dict()
                task_data['id'] = doc.id
                tasks.append(task_data)
            return tasks
        except Exception as e:
            print(f"[ERROR] get_google_tasks failed: {e}")
            return []

    async def get_shopping_list(self, user_id: str) -> list:
        """Retrieves shopping list items"""
        try:
            docs = (
                self._get_user_ref(user_id)
                .collection("shopping_lists")
                .where("status", "==", "pending")
                .stream()
            )
            items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data['id'] = doc.id
                items.append(item_data)
            return items
        except Exception as e:
            print(f"[ERROR] get_shopping_list failed: {e}")
            return []

    async def get_notes(self, user_id: str, limit: int = 50) -> list:
        """Retrieves user's notes"""
        try:
            docs = (
                self._get_user_ref(user_id)
                .collection("notes")
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            notes = []
            for doc in docs:
                note_data = doc.to_dict()
                note_data['id'] = doc.id
                notes.append(note_data)
            return notes
        except Exception as e:
            print(f"[ERROR] get_notes failed: {e}")
            return []

    async def get_task_resources(self, user_id: str, limit: int = 20) -> list:
        """Retrieves learning resources for user's tasks"""
        try:
            docs = (
                self._get_user_ref(user_id)
                .collection("task_resources")
                .where("status", "==", "active")
                .order_by("generated_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            resources = []
            for doc in docs:
                resource_data = doc.to_dict()
                resource_data['id'] = doc.id
                resources.append(resource_data)
            return resources
        except Exception as e:
            print(f"[ERROR] get_task_resources failed: {e}")
            return []
    
    async def update_resource_feedback(self, user_id: str, resource_id: str, feedback: dict) -> bool:
        """Update user feedback for resources"""
        try:
            doc_ref = self._get_user_ref(user_id).collection("task_resources").document(resource_id)
            doc_ref.update({"user_feedback": feedback})
            print(f"[FIRESTORE] Updated resource feedback: {resource_id}")
            return True
        except Exception as e:
            print(f"[ERROR] update_resource_feedback failed: {e}")
            return False