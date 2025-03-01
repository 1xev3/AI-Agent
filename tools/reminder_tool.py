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
        self.base_system_prompt = """Ты - ассистент по управлению напоминаниями.
            
            Для создания напоминания:
            1. Извлеки текст и время из запроса пользователя
            2. Если указано "через X часов/минут" - рассчитай точное время от текущего момента
            3. Если указано "завтра" - используй дату следующего дня
            4. Используй инструмент create_reminder с извлеченными данными
            
            Для удаления напоминания:
            1. Сначала используй get_all_reminders для получения списка всех напоминаний
            2. Найди напоминание, текст которого наиболее соответствует запросу пользователя
            3. Используй delete_reminder с ID найденного напоминания
            
            Для просмотра напоминаний:
            1. Используй get_all_reminders
            2. Отформатируй список напоминаний для удобного чтения
            
            Всегда подтверждай пользователю результат операции."""
        
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
        - "Напомни мне через 3 часа купить молоко"
        - "Создай напоминалку на завтра 15:00 про встречу"
        - "Удали напоминание про встречу"
        - "Покажи все мои напоминания" """
    
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
            logger.debug("Checking reminders")
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