from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import functools

Base = declarative_base()

class Database:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        
    def init_db(self, url: str = None):
        assert url is not None, "Database URL is required"
        
        self.url = url
        self.engine = create_engine(self.url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Create global database instance
db = Database()

def with_session(func):
    """Decorator for automatic session management"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with db.get_session() as session:
            return await func(*args, session=session, **kwargs)
    return wrapper 