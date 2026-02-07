"""
auth/google_oauth.py
Purpose: Handle Google OAuth 2.0 authentication flow on backend
"""

import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from typing import Dict, Optional
from core.config import settings

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"


def exchange_code_for_tokens(authorization_code: str) -> Dict:
    """Exchange authorization code for access token, refresh token, and ID token"""
    
    try:
        print("[AUTH] Exchanging authorization code for tokens")
        
        data = {
            "code": authorization_code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        response = requests.post(GOOGLE_TOKEN_URL, data=data)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get("error_description", "Token exchange failed")
            print(f"[ERROR] Token exchange failed: {error_msg}")
            raise Exception(f"OAuth error: {error_msg}")
        
        tokens = response.json()
        
        print("[AUTH] Token exchange successful")
        print(f"[AUTH] Access token: {tokens['access_token'][:20]}...")
        print(f"[AUTH] Expires in: {tokens['expires_in']} seconds")
        
        return tokens
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error during token exchange: {e}")
        raise Exception(f"Failed to connect to Google: {str(e)}")
    
    except Exception as e:
        print(f"[ERROR] Token exchange error: {e}")
        raise


def verify_id_token(id_token_str: str) -> Dict:
    """Verify Google ID token and extract user information"""
    
    try:
        print("[AUTH] Verifying ID token")
        
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            id_token_str,
            request,
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=100
        )
        
        user_info = {
            "user_id": id_info.get("sub"),
            "email": id_info.get("email"),
            "email_verified": id_info.get("email_verified", False),
            "name": id_info.get("name"),
            "picture": id_info.get("picture"),
            "given_name": id_info.get("given_name"),
            "family_name": id_info.get("family_name")
        }
        
        print(f"[AUTH] ID token verified for user: {user_info['email']}")
        print(f"[AUTH] Email verified: {user_info['email_verified']}")
        
        return user_info
        
    except ValueError as e:
        print(f"[ERROR] Invalid ID token: {e}")
        raise Exception("Invalid or expired ID token")
    
    except Exception as e:
        print(f"[ERROR] Token verification error: {e}")
        raise


def get_user_profile(access_token: str) -> Dict:
    """Get additional user profile information from Google People API"""
    
    try:
        print("[AUTH] Fetching user profile")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
        
        if response.status_code != 200:
            print(f"[WARNING] Failed to fetch profile: {response.status_code}")
            return {}
        
        print("[AUTH] Profile fetched successfully")
        return response.json()
        
    except Exception as e:
        print(f"[WARNING] Profile fetch error (non-critical): {e}")
        return {}


def authenticate_user(authorization_code: str) -> Dict:
    """Complete OAuth flow: exchange code, verify token, extract user info"""
    
    try:
        print("[AUTH] Starting OAuth authentication")
        
        tokens = exchange_code_for_tokens(authorization_code)
        user_info = verify_id_token(tokens["id_token"])
        
        user_info["refresh_token"] = tokens.get("refresh_token")
        user_info["access_token"] = tokens.get("access_token")
        
        print(f"[AUTH] Authentication complete for: {user_info['email']}")
        
        return user_info
        
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        raise


async def save_tokens_to_firestore(user_id: str, tokens: Dict) -> bool:
    """Save Google OAuth tokens to Firestore during login"""
    try:
        from services.token_service import TokenService
        
        token_service = TokenService()
        
        return await token_service.save_google_tokens(
            user_id=user_id,
            access_token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            expires_in=tokens.get("expires_in", 3600)
        )
    except Exception as e:
        print(f"[ERROR] Failed to save tokens: {e}")
        return False