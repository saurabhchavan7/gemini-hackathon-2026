from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class CaptureMetadata(BaseModel):
 """Deep context about the environment where the capture happened."""
 app_name: str = Field(..., description="The name of the active application (e.g., 'Chrome', 'Slack')")
 window_title: str = Field(..., description="The specific title of the window (e.g., 'Project Roadmap.pdf')")
 url: Optional[str] = Field(None, description="The browser URL if the capture happened in a web browser")
 platform: str = Field("windows", description="The OS platform (windows, darwin, linux)")
 screen_resolution: Optional[str] = Field(None, description="The resolution of the screen captured (e.g., '1920x1080')")
 timezone: str = Field("UTC", description="User's timezone (e.g., 'America/New_York', 'Asia/Kolkata')") # ← ADD THIS LINE

class Capture(BaseModel):
 """The Immutable Raw Record. This is the entry point of all data into LifeOS."""
 id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for this capture")
 user_id: str = Field(..., description="The Google User ID who owns this data")
 capture_type: str = Field(..., description="The format: 'screenshot', 'audio', 'text_note', or 'multi-modal'")
 
 # Storage Paths
 screenshot_path: Optional[str] = Field(None, description="Local or Cloud Storage path to the PNG image")
 audio_path: Optional[str] = Field(None, description="Local or Cloud Storage path to the audio file")
 
 # User Input
 raw_text_note: Optional[str] = Field(None, description="Any text the user typed manually during capture")
 
 # Environment Context
 context: CaptureMetadata = Field(..., description="Detailed metadata about what the user was doing")
 
 # Lifecycle
 created_at: datetime = Field(default_factory=datetime.utcnow)
 status: str = Field("processing", description="The agentic pipeline state: 'processing', 'analyzed', or 'failed'")