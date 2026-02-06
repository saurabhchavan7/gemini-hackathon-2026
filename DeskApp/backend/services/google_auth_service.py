"""
services/google_auth_service.py
Handles Google API authentication using Firestore tokens
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import Optional
from services.token_service import TokenService

class GoogleAuthService:
    """Manages Google API authentication using Firestore-stored tokens"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.token_service = TokenService()
    
    async def get_credentials(self) -> Optional[Credentials]:
        """Get valid Google credentials from Firestore"""
        try:
            token_data = await self.token_service.get_google_tokens(self.user_id)
            
            if not token_data:
                print(f"[GOOGLE_AUTH] No tokens found for user {self.user_id}")
                return None
            
            creds = Credentials(
                token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=None,
                client_secret=None
            )
            
            print(f"[GOOGLE_AUTH] Credentials retrieved for user {self.user_id}")
            return creds
            
        except Exception as e:
            print(f"[ERROR] Failed to get credentials: {e}")
            return None
    
    async def get_calendar_service(self):
        """Returns authenticated Google Calendar API service"""
        creds = await self.get_credentials()
        if not creds:
            raise Exception("Not authenticated with Google Calendar")
        return build('calendar', 'v3', credentials=creds)
    
    async def get_tasks_service(self):
        """Returns authenticated Google Tasks API service"""
        creds = await self.get_credentials()
        if not creds:
            raise Exception("Not authenticated with Google Tasks")
        return build('tasks', 'v1', credentials=creds)
    
    async def get_gmail_service(self):
        """Returns authenticated Gmail API service"""
        creds = await self.get_credentials()
        if not creds:
            raise Exception("Not authenticated with Gmail")
        return build('gmail', 'v1', credentials=creds)
    
    async def is_authenticated(self) -> bool:
        """Check if user has valid credentials"""
        return await self.token_service.check_gmail_connected(self.user_id)
    
    async def revoke_access(self):
        """Removes stored credentials"""
        return await self.token_service.revoke_tokens(self.user_id)