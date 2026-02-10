import sqlite3
from datetime import datetime

DB_PATH = "ipos.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
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
