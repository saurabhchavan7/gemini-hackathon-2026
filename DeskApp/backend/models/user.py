"""
models/user.py
User model and database operations
"""
from typing import Dict, Optional
from models.database import get_connection


def create_or_update_user(user_id: str, email: str, name: str, picture: str) -> Dict:
    """
    Create or update user in database
    
    Args:
        user_id: Google user ID (sub claim)
        email: User email
        name: User display name
        picture: Profile picture URL
    
    Returns:
        dict: User data
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (user_id, email, name, picture, created_at, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(user_id) 
            DO UPDATE SET
                email = excluded.email,
                name = excluded.name,
                picture = excluded.picture,
                updated_at = datetime('now')
        """, (user_id, email, name, picture))
        
        conn.commit()
        conn.close()
        
        print(f"[DB] User saved: {email}")
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to save user: {e}")
        raise


def get_user(user_id: str) -> Optional[Dict]:
    """
    Get user from database by user_id
    
    Args:
        user_id: Google user ID
    
    Returns:
        dict: User data or None if not found
    """
    try:
        conn = get_connection()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, email, name, picture, created_at, updated_at
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        return user_data
        
    except Exception as e:
        print(f"[ERROR] Failed to get user: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Get user from database by email
    
    Args:
        email: User email address
    
    Returns:
        dict: User data or None if not found
    """
    try:
        conn = get_connection()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, email, name, picture, created_at, updated_at
            FROM users
            WHERE email = ?
        """, (email,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        return user_data
        
    except Exception as e:
        print(f"[ERROR] Failed to get user by email: {e}")
        return None