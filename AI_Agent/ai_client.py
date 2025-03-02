
from g4f.client import AsyncClient

# Local imports
from .ai_message_storage import AIMessage

class AI_Client:
    def __init__(self, model: str, provider: str):
        self.model = model
        self.client = AsyncClient(
            provider=provider,
        )

    async def generate_message(self, messages: list[dict]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        return response.choices[0].message.content
