"""
LifeOS - Enhanced Memory Model
Stores processed knowledge with full references to capture data
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class ActionSummary(BaseModel):
    """Summary of an action for the memory record"""
    intent: str = Field(...)
    summary: str = Field(...)
    status: str = Field(default="pending", description="pending, completed, failed")
    
    # What was created
    created_type: Optional[str] = Field(None, description="task, event, note, bill, etc.")
    created_id: Optional[str] = Field(None)
    google_link: Optional[str] = Field(None)


class Memory(BaseModel):
    """
    The Processed Knowledge Record
    Links to comprehensive CaptureRecord for full details
    """
    
    # ========== IDENTIFIERS ==========
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    capture_ref: str = Field(..., description="Reference to CaptureRecord.id")
    user_id: str = Field(..., description="Owner of this memory")
    
    # ========== CONTENT ==========
    title: str = Field(..., description="Main title/headline")
    one_line_summary: str = Field(..., description="Brief description")
    full_transcript: str = Field(default="", description="Complete text from OCR + audio")
    
    # ========== 3-LAYER CLASSIFICATION ==========
    
    # Layer 1: Life Domain
    domain: str = Field(
        ...,
        description="Life domain: work_career, education_learning, money_finance, etc."
    )
    domain_confidence: float = Field(default=0.9)
    
    # Layer 2: Context Type
    context_type: str = Field(
        ...,
        description="Content type: email, web_page, chat_message, etc."
    )
    
    # Layer 3: Intent
    intent: str = Field(
        ...,
        description="Primary intent: act, schedule, pay, buy, remember, etc."
    )
    
    # ========== ACTIONS SUMMARY ==========
    total_actions: int = Field(default=0)
    actions: List[ActionSummary] = Field(default_factory=list, description="Summary of all actions taken")
    
    # ========== EXTRACTED DATA ==========
    actionable_items: List[str] = Field(default_factory=list, description="List of action summaries")
    task_context: str = Field(default="", description="Additional context for tasks")
    attendee_emails: List[str] = Field(default_factory=list)
    extracted_amounts: List[float] = Field(default_factory=list, description="Money amounts found")
    extracted_dates: List[str] = Field(default_factory=list, description="Dates found")
    
    # ========== AI REASONING ==========
    classification_reasoning: str = Field(default="", description="Why AI classified this way")
    
    # ========== METADATA ==========
    priority: int = Field(default=3, ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    
    # ========== CREATED RESOURCES ==========
    created_tasks: List[Dict[str, str]] = Field(default_factory=list, description="Tasks created from this capture")
    created_events: List[Dict[str, str]] = Field(default_factory=list, description="Calendar events created")
    created_notes: List[Dict[str, str]] = Field(default_factory=list, description="Notes created")
    created_items: List[Dict[str, str]] = Field(default_factory=list, description="Other items created")
    
    # ========== RESEARCH & RESOURCES ==========
    has_research: bool = Field(default=False)
    research_summary: str = Field(default="")
    has_resources: bool = Field(default=False)
    resources_count: int = Field(default=0)
    proactive_tips: List[str] = Field(default_factory=list)
    
    # ========== PROCESSING INFO ==========
    processing_time_ms: int = Field(default=0, description="Total processing time")
    agents_run: List[str] = Field(default_factory=list, description="Which agents processed this")
    
    # ========== TIMESTAMPS ==========
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # ========== STATUS ==========
    status: str = Field(default="active", description="active, archived, deleted")
    
    # ========== DEPRECATED (Backward Compatibility) ==========
    category: Optional[str] = Field(None, description="DEPRECATED: Use domain instead")
    
    def add_created_task(self, task_id: str, title: str, google_id: str = None):
        """Add a created task reference"""
        self.created_tasks.append({
            "id": task_id,
            "title": title,
            "google_id": google_id,
            "created_at": datetime.utcnow().isoformat()
        })
    
    def add_created_event(self, event_id: str, title: str, google_link: str = None):
        """Add a created event reference"""
        self.created_events.append({
            "id": event_id,
            "title": title,
            "google_link": google_link,
            "created_at": datetime.utcnow().isoformat()
        })
    
    def add_created_note(self, note_id: str, title: str):
        """Add a created note reference"""
        self.created_notes.append({
            "id": note_id,
            "title": title,
            "created_at": datetime.utcnow().isoformat()
        })