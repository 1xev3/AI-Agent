from AI_Agent import BaseTool, ToolParameter, AI_Agent
from typing import List, Dict, Any
from g4f.Provider import Blackbox
import aiohttp
from datetime import datetime
import json
import os

class GoogleCalendarTool(BaseTool):
    """Инструмент для работы с Google Calendar через AI агент."""
    
    def __init__(self, provider, model, calendar_id, credentials: Dict):
        self.agent = AI_Agent(
            provider=provider,
            model=model
        )
        self.base_url = "https://www.googleapis.com/calendar/v3"
        self.credentials = credentials
        self.calendar_id = calendar_id
        
        # Регистрируем внутренние инструменты для агента
        self.agent.register_tool(CreateEventTool())
        self.agent.register_tool(GetEventsTool())
        self.agent.register_tool(UpdateEventTool())
        self.agent.register_tool(DeleteEventTool())
    
    @property
    def name(self) -> str:
        return "google_calendar"
    
    @property
    def description(self) -> str:
        return "Управление календарем Google Calendar через AI ассистента. Имеется возможность создавать, получать, обновлять и удалять события."
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Запрос на управление календарем в естественной форме"
            )
        ]
    
    async def execute(self, query: str) -> Any:
        if not self.credentials:
            return {"error": "Требуется настройка учетных данных Google Calendar API"}
        
        # Передаем запрос внутреннему агенту
        return await self.agent.run(query)

class CreateEventTool(BaseTool):
    """Инструмент для создания события."""
    
    @property
    def name(self) -> str:
        return "create_event"
    
    @property
    def description(self) -> str:
        return "Создает новое событие в календаре"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="summary",
                type="string",
                description="Название события"
            ),
            ToolParameter(
                name="start_time",
                type="string",
                description="Время начала (ISO формат)"
            ),
            ToolParameter(
                name="end_time",
                type="string",
                description="Время окончания (ISO формат)"
            )
        ]
    
    async def execute(self, summary: str, start_time: str, end_time: str) -> Dict:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            
            event_data = {
                "summary": summary,
                "start": {"dateTime": start_time, "timeZone": "Europe/Moscow"},
                "end": {"dateTime": end_time, "timeZone": "Europe/Moscow"}
            }
            
            async with session.post(
                f"{self.base_url}/calendars/{self.calendar_id}/events",
                headers=headers,
                json=event_data
            ) as response:
                return await response.json()

class GetEventsTool(BaseTool):
    """Инструмент для получения списка событий."""
    
    @property
    def name(self) -> str:
        return "get_events"
    
    @property
    def description(self) -> str:
        return "Получает список событий из календаря"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="time_min",
                type="string",
                description="Начальное время (ISO формат)"
            ),
            ToolParameter(
                name="time_max",
                type="string",
                description="Конечное время (ISO формат)"
            )
        ]
    
    async def execute(self, time_min: str, time_max: str) -> Dict:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}"
            }
            
            params = {
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": True,
                "orderBy": "startTime",
                "timeZone": "Europe/Moscow"
            }
            
            async with session.get(
                f"{self.base_url}/calendars/{self.calendar_id}/events",
                headers=headers,
                params=params
            ) as response:
                return await response.json()

class UpdateEventTool(BaseTool):
    """Инструмент для обновления события."""
    
    @property
    def name(self) -> str:
        return "update_event"
    
    @property
    def description(self) -> str:
        return "Обновляет существующее событие в календаре"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="event_id",
                type="string",
                description="ID события"
            ),
            ToolParameter(
                name="summary",
                type="string",
                description="Новое название события"
            ),
            ToolParameter(
                name="start_time",
                type="string",
                description="Новое время начала (ISO формат)"
            ),
            ToolParameter(
                name="end_time",
                type="string",
                description="Новое время окончания (ISO формат)"
            )
        ]
    
    async def execute(self, event_id: str, summary: str, start_time: str, end_time: str) -> Dict:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            
            event_data = {
                "summary": summary,
                "start": {"dateTime": start_time, "timeZone": "Europe/Moscow"},
                "end": {"dateTime": end_time, "timeZone": "Europe/Moscow"}
            }
            
            async with session.patch(
                f"{self.base_url}/calendars/{self.calendar_id}/events/{event_id}",
                headers=headers,
                json=event_data
            ) as response:
                return await response.json()

class DeleteEventTool(BaseTool):
    """Инструмент для удаления события."""
    
    @property
    def name(self) -> str:
        return "delete_event"
    
    @property
    def description(self) -> str:
        return "Удаляет событие из календаря"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="event_id",
                type="string",
                description="ID события для удаления"
            )
        ]
    
    async def execute(self, event_id: str) -> Dict:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.credentials['access_token']}"
            }
            
            async with session.delete(
                f"{self.base_url}/calendars/{self.calendar_id}/events/{event_id}",
                headers=headers
            ) as response:
                return {"status": "success"} if response.status == 204 else {"status": "error"} 