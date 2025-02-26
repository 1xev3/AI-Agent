from AI_Agent import BaseTool
from typing import List

class GetInfoTool(BaseTool):
    """Инструмент для получения тестовой информации."""
    
    @property
    def name(self) -> str:
        return "get_info"
    
    @property
    def description(self) -> str:
        return "Возвращает какую-то информацию"
    
    async def execute(self) -> List[int]:
        return {"menu": {
            "id": "file",
            "value": "File",
            "popup": {
                "menuitem": [
                        {"value": "New", "onclick": "CreateNewDoc()"},
                        {"value": "Open", "onclick": "OpenDoc()"},
                        {"value": "Close", "onclick": "CloseDoc()"}
                    ]
                }
            }}