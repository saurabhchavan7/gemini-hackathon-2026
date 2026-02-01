from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class Action(BaseModel):
 """The Executable Task. This powers your 'Proactive' features and external integrations."""
 id: str = Field(..., description="Unique Action ID")
 memory_ref: str = Field(..., description="The Memory that triggered this action")
 user_id: str = Field(..., description="Owner ID")
 
 # Action Details
 action_type: str = Field(..., description="e.g., 'calendar_event', 'email_draft', 'reminder', 'search_query'")
 description: str = Field(..., description="What needs to be done (e.g., 'Draft email to John about the budget')")
 
 # Execution Metadata
 status: str = Field("pending", description="'pending', 'in_progress', 'completed', 'dismissed'")
 priority: str = Field("normal", description="'low', 'normal', 'high', 'urgent'")
 deadline: Optional[datetime] = Field(None, description="AI-extracted due date")
 
 # Integration Payload
 payload: Dict[str, Any] = Field(
 default_factory=dict, 
 description="JSON data needed for the tool (e.g., recipient email, event start time)"
 )
 
 completed_at: Optional[datetime] = Field(None)