"""
LifeOS - Google Tasks Integration
Handles task creation for actionable items without specific times
"""
from datetime import datetime
from typing import Dict, Optional
from services.google_auth_service import GoogleAuthService
from services.firestore_service import FirestoreService

class GoogleTasksService:
    """Manages Google Tasks for to-do items"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.auth_service = GoogleAuthService(user_id)
        self.db = FirestoreService()
        self.tasks_service = None
        self.default_tasklist_id = None
    
    def _get_service(self):
        """Lazy load tasks service"""
        if not self.tasks_service:
            self.tasks_service = self.auth_service.get_tasks_service()
        return self.tasks_service
    
    def _get_default_tasklist(self):
        """Get the default task list ID"""
        if not self.default_tasklist_id:
            service = self._get_service()
            tasklists = service.tasklists().list().execute()
            items = tasklists.get('items', [])
            if items:
                self.default_tasklist_id = items[0]['id']
        return self.default_tasklist_id
    
    def create_task(
        self,
        title: str,
        notes: Optional[str] = None,
        due_date: Optional[str] = None,
        source_capture_id: Optional[str] = None
    ) -> Dict:
        """Creates a task in Google Tasks and saves to Firestore"""
        
        try:
            service = self._get_service()
            tasklist_id = self._get_default_tasklist()
            
            if not tasklist_id:
                return {
                    "status": "error",
                    "message": "No task list found. Create one in Google Tasks first."
                }
            
            # Build task object
            task_body = {
                'title': title,
                'status': 'needsAction'
            }
            
            if notes:
                task_body['notes'] = notes
            
            if due_date:
                try:
                    dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    task_body['due'] = dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                except:
                    pass
            
            # Create task in Google Tasks
            created_task = service.tasks().insert(
                tasklist=tasklist_id,
                body=task_body
            ).execute()
            
            google_task_id = created_task['id']
            
            print(f"[TASKS] Created task '{title}' in Google Tasks")
            
            # Save to Firestore
            task_data = {
                "title": title,
                "notes": notes,
                "due_date": due_date,
                "google_task_id": google_task_id,
                "google_tasklist_id": tasklist_id,
                "source_capture_id": source_capture_id,
                "created_by_agent": "agent_3_orchestrator",
                "status": "active",
                "completed": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
            doc_ref = self.db._get_user_ref(self.user_id).collection("google_tasks").document()
            doc_ref.set(task_data)
            
            print(f"[FIRESTORE] Saved task reference")
            
            return {
                "status": "success",
                "message": f"Task '{title}' created successfully",
                "google_task_id": google_task_id,
                "firestore_id": doc_ref.id
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to create task: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def list_tasks(self, max_results: int = 20) -> Dict:
        """Get tasks from Google Tasks"""
        
        try:
            service = self._get_service()
            tasklist_id = self._get_default_tasklist()
            
            if not tasklist_id:
                return {"status": "error", "message": "No task list found"}
            
            tasks_result = service.tasks().list(
                tasklist=tasklist_id,
                maxResults=max_results
            ).execute()
            
            tasks = tasks_result.get('items', [])
            
            return {
                "status": "success",
                "tasks": [
                    {
                        "id": task['id'],
                        "title": task.get('title', 'Untitled'),
                        "notes": task.get('notes', ''),
                        "due": task.get('due', None),
                        "status": task.get('status', 'needsAction'),
                        "completed": task.get('status') == 'completed'
                    }
                    for task in tasks
                ]
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to list tasks: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def complete_task(self, google_task_id: str) -> Dict:
        """Mark a task as completed"""
        
        try:
            service = self._get_service()
            tasklist_id = self._get_default_tasklist()
            
            task = service.tasks().get(
                tasklist=tasklist_id,
                task=google_task_id
            ).execute()
            
            task['status'] = 'completed'
            
            service.tasks().update(
                tasklist=tasklist_id,
                task=google_task_id,
                body=task
            ).execute()
            
            print(f"[TASKS] Marked task as completed")
            
            return {
                "status": "success",
                "message": "Task marked as completed"
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to complete task: {e}")
            return {
                "status": "error",
                "message": str(e)
            }