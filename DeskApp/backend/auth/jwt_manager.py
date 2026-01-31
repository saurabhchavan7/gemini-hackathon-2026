"""
auth/jwt_manager.py
Purpose: Handle JWT (JSON Web Token) creation and validation
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from core.config import settings


def create_jwt_token(user_id: str, email: str) -> str:
    """Create a JWT token for authenticated user"""
    
    try:
        now = datetime.utcnow()
        expiration = now + timedelta(days=30)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "iat": now,
            "exp": expiration
        }
        
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm="HS256"
        )
        
        print(f"[JWT] Created token for user: {email}")
        print(f"[JWT] User ID: {user_id}")
        print(f"[JWT] Expires: {expiration.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        return token
        
    except Exception as e:
        print(f"[ERROR] JWT creation failed: {e}")
        raise Exception("Failed to create JWT token")


def verify_jwt_token(token: str) -> Dict:
    """Verify JWT token signature and expiration"""
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        
        print(f"[JWT] Token verified for user: {payload.get('email')}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        print("[ERROR] JWT token expired")
        raise jwt.ExpiredSignatureError("Token has expired")
        
    except jwt.InvalidTokenError as e:
        print(f"[ERROR] Invalid JWT: {e}")
        raise jwt.InvalidTokenError("Invalid token")
        
    except Exception as e:
        print(f"[ERROR] JWT verification error: {e}")
        raise Exception("Token verification failed")


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user_id from JWT token"""
    
    try:
        payload = verify_jwt_token(token)
        return payload.get("user_id")
    except:
        return None


def is_token_expired(token: str) -> bool:
    """Check if token is expired"""
    
    try:
        verify_jwt_token(token)
        return False
    except jwt.ExpiredSignatureError:
        return True
    except:
        return True