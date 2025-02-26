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