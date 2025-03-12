from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from datetime import datetime
from typing import List

from .db import Base
from sqlalchemy.orm import Session

class Reminder(Base):
    __tablename__ = 'reminders'
    
    id = Column(String, primary_key=True)
    text = Column(String, nullable=False)
    reminder_time = Column(DateTime, nullable=False)
    
    @classmethod
    def get_due_reminders(cls, session: Session) -> List['Reminder']:
        current_time = datetime.now()
        return session.query(cls).filter(cls.reminder_time <= current_time).all()

class TodoItem(Base):
    __tablename__ = 'todos'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now) 