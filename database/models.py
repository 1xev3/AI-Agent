from sqlalchemy import Column, String, DateTime
from .db import Base

# class Reminder(Base):
#     """SQLAlchemy model for reminders"""
#     __tablename__ = 'reminders'
    
#     id = Column(String, primary_key=True)
#     text = Column(String, nullable=False)
#     reminder_time = Column(DateTime, nullable=False)