"""
auth/google_oauth.py

Purpose: Handle Google OAuth 2.0 authentication flow on backend

Features:
- Exchange authorization code for access token
- Verify Google ID token
- Extract user information from ID token
- Get user profile from Google People API

Flow:
1. Frontend sends authorization code
2. Backend exchanges code for tokens (access + refresh + id_token)
3. Backend verifies ID token signature
4. Backend extracts user info (user_id, email, name, picture)
5. Backend returns user info to create/login user

Security:
- All token exchange happens server-side
- Client never sees access/refresh tokens
- ID token verified with Google's public keys
"""

import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from typing import Dict, Optional
import config

# Google OAuth endpoints
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"


def exchange_code_for_tokens(authorization_code: str) -> Dict:
    """
    Exchange authorization code for access token, refresh token, and ID token
    
    Args:
        authorization_code: The code received from OAuth callback
        
    Returns:
        dict: {
            "access_token": str,
            "refresh_token": str,
            "id_token": str,
            "expires_in": int
        }
        
    Raises:
        Exception: If token exchange fails
    """
    
    try:
        print(f"🔐 Exchanging authorization code for tokens...")
        
        # Prepare token request
        data = {
            "code": authorization_code,
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": config.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        # Make request to Google
        response = requests.post(GOOGLE_TOKEN_URL, data=data)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get("error_description", "Token exchange failed")
            print(f"❌ Token exchange failed: {error_msg}")
            raise Exception(f"OAuth error: {error_msg}")
        
        tokens = response.json()
        
        print(f"✅ Token exchange successful")
        print(f"   Access token received: {tokens['access_token'][:20]}...")
        print(f"   Expires in: {tokens['expires_in']} seconds")
        
        return tokens
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during token exchange: {e}")
        raise Exception(f"Failed to connect to Google: {str(e)}")
    
    except Exception as e:
        print(f"❌ Token exchange error: {e}")
        raise


def verify_id_token(id_token_str: str) -> Dict:
    """
    Verify Google ID token and extract user information
    
    Args:
        id_token_str: The ID token from Google
        
    Returns:
        dict: {
            "user_id": str (sub),
            "email": str,
            "email_verified": bool,
            "name": str,
            "picture": str,
            "given_name": str,
            "family_name": str
        }
        
    Raises:
        Exception: If token verification fails
    """
    
    try:
        print(f"🔍 Verifying ID token...")
        
        # Verify token signature with Google's public keys
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            id_token_str,
            request,
            config.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=100  # Allow some clock skew
        )
        
        # Extract user information
        user_info = {
            "user_id": id_info.get("sub"),
            "email": id_info.get("email"),
            "email_verified": id_info.get("email_verified", False),
            "name": id_info.get("name"),
            "picture": id_info.get("picture"),
            "given_name": id_info.get("given_name"),
            "family_name": id_info.get("family_name")
        }
        
        print(f"✅ ID token verified")
        print(f"   User: {user_info['email']}")
        print(f"   Email verified: {user_info['email_verified']}")
        
        return user_info
        
    except ValueError as e:
        print(f"❌ Invalid ID token: {e}")
        raise Exception("Invalid or expired ID token")
    
    except Exception as e:
        print(f"❌ Token verification error: {e}")
        raise


def get_user_profile(access_token: str) -> Dict:
    """
    Get additional user profile information from Google People API
    
    Args:
        access_token: Valid Google access token
        
    Returns:
        dict: Additional user profile data
        
    Note: This is optional - most info comes from ID token
    """
    
    try:
        print(f"👤 Fetching user profile...")
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
        
        if response.status_code != 200:
            print(f"⚠️  Failed to fetch profile: {response.status_code}")
            return {}
        
        profile = response.json()
        
        print(f"✅ Profile fetched")
        return profile
        
    except Exception as e:
        print(f"⚠️  Profile fetch error (non-critical): {e}")
        return {}


def authenticate_user(authorization_code: str) -> Dict:
    """
    Complete OAuth flow: exchange code, verify token, extract user info
    
    Args:
        authorization_code: Authorization code from OAuth callback
        
    Returns:
        dict: {
            "user_id": str,
            "email": str,
            "name": str,
            "picture": str,
            "email_verified": bool,
            "refresh_token": str (for storing in Secret Manager)
        }
        
    Raises:
        Exception: If authentication fails at any step
    """
    
    try:
        print(f"\n🔐 Starting OAuth authentication...")
        
        # Step 1: Exchange code for tokens
        tokens = exchange_code_for_tokens(authorization_code)
        
        # Step 2: Verify ID token and extract user info
        user_info = verify_id_token(tokens["id_token"])
        
        # Step 3: Add refresh token to user info (for Secret Manager storage)
        user_info["refresh_token"] = tokens.get("refresh_token")
        user_info["access_token"] = tokens.get("access_token")
        
        print(f"✅ Authentication complete for: {user_info['email']}\n")
        
        return user_info
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}\n")
        raise


# Test function
if __name__ == "__main__":
    print("🧪 Google OAuth Module Test")
    print(f"Client ID configured: {config.GOOGLE_CLIENT_ID[:20]}...")
    print(f"Client Secret configured: {'✅' if config.GOOGLE_CLIENT_SECRET else '❌'}")
    print(f"Redirect URI: {config.GOOGLE_REDIRECT_URI}")
    print("\nTo test:")
    print("1. Get authorization code from OAuth flow")
    print("2. Call: authenticate_user(code)")
