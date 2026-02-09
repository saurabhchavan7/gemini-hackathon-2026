# backend/services/notification_service.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from services.firestore_service import FirestoreService
from core.config import settings
import google.generativeai as genai
import re
import json

class NotificationService:
    
    def __init__(self):
        self.db = FirestoreService()
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.PRIMARY_MODEL)
        print("[NOTIFICATION_SERVICE] Initialized")
    
    def get_proactive_notifications(self, user_id: str) -> List[Dict]:
        """
        Analyze user's captures and generate proactive notifications
        Returns top 5 prioritized notifications
        """
        
        print(f"[NOTIFICATION] Analyzing captures for user: {user_id}")
        
        notifications = []
        
        try:
            # USE COMPREHENSIVE_CAPTURES COLLECTION
            memories_ref = self.db._get_user_ref(user_id).collection('comprehensive_captures')
            docs = memories_ref.limit(50).stream()
            
            memories = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                
                # Extract classification data (this has the actions!)
                classification = data.get('classification', {})
                if classification:
                    # Flatten the structure for easier access
                    data['domain'] = classification.get('domain', 'unknown')
                    data['actions'] = classification.get('actions', [])
                    data['title'] = classification.get('overall_summary', 'Untitled')
                
                memories.append(data)
            
            print(f"[NOTIFICATION] Found {len(memories)} comprehensive captures")
            
            # DEBUG: Print full structure of first capture
            if len(memories) > 0:
                first = memories[0]
                print(f"[NOTIFICATION] ===== SAMPLE CAPTURE STRUCTURE =====")
                print(f"[NOTIFICATION] ID: {first.get('id')}")
                print(f"[NOTIFICATION] Domain: {first.get('domain')}")
                print(f"[NOTIFICATION] Title: {first.get('title')[:80]}")
                print(f"[NOTIFICATION] Actions count: {len(first.get('actions', []))}")
                
                if first.get('actions'):
                    for idx, action in enumerate(first['actions'][:3]):  # First 3 actions
                        print(f"[NOTIFICATION] Action {idx}:")
                        print(f"  - intent: {action.get('intent')}")
                        print(f"  - summary: {action.get('summary')[:60]}")
                        print(f"  - due_date: {action.get('due_date')}")
                        print(f"  - event_time: {action.get('event_time')}")
                        print(f"  - priority: {action.get('priority')}")
                
                print(f"[NOTIFICATION] ===== END SAMPLE =====")
            
            if len(memories) == 0:
                return []
            
            # 1. URGENT: Check for deadlines in next 24 hours
            deadlines = self._check_deadlines(memories)
            notifications.extend(deadlines)
            print(f"[NOTIFICATION] Found {len(deadlines)} deadline notifications")
            
            # 2. URGENT: Check for events starting soon (< 2 hours)
            events = self._check_upcoming_events(memories)
            notifications.extend(events)
            print(f"[NOTIFICATION] Found {len(events)} event notifications")
            
            # 3. MEDIUM: Check for shopping deals with time sensitivity
            deals = self._check_shopping_deals(memories)
            notifications.extend(deals)
            print(f"[NOTIFICATION] Found {len(deals)} deal notifications")
            
            # 4. LOW: Batch reminder for unreviewed items (only if no urgent items)
            if len(notifications) < 2:
                batch = self._check_unreviewed_batch(memories)
                notifications.extend(batch)
                print(f"[NOTIFICATION] Added {len(batch)} batch notifications")
            
            # 5. INSIGHT: AI-powered connection finding (only if no urgent items)
            if len(notifications) < 3:
                insights = self._generate_ai_insights(memories)
                notifications.extend(insights)
                print(f"[NOTIFICATION] Generated {len(insights)} AI insights")
            
            # Sort by priority and return top 5
            sorted_notifs = sorted(notifications, key=lambda x: x['priority'], reverse=True)
            top_notifs = sorted_notifs[:5]
            
            print(f"[NOTIFICATION] Returning {len(top_notifs)} notifications")
            return top_notifs
            
        except Exception as e:
            print(f"[NOTIFICATION] Error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_human_date(self, date_str: str, user_timezone: str = "UTC") -> Optional[datetime]:
        """
        Parse human-readable dates like 'tomorrow', 'today 6:18 PM', 'next week'
        Returns datetime object or None
        """
        
        if not date_str:
            return None
        
        now = datetime.utcnow()
        date_str = date_str.lower().strip()
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except:
            pass
        
        # Handle relative dates
        if date_str == 'today':
            return now
        
        if date_str == 'tomorrow':
            return now + timedelta(days=1)
        
        if 'today' in date_str:
            # Extract time: "today 6:18 PM"
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', date_str, re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                ampm = time_match.group(3)
                
                if ampm and ampm.lower() == 'pm' and hour != 12:
                    hour += 12
                elif ampm and ampm.lower() == 'am' and hour == 12:
                    hour = 0
                
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if 'tomorrow' in date_str:
            # Extract time: "tomorrow 3 PM"
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', date_str, re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                ampm = time_match.group(3)
                
                if ampm and ampm.lower() == 'pm' and hour != 12:
                    hour += 12
                
                tomorrow = now + timedelta(days=1)
                return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return now + timedelta(days=1)
        
        if 'this evening' in date_str:
            return now.replace(hour=18, minute=0, second=0, microsecond=0)
        
        if 'tonight' in date_str:
            return now.replace(hour=20, minute=0, second=0, microsecond=0)
        
        if 'next week' in date_str:
            return now + timedelta(days=7)
        
        if 'in' in date_str:
            # "in 2 hours", "in 30 minutes"
            hours_match = re.search(r'in (\d+) hour', date_str)
            if hours_match:
                return now + timedelta(hours=int(hours_match.group(1)))
            
            mins_match = re.search(r'in (\d+) min', date_str)
            if mins_match:
                return now + timedelta(minutes=int(mins_match.group(1)))
        
        # Try parsing "2026-02-09 20:00 EST"
        try:
            # Remove timezone abbreviation
            date_str_clean = re.sub(r'\s+[A-Z]{2,4}$', '', date_str)
            return datetime.strptime(date_str_clean, '%Y-%m-%d %H:%M')
        except:
            pass
        
        print(f"[NOTIFICATION] Could not parse date: {date_str}")
        return None
    
    def _check_deadlines(self, memories: List[Dict]) -> List[Dict]:
        """Find items with deadlines in next 24 hours"""
        notifications = []
        now = datetime.utcnow()
        
        for memory in memories:
            actions = memory.get('actions', [])
            
            for action in actions:
                due_date_str = action.get('due_date')
                if not due_date_str:
                    continue
                
                try:
                    due_date = self._parse_human_date(due_date_str)
                    
                    if not due_date:
                        continue
                    
                    hours_until = (due_date - now).total_seconds() / 3600
                    
                    # Only notify if due within 24 hours
                    if 0 < hours_until < 24:
                        priority = 10 if hours_until < 3 else 9 if hours_until < 12 else 8
                        
                        notifications.append({
                            'id': f"deadline_{memory['id']}_{action.get('intent', 'task')}",
                            'type': 'deadline',
                            'priority': priority,
                            'title': 'Deadline Approaching!',
                            'message': f"{action.get('summary', 'Task')} is due in {int(hours_until)} hours",
                            'capture_id': memory['id'],
                            'created_at': datetime.utcnow().isoformat()
                        })
                        print(f"[NOTIFICATION] ✅ Created deadline: {action.get('summary')[:40]} in {int(hours_until)}h")
                
                except Exception as e:
                    print(f"[NOTIFICATION] Error parsing deadline '{due_date_str}': {e}")
        
        return notifications
    
    def _check_upcoming_events(self, memories: List[Dict]) -> List[Dict]:
        """Find calendar events starting in next 2 hours"""
        notifications = []
        now = datetime.utcnow()
        
        for memory in memories:
            actions = memory.get('actions', [])
            
            for action in actions:
                if action.get('intent') != 'schedule':
                    continue
                
                event_time_str = action.get('event_time')
                if not event_time_str:
                    continue
                
                try:
                    event_time = self._parse_human_date(event_time_str)
                    
                    if not event_time:
                        continue
                    
                    hours_until = (event_time - now).total_seconds() / 3600
                    
                    # Notify 0.5 to 2 hours before
                    if 0.5 < hours_until < 2:
                        minutes_until = int(hours_until * 60)
                        
                        notifications.append({
                            'id': f"event_{memory['id']}",
                            'type': 'event',
                            'priority': 9,
                            'title': 'Event Starting Soon',
                            'message': f"{action.get('summary', 'Event')} starts in {minutes_until} minutes",
                            'capture_id': memory['id'],
                            'created_at': datetime.utcnow().isoformat()
                        })
                        print(f"[NOTIFICATION] ✅ Created event: {action.get('summary')[:40]} in {minutes_until}m")
                
                except Exception as e:
                    print(f"[NOTIFICATION] Error parsing event '{event_time_str}': {e}")
        
        return notifications
    
    def _check_shopping_deals(self, memories: List[Dict]) -> List[Dict]:
        """Find shopping items with time-sensitive deals"""
        notifications = []
        
        for memory in memories:
            actions = memory.get('actions', [])
            
            for action in actions:
                if action.get('intent') != 'buy':
                    continue
                
                summary = action.get('summary', '').lower()
                
                # Keywords indicating time-sensitive deals
                deal_keywords = ['sale', 'deal', 'off', '%', 'discount', 'promo', 'limited']
                urgency_keywords = ['today', 'tonight', 'weekend', 'ending', 'expires']
                
                has_deal = any(keyword in summary for keyword in deal_keywords)
                has_urgency = any(keyword in summary for keyword in urgency_keywords)
                
                if has_deal:
                    priority = 7 if has_urgency else 5
                    
                    notifications.append({
                        'id': f"deal_{memory['id']}",
                        'type': 'shopping',
                        'priority': priority,
                        'title': 'Deal Alert',
                        'message': action.get('summary', 'Shopping deal available')[:80],
                        'capture_id': memory['id'],
                        'created_at': datetime.utcnow().isoformat()
                    })
        
        return notifications
    
    def _check_unreviewed_batch(self, memories: List[Dict]) -> List[Dict]:
        """Remind about multiple unreviewed important items"""
        notifications = []
        
        # Important domains
        important_domains = ['work_career', 'education_learning', 'money_finance', 'health_wellbeing']
        
        important_unreviewed = [
            m for m in memories 
            if m.get('domain') in important_domains
        ]
        
        # Only notify if 3+ important items
        if len(important_unreviewed) >= 3:
            domain_counts = {}
            for m in important_unreviewed:
                domain = m.get('domain', 'other')
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            top_domain = max(domain_counts.items(), key=lambda x: x[1])
            domain_name = {
                'work_career': 'work',
                'education_learning': 'learning',
                'money_finance': 'finance',
                'health_wellbeing': 'health'
            }.get(top_domain[0], 'important')
            
            notifications.append({
                'id': 'batch_reminder',
                'type': 'reminder',
                'priority': 4,
                'title': '📋 Review Your Captures',
                'message': f"You have {len(important_unreviewed)} {domain_name} items to review",
                'capture_id': important_unreviewed[0]['id'],
                'created_at': datetime.utcnow().isoformat()
            })
        
        return notifications
    
    def _generate_ai_insights(self, memories: List[Dict]) -> List[Dict]:
        """Use Gemini to find connections and generate insights"""
        notifications = []
        
        if len(memories) < 5:
            return notifications
        
        try:
            recent = memories[:20]
            
            context_items = []
            for m in recent:
                title = m.get('title', 'Untitled')
                domain = m.get('domain', 'unknown')
                actions = m.get('actions', [])
                intent = actions[0].get('intent', 'none') if actions else 'none'
                context_items.append(f"- {title[:60]} (domain: {domain}, intent: {intent})")
            
            context = "\n".join(context_items)
            
            prompt = f"""Analyze these captures and find ONE actionable insight:

{context}

Respond with JSON ONLY:
{{
  "has_insight": true/false,
  "title": "emoji + short title (under 40 chars)",
  "message": "actionable insight (under 80 chars)"
}}"""
            
            response = self.model.generate_content(prompt)
            text = response.text.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(text)
            
            if result.get('has_insight'):
                notifications.append({
                    'id': f"insight_{int(datetime.utcnow().timestamp())}",
                    'type': 'insight',
                    'priority': 3,
                    'title': result['title'],
                    'message': result['message'],
                    'capture_id': None,
                    'created_at': datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            print(f"[NOTIFICATION] AI insight generation failed: {e}")
        
        return notifications