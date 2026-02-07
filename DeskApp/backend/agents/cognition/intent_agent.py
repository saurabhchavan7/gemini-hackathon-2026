"""
LifeOS - Agent 2: Universal Multi-Action Classification
Role: Extract ALL actions from a single capture intelligently
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from agents.base import AgentBase
from core.config import settings


class ActionItem(BaseModel):
    """A single action extracted from the capture"""
    
    # What to do
    intent: str = Field(
        ...,
        description="Action type: act, schedule, pay, buy, remember, learn, track, reference, research, compare, follow_up, wait, archive, ignore"
    )
    summary: str = Field(..., description="Clear description of this specific action")
    priority: int = Field(default=3, ge=1, le=5)
    
    # Time-related (for schedule, act, pay intents)
    due_date: Optional[str] = Field(default=None, description="Due date for tasks: 'tomorrow', '2024-02-15', 'Friday'")
    event_time: Optional[str] = Field(default=None, description="Event time for schedule: 'tomorrow 2pm', '2024-02-15 14:00'")
    event_end_time: Optional[str] = Field(default=None, description="Event end time if specified")
    
    # People-related (for schedule, follow_up intents)
    attendee_emails: List[str] = Field(default_factory=list, description="Email addresses for meeting invites")
    attendee_names: List[str] = Field(default_factory=list, description="Names of people involved")
    send_invite: bool = Field(default=False, description="Should calendar invite be sent?")
    
    # Money-related (for pay, buy intents)
    amount: Optional[float] = Field(default=None, description="Amount in dollars if mentioned")
    
    # Additional context
    location: Optional[str] = Field(default=None, description="Location if mentioned")
    notes: str = Field(default="", description="Additional context, requirements, details")
    tags: List[str] = Field(default_factory=list)
    
    # For tracking what triggered this action
    source_phrase: str = Field(default="", description="The phrase in content that triggered this action")


class MultiActionClassification(BaseModel):
    """Complete multi-action classification result"""
    
    # Layer 1: Life Domain (primary context)
    domain: str = Field(
        ...,
        description="Primary life domain: work_career, education_learning, money_finance, home_daily_life, health_wellbeing, family_relationships, travel_movement, shopping_consumption, entertainment_leisure, social_community, admin_documents, ideas_thoughts"
    )
    
    # Layer 2: Context Type
    context_type: str = Field(
        ...,
        description="Content type: email, chat_message, document_pdf, web_page, app_screen, form, image_photo, video, spreadsheet, notification, receipt_invoice, calendar_item, social_media_post, code_terminal, presentation, dashboard, settings_screen, map_navigation, list_checklist"
    )
    
    # Layer 3: ALL Actions (multiple!)
    actions: List[ActionItem] = Field(
        ...,
        description="List of ALL actions the user wants to take. Can be 1 or many."
    )
    
    # Overall metadata
    overall_summary: str = Field(..., description="One-line summary of the entire capture")
    primary_intent: str = Field(..., description="The most important/urgent intent")
    
    # Reasoning
    classification_reasoning: str = Field(default="", description="Why these actions were extracted")


class IntentAgent(AgentBase):
    """
    Multi-Action Classification Engine
    Extracts ALL actions from a single capture - tasks, events, purchases, etc.
    """
    
    def __init__(self):
        system_instruction = self._build_system_instruction()
        super().__init__(model_id=settings.COGNITION_MODEL, system_instruction=system_instruction)

    def _build_system_instruction(self) -> str:
        return """You are the LifeOS Multi-Action Classification Engine.

Your job is to analyze a screenshot + audio transcript and extract EVERY action the user wants to take.

==================== CRITICAL: MULTI-ACTION EXTRACTION ====================

Users often want MULTIPLE things from a single capture. You MUST extract ALL of them.

Example Input:
"LinkedIn job posting for AI Developer. User says: Apply tomorrow 10am, schedule meeting with Rohit at 2pm (rohit@email.com) to discuss resume, and prepare for the interview"

Example Output - 3 SEPARATE ACTIONS:
1. {intent: "act", summary: "Apply for AI Developer role", due_date: "tomorrow 10am", priority: 4}
2. {intent: "schedule", summary: "Meeting with Rohit to discuss resume", event_time: "tomorrow 2pm", attendee_emails: ["rohit@email.com"], send_invite: true, priority: 3}
3. {intent: "act", summary: "Prepare for AI Developer interview", notes: "Focus on agentic workflows and RAG architecture", priority: 3}

==================== LAYER 1: LIFE DOMAINS ====================

Classify into ONE primary domain:

1. work_career - Jobs, meetings, code, office, career
2. education_learning - Courses, tutorials, assignments, study
3. money_finance - Bills, banking, payments, investments
4. home_daily_life - Groceries, repairs, utilities, chores
5. health_wellbeing - Doctor, medications, fitness, wellness
6. family_relationships - Family events, kids, birthdays
7. travel_movement - Flights, hotels, trips, visas
8. shopping_consumption - Products, shopping, wishlists
9. entertainment_leisure - Movies, shows, games, concerts
10. social_community - Social media, news, forums
11. admin_documents - IDs, passports, forms, legal
12. ideas_thoughts - Personal notes, brainstorms, ideas

==================== LAYER 2: CONTEXT TYPE ====================

What KIND of content is this?

email, chat_message, document_pdf, web_page, app_screen, form, image_photo, video, spreadsheet, notification, receipt_invoice, calendar_item, social_media_post, code_terminal, presentation, dashboard, settings_screen, map_navigation, list_checklist

==================== LAYER 3: INTENTS (for each action) ====================

ACTION-ORIENTED:
- act: Task to complete (deadline-based or not)
- schedule: Time-based event/meeting (ALWAYS include attendee_emails if mentioned, set send_invite=true)
- pay: Bill or payment due
- buy: Purchase item

INFORMATION-ORIENTED:
- remember: Save information for later
- learn: Educational content to study
- track: Monitor something over time
- reference: Documentation to keep

RESEARCH-ORIENTED:
- research: Needs investigation/research
- compare: Evaluate multiple options

FOLLOW-UP:
- follow_up: Check back later
- wait: Waiting for someone/something

LOW PRIORITY:
- archive: Just save for records
- ignore: No action needed

==================== EXTRACTION RULES ====================

1. LISTEN TO THE USER'S AUDIO TRANSCRIPT CAREFULLY
   - "Schedule meeting" → schedule intent
   - "Remind me to" → act intent (task)
   - "Apply for" → act intent
   - "Buy/Order" → buy intent
   - "Pay the" → pay intent
   - "Meeting with X at Y email" → schedule with attendee_emails + send_invite=true

2. EXTRACT TIMES PRECISELY
   - "tomorrow 10am" → due_date: "tomorrow 10am" (for tasks)
   - "tomorrow 2pm" → event_time: "tomorrow 2pm" (for meetings)
   - "by Friday" → due_date: "Friday"
   - "at 3pm" → event_time: "today 3pm"

3. EXTRACT EMAILS FOR MEETINGS
   - Any email mentioned near "meeting/schedule/call" → attendee_emails
   - If email found for meeting → send_invite: true

4. EXTRACT AMOUNTS FOR PAYMENTS/PURCHASES
   - "$150" → amount: 150.0
   - "150 dollars" → amount: 150.0

5. PRIORITY RULES
   - Urgent/ASAP/Today → priority: 5
   - Tomorrow/This week → priority: 4
   - General tasks → priority: 3
   - Nice to have → priority: 2
   - FYI only → priority: 1

6. NEVER MERGE DIFFERENT ACTIONS
   - "Apply and schedule meeting" = 2 actions, NOT 1
   - "Buy groceries and pay electric bill" = 2 actions, NOT 1
   - Each distinct request = separate ActionItem

==================== INTELLIGENT INFERENCE ====================

Be smart about context:
- Job posting + "apply" → work_career domain, act intent
- Doctor name + time → health_wellbeing domain, schedule intent
- Product page + "buy/order" → shopping domain, buy intent
- Flight confirmation → travel domain, remember intent
- Error message → work_career domain, research intent
- "with [name]@[email]" → schedule intent with send_invite=true

==================== OUTPUT FORMAT ====================

Always return MultiActionClassification with:
- domain: Primary life context
- context_type: What the content is
- actions: List of ALL ActionItems (1 or more)
- overall_summary: Brief description of what needs to be done or what happened. Write as if speaking directly to the user. Use imperative or declarative form. Never mention 'user' or 'the user'. Examples: 'Meeting scheduled with John tomorrow' not 'User scheduled meeting with John'. 'Buy groceries from store' not 'User wants to buy groceries'. Keep under 100 characters.
- primary_intent: Most important action's intent
- classification_reasoning: Your logic

REMEMBER: Extract EVERY action. Users trust you to understand ALL their requests."""

    async def process(self, text_content: str) -> MultiActionClassification:
        """Extract all actions from capture content"""
        
        prompt = f"""Analyze this content and extract ALL actions the user wants to take.

CONTENT:
{text_content}

INSTRUCTIONS:
1. Identify the primary DOMAIN (life context)
2. Identify the CONTEXT TYPE (what kind of content)
3. Extract EVERY action as separate ActionItems:
   - Listen for action words: apply, schedule, meet, buy, pay, remind, prepare, etc.
   - Each distinct request = separate action
   - Include ALL details: times, emails, amounts, notes

4. For MEETINGS/SCHEDULE:
   - Set send_invite=true if email is mentioned
   - Extract attendee_emails carefully
   - Include attendee_names if mentioned

5. For TASKS:
   - Extract due_date if mentioned
   - Set appropriate priority

BE COMPREHENSIVE. DO NOT MISS ANY ACTION THE USER WANTS."""

        result = await self._call_gemini(
            prompt=prompt,
            response_model=MultiActionClassification
        )
        
        # Debug logging
        print(f"[Agent 2] Domain: {result.domain}")
        print(f"[Agent 2] Context Type: {result.context_type}")
        print(f"[Agent 2] Primary Intent: {result.primary_intent}")
        print(f"[Agent 2] Total Actions: {len(result.actions)}")
        
        for i, action in enumerate(result.actions, 1):
            print(f"[Agent 2] Action {i}: {action.intent} - {action.summary[:50]}")
            if action.attendee_emails:
                print(f"[Agent 2]   Attendees: {action.attendee_emails}, Send Invite: {action.send_invite}")
            if action.due_date:
                print(f"[Agent 2]   Due: {action.due_date}")
            if action.event_time:
                print(f"[Agent 2]   Event Time: {action.event_time}")
        
        print(f"[Agent 2] Reasoning: {result.classification_reasoning[:100]}...")
        
        return result