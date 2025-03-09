from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

@dataclass
class ToolParameter:
    """Описание параметра инструмента."""
    name: str
    type: str
    description: str

    def to_string(self) -> str:
        """Преобразовать параметр в строку."""
        return f"{self.name}: {self.type} | {self.description})"

BASE_TOOL_PROMPT = """Tool: {name}
Description: {description}
Parameters: {parameters}
Returns: {returns}"""

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
    
    @property
    def returns(self) -> str:
        """Описание возвращаемых значений инструмента."""
        return "Any"
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Выполнить инструмент с заданными параметрами."""
        pass

    def to_string(self) -> str:
        """Преобразовать информацию об инструменте в строку."""
        params_str = " ".join([param.to_string() for param in self.parameters])

        return BASE_TOOL_PROMPT.format(
            name=self.name,
            description=self.description,
            parameters=params_str,
            returns=self.returns
        )
    
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