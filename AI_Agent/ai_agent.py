# Standard library imports
import json
import logging
from typing import Dict, List, Type, Any, Union

# Local imports
from .ai_client import AI_Client
from .ai_message_storage import AIMessageStorage 
from .tool_base import BaseTool

# System prompt template
SYSTEM_PROMPT_TEMPLATE = """Always respond in User language!
{who_am_i}
You have access to the following tools:
## Tools:
{tools_description}

## Rules:
To use tools, respond in JSON format (only one main JSON object):
{{
    "actions": [
        {{"tool_name": {{"param1": "value1", "param2": "value2"}}}},
        {{"another_tool": {{"param": "value"}}}}
    ],
    "thoughts": "Brief explanation of your actions"
}}
To use final answer, respond:
{{
    "final_answer": "your text"
}}
Do not respond with both actions and final_answer at the same time!
If there are no more actions, do not add actions
Tool results are stored in memory in the format {{"tool": "tool_name", "result": value}}"""

class AI_Agent:
    def __init__(
        self,
        client: AI_Client,
        message_storage: AIMessageStorage,
        who_am_i: str = "You are an AI assistant",
        max_iterations: int = 20
    ):
        self.who_am_i = who_am_i
        self.tools: Dict[str, BaseTool] = {}
        self.client = client
        self.message_storage = message_storage or AIMessageStorage(max_size=20)
        self.max_iterations = max_iterations

        self.update_system_prompt(self._create_system_prompt())


    def register_tool(self, tool_class: Type[BaseTool]) -> None:
        """Регистрирует новый инструмент."""
        tool = tool_class
        self.tools[tool.name] = tool
        self.update_system_prompt(self._create_system_prompt())

    def update_who_am_i(self, new_prompt: str) -> None:
        """Updates who am i prompt and reinitializes the agent"""
        self.who_am_i = new_prompt
        self.update_system_prompt(self._create_system_prompt())

    def clear_messages(self) -> None:
        """Clears all messages from the message storage"""
        self.message_storage.clear_messages()

    def update_system_prompt(self, new_prompt: str) -> None:
        """Updates system prompt and reinitializes the agent"""
        self.message_storage.update_system_prompt(new_prompt)

    def _create_tool_description(self) -> str:
        """Создает описание доступных инструментов для промпта."""
        tools_desc = []
        for tool in self.tools.values():
            tool_info = tool.to_string()
            tools_desc.append(tool_info)
        return "\n".join(tools_desc)
    
    def clear_memory(self) -> None:
        """Очищает память агента."""
        self.message_storage.clear_messages()
        
    def update_memory(self, role: str, content: Union[str, Dict, List, Any]) -> None:
        """Обновляет память агента."""
        if content is None:  # Пропускаем пустые сообщения
            return
        self.message_storage.add_message(role, content)
        
    def _create_system_prompt(self) -> str:
        """Creates system prompt with tools description."""
        return SYSTEM_PROMPT_TEMPLATE.format(
            who_am_i=self.who_am_i,
            tools_description=self._create_tool_description()
        )
        
    async def _execute_tool_call(self, tool_call: Dict) -> Any:
        """Выполняет один вызов инструмента."""
        # Получаем первую (и единственную) пару ключ-значение из словаря
        tool_name, tool_params = next(iter(tool_call.items()))
        
        if tool_name not in self.tools:
            raise ValueError(f"Инструмент {tool_name} не найден")
            
        tool = self.tools[tool_name]
        result = await tool.execute(**tool_params)
        self.message_storage.add_message("user", {
            "tool": tool_name,
            "result": result
        })
        return result
        
    async def run(self, user_input: str = None) -> str:
        """Launches agent with given request."""
        
        iteration_count = 0
        while True:
            if iteration_count >= self.max_iterations:
                return "Превышено максимальное количество итераций выполнения"
            iteration_count += 1
            
            # Add user input only once at the beginning of iteration
            if user_input is not None:
                self.message_storage.add_message("user", user_input)
                
            messages = self.message_storage.get_messages_as_dict()
            try:
                response_text = await self.client.generate_message(messages)
                
                # Add assistant response if it exists
                if response_text:
                    self.message_storage.add_message("assistant", response_text)
            
                try:
                    if not response_text.strip().startswith('{'):
                        decision = {"final_answer": response_text}
                    else:
                        cleaned_response = response_text.strip().strip('"')
                        decision = json.loads(cleaned_response)
                    
                    if "final_answer" in decision:
                        return decision['final_answer']
                    
                    if "actions" in decision:
                        for tool_call in decision["actions"]:
                            await self._execute_tool_call(tool_call)
                        user_input = None
                        continue
                        
                except json.JSONDecodeError:
                    self.message_storage.add_message("user", f"ERROR: Bad answer from AI Model: {response_text}")
                    return f"Ошибка: неверный формат ответа от модели: {response_text}"
                
            except Exception as e:
                logging.error(f"Ошибка при выполнении: {str(e)}")
                self.message_storage.add_message("user", f"Error: {str(e)}")
                raise e
                return f"Ошибка при выполнении: {str(e)}" 