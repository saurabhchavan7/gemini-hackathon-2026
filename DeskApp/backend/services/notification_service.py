from datetime import datetime, timedelta
from typing import List, Dict
from services.firestore_service import FirestoreService
from core.config import settings
import google.generativeai as genai

class NotificationService:
    
    def __init__(self):
        self.db = FirestoreService()
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("[NOTIFICATION_SERVICE] Initialized")
    
    def get_proactive_notifications(self, user_id: str) -> List[Dict]:
        """
        Analyze user's captures and generate proactive notifications
        """
        
        print(f"[NOTIFICATION] Analyzing captures for user: {user_id}")
        
        notifications = []
        
        try:
            # Get all active memories
            memories_ref = self.db._get_user_ref(user_id).collection(settings.COLLECTION_MEMORIES)
            docs = memories_ref.where('status', '==', 'active').stream()
            
            memories = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                memories.append(data)
            
            print(f"[NOTIFICATION] Found {len(memories)} active memories")
            
            # 1. Check for urgent deadlines
            deadlines = self._check_deadlines(memories)
            notifications.extend(deadlines)
            
            # 2. Check for unreviewed high priority items
            unreviewed = self._check_unreviewed_high_priority(memories)
            notifications.extend(unreviewed)
            
            # 3. Check for opportunities (deals, events)
            opportunities = self._check_opportunities(memories)
            notifications.extend(opportunities)
            
            # 4. AI-powered insight (once per hour max)
            insights = self._generate_ai_insights(memories)
            notifications.extend(insights)
            
            print(f"[NOTIFICATION] Generated {len(notifications)} notifications")
            
            return sorted(notifications, key=lambda x: x['priority'], reverse=True)[:5]
            
        except Exception as e:
            print(f"[NOTIFICATION] Error: {e}")
            return []
    
    def _check_deadlines(self, memories: List[Dict]) -> List[Dict]:
        """Find items with deadlines in next 24 hours"""
        notifications = []
        now = datetime.utcnow()
        
        for memory in memories:
            actions = memory.get('actions', [])
            
            for action in actions:
                due_date = action.get('due_date')
                if not due_date:
                    continue
                
                try:
                    due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    hours_until = (due - now).total_seconds() / 3600
                    
                    if 0 < hours_until < 24:
                        notifications.append({
                            'id': f"deadline_{memory['id']}",
                            'type': 'deadline',
                            'priority': 10 if hours_until < 3 else 8,
                            'title': '⏰ Deadline Approaching!',
                            'message': f"{action.get('summary', 'Task')} is due in {int(hours_until)} hours",
                            'capture_id': memory['id'],
                            'created_at': datetime.utcnow().isoformat()
                        })
                except:
                    pass
        
        return notifications
    
    def _check_unreviewed_high_priority(self, memories: List[Dict]) -> List[Dict]:
        """Find high priority items not yet reviewed"""
        notifications = []
        
        unreviewed = [m for m in memories if m.get('status') == 'active']
        
        # Focus on work/education domains
        important_domains = ['work_career', 'education_learning', 'money_finance']
        high_priority = [m for m in unreviewed if m.get('domain') in important_domains]
        
        if len(high_priority) >= 3:
            notifications.append({
                'id': 'unreviewed_batch',
                'type': 'reminder',
                'priority': 6,
                'title': '📋 Items Need Your Attention',
                'message': f"You have {len(high_priority)} important unreviewed items",
                'capture_id': high_priority[0]['id'],
                'created_at': datetime.utcnow().isoformat()
            })
        
        return notifications
    
    def _check_opportunities(self, memories: List[Dict]) -> List[Dict]:
        """Find time-sensitive opportunities"""
        notifications = []
        
        for memory in memories:
            actions = memory.get('actions', [])
            
            for action in actions:
                # Check for shopping deals with keywords
                summary = action.get('summary', '').lower()
                if action.get('intent') == 'buy' and any(word in summary for word in ['sale', 'deal', 'off', '%']):
                    notifications.append({
                        'id': f"deal_{memory['id']}",
                        'type': 'opportunity',
                        'priority': 5,
                        'title': '🛍️ Deal Reminder',
                        'message': action.get('summary', 'Shopping deal available'),
                        'capture_id': memory['id'],
                        'created_at': datetime.utcnow().isoformat()
                    })
                
                # Check for upcoming events (within 2 hours)
                event_time = action.get('event_time')
                if event_time and action.get('intent') == 'schedule':
                    try:
                        event = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                        hours_until = (event - datetime.utcnow()).total_seconds() / 3600
                        
                        if 0.5 < hours_until < 2:
                            notifications.append({
                                'id': f"event_{memory['id']}",
                                'type': 'reminder',
                                'priority': 9,
                                'title': '📅 Event Starting Soon',
                                'message': f"{action.get('summary', 'Event')} starts in {int(hours_until * 60)} minutes",
                                'capture_id': memory['id'],
                                'created_at': datetime.utcnow().isoformat()
                            })
                    except:
                        pass
        
        return notifications
    
    def _generate_ai_insights(self, memories: List[Dict]) -> List[Dict]:
        """Use Gemini to find connections and insights"""
        notifications = []
        
        # Only run if we have enough data
        if len(memories) < 3:
            return notifications
        
        try:
            # Sample recent memories
            recent = sorted(memories, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
            
            # Build context
            context = "\n".join([
                f"- {m.get('title', 'Untitled')} (domain: {m.get('domain', 'unknown')})"
                for m in recent
            ])
            
            prompt = f"""Analyze these recent captures and find ONE actionable insight:

{context}

Respond with ONLY a JSON object:
{{
  "has_insight": true/false,
  "title": "short title (max 50 chars)",
  "message": "actionable message (max 100 chars)"
}}

Only return an insight if you find a meaningful connection or time-sensitive pattern."""
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Parse JSON
            import json
            text = text.replace('```json', '').replace('```', '').strip()
            result = json.loads(text)
            
            if result.get('has_insight'):
                notifications.append({
                    'id': 'ai_insight',
                    'type': 'insight',
                    'priority': 4,
                    'title': result['title'],
                    'message': result['message'],
                    'capture_id': None,
                    'created_at': datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            print(f"[NOTIFICATION] AI insight failed: {e}")
        
        return notifications