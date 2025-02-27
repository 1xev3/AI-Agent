import asyncio
from AI_Agent import AI_Agent
from tools import ConsolePrintTool, GetInfoTool
from g4f.Provider import Blackbox
from settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting the application")

async def main():
    # Создаем агента с базовым системным промптом
    provider = Blackbox
    model = "llama-3.1-8b"#"gemini-1.5-flash"#"mixtral-small-28b",
    agent = AI_Agent(
        provider=provider,
        model=model
    )
    
    # Регистрируем инструменты
    agent.register_tool(GetInfoTool())
    agent.register_tool(ConsolePrintTool())
    
    while True:
        user_input = input("Enter your query: ")
        result = await agent.run(user_input)
        print("Result: ", result)
    
if __name__ == "__main__":
    asyncio.run(main()) 