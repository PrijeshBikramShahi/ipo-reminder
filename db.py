from typing import List, Dict, Optional
from datetime import datetime
import sqlite3

DB_PATH = "ipos.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database and create tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # IPOs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # FCM tokens table (NEW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fcm_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            device_id TEXT,
            platform TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)
    
    # User preferences table (NEW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fcm_token_id INTEGER,
            notification_days_before INTEGER DEFAULT 1,
            notification_time TEXT DEFAULT '08:00',
            notify_on_opening INTEGER DEFAULT 1,
            notify_day_before INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (fcm_token_id) REFERENCES fcm_tokens (id)
        )
    """)
    
    # Notification log table (NEW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ipo_id INTEGER,
            fcm_token_id INTEGER,
            notification_type TEXT,
            sent_at TEXT NOT NULL,
            success INTEGER DEFAULT 1,
            error_message TEXT,
            FOREIGN KEY (ipo_id) REFERENCES ipos (id),
            FOREIGN KEY (fcm_token_id) REFERENCES fcm_tokens (id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def save_ipo(company: str, start_date: str, end_date: str) -> int:
    """Save a single IPO record"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO ipos (company, start_date, end_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (company, start_date, end_date, now, now))
    
    ipo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return ipo_id


def save_ipos(ipos: List[Dict[str, str]]) -> int:
    """Save multiple IPO records"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    records = [
        (ipo["company"], ipo["startDate"], ipo["endDate"], now, now)
        for ipo in ipos
    ]
    
    cursor.executemany("""
        INSERT INTO ipos (company, start_date, end_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, records)
    
    count = cursor.rowcount
    conn.commit()
    conn.close()

    return count

def get_upcoming_ipos(limit: Optional[int] = None) -> List[Dict[str, str]]:
    """Retrieve upcoming IPOs from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT company, start_date, end_date FROM ipos ORDER BY start_date ASC"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"company": row["company"], "startDate": row["start_date"], "endDate": row["end_date"]}
        for row in rows
    ]


def clear_all_ipos():
    """Delete all IPO records from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM ipos")
    
    conn.commit()
    conn.close()


def get_ipo_count() -> int:
    """Get total count of IPOs in database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM ipos")
    count = cursor.fetchone()["count"]
    
    conn.close()
    return count

# FCM Token Management
def save_fcm_token(token: str, device_id: str = None, platform: str = None) -> int:
    """Save or update FCM token"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # Check if token exists
    cursor.execute("SELECT id FROM fcm_tokens WHERE token = ?", (token,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing token
        cursor.execute("""
            UPDATE fcm_tokens 
            SET device_id = ?, platform = ?, updated_at = ?, active = 1
            WHERE token = ?
        """, (device_id, platform, now, token))
        token_id = existing['id']
    else:
        # Insert new token
        cursor.execute("""
            INSERT INTO fcm_tokens (token, device_id, platform, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (token, device_id, platform, now, now))
        token_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return token_id


def get_all_active_tokens() -> List[str]:
    """Get all active FCM tokens"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT token FROM fcm_tokens WHERE active = 1")
    rows = cursor.fetchall()
    conn.close()
    
    return [row['token'] for row in rows]


def deactivate_fcm_token(token: str):
    """Deactivate an FCM token"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE fcm_tokens 
        SET active = 0, updated_at = ?
        WHERE token = ?
    """, (now, token))
    
    conn.commit()
    conn.close()


def log_notification(ipo_id: int, fcm_token_id: int, notification_type: str, 
                     success: bool, error_message: str = None):
    """Log notification send attempt"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO notification_log 
        (ipo_id, fcm_token_id, notification_type, sent_at, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (ipo_id, fcm_token_id, notification_type, now, 1 if success else 0, error_message))
    
    conn.commit()
    conn.close()
