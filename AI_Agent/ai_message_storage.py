import json
from typing import Dict, List, Any, Union
from sqlalchemy.orm import Session

class AIMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

class AIMessageStorage:
    def __init__(self, max_size: int = 20, system_prompt: str = ""):
        self.messages: List[AIMessage] = []
        self.max_size = max_size
        self.system_prompt = system_prompt

        self.add_message("system", self.system_prompt)

    def update_system_prompt(self, new_prompt: str) -> None:
        """Updates system prompt and reinitializes the agent"""
        self.system_prompt = new_prompt
        self.messages[0].content = self.system_prompt

    def add_message(self, role: str, content: Union[str, Dict, List, Any]):
        # Convert content to string if it's not already a string
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)

        self.messages.append(AIMessage(role, content))

        # Remove the oldest message if the size exceeds the limit
        if len(self.messages) > self.max_size:
            self.messages.pop(1)

    def get_messages(self) -> List[AIMessage]:
        return self.messages
    
    def get_messages_as_dict(self) -> List[Dict[str, str]]:
        return [{"role": message.role, "content": message.content} for message in self.messages]
    
    def clear_messages(self):
        self.messages = self.messages[:1]
    
    def load_from_db(self, user_id: str, session: Session):
        pass

    def save_to_db(self, user_id: str, session: Session):
        pass
