import asyncio
from AI_Agent import AI_Agent
from tools import ConsolePrintTool, GetInfoTool, GoogleCalendarTool
from g4f.Provider import Blackbox
from settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Создаем агента с базовым системным промптом
    provider = Blackbox
    model = "gemini-1.5-flash"#"mixtral-small-28b",
    agent = AI_Agent(
        provider=provider,
        model=model
    )
    
    # Регистрируем инструменты
    agent.register_tool(GetInfoTool)
    agent.register_tool(ConsolePrintTool)
    agent.register_tool(GoogleCalendarTool(
        provider=provider, 
        model=model, 
        calendar_id=settings.GOOGLE_CALENDAR_ID,
        credentials=settings.GOOGLE_CALENDAR_TOKEN
    ))
    
    
    while True:
        user_input = input("Enter your query: ")
        result = await agent.run(user_input)
        print("Result: ", result)
    
if __name__ == "__main__":
    asyncio.run(main()) 