from sqlalchemy import Column, String, DateTime
from .db import Base
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

# class Reminder(Base):
#     __tablename__ = 'reminders'
    
#     id = Column(String, primary_key=True)
#     user_id = Column(String, nullable=False)
#     text = Column(String, nullable=False)
#     reminder_time = Column(DateTime, nullable=False)
    
#     @classmethod
#     def get_due_reminders(cls, session: Session) -> List['Reminder']:
#         current_time = datetime.now()
#         return session.query(cls).filter(cls.reminder_time <= current_time).all()


# class TodoItem(Base):
#     __tablename__ = 'todos'
    
#     id = Column(String, primary_key=True)
#     user_id = Column(String, nullable=False)
#     title = Column(String, nullable=False)
#     description = Column(String, nullable=True)