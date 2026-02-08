import os
from datetime import datetime
from google.cloud import firestore
from core.config import settings
from models.capture import Capture, CaptureRecord
from models.memory import Memory
from models.action import Action
from typing import Optional, List

"""
LifeOS - Firestore Service (Expanded for 3-Layer Classification)
Manages 12 domain-specific collections + Comprehensive Captures
UNIFIED: All methods use capture_id (not id, source_capture_id, or capture_ref)
"""

DOMAIN_COLLECTIONS = {
    "work_career": "work_items",
    "education_learning": "learning_items",
    "money_finance": "financial_items",
    "home_daily_life": "home_items",
    "health_wellbeing": "health_items",
    "family_relationships": "family_items",
    "travel_movement": "travel_items",
    "shopping_consumption": "shopping_lists",
    "entertainment_leisure": "media_items",
    "social_community": "social_items",
    "admin_documents": "document_items",
    "ideas_thoughts": "notes"
}

class FirestoreService:
    def __init__(self):
        self.project_id = settings.PROJECT_ID or os.getenv("GCP_PROJECT_ID", "")
        if not self.project_id:
            raise ValueError("[FIRESTORE] Missing GCP_PROJECT_ID; set it in the environment.")
        try:
            self.db = firestore.Client(project=self.project_id)
            print(f"[FIRESTORE] Initialized for project: {self.project_id}")
        except Exception as e:
            print(f"[ERROR] Firestore initialization failed: {e}")
            raise e

    def _get_user_ref(self, user_id: str):
        """Helper to get the root document for a user"""
        return self.db.collection("users").document(user_id)

    def _get_collection_for_domain(self, domain: str) -> str:
        """Returns the appropriate collection name for a domain"""
        return DOMAIN_COLLECTIONS.get(domain, "notes")

    # ============================================
    # CORE METHODS - UNIFIED capture_id
    # ============================================

    async def save_capture(self, capture: Capture) -> bool:
        """
        Saves a raw capture into the user's subcollection
        UNIFIED: Uses capture.capture_id (not capture.id)
        """
        try:
            doc_ref = self._get_user_ref(capture.user_id).collection(settings.COLLECTION_CAPTURES).document(capture.capture_id)
            doc_ref.set(capture.model_dump())
            print(f"[FIRESTORE] Capture {capture.capture_id} saved")
            return True
        except Exception as e:
            print(f"[ERROR] save_capture failed: {e}")
            return False

    async def save_memory(self, memory: Memory) -> bool:
        """
        Saves a processed memory with 3-layer classification
        UNIFIED: Uses memory.capture_id (not memory.id)
        """
        try:
            doc_ref = self._get_user_ref(memory.user_id).collection(settings.COLLECTION_MEMORIES).document(memory.capture_id)
            doc_ref.set(memory.model_dump())
            print(f"[FIRESTORE] Memory {memory.capture_id} archived (domain: {memory.domain})")
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

    # ============================================
    # COMPREHENSIVE CAPTURE METHODS
    # ============================================

    async def save_comprehensive_capture(self, capture: 'CaptureRecord') -> bool:
        """
        Saves a comprehensive capture with full metadata
        Stored in users/{user_id}/comprehensive_captures/{capture_id}
        UNIFIED: Uses capture.capture_id
        """
        try:
            doc_ref = (
                self._get_user_ref(capture.user_id)
                .collection("comprehensive_captures")
                .document(capture.capture_id)  #  Use capture_id
            )
            
            # Convert to dict with proper serialization
            capture_dict = capture.model_dump()
            
            # Firestore doesn't like datetime objects, convert to ISO strings
            capture_dict = self._serialize_datetimes(capture_dict)
            
            doc_ref.set(capture_dict)
            
            print(f"[FIRESTORE] Comprehensive capture {capture.capture_id} saved")
            print(f"[FIRESTORE] Status: {capture.status}")
            
            # Safe check for classification domain
            if hasattr(capture, 'classification') and hasattr(capture.classification, 'domain'):
                print(f"[FIRESTORE] Domain: {capture.classification.domain}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] save_comprehensive_capture failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def update_comprehensive_capture(self, capture: 'CaptureRecord') -> bool:
        """
        Updates an existing comprehensive capture
        Used by background agents to add their results
        UNIFIED: Uses capture.capture_id
        """
        try:
            doc_ref = (
                self._get_user_ref(capture.user_id)
                .collection("comprehensive_captures")
                .document(capture.capture_id)  # ✅ Use capture_id
            )
            
            capture_dict = capture.model_dump()
            capture_dict = self._serialize_datetimes(capture_dict)
            
            doc_ref.set(capture_dict, merge=True)
            
            print(f"[FIRESTORE] Comprehensive capture {capture.capture_id} updated")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] update_comprehensive_capture failed: {e}")
            return False
        
    async def update_capture_fields(
        self,
        user_id: str,
        capture_id: str,
        field_updates: dict
    ) -> bool:
        """
        Update specific fields in comprehensive_captures WITHOUT loading full document
        
        Args:
            user_id: User ID
            capture_id: Capture document ID
            field_updates: Dict of field paths to update
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc_ref = (
                self._get_user_ref(user_id)
                .collection("comprehensive_captures")
                .document(capture_id)
            )
            
            # Serialize any datetime objects in updates
            serialized_updates = self._serialize_datetimes(field_updates)
            
            # Use Firestore's update method (not set!)
            doc_ref.update(serialized_updates)
            
            print(f"[FIRESTORE] Updated capture {capture_id} fields: {list(field_updates.keys())}")
            return True
            
        except Exception as e:
            print(f"[ERROR] update_capture_fields failed for {capture_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def get_comprehensive_capture(self, user_id: str, capture_id: str) -> dict:
        """
        Retrieves a comprehensive capture by ID
        Returns full capture with all agent results
        """
        try:
            doc_ref = (
                self._get_user_ref(user_id)
                .collection("comprehensive_captures")
                .document(capture_id)
            )
            
            doc = doc_ref.get()
            
            if not doc.exists:
                print(f"[FIRESTORE] Comprehensive capture {capture_id} not found")
                return None
            
            capture_data = doc.to_dict()
            capture_data['id'] = doc.id  # For backward compatibility
            
            print(f"[FIRESTORE] Retrieved comprehensive capture {capture_id}")
            print(f"[FIRESTORE] Status: {capture_data.get('status')}")
            
            return capture_data
            
        except Exception as e:
            print(f"[ERROR] get_comprehensive_capture failed: {e}")
            return None

    async def list_comprehensive_captures(
        self, 
        user_id: str, 
        limit: int = 20,
        status: str = None
    ) -> list:
        """List comprehensive captures for a user"""
        try:
            query = (
                self._get_user_ref(user_id)
                .collection("comprehensive_captures")
                .order_by("created_at", direction=firestore.Query.DESCENDING)
            )
            
            if status:
                query = query.where("status", "==", status)
            
            docs = query.limit(limit).stream()
            
            captures = []
            for doc in docs:
                capture_data = doc.to_dict()
                capture_data['id'] = doc.id  # For backward compatibility
                captures.append(capture_data)
            
            print(f"[FIRESTORE] Retrieved {len(captures)} comprehensive captures")
            
            return captures
            
        except Exception as e:
            print(f"[ERROR] list_comprehensive_captures failed: {e}")
            return []

    def _serialize_datetimes(self, obj):
        """
        Recursively convert datetime objects to ISO format strings
        Firestore doesn't accept Python datetime objects directly
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetimes(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        else:
            return obj

    # ============================================
    # STATISTICS
    # ============================================

    async def get_capture_statistics(self, user_id: str) -> dict:
        """Get statistics about user's comprehensive captures"""
        try:
            docs = (
                self._get_user_ref(user_id)
                .collection("comprehensive_captures")
                .stream()
            )
            
            total = 0
            by_status = {"processing": 0, "completed": 0, "failed": 0, "partial_failure": 0}
            by_domain = {}
            total_processing_time = 0
            
            for doc in docs:
                data = doc.to_dict()
                total += 1
                
                # Count by status
                status = data.get("status", "unknown")
                if status in by_status:
                    by_status[status] += 1
                
                # Count by domain
                domain = data.get("classification", {}).get("domain", "unknown")
                by_domain[domain] = by_domain.get(domain, 0) + 1
                
                # Sum processing time
                timeline = data.get("timeline", {})
                proc_time = timeline.get("total_processing_time_ms", 0)
                total_processing_time += proc_time
            
            avg_processing_time = total_processing_time / total if total > 0 else 0
            
            stats = {
                "total_captures": total,
                "by_status": by_status,
                "by_domain": by_domain,
                "avg_processing_time_ms": int(avg_processing_time),
                "success_rate": round(by_status["completed"] / total * 100, 1) if total > 0 else 0
            }
            
            print(f"[FIRESTORE] Capture statistics: {total} total, {stats['success_rate']}% success")
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] get_capture_statistics failed: {e}")
            return {
                "total_captures": 0,
                "by_status": {},
                "by_domain": {},
                "avg_processing_time_ms": 0,
                "success_rate": 0
            }

    # ============================================
    # MEMORY & GRAPH RETRIEVAL
    # ============================================

    async def get_user_memories(self, user_id: str, limit: int = 20, domain: str = None) -> list:
        """Retrieves memories with optional domain filter"""
        try:
            query = self._get_user_ref(user_id).collection(settings.COLLECTION_MEMORIES)
            
            if domain:
                query = query.where("domain", "==", domain)
            
            docs = query.limit(limit).stream()
            
            memories = []
            for doc in docs:
                memory_data = doc.to_dict()
                memory_data['id'] = doc.id  # For backward compatibility
                memories.append(memory_data)
            return memories
        except Exception as e:
            print(f"[ERROR] get_user_memories failed: {e}")
            return []

    async def get_memories_by_intent(self, user_id: str, intent: str, limit: int = 20) -> list:
        """Retrieves memories filtered by intent"""
        try:
            docs = (
                self._get_user_ref(user_id)
                .collection(settings.COLLECTION_MEMORIES)
                .where("intent", "==", intent)
                .limit(limit)
                .stream()
            )
            
            memories = []
            for doc in docs:
                memory_data = doc.to_dict()
                memory_data['id'] = doc.id  # For backward compatibility
                memories.append(memory_data)
            return memories
        except Exception as e:
            print(f"[ERROR] get_memories_by_intent failed: {e}")
            return []

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

    # ============================================
    # COLLECTION RETRIEVAL METHODS
    # ============================================

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

    async def get_notes(self, user_id: str, limit: int = 50, domain: str = None) -> list:
        """Retrieves user's notes with optional domain filter"""
        try:
            query = self._get_user_ref(user_id).collection("notes")
            
            if domain:
                query = query.where("domain", "==", domain)
            
            docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
            
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

    # ============================================
    # DOMAIN-SPECIFIC COLLECTION METHODS
    # ============================================

    async def get_financial_items(self, user_id: str, status: str = "pending", limit: int = 50) -> list:
        """Retrieves financial items (bills, payments, subscriptions)"""
        try:
            query = self._get_user_ref(user_id).collection("financial_items")
            
            if status:
                query = query.where("status", "==", status)
            
            docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data['id'] = doc.id
                items.append(item_data)
            return items
        except Exception as e:
            print(f"[ERROR] get_financial_items failed: {e}")
            return []

    async def get_health_items(self, user_id: str, item_type: str = None, limit: int = 50) -> list:
        """Retrieves health items (appointments, medications, records)"""
        try:
            query = self._get_user_ref(user_id).collection("health_items")
            
            if item_type:
                query = query.where("item_type", "==", item_type)
            
            docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data['id'] = doc.id
                items.append(item_data)
            return items
        except Exception as e:
            print(f"[ERROR] get_health_items failed: {e}")
            return []

    async def get_travel_items(self, user_id: str, status: str = "upcoming", limit: int = 50) -> list:
        """Retrieves travel items (bookings, itineraries)"""
        try:
            query = self._get_user_ref(user_id).collection("travel_items")
            
            if status:
                query = query.where("status", "==", status)
            
            docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data['id'] = doc.id
                items.append(item_data)
            return items
        except Exception as e:
            print(f"[ERROR] get_travel_items failed: {e}")
            return []

    async def get_family_items(self, user_id: str, limit: int = 50) -> list:
        """Retrieves family items (events, birthdays, school)"""
        try:
            docs = (
                self._get_user_ref(user_id)
                .collection("family_items")
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            
            items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data['id'] = doc.id
                items.append(item_data)
            return items
        except Exception as e:
            print(f"[ERROR] get_family_items failed: {e}")
            return []

    async def get_media_items(self, user_id: str, media_type: str = None, status: str = "to_watch", limit: int = 50) -> list:
        """Retrieves media items (watchlist - movies, shows, books)"""
        try:
            query = self._get_user_ref(user_id).collection("media_items")
            
            if status:
                query = query.where("status", "==", status)
            if media_type:
                query = query.where("media_type", "==", media_type)
            
            docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data['id'] = doc.id
                items.append(item_data)
            return items
        except Exception as e:
            print(f"[ERROR] get_media_items failed: {e}")
            return []

    async def get_learning_items(self, user_id: str, item_type: str = None, limit: int = 50) -> list:
        """Retrieves learning items (courses, assignments, topics)"""
        try:
            query = self._get_user_ref(user_id).collection("learning_items")
            
            if item_type:
                query = query.where("item_type", "==", item_type)
            
            docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data['id'] = doc.id
                items.append(item_data)
            return items
        except Exception as e:
            print(f"[ERROR] get_learning_items failed: {e}")
            return []

    async def get_document_items(self, user_id: str, doc_type: str = None, limit: int = 50) -> list:
        """Retrieves document items (IDs, forms, legal docs)"""
        try:
            query = self._get_user_ref(user_id).collection("document_items")
            
            if doc_type:
                query = query.where("doc_type", "==", doc_type)
            
            docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data['id'] = doc.id
                items.append(item_data)
            return items
        except Exception as e:
            print(f"[ERROR] get_document_items failed: {e}")
            return []

    # ============================================
    # GENERIC DOMAIN ACCESS
    # ============================================

    async def get_items_by_domain(self, user_id: str, domain: str, limit: int = 50) -> list:
        """Generic method to retrieve items from any domain collection"""
        try:
            collection_name = self._get_collection_for_domain(domain)
            
            docs = (
                self._get_user_ref(user_id)
                .collection(collection_name)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            
            items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data['id'] = doc.id
                items.append(item_data)
            
            print(f"[FIRESTORE] Retrieved {len(items)} items from {collection_name}")
            return items
        except Exception as e:
            print(f"[ERROR] get_items_by_domain failed: {e}")
            return []

    async def save_to_domain_collection(self, user_id: str, domain: str, data: dict) -> str:
        """Generic method to save to any domain collection"""
        try:
            collection_name = self._get_collection_for_domain(domain)
            
            # Ensure domain is set in data
            data['domain'] = domain
            
            doc_ref = self._get_user_ref(user_id).collection(collection_name).document()
            doc_ref.set(data)
            
            print(f"[FIRESTORE] Saved to {collection_name}: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"[ERROR] save_to_domain_collection failed: {e}")
            return None

    async def save_user_file(self, user_id: str, file_meta: dict) -> str:
        """Save uploaded file metadata for a user"""
        try:
            if 'uploaded_at' not in file_meta:
                file_meta['uploaded_at'] = datetime.utcnow().isoformat()

            file_meta = self._serialize_datetimes(file_meta)

            doc_ref = self._get_user_ref(user_id).collection('files').document()
            doc_ref.set(file_meta)

            print(f"[FIRESTORE] Saved user file metadata: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"[ERROR] save_user_file failed: {e}")
            return None

    async def save_file_metadata(self, user_id: str, file_id: str, meta: dict) -> str:
        """Save document metadata"""
        try:
            meta = self._serialize_datetimes(meta)
            doc_ref = self._get_user_ref(user_id).collection('files').document(file_id)
            doc_ref.set(meta)
            print(f"[FIRESTORE] Saved file metadata: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"[ERROR] save_file_metadata failed: {e}")
            return None

    # ============================================
    # DASHBOARD METHODS
    # ============================================

    async def get_domain_counts(self, user_id: str) -> dict:
        """Returns count of items per domain for dashboard"""
        counts = {}
        
        for domain, collection in DOMAIN_COLLECTIONS.items():
            try:
                docs = self._get_user_ref(user_id).collection(collection).limit(100).stream()
                counts[domain] = sum(1 for _ in docs)
            except:
                counts[domain] = 0
        
        return counts

    async def get_recent_across_domains(self, user_id: str, limit: int = 10) -> list:
        """Returns most recent items across all domains"""
        all_items = []
        
        for domain, collection in DOMAIN_COLLECTIONS.items():
            try:
                docs = (
                    self._get_user_ref(user_id)
                    .collection(collection)
                    .order_by("created_at", direction=firestore.Query.DESCENDING)
                    .limit(3)
                    .stream()
                )
                
                for doc in docs:
                    item_data = doc.to_dict()
                    item_data['id'] = doc.id
                    item_data['_collection'] = collection
                    all_items.append(item_data)
            except:
                continue
        
        # Sort by created_at and return top N
        all_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return all_items[:limit]

    # ============================================
    # V2 ENHANCED METHODS - Fetch Subcollections
    # ============================================

    async def get_research_results(self, user_id: str, doc_id: str) -> dict:
        """
        Fetch research results from research_results subcollection
        
        Args:
            user_id: User ID
            doc_id: Document ID from research.firestore_doc_id
            
        Returns:
            Research results dict with sources, summary, etc.
        """
        try:
            doc_ref = (
                self._get_user_ref(user_id)
                .collection("research_results")
                .document(doc_id)
            )
            
            doc = doc_ref.get()
            
            if not doc.exists:
                print(f"[FIRESTORE] Research results {doc_id} not found")
                return None
            
            data = doc.to_dict()
            print(f"[FIRESTORE] Retrieved research results: {doc_id}")
            return data
            
        except Exception as e:
            print(f"[ERROR] get_research_results failed: {e}")
            return None

    async def get_resource_findings(self, user_id: str, doc_id: str) -> dict:
        """
        Fetch learning resources from resource_findings subcollection
        
        Args:
            user_id: User ID
            doc_id: Document ID from resources.firestore_doc_id
            
        Returns:
            Resource findings dict with resources array, ai_reasoning, etc.
        """
        try:
            doc_ref = (
                self._get_user_ref(user_id)
                .collection("resource_findings")
                .document(doc_id)
            )
            
            doc = doc_ref.get()
            
            if not doc.exists:
                print(f"[FIRESTORE] Resource findings {doc_id} not found")
                return None
            
            data = doc.to_dict()
            print(f"[FIRESTORE] Retrieved resource findings: {doc_id}")
            return data
            
        except Exception as e:
            print(f"[ERROR] get_resource_findings failed: {e}")
            return None

    async def get_enhanced_capture_data(self, user_id: str, capture_id: str) -> dict:
        """
        V2 ENHANCED: Fetches comprehensive capture with ALL subcollections
        
        This method:
        1. Fetches main comprehensive_captures document
        2. Fetches research_results if firestore_doc_id exists
        3. Fetches resource_findings if firestore_doc_id exists
        4. Merges all data into rich response
        
        Args:
            user_id: User ID
            capture_id: Capture ID
            
        Returns:
            Complete capture data with all subcollections merged
        """
        try:
            # 1. Get main comprehensive capture
            main_capture = await self.get_comprehensive_capture(user_id, capture_id)
            
            if not main_capture:
                print(f"[FIRESTORE V2] Capture {capture_id} not found")
                return None
            
            print(f"[FIRESTORE V2] Building enhanced capture for {capture_id}")
            
            # 2. Fetch research results if available
            if main_capture.get('research', {}).get('firestore_doc_id'):
                research_doc_id = main_capture['research']['firestore_doc_id']
                print(f"[FIRESTORE V2] Fetching research results: {research_doc_id}")
                
                research_data = await self.get_research_results(user_id, research_doc_id)
                
                if research_data:
                    # Merge research data into main capture
                    main_capture['research']['sources'] = research_data.get('sources', [])
                    main_capture['research']['summary'] = research_data.get('summary', '')
                    main_capture['research']['sources_count'] = research_data.get('sources_count', 0)
                    print(f"[FIRESTORE V2] Merged {len(research_data.get('sources', []))} research sources")
            
            # 3. Fetch resource findings if available
            if main_capture.get('resources', {}).get('firestore_doc_id'):
                resource_doc_id = main_capture['resources']['firestore_doc_id']
                print(f"[FIRESTORE V2] Fetching resource findings: {resource_doc_id}")
                
                resource_data = await self.get_resource_findings(user_id, resource_doc_id)
                
                if resource_data:
                    # Merge resource data into main capture
                    main_capture['resources']['resources'] = resource_data.get('resources', [])
                    main_capture['resources']['ai_reasoning'] = resource_data.get('ai_reasoning', '')
                    main_capture['resources']['learning_path'] = resource_data.get('learning_path', '')
                    print(f"[FIRESTORE V2] Merged {len(resource_data.get('resources', []))} learning resources")
            
            print(f"[FIRESTORE V2] Enhanced capture ready with all subcollections")
            return main_capture
            
        except Exception as e:
            print(f"[ERROR] get_enhanced_capture_data failed: {e}")
            import traceback
            traceback.print_exc()
            return None