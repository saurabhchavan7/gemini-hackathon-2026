"""
LifeOS - Gmail Service
Handles reading emails and creating drafts
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from services.google_auth_service import GoogleAuthService
from services.firestore_service import FirestoreService
import base64
import re

class GmailService:
    """Manages Gmail operations for email intelligence"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.auth_service = GoogleAuthService(user_id)
        self.db = FirestoreService()
        self.gmail_service = None
    
    def _get_service(self):
        """Lazy load Gmail service"""
        if not self.gmail_service:
            self.gmail_service = self.auth_service.get_gmail_service()
        return self.gmail_service
    
    def get_yesterdays_emails(self, max_results: int = 20, include_today: bool = True) -> List[Dict]:
        """Fetch emails from yesterday and optionally today"""
        
        try:
            service = self._get_service()
            
            now = datetime.now()
            
            if include_today:
                start_time = now - timedelta(hours=48)
                end_time = now
                print("[GMAIL] Checking emails from last 48 hours (yesterday + today)")
            else:
                yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
                yesterday_end = yesterday_start.replace(hour=23, minute=59, second=59)
                start_time = yesterday_start
                end_time = yesterday_end
                print("[GMAIL] Checking emails from yesterday only")
            
            after_timestamp = int(start_time.timestamp())
            before_timestamp = int(end_time.timestamp())
            
            print(f"[GMAIL] Date range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
            
            query = f'after:{after_timestamp} before:{before_timestamp} -from:me'
            print(f"[GMAIL] Searching with query: {query}")
            
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            print(f"[GMAIL] Found {len(messages)} emails")
            
            emails = []
            for msg in messages:
                email_data = self._get_email_details(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch emails: {e}")
            return []
    
    def _get_email_details(self, message_id: str) -> Optional[Dict]:
        """Get full details of an email"""
        
        try:
            service = self._get_service()
            
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            body = self._get_email_body(message['payload'])
            
            from_match = re.match(r'(.+?)\s*<(.+?)>', from_email)
            if from_match:
                from_name = from_match.group(1).strip('"')
                from_addr = from_match.group(2)
            else:
                from_name = from_email
                from_addr = from_email
            
            thread_id = message.get('threadId', '')
            
            return {
                "id": message_id,
                "thread_id": thread_id,
                "subject": subject,
                "from_name": from_name,
                "from_email": from_addr,
                "date": date,
                "snippet": message.get('snippet', '')[:200],
                "body": body[:1000],
                "labels": message.get('labelIds', [])
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to get email {message_id}: {e}")
            return None
    
    def _get_email_body(self, payload: dict) -> str:
        """Extract email body from payload"""
        
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
        elif 'body' in payload:
            data = payload['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body
    
    def check_if_user_replied(self, thread_id: str) -> bool:
        """Check if user already replied in this thread"""
        
        try:
            service = self._get_service()
            
            thread = service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()
            
            messages = thread.get('messages', [])
            
            if len(messages) < 2:
                return False
            
            last_message = messages[-1]
            headers = last_message['payload']['headers']
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
            
            profile = service.users().getProfile(userId='me').execute()
            user_email = profile['emailAddress']
            
            return user_email in from_email
            
        except Exception as e:
            print(f"[WARNING] Could not check reply status: {e}")
            return False
    
    def create_draft(self, to_email: str, subject: str, body: str, thread_id: Optional[str] = None) -> Dict:
        """Create a draft email in Gmail"""
        
        try:
            service = self._get_service()
            
            message_text = f"To: {to_email}\nSubject: {subject}\n\n{body}"
            message_bytes = message_text.encode('utf-8')
            message_b64 = base64.urlsafe_b64encode(message_bytes).decode('utf-8')
            
            draft_body = {
                'message': {
                    'raw': message_b64
                }
            }
            
            if thread_id:
                draft_body['message']['threadId'] = thread_id
            
            draft = service.users().drafts().create(
                userId='me',
                body=draft_body
            ).execute()
            
            draft_id = draft['id']
            
            print(f"[GMAIL] Created draft for: {subject}")
            
            return {
                "status": "success",
                "draft_id": draft_id,
                "message": "Draft created in Gmail"
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to create draft: {e}")
            return {
                "status": "error",
                "message": str(e)
            }