"""
LifeOS Database Setup
Creates SQLite database with required tables
"""

import sqlite3
import os

# Database path
DB_DIR = "./data"
DB_PATH = os.path.join(DB_DIR, "lifeos.db")


def init_database():
    """Create database and tables if they don't exist"""
    
    # Ensure directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Items table - stores captures + AI analysis
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id TEXT PRIMARY KEY,
        user_id TEXT,  -- NEW
        screenshot_path TEXT,
        audio_path TEXT,  -- NEW
        audio_transcript TEXT,  -- NEW
        text_note TEXT,   -- NEW
        app_name TEXT,
        window_title TEXT,
        url TEXT,
        timestamp TEXT,
        
        -- Gemini Analysis
        extracted_text TEXT,
        content_type TEXT,
        title TEXT,
        entities TEXT,
        deadline TEXT,
        
        -- Metadata
        created_at TEXT,
        updated_at TEXT,
        is_archived INTEGER DEFAULT 0
    )
""")
    
    # Reminders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id TEXT PRIMARY KEY,
            item_id TEXT,
            reminder_type TEXT,
            trigger_at TEXT,
            message TEXT,
            is_sent INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    # Tags table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)
    
    # Item-Tags junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_tags (
            item_id TEXT,
            tag_id INTEGER,
            PRIMARY KEY (item_id, tag_id),
            FOREIGN KEY (item_id) REFERENCES items(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized: {DB_PATH}")


def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)


if __name__ == "__main__":
    init_database()
    print("📦 Database ready!")
    print(f"🔧 Setting up database at: {DB_PATH}")