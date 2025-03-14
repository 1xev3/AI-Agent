from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from datetime import datetime
from typing import List

from .db import Base
from sqlalchemy.orm import Session

class Reminder(Base):
    __tablename__ = 'reminders'
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False) # For agent identification
    
    text = Column(String, nullable=False)
    reminder_time = Column(DateTime, nullable=False)
    
    @classmethod
    def get_due_reminders(cls, session: Session) -> List['Reminder']:
        current_time = datetime.now()
        return session.query(cls).filter(cls.reminder_time <= current_time).all()

class TodoItem(Base):
    __tablename__ = 'todos'
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False) # For agent identification

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)