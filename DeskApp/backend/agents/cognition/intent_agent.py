"""
LifeOS - Intent Agent  
Role: Classification and extraction
"""
from typing import List
from pydantic import BaseModel, Field
from agents.base import AgentBase
from core.config import settings

class IntentResult(BaseModel):
    """The structured decision made by the Intent Agent"""
    category: str = Field(..., description="Bucket: 'Work', 'Personal', 'Finance', 'Inspiration', 'Learning'")
    intent: str = Field(
        ..., 
        description="Goal: 'Task', 'Reference', 'Learning', 'Purchase', 'Event', 'Research'"
    )
    priority: int = Field(default=1, ge=1, le=5, description="1 (Low) to 5 (Critical)")
    one_line_summary: str = Field(..., description="Catchy summary of the content")
    tags: List[str] = Field(default_factory=list)
    actionable_items: List[str] = Field(
        default_factory=list, 
        description="Clean, discrete action items - one sentence each, max 100 chars per item"
    )

class IntentAgent(AgentBase):
    def __init__(self):
        system_instruction = (
            "You are an intelligent text analyzer. Your role is to understand what the user wants to accomplish.\n\n"
            
            "INTENT CLASSIFICATION:\n\n"
            
            "Event: Anything with specific date/time for meeting, call, or appointment\n"
            "- Triggers: time mentions (2pm, tomorrow, Friday), meeting words (meet, call, discussion)\n"
            "- Examples: 'Team sync Monday 3pm', 'Dentist appointment tomorrow'\n\n"
            
            "Task: Action items to be done, without specific meeting times\n"
            "- Triggers: action verbs (finish, complete, review, update, prepare)\n"
            "- Examples: 'Finish report by Friday', 'Review pull requests'\n\n"
            
            "Purchase: Products or services to buy\n"
            "- Examples: 'Buy groceries', 'Sony headphones $299'\n\n"
            
            "Reference: Information to save for later\n"
            "- Examples: 'Python documentation', 'Interesting AI article'\n\n"
            
            "Learning: Educational content\n"
            "- Examples: 'Machine learning course', 'JavaScript tutorial'\n\n"
            
            "Research: Technical problems, errors, bugs\n"
            "- Triggers: error messages, 'not working', 'bug'\n"
            "- Examples: 'TypeError in Python', 'CSS not rendering'\n\n"
            
            "ACTIONABLE ITEMS EXTRACTION:\n\n"
            
            "Extract discrete, actionable tasks. Follow these principles:\n"
            "- Clear action items with verbs: 'Finish X', 'Review Y'\n"
            "- Ignore: Meeting times (those are Events), UI artifacts, meta-text, file paths\n"
            "- Format: Start with action verb, under 100 chars, capitalize first word\n"
            "- Remove filler: 'need to', 'have to', 'should', bullet points, dashes\n\n"
            
            "Examples:\n"
            "Input: 'need to finish report - call John tomorrow at 2pm'\n"
            "Actionable items: ['Finish report']\n"
            "Note: 'call John' becomes Event, not task\n\n"
            
            "Quality over quantity. Better 2 clean tasks than 10 messy ones."
        )
        super().__init__(model_id=settings.COGNITION_MODEL, system_instruction=system_instruction)

    async def process(self, text_content: str) -> IntentResult:
        """Processes text to determine user intent with smart extraction"""
        
        prompt = (
            f"Analyze this text and categorize it:\n\n"
            f"TEXT:\n{text_content}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Determine primary intent (Event, Task, Purchase, etc.)\n"
            f"2. Extract ONLY clean, actionable tasks (follow the rules)\n"
            f"3. Ignore meta-text, file paths, and UI elements\n"
            f"4. If mentions meeting time, classify as Event (not Task)\n"
            f"5. Each actionable_item: <100 chars, starts with action verb\n"
        )
        
        return await self._call_gemini(
            prompt=prompt,
            response_model=IntentResult
        )