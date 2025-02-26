from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

@dataclass
class ToolParameter:
    """Описание параметра инструмента."""
    name: str
    type: str
    description: str
    required: bool = True

class BaseTool(ABC):
    """Базовый класс для всех инструментов."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Название инструмента."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Описание инструмента."""
        pass
    
    @property
    def parameters(self) -> List[ToolParameter]:
        """Описание параметров инструмента."""
        return []
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Выполнить инструмент с заданными параметрами."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать информацию об инструменте в словарь."""
        params_dict = []
        for param in self.parameters:
            params_dict.append({
                "name": param.name,
                "type": param.type,
                "description": param.description,
                "required": param.required
            })
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": params_dict
        }

class GetInfoTool(BaseTool):
    """Инструмент для получения тестовой информации."""
    
    @property
    def name(self) -> str:
        return "get_info"
    
    @property
    def description(self) -> str:
        return "Возвращает тестовый массив чисел [1,2,3]"
    
    async def execute(self) -> List[int]:
        return [1, 2, 3]

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
        return None 