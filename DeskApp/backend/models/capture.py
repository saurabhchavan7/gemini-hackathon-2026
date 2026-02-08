"""
LifeOS - Comprehensive Capture Model
Stores complete end-to-end processing details for full transparency
ALL MODELS NOW USE capture_id (not id)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


# ============================================
# INPUT METADATA
# ============================================

class CaptureContext(BaseModel):
    """Environment context where capture happened"""
    app_name: str = Field(default="Unknown", description="Active application name")
    window_title: str = Field(default="Unknown", description="Window title")
    url: Optional[str] = Field(None, description="Browser URL if applicable")
    platform: str = Field(default="windows", description="OS platform")
    screen_resolution: Optional[str] = Field(None, description="Screen resolution")
    timezone: str = Field(default="UTC", description="User's timezone")


class RawInput(BaseModel):
    """All raw input data from the capture"""
    screenshot_path: Optional[str] = Field(None, description="Path to screenshot file")
    audio_path: Optional[str] = Field(None, description="Path to audio file")
    text_note: Optional[str] = Field(None, description="Text note user typed")
    context: CaptureContext = Field(default_factory=CaptureContext)
    screenshot_size_bytes: Optional[int] = Field(None)
    audio_duration_seconds: Optional[float] = Field(None)


# ============================================
# AGENT 1: PERCEPTION OUTPUT
# ============================================

class PerceptionResult(BaseModel):
    """Output from Agent 1 (Perception)"""
    ocr_text: str = Field(default="", description="Text extracted from screenshot via OCR")
    audio_transcript: str = Field(default="", description="Transcribed audio content")
    visual_description: str = Field(default="", description="AI description of what's in the screenshot")
    combined_content: str = Field(default="", description="OCR + Transcript + Text Note combined")
    ocr_confidence: Optional[float] = Field(None, description="OCR confidence score 0-1")
    transcript_confidence: Optional[float] = Field(None, description="Transcription confidence 0-1")
    processing_time_ms: int = Field(default=0)
    cached: bool = Field(default=False, description="Whether result was from cache")
    cache_key: Optional[str] = Field(None)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)


# ============================================
# AGENT 2: CLASSIFICATION OUTPUT
# ============================================

class ExtractedAction(BaseModel):
    """Single action extracted by Agent 2"""
    intent: str = Field(..., description="Action intent: act, schedule, pay, buy, etc.")
    summary: str = Field(..., description="What needs to be done")
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[str] = Field(None)
    event_time: Optional[str] = Field(None)
    event_end_time: Optional[str] = Field(None)
    attendee_emails: List[str] = Field(default_factory=list)
    attendee_names: List[str] = Field(default_factory=list)
    send_invite: bool = Field(default=False)
    amount: Optional[float] = Field(None, description="Money amount if mentioned")
    location: Optional[str] = Field(None)
    notes: str = Field(default="")
    tags: List[str] = Field(default_factory=list)
    source_phrase: str = Field(default="", description="Phrase that triggered this action")


class ClassificationResult(BaseModel):
    """Output from Agent 2 (Classification) - ALL FIELDS OPTIONAL until populated"""
    domain: str = Field(default="", description="Life domain (Layer 1)")
    domain_confidence: float = Field(default=0.0)
    context_type: str = Field(default="", description="Content type (Layer 2)")
    primary_intent: str = Field(default="", description="Primary intent (Layer 3)")
    overall_summary: str = Field(default="")
    actions: List[ExtractedAction] = Field(default_factory=list)
    total_actions: int = Field(default=0)
    classification_reasoning: str = Field(default="", description="Why AI classified this way")
    processing_time_ms: int = Field(default=0)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)


# ============================================
# AGENT 3: EXECUTION OUTPUT
# ============================================

class ExecutedAction(BaseModel):
    """Result of a single executed action by Agent 3"""
    action_index: int = Field(..., description="Which action from classification")
    intent: str = Field(...)
    summary: str = Field(...)
    tool_used: str = Field(..., description="Tool function called")
    tool_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters passed to tool")
    status: str = Field(..., description="success, error, skipped")
    result_data: Dict[str, Any] = Field(default_factory=dict, description="Tool return data")
    error_message: Optional[str] = Field(None)
    created_task_id: Optional[str] = Field(None)
    created_event_id: Optional[str] = Field(None)
    created_note_id: Optional[str] = Field(None)
    created_item_id: Optional[str] = Field(None)
    google_task_id: Optional[str] = Field(None)
    google_calendar_id: Optional[str] = Field(None)
    google_calendar_link: Optional[str] = Field(None)
    invites_sent_to: List[str] = Field(default_factory=list)
    processing_time_ms: int = Field(default=0)


class ExecutionResult(BaseModel):
    """Output from Agent 3 (Orchestrator)"""
    has_data: bool = Field(default=False, description="Flag: execution_results/{capture_id} exists")
    total_actions: int = Field(default=0)
    successful: int = Field(default=0)
    failed: int = Field(default=0)
    skipped: int = Field(default=0)
    actions_executed: List[ExecutedAction] = Field(default_factory=list)
    processing_time_ms: int = Field(default=0)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)


# ============================================
# AGENT 4: RESEARCH OUTPUT
# ============================================

class ResearchResult(BaseModel):
    """Output from Agent 4 (Research)"""
    has_data: bool = Field(default=False, description="Flag: research_results/{capture_id} exists")
    triggered: bool = Field(default=False)
    trigger_reason: Optional[str] = Field(None, description="Why research was triggered")
    query: str = Field(default="")
    research_type: str = Field(default="", description="technical, learning, comparison, domain_specific")
    results_text: str = Field(default="", description="Research findings")
    results_summary: str = Field(default="", description="Brief summary")
    sources_count: int = Field(default=0)
    sources: List[Dict[str, str]] = Field(default_factory=list, description="List of {title, url}")
    processing_time_ms: int = Field(default=0)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)


# ============================================
# AGENT 7: PROACTIVE OUTPUT
# ============================================

class ProactiveResult(BaseModel):
    """Output from Agent 7 (Proactive)"""
    triggered: bool = Field(default=False)
    trigger_reason: Optional[str] = Field(None)
    domain_analyzed: str = Field(default="")
    intents_analyzed: List[str] = Field(default_factory=list)
    tips: List[str] = Field(default_factory=list, description="Proactive suggestions")
    tips_text: str = Field(default="", description="Full tips as text")
    processing_time_ms: int = Field(default=0)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)


# ============================================
# AGENT 8: RESOURCES OUTPUT
# ============================================

class FoundResource(BaseModel):
    """A single resource found by Agent 8"""
    title: str = Field(...)
    url: str = Field(...)
    description: str = Field(default="")
    resource_type: str = Field(default="", description="article, video, tutorial, documentation")
    source: str = Field(default="", description="YouTube, Medium, Official Docs, etc.")
    relevance_score: float = Field(default=0.0)
    thumbnail_url: Optional[str] = Field(None)


class ResourcesResult(BaseModel):
    """Output from Agent 8 (Resource Finder)"""
    has_data: bool = Field(default=False, description="Flag: task_resources/{capture_id} exists")
    triggered: bool = Field(default=False)
    trigger_reason: Optional[str] = Field(None)
    needs_resources: bool = Field(default=False)
    ai_reasoning: str = Field(default="", description="Why AI decided resources were needed")
    resources: List[FoundResource] = Field(default_factory=list)
    resources_count: int = Field(default=0)
    learning_path: str = Field(default="", description="Suggested learning path")
    summary: str = Field(default="")
    processing_time_ms: int = Field(default=0)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)


# ============================================
# PROCESSING TIMELINE
# ============================================

class ProcessingTimeline(BaseModel):
    """Complete timeline of processing stages"""
    capture_received: Optional[datetime] = Field(None)
    perception_started: Optional[datetime] = Field(None)
    perception_completed: Optional[datetime] = Field(None)
    classification_started: Optional[datetime] = Field(None)
    classification_completed: Optional[datetime] = Field(None)
    firestore_save_started: Optional[datetime] = Field(None)
    firestore_save_completed: Optional[datetime] = Field(None)
    execution_started: Optional[datetime] = Field(None)
    execution_completed: Optional[datetime] = Field(None)
    research_started: Optional[datetime] = Field(None)
    research_completed: Optional[datetime] = Field(None)
    proactive_started: Optional[datetime] = Field(None)
    proactive_completed: Optional[datetime] = Field(None)
    resources_started: Optional[datetime] = Field(None)
    resources_completed: Optional[datetime] = Field(None)
    all_agents_completed: Optional[datetime] = Field(None)
    total_processing_time_ms: int = Field(default=0)
    
    def calculate_total_time(self):
        """Calculate total processing time"""
        if self.capture_received and self.all_agents_completed:
            delta = self.all_agents_completed - self.capture_received
            self.total_processing_time_ms = int(delta.total_seconds() * 1000)


# ============================================
# MAIN CAPTURE RECORD (COMPREHENSIVE)
# ============================================

class CaptureRecord(BaseModel):
    """
    Comprehensive Capture Record
    Stores EVERYTHING about a capture for full transparency
    UNIFIED: Uses capture_id everywhere (not id)
    """
    
    # ========== IDENTIFIERS ==========
    capture_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="UNIFIED ID")
    user_id: str = Field(..., description="Owner of this capture")
    capture_type: str = Field(..., description="screenshot, audio, text_note, multi-modal")
    
    # ========== RAW INPUT ==========
    input: RawInput = Field(default_factory=RawInput)
    
    # ========== AGENT OUTPUTS (All start empty, populated as agents complete) ==========
    perception: PerceptionResult = Field(default_factory=PerceptionResult)
    classification: ClassificationResult = Field(default_factory=ClassificationResult)
    execution: ExecutionResult = Field(default_factory=ExecutionResult)
    research: ResearchResult = Field(default_factory=ResearchResult)
    proactive: ProactiveResult = Field(default_factory=ProactiveResult)
    resources: ResourcesResult = Field(default_factory=ResourcesResult)
    
    # ========== TIMELINE ==========
    timeline: ProcessingTimeline = Field(default_factory=ProcessingTimeline)
    
    # ========== STATUS ==========
    status: str = Field(default="processing", description="processing, completed, partial_failure, failed")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Any errors that occurred")
    
    # ========== TIMESTAMPS ==========
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # ========== REFERENCES ==========
    memory_id: Optional[str] = Field(None, description="Reference to Memory document")
    
    # Backward compatibility alias
    @property
    def id(self) -> str:
        """Backward compatibility: return capture_id when accessing .id"""
        return self.capture_id
    
    def add_error(self, agent: str, error: str, details: Dict = None):
        """Add an error to the record"""
        self.errors.append({
            "agent": agent,
            "error": error,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def mark_completed(self):
        """Mark capture as completed and calculate total time"""
        self.status = "completed"
        self.timeline.all_agents_completed = datetime.utcnow()
        self.timeline.calculate_total_time()
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error: str):
        """Mark capture as failed"""
        self.status = "failed"
        self.add_error("system", error)
        self.updated_at = datetime.utcnow()


# ============================================
# BACKWARD COMPATIBILITY
# ============================================

class CaptureMetadata(BaseModel):
    """DEPRECATED: Use CaptureContext instead"""
    app_name: str = Field(default="Unknown")
    window_title: str = Field(default="Unknown")
    url: Optional[str] = Field(None)
    platform: str = Field(default="windows")
    screen_resolution: Optional[str] = Field(None)
    timezone: str = Field(default="UTC")


class Capture(BaseModel):
    """DEPRECATED: Use CaptureRecord instead"""
    capture_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="UNIFIED ID")
    user_id: str = Field(...)
    capture_type: str = Field(...)
    screenshot_path: Optional[str] = Field(None)
    audio_path: Optional[str] = Field(None)
    raw_text_note: Optional[str] = Field(None)
    context: CaptureMetadata = Field(default_factory=CaptureMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="processing")
    
    # Backward compatibility alias
    @property
    def id(self) -> str:
        """Backward compatibility: return capture_id when accessing .id"""
        return self.capture_id