from typing import List, Dict, Optional
from datetime import datetime
import sqlite3

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