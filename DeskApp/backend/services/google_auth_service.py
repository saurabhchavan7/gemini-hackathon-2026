"""
LifeOS - Google API Authentication Service
Handles OAuth2 flow for Google Calendar, Tasks, and Gmail
"""
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import Optional

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly'
]

class GoogleAuthService:
    """Manages Google API authentication and service creation"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials_file = 'google_credentials.json'
        self.token_dir = 'tokens'
        self.token_file = os.path.join(self.token_dir, f'token_{user_id}.pickle')
        
        os.makedirs(self.token_dir, exist_ok=True)
    
    def get_credentials(self) -> Optional[Credentials]:
        """Gets valid user credentials from storage or initiates OAuth flow"""
        creds = None
        
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print(f"[GOOGLE_AUTH] Refreshing expired token for user {self.user_id}")
                creds.refresh(Request())
            else:
                print(f"[GOOGLE_AUTH] Starting OAuth flow for user {self.user_id}")
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"[ERROR] {self.credentials_file} not found! "
                        "Download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, 
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            print(f"[GOOGLE_AUTH] Credentials saved for user {self.user_id}")
        
        return creds
    
    def get_calendar_service(self):
        """Returns authenticated Google Calendar API service"""
        creds = self.get_credentials()
        return build('calendar', 'v3', credentials=creds)
    
    def get_tasks_service(self):
        """Returns authenticated Google Tasks API service"""
        creds = self.get_credentials()
        return build('tasks', 'v1', credentials=creds)
    
    def get_gmail_service(self):
        """Returns authenticated Gmail API service"""
        creds = self.get_credentials()
        return build('gmail', 'v1', credentials=creds)
    
    def is_authenticated(self) -> bool:
        """Check if user has valid credentials"""
        if not os.path.exists(self.token_file):
            return False
        
        try:
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
                return creds and creds.valid
        except:
            return False
    
    def revoke_access(self):
        """Removes stored credentials (logout)"""
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            print(f"[GOOGLE_AUTH] Access revoked for user {self.user_id}")
            return True
        return False
    
    def get_auth_url(self) -> str:
        """Generate OAuth URL without opening browser"""
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(f"[ERROR] {self.credentials_file} not found!")
        
        from google_auth_oauthlib.flow import Flow
        
        flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=SCOPES,
            redirect_uri='http://localhost:3001/auth/google/callback'
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        return authorization_url