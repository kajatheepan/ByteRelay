from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from core.config import settings
from contextlib import contextmanager



engine = create_engine(f"sqlite:///{settings.database_path}")


@event.listens_for(engine, "connect")
def enable_wal(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()