import asyncio
from agent import Agent
from tools import ConsolePrintTool, GetInfoTool
from g4f.Provider import Blackbox
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Создаем агента с базовым системным промптом
    agent = Agent(
        provider=Blackbox,
        model="gemini-1.5-flash"#"mixtral-small-28b",
    )
    
    # Регистрируем инструменты
    agent.register_tool(GetInfoTool)
    agent.register_tool(ConsolePrintTool)
    
    
    while True:
        user_input = input("Enter your query: ")
        result = await agent.run(user_input)
        print("Result: ", result)
    
if __name__ == "__main__":
    asyncio.run(main()) 