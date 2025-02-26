from AI_Agent import BaseTool, ToolParameter
from typing import List

class ConsolePrintTool(BaseTool):
    """Инструмент для вывода текста в консоль."""
    
    @property
    def name(self) -> str:
        return "console_print"
    
    @property
    def description(self) -> str:
        return "Выводит текст в консоль"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="text",
                type="string",
                description="Текст для вывода в консоль"
            )
        ]
    
    async def execute(self, text: str) -> None:
        print("ConsolePrintTool: ", text)
        return "Ok" 