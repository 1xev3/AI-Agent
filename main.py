import asyncio
from AI_Agent import AI_Agent
from tools import ReminderAgentTool, TodoAgentTool
from g4f.Provider import Blackbox
from settings import settings
from database.db import db 
import logging
from tools.reminder_tool import ReminderChecker, Reminder

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("Starting the application")

async def init_database():
    """Initialize database and create all tables"""
    try:
        db.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def async_input(prompt: str) -> str:
    """Асинхронная версия input()"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

async def main():
    # Инициализируем базу данных
    await init_database()

    async def reminder_callback(reminder: Reminder):
        print(f"\n🔔 НАПОМИНАНИЕ: {reminder.text}")
    
    # Создаем и запускаем checker напоминаний
    reminder_checker = ReminderChecker(callback=reminder_callback, check_interval=30)  # Проверка каждые 30 секунд
    await reminder_checker.start()
    
    # Создаем агента с базовым системным промптом
    provider = Blackbox
    model = "llama-3.1-8b"#"gemini-1.5-flash"#"mixtral-small-28b",
    agent = AI_Agent(
        provider=provider,
        model=model
    )
    
    # Регистрируем инструменты
    agent.register_tool(ReminderAgentTool(model=model, provider=provider))
    agent.register_tool(TodoAgentTool(model=model, provider=provider))
    
    logger.info("AI Agent initialized with all tools")
    
    try:
        while True:
            try:
                user_input = await async_input("Enter your query: ")
                result = await agent.run(user_input)
                print("Result: ", result)
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"An error occurred: {e}")
    finally:
        await reminder_checker.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}") 