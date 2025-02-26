import asyncio
from agent import Agent
from tools import ConsolePrintTool, GetInfoTool
from g4f.Provider import Blackbox
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
    # Создаем агента с базовым системным промптом
    agent = Agent(
        provider=Blackbox,
        model="mixtral-small-28b",
    )
    
    # Регистрируем инструменты
    agent.register_tool(GetInfoTool)
    agent.register_tool(ConsolePrintTool)
    
    # Пример использования с несколькими запросами
    queries = [
        "Получи информацию, выведи всю информацию через зяпятую, а затем проанализируй - если первое число больше 0, выведи 'Число положительное'",
        "Получи информацию и посчитай сумму всех чисел. Не выводи в консоль.",
    ]
    
    for query in queries:
        result = await agent.run(query)
        print("Result: ", result)
    
if __name__ == "__main__":
    asyncio.run(main()) 