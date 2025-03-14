# Standard library imports
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Callable

# Third party imports
from sqlalchemy.orm import Session

# Local imports
from AgentForge.core.tool_base import BaseTool, ToolParameter
from AgentForge.core.agent import Agent
from AgentForge.core.message_storage import MessageStorage
from AgentForge.database.db import with_session
from AgentForge.database.models import Reminder

logger = logging.getLogger(__name__)

WHO_AM_I = """You are a reminder management assistant. Always respond in User language!
Current system time: {current_time}

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



class CreateReminderTool(BaseTool):
    name = "create_reminder"
    description = "Creates a new reminder"
    parameters = [
        ToolParameter(
            name="text",
            type="string",
            description="Text of the reminder"
        ),
        ToolParameter(
            name="date_time_str",
            type="string",
            description="Datetime for the reminder in format YYYY-MM-DD HH:MM"
        )
    ]
    returns = "Result of action"
    
    @with_session
    async def execute(self, text: str, date_time_str: str, session: Session) -> Dict:
        reminder_id = f"rem_{uuid.uuid4().hex[:8]}"
        agent_id = self.parent_agent.get_id()
        reminder_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
        
        reminder = Reminder(
            id=reminder_id,
            agent_id=agent_id,
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
    name = "delete_reminder"
    description = "Deletes a reminder by its ID"
    parameters = [
        ToolParameter(
            name="reminder_id",
            type="string",
            description="ID of the reminder to delete"
        )
    ]
    returns = "Result of action"
    
    @with_session
    async def execute(self, reminder_id: str, session: Session) -> Dict:
        agent_id = self.parent_agent.get_id()
        logger.info(f"Deleting reminder with ID: {reminder_id}")
        reminder = session.query(Reminder).filter_by(id=reminder_id, agent_id=agent_id).first()
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
    name = "get_all_reminders"
    description = "Returns all existing reminders"
    parameters = []
    returns = "List of reminders"
    
    @with_session
    async def execute(self, session: Session) -> List[Dict]:
        logger.info("Getting all reminders")
        reminders = session.query(Reminder).all()
        return [{
            "id": r.id,
            "text": r.text,
            "datetime": r.reminder_time.strftime("%Y-%m-%d %H:%M")
        } for r in reminders]

class ReminderAgentTool(BaseTool):
    name = "reminder_manager"
    description = "Manages reminders using natural language commands"
    parameters = [
        ToolParameter(
            name="request",
            type="string",
            description="Natural language request for managing reminders"
        )
    ]
    returns = "Result of action"

    def on_register(self, parent_agent: Agent):
        client = parent_agent.client
        self.agent = Agent(
            client=client,
            agent_id=parent_agent.get_id(),
            message_storage=MessageStorage(), #will be updated AI Agent
            who_am_i=WHO_AM_I.format(current_time=datetime.now().strftime("%Y-%m-%d %H:%M")),
            tools=[
                CreateReminderTool(), 
                DeleteReminderTool(), 
                GetAllRemindersTool()
            ]
        )

    def _get_system_prompt(self) -> str:
        """Get system prompt with current time"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        return WHO_AM_I.format(current_time=current_time)
    
    async def execute(self, request: str) -> str:
        # Update system prompt with current time before each execution
        self.agent.clear_messages()
        self.agent.update_who_am_i(self._get_system_prompt())
        logger.info(f"Running agent with request: {request}")
        res = await self.agent.run(request)
        return res



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