from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

@dataclass
class ToolParameter:
    """Description of the tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True

    def to_string(self) -> str:
        """Преобразовать параметр в строку."""
        required_str = "required" if self.required else "optional"
        return f"- {self.name} ({self.type}, {required_str}): {self.description}"


BASE_TOOL_PROMPT = """Tool: {name}
Description: {description}
Parameters: {parameters}
Returns: {returns}"""

class BaseTool(ABC):
    """Base class for all tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the tool."""
        pass
    
    @property
    def parameters(self) -> List[ToolParameter]:
        """Description of the parameters of the tool."""
        return []
    
    @property
    def returns(self) -> str:
        """Description of the returned values of the tool."""
        return "Any"
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute tool with given parameters."""
        pass
    
    def on_register(self, parent_agent):
        """Called when the tool is registered in the agent"""
        pass

    def to_string(self) -> str:
        """Convert tool information to string."""
        params_str = " ".join([param.to_string() for param in self.parameters])

        return BASE_TOOL_PROMPT.format(
            name=self.name,
            description=self.description,
            parameters=params_str,
            returns=self.returns
        )