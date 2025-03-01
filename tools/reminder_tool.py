from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Callable
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Session
from AI_Agent import BaseTool, ToolParameter, AI_Agent
from database.db import Base, with_session
import logging
import asyncio

logger = logging.getLogger(__name__)

class Reminder(Base):
    __tablename__ = 'reminders'
    
    id = Column(String, primary_key=True)
    text = Column(String, nullable=False)
    reminder_time = Column(DateTime, nullable=False)
    
    @classmethod
    def get_due_reminders(cls, session: Session) -> List['Reminder']:
        current_time = datetime.now()
        return session.query(cls).filter(cls.reminder_time <= current_time).all()

class CreateReminderTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_reminder"
    
    @property
    def description(self) -> str:
        return "Creates a new reminder"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="text",
                type="string",
                description="Text of the reminder"
            ),
            ToolParameter(
                name="datetime_str",
                type="string",
                description="Datetime for the reminder in format YYYY-MM-DD HH:MM"
            )
        ]
    
    @with_session
    async def execute(self, text: str, datetime_str: str, session: Session) -> Dict:
        reminder_id = f"rem_{uuid.uuid4().hex[:8]}"  # Увеличили длину ID для уникальности
        reminder_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        
        reminder = Reminder(
            id=reminder_id,
            text=text,
            reminder_time=reminder_time
        )
        session.add(reminder)
        logger.info(f"Reminder created: {reminder.id} - {reminder.text} at {reminder.reminder_time}")
        
        return {
            "id": reminder.id,
            "text": reminder.text,
            "datetime": reminder.reminder_time.strftime("%Y-%m-%d %H:%M")
        }

class DeleteReminderTool(BaseTool):
    @property
    def name(self) -> str:
        return "delete_reminder"
    
    @property
    def description(self) -> str:
        return "Deletes a reminder by its ID"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="reminder_id",
                type="string",
                description="ID of the reminder to delete"
            )
        ]
    
    @with_session
    async def execute(self, reminder_id: str, session: Session) -> Dict:
        reminder = session.query(Reminder).filter_by(id=reminder_id).first()
        if reminder:
            session.delete(reminder)
            return {
                "success": True, 
                "message": f"Reminder '{reminder.text}' deleted"
            }
        return {
            "success": False, 
            "message": f"No reminder found with ID {reminder_id}"
        }

class GetAllRemindersTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_all_reminders"
    
    @property
    def description(self) -> str:
        return "Returns all existing reminders"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return []
    
    @with_session
    async def execute(self, session: Session) -> List[Dict]:
        reminders = session.query(Reminder).all()
        return [{
            "id": r.id,
            "text": r.text,
            "datetime": r.reminder_time.strftime("%Y-%m-%d %H:%M")
        } for r in reminders]

class ReminderAgentTool(BaseTool):
    def __init__(self, model: str, provider: str):
        self.base_system_prompt = """You are a reminder management assistant. Always respond in User language!
        
For creating a reminder:
1. Extract text and time from user request
2. If "in X hours/minutes" is specified - calculate exact time from current moment
3. If "tomorrow" is specified - use next day's date
4. Use create_reminder tool with extracted data

For deleting a reminder:
1. First use get_all_reminders to get list of all reminders
2. Find reminder whose text best matches user request
3. Use delete_reminder with ID of found reminder

For viewing reminders:
1. Use get_all_reminders
2. Format reminder list for easy reading

Always confirm operation result to user."""
        
        self.agent = AI_Agent(
            model=model,
            provider=provider,
            system_prompt=self._get_system_prompt(),
            memory_size=20
        )
        
        self.agent.register_tool(CreateReminderTool())
        self.agent.register_tool(DeleteReminderTool())
        self.agent.register_tool(GetAllRemindersTool())
        self.agent.init()

    def _get_system_prompt(self) -> str:
        """Get system prompt with current time"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""Текущее системное время: {current_time}

{self.base_system_prompt}"""

    @property
    def name(self) -> str:
        return "reminder_manager"
    
    @property
    def description(self) -> str:
        return """Manages reminders using natural language commands. Examples:
        - "Remind me to buy milk in 3 hours"
        - "Create a reminder for tomorrow at 15:00 about the meeting"
        - "Delete the reminder about the meeting"
        - "Show all my reminders" """
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="request",
                type="string",
                description="Natural language request for managing reminders"
            )
        ]
    
    async def execute(self, request: str) -> str:
        # Update system prompt with current time before each execution
        self.agent.update_system_prompt(self._get_system_prompt())
        return await self.agent.run(request)

class ReminderChecker:
    def __init__(self, callback: Callable, check_interval: int = 60):
        """
        Initialize reminder checker
        Args:
            check_interval: interval in seconds to check for due reminders
        """
        logger.info(f"Reminder checker initialized with interval {check_interval} seconds")
        self.check_interval = check_interval
        self._running = False
        self._task = None
        self.callback = callback

    async def start(self):
        """Start checking reminders"""
        self._running = True
        self._task = asyncio.create_task(self._check_reminders())
        logger.info("Reminder checker started")

    async def stop(self):
        """Stop checking reminders"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Reminder checker stopped")

    @with_session
    async def _check_reminders(self, session: Session):
        """Main loop for checking reminders"""
        while self._running:
            # logger.debug("Checking reminders")
            try:
                due_reminders = Reminder.get_due_reminders(session)
                for reminder in due_reminders:
                    logger.info(f"Reminder found: {reminder.text} at {reminder.reminder_time}")
                    await self.callback(reminder)
                    session.delete(reminder)
                    session.commit()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error checking reminders: {e}")
                await asyncio.sleep(self.check_interval)