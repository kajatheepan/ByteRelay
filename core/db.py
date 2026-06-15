from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from core.config import settings
from contextlib import contextmanager
from datetime import datetime, timezone


engine = create_engine(f"sqlite:///{settings.database_path}")


# Runs on every new connection, since SQLite PRAGMAs are per-connection,
# not permanent database settings.
@event.listens_for(engine, "connect")
def enable_wal(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # lets reads/writes happen concurrently
    cursor.execute("PRAGMA foreign_keys=ON")   # required or ON DELETE CASCADE silently does nothing
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


# Use this everywhere instead of calling SessionLocal() directly — it
# guarantees the session is closed even if an exception happens inside.
# Usage: with get_session() as session: ...
@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# All timestamps in this app are stored as UTC ISO 8601 strings, never local time.
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")