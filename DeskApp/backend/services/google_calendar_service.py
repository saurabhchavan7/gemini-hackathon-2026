"""
LifeOS - Google Calendar Integration
Handles calendar event creation with smart features
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from services.google_auth_service import GoogleAuthService
from services.firestore_service import FirestoreService
import re

class GoogleCalendarService:
    """Smart calendar integration with conflict detection"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.auth_service = GoogleAuthService(user_id)
        self.db = FirestoreService()
        self.calendar_service = None
    
    def _get_service(self):
        """Lazy load calendar service"""
        if not self.calendar_service:
            import asyncio
            loop = asyncio.get_event_loop()
            self.calendar_service = loop.run_until_complete(self.auth_service.get_calendar_service())
        return self.calendar_service

    async def initialize(self):
        """Initialize Calendar service - call this before using"""
        self.calendar_service = await self.auth_service.get_calendar_service()
        print(f"[CALENDAR] Service initialized for user {self.user_id}")
    
    def _parse_datetime(self, time_str: str) -> Optional[datetime]:
        """Parse various datetime formats"""
        
        # Try ISO format first
        try:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except:
            pass
        
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except:
                continue
        
        return None
    
    def create_event(
        self,
        title: str,
        start_time: str,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        source_capture_id: Optional[str] = None,
        user_timezone: str = "UTC",
        send_invites: bool = False
    ) -> Dict:
        """Creates a calendar event in Google Calendar and saves to Firestore"""
        
        try:
            service = self._get_service()
            
            # Parse start time
            start_dt = self._parse_datetime(start_time)
            if not start_dt:
                return {
                    "status": "error",
                    "message": f"Could not parse start time: {start_time}"
                }
            
            # Parse or calculate end time
            if end_time:
                end_dt = self._parse_datetime(end_time)
            else:
                end_dt = start_dt + timedelta(hours=1)
            
            # Build event object with user's timezone
            event_body = {
                'summary': title,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': user_timezone,
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': user_timezone,
                },
            }
            
            if description:
                event_body['description'] = description
            
            if location:
                event_body['location'] = location
            
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]
            
            # Determine if we should send email invites
            send_updates = 'all' if (send_invites and attendees) else 'none'
            
            if attendees:
                print(f"[CALENDAR] Adding {len(attendees)} attendees: {attendees}")
                if send_invites:
                    print(f"[CALENDAR] Will send email invites to attendees")
            
            # Create event in Google Calendar
            created_event = service.events().insert(
                calendarId='primary',
                body=event_body,
                sendUpdates=send_updates
            ).execute()
            
            google_event_id = created_event['id']
            google_event_link = created_event.get('htmlLink', '')
            
            print(f"[CALENDAR] Created event '{title}' in Google Calendar")
            
            # Save to Firestore
            event_data = {
                "title": title,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "description": description,
                "location": location,
                "attendees": attendees or [],
                "google_calendar_id": google_event_id,
                "google_calendar_link": google_event_link,
                "source_capture_id": source_capture_id,
                "created_by_agent": "agent_3_orchestrator",
                "status": "synced",
                "created_at": datetime.utcnow().isoformat()
            }
            
            doc_ref = self.db._get_user_ref(self.user_id).collection("google_calendar_events").document()
            doc_ref.set(event_data)
            
            print(f"[FIRESTORE] Saved calendar event reference")
            
            return {
                "status": "success",
                "message": f"Event '{title}' created successfully",
                "google_event_id": google_event_id,
                "google_link": google_event_link,
                "firestore_id": doc_ref.id,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat()
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to create calendar event: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def check_conflicts(self, start_time: str, end_time: Optional[str] = None) -> Dict:
        """Check if there are conflicting events at the given time"""
        
        try:
            service = self._get_service()
            
            start_dt = self._parse_datetime(start_time)
            if not start_dt:
                return {"status": "error", "message": "Invalid start time"}
            
            if end_time:
                end_dt = self._parse_datetime(end_time)
            else:
                end_dt = start_dt + timedelta(hours=1)
            
            # Query Google Calendar
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_dt.isoformat() + 'Z',
                timeMax=end_dt.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if events:
                conflicts = [
                    {
                        "title": event.get('summary', 'Untitled'),
                        "start": event['start'].get('dateTime', event['start'].get('date')),
                        "end": event['end'].get('dateTime', event['end'].get('date'))
                    }
                    for event in events
                ]
                
                return {
                    "status": "conflict",
                    "message": f"Found {len(conflicts)} conflicting event(s)",
                    "conflicts": conflicts
                }
            else:
                return {
                    "status": "clear",
                    "message": "No conflicts found"
                }
                
        except Exception as e:
            print(f"[ERROR] Failed to check conflicts: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def list_upcoming_events(self, max_results: int = 10) -> Dict:
        """Get upcoming events from Google Calendar"""
        
        try:
            service = self._get_service()
            
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return {
                "status": "success",
                "events": [
                    {
                        "id": event['id'],
                        "title": event.get('summary', 'Untitled'),
                        "start": event['start'].get('dateTime', event['start'].get('date')),
                        "end": event['end'].get('dateTime', event['end'].get('date')),
                        "link": event.get('htmlLink', '')
                    }
                    for event in events
                ]
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to list events: {e}")
            return {
                "status": "error",
                "message": str(e)
            }