from typing import List, Dict, Any, Optional

class AIClient:
    """Базовый класс для работы с LLM."""
    
    def __init__(self, model: str = None, provider: Any = None):
        self.model = model
        self.provider = provider
    
    async def generate_message(self, messages: List[Dict[str, str]]) -> str:
        """
        Генерирует ответ от модели на основе сообщений.
        
        Args:
            messages: Список сообщений в формате [{"role": "...", "content": "..."}]
            
        Returns:
            str: Ответ модели
        """
        raise NotImplementedError("Subclasses must implement generate_message")


class G4FClient(AIClient):
    """Клиент для работы с g4f."""
    
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