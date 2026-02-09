"""
LifeOS - Agent 3: Universal Orchestrator (Multi-Action Processing)
Role: Process ALL actions from a capture intelligently
NOW PASSES capture_id to ALL tools
"""
from datetime import datetime, timedelta
import re
import pytz
from typing import List, Dict, Any
from agents.base import AgentBase
from core.config import settings
from .tools import (
    # Existing tools
    create_calendar_event, 
    add_to_shopping_list, 
    create_task, 
    create_note,
    # New tools
    add_to_bills,
    create_health_item,
    create_travel_item,
    add_to_watchlist,
    create_family_event,
    create_tracker,
    create_comparison,
    create_reminder,
    create_waiting_item,
    archive_item,
    save_document,
    create_learning_item,
    # Tool registry
    get_tool_for_intent,
    TOOL_REGISTRY,
    DOMAIN_TOOL_OVERRIDES
)


class PlanningAgent(AgentBase):
    """
    Multi-Action Orchestrator
    Processes ALL actions from Agent 2's multi-action classification
    """
    
    def __init__(self):
        system_instruction = (
            "You are the LifeOS Universal Orchestrator.\n"
            "You process multiple actions from a single capture.\n"
            "Execute each action with the appropriate tool.\n"
        )
        super().__init__(
            model_id=settings.ORCHESTRATOR_MODEL,
            system_instruction=system_instruction,
            tools=[create_calendar_event, add_to_shopping_list, create_task, create_note]
        )

    async def process(self, intent_data: dict):
        """
        Multi-Action Processing
        
        NEW Input Format (from Multi-Action Agent 2):
        {
            "domain": str,
            "context_type": str,
            "actions": [ActionItem, ActionItem, ...],  # MULTIPLE ACTIONS!
            "overall_summary": str,
            "primary_intent": str,
            "user_id": str,
            "capture_id": str,
            "user_timezone": str,
            "full_context": str
        }
        
        Also supports OLD format for backward compatibility.
        """
        
        user_id = intent_data.get('user_id')
        domain = intent_data.get('domain', 'ideas_thoughts')
        context_type = intent_data.get('context_type', 'app_screen')
        user_timezone = intent_data.get('user_timezone', 'UTC')
        full_context = intent_data.get('full_context', '')
        
        # Check if this is NEW multi-action format or OLD single-intent format
        actions = intent_data.get('actions', [])
        
        if actions:
            # NEW FORMAT: Multiple actions
            print(f"[Agent 3] Processing {len(actions)} actions (domain: {domain})")
            return await self._process_multiple_actions(
                actions=actions,
                domain=domain,
                user_id=user_id,
                capture_id=intent_data.get('capture_id'),
                user_timezone=user_timezone,
                full_context=full_context
            )
        else:
            # OLD FORMAT: Single intent (backward compatibility)
            print(f"[Agent 3] Legacy mode: single intent")
            return await self._process_single_intent(intent_data)

    async def _process_multiple_actions(
        self,
        actions: list,
        domain: str,
        user_id: str,
        capture_id: str,
        user_timezone: str,
        full_context: str
    ) -> dict:
        """Process multiple actions from a single capture"""
        
        results = []
        
        for i, action in enumerate(actions, 1):
            # Handle both dict and object formats
            if isinstance(action, dict):
                intent = action.get('intent', 'remember')
                summary = action.get('summary', '')
                priority = action.get('priority', 3)
                due_date = action.get('due_date')
                event_time = action.get('event_time')
                event_end_time = action.get('event_end_time')
                attendee_emails = action.get('attendee_emails', [])
                attendee_names = action.get('attendee_names', [])
                send_invite = action.get('send_invite', False)
                amount = action.get('amount')
                location = action.get('location')
                notes = action.get('notes', '')
                tags = action.get('tags', [])
            else:
                # Pydantic model
                intent = action.intent
                summary = action.summary
                priority = action.priority
                due_date = action.due_date
                event_time = action.event_time
                event_end_time = action.event_end_time
                attendee_emails = action.attendee_emails or []
                attendee_names = action.attendee_names or []
                send_invite = action.send_invite
                amount = action.amount
                location = action.location
                notes = action.notes or ''
                tags = action.tags or []
            
            print(f"[Agent 3] Action {i}/{len(actions)}: {intent} - {summary[:50]}")
            
            try:
                result = await self._execute_action(
                    intent=intent,
                    summary=summary,
                    domain=domain,
                    user_id=user_id,
                    capture_id=capture_id,
                    user_timezone=user_timezone,
                    priority=priority,
                    due_date=due_date,
                    event_time=event_time,
                    event_end_time=event_end_time,
                    attendee_emails=attendee_emails,
                    attendee_names=attendee_names,
                    send_invite=send_invite,
                    amount=amount,
                    location=location,
                    notes=notes,
                    tags=tags,
                    full_context=full_context
                )
                results.append({"action": summary, "intent": intent, "result": result})
                print(f"[Agent 3] Action {i} completed: {result.get('status', 'unknown')}")
                
            except Exception as e:
                print(f"[ERROR] Action {i} failed: {e}")
                results.append({"action": summary, "intent": intent, "result": {"status": "error", "message": str(e)}})
        
        # Summary (OUTSIDE the for loop!)
        success_count = sum(1 for r in results if r.get('result', {}).get('status') == 'success')
        print(f"[Agent 3] Completed: {success_count}/{len(actions)} actions successful")
        
        # Save execution results using capture_id
        if capture_id and user_id:
            await self._save_execution_results(user_id, capture_id, results)
        
        return {
            "status": "success" if success_count > 0 else "error",
            "total_actions": len(actions),
            "successful": success_count,
            "results": results
        }
    
    async def _save_execution_results(
        self,
        user_id: str,
        capture_id: str,
        results: list
    ) -> bool:
        """Save execution results to separate collection using capture_id"""
        try:
            from services.firestore_service import FirestoreService
            
            db = FirestoreService()
            
            # Build execution summary
            execution_doc = {
                "capture_id": capture_id,
                "actions": [],
                "created_at": datetime.utcnow().isoformat()
            }
            
            for r in results:
                result_data = r.get('result', {})
                
                action_entry = {
                    "intent": r.get('intent'),
                    "summary": r.get('action'),
                    "status": result_data.get('status', 'unknown'),
                    "google_task_id": result_data.get('google_task_id'),
                    "google_event_id": result_data.get('google_event_id'),
                    "google_calendar_link": result_data.get('google_link'),
                    "firestore_doc_id": result_data.get('firestore_doc_id'),
                    "error_message": result_data.get('message') if result_data.get('status') == 'error' else None
                }
                
                execution_doc["actions"].append(action_entry)
            
            # Save to execution_results/{capture_id}
            doc_ref = db._get_user_ref(user_id).collection("execution_results").document(capture_id)
            doc_ref.set(execution_doc)
            
            print(f"[Agent 3] Saved execution to: execution_results/{capture_id}")
            
            # Update main capture with simple flag
            success_count = sum(1 for r in results if r.get('result', {}).get('status') == 'success')
            
            field_updates = {
                "execution.has_data": True,
                "execution.total_actions": len(results),
                "execution.successful": success_count,
                "execution.failed": len(results) - success_count,
                "execution.completed_at": datetime.utcnow().isoformat(),
                "timeline.execution_completed": datetime.utcnow().isoformat()
            }
            
            await db.update_capture_fields(user_id, capture_id, field_updates)
            print(f"[Agent 3] ✓ Execution linked to capture {capture_id}")
            
            return True
            
        except Exception as e:
            print(f"[Agent 3] WARNING: Failed to save execution: {e}")
            return False

    async def _process_single_intent(self, intent_data: dict) -> dict:
        """Backward compatibility: Process old single-intent format"""
        
        # Convert old format to new action format
        action = {
            "intent": intent_data.get('intent', 'remember'),
            "summary": intent_data.get('summary', ''),
            "priority": intent_data.get('priority', 3),
            "due_date": None,
            "event_time": None,
            "attendee_emails": intent_data.get('attendee_emails', []),
            "notes": intent_data.get('task_context', ''),
            "tags": intent_data.get('tags', [])
        }
        
        # If there are actionable_items, create multiple actions
        actionable_items = intent_data.get('actionable_items', [])
        if actionable_items:
            actions = []
            for item in actionable_items[:5]:
                actions.append({
                    **action,
                    "summary": item
                })
        else:
            actions = [action]
        
        return await self._process_multiple_actions(
            actions=actions,
            domain=intent_data.get('domain', 'ideas_thoughts'),
            user_id=intent_data.get('user_id'),
            capture_id=intent_data.get('capture_id'),
            user_timezone=intent_data.get('user_timezone', 'UTC'),
            full_context=intent_data.get('full_context', '')
        )

    async def _execute_action(
        self,
        intent: str,
        summary: str,
        domain: str,
        user_id: str,
        capture_id: str,
        user_timezone: str,
        priority: int,
        due_date: str,
        event_time: str,
        event_end_time: str,
        attendee_emails: list,
        attendee_names: list,
        send_invite: bool,
        amount: float,
        location: str,
        notes: str,
        tags: list,
        full_context: str
    ) -> dict:
        """Execute a single action with the appropriate tool"""
        
        # ==========================================
        # SCHEDULE INTENT (Calendar Events)
        # ==========================================
        if intent == "schedule":
            print(f"[Agent 3] SCHEDULE: Creating calendar event")
            
            # Parse event time
            parsed_time = self._parse_datetime(event_time, user_timezone)
            parsed_end = self._parse_datetime(event_end_time, user_timezone) if event_end_time else None
            
            if not parsed_end and parsed_time:
                # Default 1 hour duration
                parsed_end = (datetime.fromisoformat(parsed_time.replace('Z', '+00:00')) + timedelta(hours=1)).isoformat()
            
            # Domain-specific calendar creation
            if domain == "health_wellbeing":
                return await create_health_item(
                    user_id=user_id,
                    title=summary,
                    item_type="appointment",
                    date_time=parsed_time,
                    notes=notes,
                    add_to_calendar=True,
                    capture_id=capture_id
                )
            elif domain == "family_relationships":
                return await create_family_event(
                    user_id=user_id,
                    title=summary,
                    event_type="event",
                    date_time=parsed_time,
                    person=attendee_names[0] if attendee_names else None,
                    notes=notes,
                    add_to_calendar=True,
                    capture_id=capture_id
                )
            else:
                # Standard calendar event
                return await create_calendar_event(
                    user_id=user_id,
                    event_title=summary,
                    start_time=parsed_time,
                    end_time=parsed_end,
                    description=notes,
                    location=location,
                    user_timezone=user_timezone,
                    attendees=attendee_emails if attendee_emails else None,
                    send_invites=send_invite and bool(attendee_emails),
                    domain=domain,
                    capture_id=capture_id
                )
        
        # ==========================================
        # ACT INTENT (Tasks)
        # ==========================================
        elif intent == "act":
            print(f"[Agent 3] ACT: Creating task")
            
            parsed_due = self._parse_date(due_date) if due_date else None
            
            if domain == "education_learning":
                return await create_learning_item(
                    user_id=user_id,
                    title=summary,
                    item_type="assignment",
                    notes=notes,
                    due_date=parsed_due,
                    capture_id=capture_id
                )
            else:
                return await create_task(
                    user_id=user_id,
                    task_title=summary,
                    notes=notes if notes else f"Priority: {priority}",
                    due_date=parsed_due,
                    domain=domain,
                    priority=priority,
                    capture_id=capture_id
                )
        
        # ==========================================
        # PAY INTENT (Bills)
        # ==========================================
        elif intent == "pay":
            print(f"[Agent 3] PAY: Adding to bills")
            
            return add_to_bills(
                user_id=user_id,
                bill_name=summary,
                amount=amount or 0.0,
                due_date=self._parse_date(due_date),
                category=self._categorize_bill(summary + " " + notes),
                capture_id=capture_id
            )
        
        # ==========================================
        # BUY INTENT (Shopping)
        # ==========================================
        elif intent == "buy":
            print(f"[Agent 3] BUY: Adding to shopping/watchlist")
            
            if domain == "entertainment_leisure":
                return add_to_watchlist(
                    user_id=user_id,
                    title=summary,
                    media_type=self._detect_media_type(summary + " " + notes),
                    notes=notes,
                    capture_id=capture_id
                )
            else:
                return add_to_shopping_list(
                    user_id=user_id,
                    item_name=summary,
                    price=amount or 0.0,
                    domain=domain,
                    capture_id=capture_id
                )
        
        # ==========================================
        # REMEMBER INTENT (Save)
        # ==========================================
        elif intent == "remember":
            print(f"[Agent 3] REMEMBER: Saving to domain storage")
            
            if domain == "health_wellbeing":
                return await create_health_item(
                    user_id=user_id,
                    title=summary,
                    item_type="record",
                    notes=notes,
                    add_to_calendar=False,
                    capture_id=capture_id
                )
            elif domain == "travel_movement":
                return create_travel_item(
                    user_id=user_id,
                    title=summary,
                    item_type="info",
                    notes=notes,
                    capture_id=capture_id
                )
            elif domain == "entertainment_leisure":
                return add_to_watchlist(
                    user_id=user_id,
                    title=summary,
                    media_type=self._detect_media_type(summary + " " + notes),
                    notes=notes,
                    capture_id=capture_id
                )
            elif domain == "admin_documents":
                return await save_document(
                    user_id=user_id,
                    title=summary,
                    content=notes or full_context[:1000],
                    notes="",
                    capture_id=capture_id
                )
            else:
                return create_note(
                    user_id=user_id,
                    title=summary,
                    content=notes or full_context[:1000],
                    domain=domain,
                    tags=tags,
                    capture_id=capture_id
                )
        
        # ==========================================
        # LEARN INTENT (Educational)
        # ==========================================
        elif intent == "learn":
            print(f"[Agent 3] LEARN: Creating learning item")
            
            return await create_learning_item(
                user_id=user_id,
                title=summary,
                item_type="topic",
                content=full_context[:1000],
                notes=notes,
                capture_id=capture_id
            )
        
        # ==========================================
        # TRACK INTENT (Monitoring)
        # ==========================================
        elif intent == "track":
            print(f"[Agent 3] TRACK: Creating tracker")
            
            return create_tracker(
                user_id=user_id,
                title=summary,
                tracker_type=self._detect_tracker_type(summary + " " + notes),
                domain=domain,
                capture_id=capture_id
            )
        
        # ==========================================
        # REFERENCE INTENT (Documentation)
        # ==========================================
        elif intent == "reference":
            print(f"[Agent 3] REFERENCE: Saving as reference note")
            
            return create_note(
                user_id=user_id,
                title=f"Ref: {summary}",
                content=notes or full_context[:2000],
                domain=domain,
                tags=tags + ["reference"],
                capture_id=capture_id
            )
        
        # ==========================================
        # RESEARCH INTENT (Delegated)
        # ==========================================
        elif intent == "research":
            print(f"[Agent 3] RESEARCH: Delegating to Research Agent")
            # Research Agent handles this via event bus
            return {"status": "delegated", "to": "research_agent"}
        
        # ==========================================
        # COMPARE INTENT (Evaluation)
        # ==========================================
        elif intent == "compare":
            print(f"[Agent 3] COMPARE: Creating comparison")
            
            return create_comparison(
                user_id=user_id,
                title=summary,
                notes=notes or full_context[:1000],
                domain=domain,
                capture_id=capture_id
            )
        
        # ==========================================
        # FOLLOW_UP INTENT (Reminder)
        # ==========================================
        elif intent == "follow_up":
            print(f"[Agent 3] FOLLOW_UP: Creating reminder")
            
            return await create_reminder(
                user_id=user_id,
                title=summary,
                remind_date=self._parse_date(due_date),
                notes=notes,
                domain=domain,
                capture_id=capture_id
            )
        
        # ==========================================
        # WAIT INTENT (Pending)
        # ==========================================
        elif intent == "wait":
            print(f"[Agent 3] WAIT: Creating waiting item")
            
            return await create_waiting_item(
                user_id=user_id,
                title=summary,
                waiting_for=attendee_names[0] if attendee_names else None,
                notes=notes,
                domain=domain,
                capture_id=capture_id
            )
        
        # ==========================================
        # ARCHIVE INTENT (Records)
        # ==========================================
        elif intent == "archive":
            print(f"[Agent 3] ARCHIVE: Archiving item")
            
            if domain == "admin_documents":
                return await save_document(
                    user_id=user_id,
                    title=summary,
                    content=notes or full_context[:1000],
                    notes="Archived",
                    capture_id=capture_id
                )
            else:
                return archive_item(
                    user_id=user_id,
                    title=summary,
                    content=notes or full_context[:1000],
                    domain=domain,
                    capture_id=capture_id
                )
        
        # ==========================================
        # IGNORE INTENT (Skip)
        # ==========================================
        elif intent == "ignore":
            print(f"[Agent 3] IGNORE: Skipping")
            return {"status": "skipped", "reason": "ignore intent"}
        
        # ==========================================
        # FALLBACK
        # ==========================================
        else:
            print(f"[Agent 3] UNKNOWN intent '{intent}': Saving as note")
            return create_note(
                user_id=user_id,
                title=summary,
                content=notes or full_context[:1000],
                domain=domain,
                tags=tags,
                capture_id=capture_id
            )

    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _parse_datetime(self, time_str: str, timezone: str = "UTC") -> str:
        """Parse datetime string to ISO format"""
        if not time_str:
            return None
        
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            
            time_lower = time_str.lower()
            
            # Handle relative dates
            if 'tomorrow' in time_lower:
                date = now + timedelta(days=1)
            elif 'today' in time_lower:
                date = now
            elif 'next week' in time_lower:
                date = now + timedelta(weeks=1)
            elif 'monday' in time_lower:
                days_ahead = 0 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                date = now + timedelta(days=days_ahead)
            elif 'tuesday' in time_lower:
                days_ahead = 1 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                date = now + timedelta(days=days_ahead)
            elif 'wednesday' in time_lower:
                days_ahead = 2 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                date = now + timedelta(days=days_ahead)
            elif 'thursday' in time_lower:
                days_ahead = 3 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                date = now + timedelta(days=days_ahead)
            elif 'friday' in time_lower:
                days_ahead = 4 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                date = now + timedelta(days=days_ahead)
            elif 'saturday' in time_lower:
                days_ahead = 5 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                date = now + timedelta(days=days_ahead)
            elif 'sunday' in time_lower:
                days_ahead = 6 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                date = now + timedelta(days=days_ahead)
            else:
                date = now
            
            # Extract time
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?', time_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                meridiem = time_match.group(3)
                
                if meridiem and meridiem.lower() == 'pm' and hour != 12:
                    hour += 12
                elif meridiem and meridiem.lower() == 'am' and hour == 12:
                    hour = 0
                
                date = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                # Default to 9 AM if no time specified
                date = date.replace(hour=9, minute=0, second=0, microsecond=0)
            
            return date.strftime("%Y-%m-%dT%H:%M:%S")
            
        except Exception as e:
            print(f"[Agent 3] DateTime parse error: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None
        
        try:
            now = datetime.utcnow()
            date_lower = date_str.lower()
            
            if 'today' in date_lower:
                return now.strftime("%Y-%m-%d")
            elif 'tomorrow' in date_lower:
                return (now + timedelta(days=1)).strftime("%Y-%m-%d")
            elif 'next week' in date_lower:
                return (now + timedelta(weeks=1)).strftime("%Y-%m-%d")
            elif 'friday' in date_lower:
                days_ahead = 4 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            
            # Try to parse specific date
            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-]?(\d{2,4})?', date_str)
            if date_match:
                month = int(date_match.group(1))
                day = int(date_match.group(2))
                year = int(date_match.group(3)) if date_match.group(3) else now.year
                if year < 100:
                    year += 2000
                return f"{year}-{month:02d}-{day:02d}"
            
            return None
            
        except Exception as e:
            print(f"[Agent 3] Date parse error: {e}")
            return None
    
    def _categorize_bill(self, text: str) -> str:
        """Categorize a bill based on content"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ['electric', 'gas', 'water', 'utility', 'power']):
            return "utilities"
        elif any(w in text_lower for w in ['internet', 'phone', 'mobile', 'wifi', 'broadband']):
            return "telecom"
        elif any(w in text_lower for w in ['rent', 'mortgage', 'lease', 'housing']):
            return "housing"
        elif any(w in text_lower for w in ['insurance', 'premium']):
            return "insurance"
        elif any(w in text_lower for w in ['subscription', 'netflix', 'spotify', 'membership']):
            return "subscription"
        elif any(w in text_lower for w in ['credit card', 'loan', 'emi', 'debt']):
            return "debt"
        elif any(w in text_lower for w in ['tax', 'irs', 'income tax']):
            return "tax"
        else:
            return "other"
    
    def _detect_media_type(self, text: str) -> str:
        """Detect type of media from content"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ['movie', 'film', 'cinema', 'theatre']):
            return "movie"
        elif any(w in text_lower for w in ['show', 'series', 'episode', 'season', 'tv']):
            return "tv_show"
        elif any(w in text_lower for w in ['book', 'read', 'author', 'novel', 'kindle']):
            return "book"
        elif any(w in text_lower for w in ['podcast', 'listen']):
            return "podcast"
        elif any(w in text_lower for w in ['album', 'song', 'music', 'artist', 'spotify']):
            return "music"
        elif any(w in text_lower for w in ['game', 'play', 'gaming', 'steam', 'xbox', 'playstation']):
            return "game"
        elif any(w in text_lower for w in ['concert', 'ticket', 'event', 'show']):
            return "event"
        else:
            return "other"
    
    def _detect_tracker_type(self, text: str) -> str:
        """Detect type of tracking from content"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ['weight', 'calories', 'exercise', 'workout', 'steps']):
            return "fitness"
        elif any(w in text_lower for w in ['spend', 'budget', 'expense', 'money', 'savings']):
            return "financial"
        elif any(w in text_lower for w in ['habit', 'daily', 'streak', 'routine']):
            return "habit"
        elif any(w in text_lower for w in ['progress', 'goal', 'milestone', 'target']):
            return "progress"
        elif any(w in text_lower for w in ['order', 'shipping', 'delivery', 'package', 'tracking']):
            return "delivery"
        elif any(w in text_lower for w in ['medication', 'medicine', 'pill', 'dose']):
            return "medication"
        elif any(w in text_lower for w in ['symptom', 'pain', 'health']):
            return "health"
        else:
            return "general"