from typing import List, Dict, Any, Optional

class AIClient:
    """Base class for working with LLM."""
    
    def __init__(self, model: str = None, provider: Any = None):
        self.model = model
        self.provider = provider
    
    async def generate_message(self, messages: List[Dict[str, str]]) -> str:
        """
        Generates an answer from the model based on messages.
        
        Args:
            messages: List of messages in the format [{"role": "...", "content": "..."}]
            
        Returns:
            str: Model answer
        """
        raise NotImplementedError("Subclasses must implement generate_message")


class G4FClient(AIClient):
    """Client for working with g4f."""
    
    def __init__(self, model: str, provider: Any):
        super().__init__(model, provider)
        from g4f.client import AsyncClient
        self.client = AsyncClient(provider=provider)
    
    async def generate_message(self, messages: List[Dict[str, str]]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content 