import json
from typing import Dict, List, Any, Union
from sqlalchemy.orm import Session

class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class MessageStorage:
    def __init__(self, max_size: int = 20, system_prompt: str = ""):
        self.messages: List[Message] = []
        self.max_size = max_size
        self.system_prompt = system_prompt

        if system_prompt:
            self.add_message("system", self.system_prompt)

    def update_system_prompt(self, new_prompt: str) -> None:
        """Updates system prompt and reinitializes the agent"""
        self.system_prompt = new_prompt
        
        if not self.messages:
            self.add_message("system", self.system_prompt)
        else:
            self.messages[0].content = self.system_prompt

    def add_message(self, role: str, content: Union[str, Dict, List, Any]):
        # Convert content to string if it's not already a string
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)

        self.messages.append(Message(role, content))

        # Remove the oldest message if the size exceeds the limit
        if len(self.messages) > self.max_size:
            self.messages.pop(1)  # Keep system prompt

    def get_messages(self) -> List[Message]:
        return self.messages
    
    def get_messages_as_dict(self) -> List[Dict[str, str]]:
        return [{"role": message.role, "content": message.content} for message in self.messages]
    
    def clear_messages(self):
        if self.messages and self.messages[0].role == "system":
            self.messages = self.messages[:1]  # Keep only system message
        else:
            self.messages = []
            if self.system_prompt:
                self.add_message("system", self.system_prompt)

    def clone(self):
        msg_storage = MessageStorage(max_size=self.max_size, system_prompt=self.system_prompt)
        msg_storage.messages = self.messages.copy()
        return msg_storage
    
    def load_from_db(self, user_id: str, session: Session):
        # Implement loading from database
        pass

    def save_to_db(self, user_id: str, session: Session):
        # Implement saving to database
        pass 