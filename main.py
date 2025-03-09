import asyncio
from AI_Agent import AI_Agent, AI_Client, AIMessageStorage

from tools import ReminderAgentTool, TodoAgentTool, SearchAgentTool
from g4f.Provider import Blackbox
from settings import settings
from database.db import db 
import logging
from tools.reminder_tool import ReminderChecker, Reminder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler('app.log', encoding='utf-8')
    ]
)
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
    
    try:
        # Создаем и запускаем checker напоминаний
        reminder_checker = ReminderChecker(callback=reminder_callback, check_interval=30)
        await reminder_checker.start()
        
        # Создаем агента с базовым системным промптом
        provider = Blackbox
        model = "llama-3.1-8b"
        client = AI_Client(model=model, provider=provider)
        message_storage = AIMessageStorage(max_size=20)
        agent = AI_Agent(
            client=client,
            message_storage=message_storage
        )
        
        # Регистрируем инструменты
        logger.debug("Registering ReminderAgentTool...")
        agent.register_tool(ReminderAgentTool(client=client))
        logger.debug("Registering TodoAgentTool...")
        agent.register_tool(TodoAgentTool(client=client))
        logger.debug("Registering SearchAgentTool...")
        agent.register_tool(SearchAgentTool(client=client))
        
        logger.info("AI Agent initialized with all tools")
        
        while True:
            try:
                user_input = await async_input("Enter your query: ")
                logger.debug(f"Processing user input: {user_input}")
                result = await agent.run(user_input)
                print("Result: ", result)
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}", exc_info=True)
        raise
    finally:
        await reminder_checker.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}") 