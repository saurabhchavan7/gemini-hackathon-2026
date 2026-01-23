"""
auth/jwt_manager.py

Purpose: Handle JWT (JSON Web Token) creation and validation for user authentication

Features:
- Create JWT tokens with user information
- Sign tokens with secret key
- Set 30-day expiration
- Verify and decode JWT tokens
- Validate token signature and expiration
- Extract user_id from valid tokens

JWT Structure:
- Header: { "alg": "HS256", "typ": "JWT" }
- Payload: { "user_id": "xxx", "email": "xxx", "exp": timestamp, "iat": timestamp }
- Signature: HMACSHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), secret)

Security:
- Tokens signed with HS256 algorithm
- Secret key stored in environment variable
- Tokens expire after 30 days
- Signature verification prevents tampering
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
import config


def create_jwt_token(user_id: str, email: str) -> str:
    """
    Create a JWT token for authenticated user
    
    Args:
        user_id: Unique user identifier (from Google sub claim)
        email: User's email address
        
    Returns:
        str: Signed JWT token
        
    Example:
        token = create_jwt_token("12345", "user@example.com")
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    
    try:
        # Current time
        now = datetime.utcnow()
        
        # Expiration time (30 days from now)
        expiration = now + timedelta(days=config.JWT_EXPIRATION_DAYS)
        
        # JWT payload
        payload = {
            "user_id": user_id,
            "email": email,
            "iat": now,  # Issued at
            "exp": expiration  # Expires at
        }
        
        # Sign the token with secret key
        token = jwt.encode(
            payload,
            config.JWT_SECRET,
            algorithm=config.JWT_ALGORITHM
        )
        
        print(f"✅ JWT created for user: {email}")
        print(f"   User ID: {user_id}")
        print(f"   Expires: {expiration.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"   Valid for: {config.JWT_EXPIRATION_DAYS} days")
        
        return token
        
    except Exception as e:
        print(f"❌ JWT creation failed: {e}")
        raise Exception("Failed to create JWT token")


def verify_jwt_token(token: str) -> Dict:
    """
    Verify JWT token signature and expiration, then extract payload
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Decoded token payload with user_id and email
        
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid or tampered with
        Exception: For other verification errors
        
    Example:
        try:
            payload = verify_jwt_token(token)
            user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            print("Token expired")
    """
    
    try:
        # Decode and verify token
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM]
        )
        
        print(f"✅ JWT verified for user: {payload.get('email')}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        print(f"❌ JWT expired")
        raise jwt.ExpiredSignatureError("Token has expired")
        
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid JWT: {e}")
        raise jwt.InvalidTokenError("Invalid token")
        
    except Exception as e:
        print(f"❌ JWT verification error: {e}")
        raise Exception("Token verification failed")


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user_id from JWT token (convenience function)
    
    Args:
        token: JWT token string
        
    Returns:
        str: user_id if token is valid
        None: if token is invalid or expired
        
    Example:
        user_id = get_user_id_from_token(token)
        if user_id:
            print(f"User ID: {user_id}")
    """
    
    try:
        payload = verify_jwt_token(token)
        return payload.get("user_id")
    except:
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if token is expired without raising exception
    
    Args:
        token: JWT token string
        
    Returns:
        bool: True if expired, False if valid
    """
    
    try:
        verify_jwt_token(token)
        return False  # Token is valid
    except jwt.ExpiredSignatureError:
        return True  # Token expired
    except:
        return True  # Token invalid (treat as expired)


def decode_token_without_verification(token: str) -> Optional[Dict]:
    """
    Decode token payload WITHOUT verifying signature (for debugging only)
    
    ⚠️  WARNING: Do NOT use this for authentication!
    This is only for debugging or extracting claims from tokens you trust.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Decoded payload (unverified)
        None: if token is malformed
    """
    
    try:
        # Decode without verification
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        return payload
    except:
        return None


def refresh_token(old_token: str) -> Optional[str]:
    """
    Create a new token from an old one (if still valid)
    Useful for extending session before expiration
    
    Args:
        old_token: Current JWT token
        
    Returns:
        str: New JWT token with extended expiration
        None: if old token is invalid
    """
    
    try:
        # Verify old token
        payload = verify_jwt_token(old_token)
        
        # Create new token with same user info
        new_token = create_jwt_token(
            payload["user_id"],
            payload["email"]
        )
        
        print(f"✅ Token refreshed for: {payload['email']}")
        
        return new_token
        
    except:
        print(f"❌ Cannot refresh invalid/expired token")
        return None


# Test function
if __name__ == "__main__":
    print("🧪 JWT Manager Test\n")
    
    # Check configuration
    if not config.JWT_SECRET:
        print("❌ JWT_SECRET not configured!")
        exit(1)
    
    print(f"✅ JWT_SECRET configured: {config.JWT_SECRET[:10]}...")
    print(f"✅ Algorithm: {config.JWT_ALGORITHM}")
    print(f"✅ Expiration: {config.JWT_EXPIRATION_DAYS} days\n")
    
    # Test token creation
    print("Testing token creation...")
    test_token = create_jwt_token("test_user_123", "test@example.com")
    print(f"\nGenerated token: {test_token[:50]}...\n")
    
    # Test token verification
    print("Testing token verification...")
    payload = verify_jwt_token(test_token)
    print(f"Decoded payload: {payload}\n")
    
    # Test user_id extraction
    print("Testing user_id extraction...")
    user_id = get_user_id_from_token(test_token)
    print(f"Extracted user_id: {user_id}\n")
    
    print("✅ All tests passed!")
