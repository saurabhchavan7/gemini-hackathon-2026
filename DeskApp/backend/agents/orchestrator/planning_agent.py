from agents.base import AgentBase
from .tools import create_calendar_event, add_to_shopping_list, create_task, create_note

class PlanningAgent(AgentBase):
    def __init__(self):
        system_instruction = (
            "You are the LifeOS Orchestrator. Analyze the user's intent and take appropriate actions.\n\n"
            
            "TOOL SELECTION RULES:\n\n"
            
            "1. Intent='Event' OR specific time mentioned -> create_calendar_event()\n"
            "   Only create the EVENT, do NOT create tasks\n"
            "   Extract: event title, date/time, location, description\n\n"
            
            "2. Intent='Task' -> create_task()\n"
            "   Create tasks ONLY, no calendar events\n\n"
            
            "3. Intent='Purchase' -> add_to_shopping_list()\n\n"
            
            "4. Intent='Reference' OR 'Learning' -> create_note()\n\n"
        )
        super().__init__(
            model_id="gemini-2.5-flash", 
            system_instruction=system_instruction,
            tools=[create_calendar_event, add_to_shopping_list, create_task, create_note]
        )

    async def execute_tool_call(self, tool_call, user_id: str):
        """Maps Gemini's request to local Python functions"""
        name = tool_call.name
        args = dict(tool_call.args)
        args['user_id'] = user_id
        
        available_tools = {
            "add_to_shopping_list": add_to_shopping_list,
            "create_calendar_event": create_calendar_event,
            "create_task": create_task,
            "create_note": create_note
        }
        
        if name in available_tools:
            print(f"[TOOL] Executing {name} with args: {args}")
            return available_tools[name](**args)
        return {"error": "Tool not found"}

    async def process(self, intent_data: dict):
        """Process intent with proper separation of concerns"""
        
        print(f"[Agent 3] Orchestrator processing: {intent_data.get('intent')}")
        
        user_id = intent_data.get('user_id')
        intent = intent_data.get('intent')
        summary = intent_data.get('summary', '')
        full_context = intent_data.get('full_context', summary)
        actionable_items = intent_data.get('actionable_items', [])
        user_timezone = intent_data.get('user_timezone', 'UTC')
        
        print(f"[Agent 3] User timezone: {user_timezone}")
        
        # Detect meeting vs tasks
        has_meeting = any(word in full_context.lower() for word in ['meet', 'meeting', 'call', 'discussion'])
        has_time = any(word in full_context.lower() for word in ['tomorrow', 'today', 'pm', 'am', 'at ', 'o\'clock'])
        has_tasks = len(actionable_items) > 0
        
        print(f"[Agent 3] Detection: meeting={has_meeting}, time={has_time}, tasks={has_tasks} ({len(actionable_items)} items)")
        
        # SCENARIO 1: Meeting with time mentioned
        if has_meeting and has_time:
            print("[Agent 3] Meeting detected - creating calendar event")
            
            from datetime import datetime, timedelta
            import pytz
            
            try:
                user_tz = pytz.timezone(user_timezone)
                current_date = datetime.now(user_tz)
                tomorrow_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
            except:
                current_date = datetime.utcnow()
                tomorrow_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
                user_timezone = "UTC"
            
            meeting_prompt = (
                f"USER TIMEZONE: {user_timezone}\n"
                f"CURRENT DATE: {current_date.strftime('%Y-%m-%d')}\n"
                f"TOMORROW: {tomorrow_date}\n\n"
                f"Extract ONLY the meeting details:\n{full_context}\n\n"
                f"Create calendar event with proper time in {user_timezone} timezone.\n"
                f"DO NOT create any tasks - only the calendar event!"
            )
            
            response = await self._call_gemini(prompt=meeting_prompt)
            
            # Execute only calendar event creation
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        result = await self.execute_tool_call(part.function_call, user_id)
                        print(f"[Agent 3] Calendar created: {result.get('status')}")
            
            # NOW create tasks separately (after calendar)
            if has_tasks and actionable_items:
                print(f"[Agent 3] Creating {len(actionable_items)} tasks from action items")
                for item in actionable_items[:5]:
                    if 'meet' not in item.lower():  # Skip meeting-related items
                        result = create_task(user_id=user_id, task_title=item, notes=None)
                        print(f"[Agent 3] Task created: {item}")
            
            return {"status": "success"}
        
        # SCENARIO 2: Purchase
        elif intent == "Purchase":
            print("[Agent 3] Direct routing: Purchase -> Shopping List")
            
            item_name = summary.split('for')[0].strip() if 'for' in summary else summary
            
            import re
            price = 0.0
            if '$' in full_context:
                price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', full_context)
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))
            
            result = add_to_shopping_list(user_id=user_id, item_name=item_name, price=price)
            return result
        
        # SCENARIO 3: Tasks only (no meeting)
        elif intent == "Task" and actionable_items:
            print(f"[Agent 3] Direct routing: Creating {len(actionable_items)} tasks")
            
            for item in actionable_items[:5]:
                result = create_task(user_id=user_id, task_title=item, notes=None)
                print(f"[Agent 3] Task created: {item}")
            
            return {"status": "success", "tasks_created": len(actionable_items)}
        
        # SCENARIO 4: Reference/Learning
        elif intent in ["Reference", "Learning"]:
            print("[Agent 3] Direct routing: Reference -> Notes")
            result = create_note(user_id=user_id, title=summary, content=full_context)
            return result
        
        # SCENARIO 5: Complex Event parsing needed
        elif intent == "Event":
            print("[Agent 3] Complex Event - using Gemini for parsing")
            prompt = f"Create calendar event from: {full_context}"
            response = await self._call_gemini(prompt=prompt)
            
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        result = await self.execute_tool_call(part.function_call, user_id)
                        return result
        
        return {"status": "skipped"}