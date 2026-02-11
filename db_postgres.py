import os
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Boolean, DateTime, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import List, Dict, Optional

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ipos.db')

# Normalize Render URL for SQLAlchemy + psycopg (required for Python 3.13)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql+psycopg://", 1
    )

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set to True for debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database models using SQLAlchemy Core
metadata = MetaData()

ipos = Table('ipos', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('company', String(255), nullable=False, index=True),
    Column('start_date', DateTime, nullable=False, index=True),
    Column('end_date', DateTime, nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
)

fcm_tokens = Table('fcm_tokens', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('token', String(500), unique=True, nullable=False, index=True),
    Column('device_id', String(255)),
    Column('platform', String(50)),
    Column('created_at', DateTime, default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP')),
    Column('active', Boolean, default=True, index=True)
)

user_preferences = Table('user_preferences', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('fcm_token_id', Integer, nullable=False),
    Column('notification_days_before', Integer, default=1),
    Column('notification_time', String(10), default='08:00'),
    Column('notify_on_opening', Boolean, default=True),
    Column('notify_day_before', Boolean, default=True),
    Column('created_at', DateTime, default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
)

notification_log = Table('notification_log', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('ipo_id', Integer, nullable=False),
    Column('fcm_token_id', Integer, nullable=False),
    Column('notification_type', String(50)),
    Column('sent_at', DateTime, default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP')),
    Column('success', Boolean, default=True),
    Column('error_message', String(500))
)


def init_db():
    """Initialize database tables"""
    try:
        metadata.create_all(bind=engine)
        print("✅ Database tables created/verified successfully")
        return True
    except SQLAlchemyError as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def save_ipo(company: str, start_date: str, end_date: str) -> int:
    """Save a single IPO record"""
    try:
        with engine.connect() as conn:
            # Convert string dates to datetime objects
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            result = conn.execute(
                ipos.insert().values(
                    company=company,
                    start_date=start_dt,
                    end_date=end_dt,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            ipo_id = result.lastrowid
            conn.commit()
            return ipo_id
    except SQLAlchemyError as e:
        print(f"❌ Error saving IPO: {e}")
        return 0


def save_ipos(ipos_data: List[Dict[str, str]]) -> int:
    """Save multiple IPO records"""
    try:
        with engine.connect() as conn:
            # Prepare data for bulk insert
            records = []
            now = datetime.utcnow()
            
            for ipo in ipos_data:
                # Convert string dates to datetime objects
                start_dt = datetime.fromisoformat(ipo["startDate"].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(ipo["endDate"].replace('Z', '+00:00'))
                
                records.append({
                    "company": ipo["company"],
                    "start_date": start_dt,
                    "end_date": end_dt,
                    "created_at": now,
                    "updated_at": now
                })
            
            if records:
                result = conn.execute(ipos.insert(), records)
                count = result.rowcount
                conn.commit()
                print(f"✅ Saved {count} IPO records to database")
                return count
            return 0
    except SQLAlchemyError as e:
        print(f"❌ Error saving IPOs: {e}")
        return 0


def get_upcoming_ipos(limit: Optional[int] = None) -> List[Dict[str, str]]:
    """Retrieve upcoming IPOs from the database"""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT company, start_date, end_date 
                FROM ipos 
                WHERE start_date >= CURRENT_TIMESTAMP 
                ORDER BY start_date ASC
            """)
            
            if limit:
                query = text(f"""
                    SELECT company, start_date, end_date 
                    FROM ipos 
                    WHERE start_date >= CURRENT_TIMESTAMP 
                    ORDER BY start_date ASC 
                    LIMIT {limit}
                """)
            
            result = conn.execute(query)
            rows = result.fetchall()
            
            # Convert to list of dictionaries
            ipos_list = []
            for row in rows:
                ipos_list.append({
                    "company": row.company,
                    "startDate": row.start_date.isoformat(),
                    "endDate": row.end_date.isoformat()
                })
            
            return ipos_list
    except SQLAlchemyError as e:
        print(f"❌ Error retrieving IPOs: {e}")
        return []


def clear_all_ipos():
    """Delete all IPO records from the database"""
    try:
        with engine.connect() as conn:
            conn.execute(ipos.delete())
            conn.commit()
            print("✅ Cleared all IPO records")
    except SQLAlchemyError as e:
        print(f"❌ Error clearing IPOs: {e}")


def get_ipo_count() -> int:
    """Get total count of IPOs in database"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM ipos"))
            count = result.fetchone()[0]
            return count
    except SQLAlchemyError as e:
        print(f"❌ Error getting IPO count: {e}")
        return 0


# FCM Token Management
def save_fcm_token(token: str, device_id: str = None, platform: str = None) -> int:
    """Save or update FCM token"""
    try:
        with engine.connect() as conn:
            now = datetime.utcnow()
            
            # Check if token exists
            result = conn.execute(
                text("SELECT id FROM fcm_tokens WHERE token = :token"),
                {"token": token}
            )
            existing = result.fetchone()
            
            if existing:
                # Update existing token
                conn.execute(
                    text("""
                        UPDATE fcm_tokens 
                        SET device_id = :device_id, platform = :platform, updated_at = :updated_at, active = true
                        WHERE token = :token
                    """),
                    {"token": token, "device_id": device_id, "platform": platform, "updated_at": now}
                )
                token_id = existing[0]
            else:
                # Insert new token
                result = conn.execute(
                    fcm_tokens.insert().values(
                        token=token,
                        device_id=device_id,
                        platform=platform,
                        created_at=now,
                        updated_at=now,
                        active=True
                    )
                )
                token_id = result.lastrowid
            
            conn.commit()
            return token_id
    except SQLAlchemyError as e:
        print(f"❌ Error saving FCM token: {e}")
        return 0


def get_all_active_tokens() -> List[str]:
    """Get all active FCM tokens"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT token FROM fcm_tokens WHERE active = true")
            )
            rows = result.fetchall()
            return [row[0] for row in rows]
    except SQLAlchemyError as e:
        print(f"❌ Error getting active tokens: {e}")
        return []


def deactivate_fcm_token(token: str):
    """Deactivate an FCM token"""
    try:
        with engine.connect() as conn:
            now = datetime.utcnow()
            conn.execute(
                text("""
                    UPDATE fcm_tokens 
                    SET active = false, updated_at = :updated_at
                    WHERE token = :token
                """),
                {"token": token, "updated_at": now}
            )
            conn.commit()
            print(f"✅ Deactivated FCM token: {token[:20]}...")
    except SQLAlchemyError as e:
        print(f"❌ Error deactivating FCM token: {e}")


def log_notification(ipo_id: int, fcm_token_id: int, notification_type: str, 
                     success: bool, error_message: str = None):
    """Log notification send attempt"""
    try:
        with engine.connect() as conn:
            conn.execute(
                notification_log.insert().values(
                    ipo_id=ipo_id,
                    fcm_token_id=fcm_token_id,
                    notification_type=notification_type,
                    sent_at=datetime.utcnow(),
                    success=success,
                    error_message=error_message
                )
            )
            conn.commit()
    except SQLAlchemyError as e:
        print(f"❌ Error logging notification: {e}")


def get_database_stats() -> Dict[str, int]:
    """Get comprehensive database statistics"""
    try:
        with engine.connect() as conn:
            stats = {}
            
            # Count IPOs
            result = conn.execute(text("SELECT COUNT(*) FROM ipos"))
            stats['total_ipos'] = result.fetchone()[0]
            
            # Count active tokens
            result = conn.execute(text("SELECT COUNT(*) FROM fcm_tokens WHERE active = true"))
            stats['active_tokens'] = result.fetchone()[0]
            
            # Count total tokens
            result = conn.execute(text("SELECT COUNT(*) FROM fcm_tokens"))
            stats['total_tokens'] = result.fetchone()[0]
            
            # Count notifications sent today
            result = conn.execute(text("""
                SELECT COUNT(*) FROM notification_log 
                WHERE DATE(sent_at) = CURRENT_DATE AND success = true
            """))
            stats['notifications_today'] = result.fetchone()[0]
            
            return stats
    except SQLAlchemyError as e:
        print(f"❌ Error getting database stats: {e}")
        return {}


# Health check function
def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except SQLAlchemyError:
        return False


if __name__ == "__main__":
    # Test database connection
    print(f"Database URL: {DATABASE_URL}")
    print(f"Connection successful: {check_database_connection()}")
    init_db()