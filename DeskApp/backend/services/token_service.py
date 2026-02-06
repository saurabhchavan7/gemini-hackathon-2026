"""
services/token_service.py
Manages Google OAuth tokens in Firestore with automatic refresh
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from services.firestore_service import FirestoreService
from core.config import settings


class TokenService:
    """Manages Google OAuth tokens with Firestore persistence and auto-refresh"""
    
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    
    def __init__(self):
        self.db = FirestoreService()
    
    async def save_google_tokens(
        self,
        user_id: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: int
    ) -> bool:
        """
        Save Google OAuth tokens to Firestore
        
        Args:
            user_id: User's unique ID
            access_token: Google access token
            refresh_token: Google refresh token (may be None on refresh)
            expires_in: Token expiry in seconds
        
        Returns:
            bool: Success status
        """
        try:
            expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
            
            token_data = {
                "access_token": access_token,
                "expires_at": expiry_time.isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if refresh_token:
                token_data["refresh_token"] = refresh_token
            
            doc_ref = self.db._get_user_ref(user_id).collection("google_tokens").document("gmail")
            
            existing = doc_ref.get()
            if existing.exists and not refresh_token:
                existing_data = existing.to_dict()
                token_data["refresh_token"] = existing_data.get("refresh_token")
            
            doc_ref.set(token_data)
            
            print(f"[TOKEN_SERVICE] Tokens saved for user {user_id}")
            print(f"[TOKEN_SERVICE] Token expires at: {expiry_time.isoformat()}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save tokens: {e}")
            return False
    
    async def get_google_tokens(self, user_id: str) -> Optional[Dict]:
        """
        Retrieve Google OAuth tokens from Firestore
        Auto-refreshes if expired
        
        Args:
            user_id: User's unique ID
        
        Returns:
            dict: Token data with access_token, refresh_token, expires_at
            None: If no tokens found or refresh failed
        """
        try:
            doc_ref = self.db._get_user_ref(user_id).collection("google_tokens").document("gmail")
            doc = doc_ref.get()
            
            if not doc.exists:
                print(f"[TOKEN_SERVICE] No tokens found for user {user_id}")
                return None
            
            token_data = doc.to_dict()
            
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            now = datetime.utcnow()
            
            if now >= expires_at:
                print(f"[TOKEN_SERVICE] Access token expired, refreshing...")
                return await self._refresh_access_token(user_id, token_data)
            
            print(f"[TOKEN_SERVICE] Valid tokens retrieved for user {user_id}")
            return token_data
            
        except Exception as e:
            print(f"[ERROR] Failed to get tokens: {e}")
            return None
    
    async def _refresh_access_token(self, user_id: str, token_data: Dict) -> Optional[Dict]:
        """
        Refresh expired access token using refresh token
        
        Args:
            user_id: User's unique ID
            token_data: Current token data with refresh_token
        
        Returns:
            dict: Updated token data
            None: If refresh failed
        """
        try:
            refresh_token = token_data.get("refresh_token")
            
            if not refresh_token:
                print(f"[ERROR] No refresh token available for user {user_id}")
                return None
            
            print(f"[TOKEN_SERVICE] Refreshing access token for user {user_id}")
            
            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            
            response = requests.post(self.GOOGLE_TOKEN_URL, data=data)
            
            if response.status_code != 200:
                error_msg = response.json().get("error_description", "Token refresh failed")
                print(f"[ERROR] Token refresh failed: {error_msg}")
                return None
            
            new_tokens = response.json()
            
            await self.save_google_tokens(
                user_id=user_id,
                access_token=new_tokens["access_token"],
                refresh_token=None,
                expires_in=new_tokens["expires_in"]
            )
            
            print(f"[TOKEN_SERVICE] Token refreshed successfully")
            
            return await self.get_google_tokens(user_id)
            
        except Exception as e:
            print(f"[ERROR] Token refresh error: {e}")
            return None
    
    async def revoke_tokens(self, user_id: str) -> bool:
        """
        Delete user's Google OAuth tokens
        
        Args:
            user_id: User's unique ID
        
        Returns:
            bool: Success status
        """
        try:
            doc_ref = self.db._get_user_ref(user_id).collection("google_tokens").document("gmail")
            doc_ref.delete()
            
            print(f"[TOKEN_SERVICE] Tokens revoked for user {user_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to revoke tokens: {e}")
            return False
    
    async def check_gmail_connected(self, user_id: str) -> bool:
        """
        Check if user has valid Gmail tokens
        
        Args:
            user_id: User's unique ID
        
        Returns:
            bool: True if Gmail is connected and tokens are valid
        """
        tokens = await self.get_google_tokens(user_id)
        return tokens is not None