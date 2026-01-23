"""
models/user.py

Purpose: User management and database operations

Features:
- Create new users in database
- Get user by user_id
- Update user information
- Check if user exists
- Store user profile data (email, name, picture)

Database:
- Currently uses SQLite (from existing database.py)
- Can be switched to Firestore later if needed

User Schema:
- user_id: Unique identifier from Google (sub claim)
- email: User's email address
- name: Full name
- picture: Profile picture URL
- created_at: Account creation timestamp
- updated_at: Last update timestamp
"""

import sqlite3
from datetime import datetime
from typing import Dict, Optional
from models.database import get_connection


def create_user(user_id: str, email: str, name: str, picture: str) -> Dict:
    """
    Create a new user in the database
    
    Args:
        user_id: Unique user identifier from Google OAuth (sub)
        email: User's email address
        name: User's full name
        picture: Profile picture URL
        
    Returns:
        dict: Created user data
        
    Raises:
        Exception: If user creation fails
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Check if users table exists, create if not
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                picture TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (user_id, email, name, picture, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, email, name, picture, now, now))
        
        conn.commit()
        conn.close()
        
        print(f"✅ User created: {email}")
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": now,
            "updated_at": now
        }
        
    except sqlite3.IntegrityError:
        # User already exists - this is okay, return existing user
        print(f"ℹ️  User already exists: {email}")
        return get_user(user_id)
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        raise Exception(f"Failed to create user: {str(e)}")


def get_user(user_id: str) -> Optional[Dict]:
    """
    Get user by user_id
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        dict: User data if found
        None: If user not found
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, email, name, picture, created_at, updated_at
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print(f"⚠️  User not found: {user_id}")
            return None
        
        user = {
            "user_id": row[0],
            "email": row[1],
            "name": row[2],
            "picture": row[3],
            "created_at": row[4],
            "updated_at": row[5]
        }
        
        print(f"✅ User retrieved: {user['email']}")
        return user
        
    except Exception as e:
        print(f"❌ Failed to get user: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Get user by email address
    
    Args:
        email: User's email address
        
    Returns:
        dict: User data if found
        None: If user not found
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, email, name, picture, created_at, updated_at
            FROM users
            WHERE email = ?
        """, (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "user_id": row[0],
            "email": row[1],
            "name": row[2],
            "picture": row[3],
            "created_at": row[4],
            "updated_at": row[5]
        }
        
    except Exception as e:
        print(f"❌ Failed to get user by email: {e}")
        return None


def update_user(user_id: str, name: str = None, picture: str = None) -> Optional[Dict]:
    """
    Update user information
    
    Args:
        user_id: User's unique identifier
        name: New name (optional)
        picture: New picture URL (optional)
        
    Returns:
        dict: Updated user data
        None: If user not found
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Build update query dynamically based on provided fields
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if picture is not None:
            updates.append("picture = ?")
            params.append(picture)
        
        if not updates:
            # Nothing to update
            return get_user(user_id)
        
        updates.append("updated_at = ?")
        params.append(now)
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        print(f"✅ User updated: {user_id}")
        
        return get_user(user_id)
        
    except Exception as e:
        print(f"❌ Failed to update user: {e}")
        return None


def user_exists(user_id: str) -> bool:
    """
    Check if user exists in database
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        bool: True if user exists, False otherwise
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM users WHERE user_id = ?
        """, (user_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
        
    except Exception as e:
        print(f"❌ Failed to check user existence: {e}")
        return False


def create_or_update_user(user_id: str, email: str, name: str, picture: str) -> Dict:
    """
    Create user if new, or update if exists (upsert operation)
    
    Args:
        user_id: Unique user identifier
        email: User's email
        name: User's name
        picture: Profile picture URL
        
    Returns:
        dict: User data
    """
    
    if user_exists(user_id):
        print(f"ℹ️  User exists, updating: {email}")
        update_user(user_id, name=name, picture=picture)
        return get_user(user_id)
    else:
        print(f"ℹ️  New user, creating: {email}")
        return create_user(user_id, email, name, picture)


def delete_user(user_id: str) -> bool:
    """
    Delete user from database (use with caution!)
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        bool: True if deleted, False if failed
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        if deleted:
            print(f"✅ User deleted: {user_id}")
        else:
            print(f"⚠️  User not found for deletion: {user_id}")
        
        return deleted
        
    except Exception as e:
        print(f"❌ Failed to delete user: {e}")
        return False


# Test function
if __name__ == "__main__":
    print("🧪 User Model Test\n")
    
    # Test user creation
    print("Testing user creation...")
    test_user = create_user(
        user_id="test_123",
        email="test@example.com",
        name="Test User",
        picture="https://example.com/avatar.jpg"
    )
    print(f"Created: {test_user}\n")
    
    # Test user retrieval
    print("Testing user retrieval...")
    retrieved = get_user("test_123")
    print(f"Retrieved: {retrieved}\n")
    
    # Test user update
    print("Testing user update...")
    updated = update_user("test_123", name="Updated Name")
    print(f"Updated: {updated}\n")
    
    # Test user existence check
    print("Testing user existence...")
    exists = user_exists("test_123")
    print(f"Exists: {exists}\n")
    
    # Clean up
    print("Cleaning up...")
    delete_user("test_123")
    
    print("✅ All tests passed!")
