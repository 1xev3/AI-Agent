import json
from typing import Dict, List, Type, Optional, Any, Union
from g4f.client import AsyncClient
from .tool_base import BaseTool
import logging
import pprint

class AI_Agent:
    def __init__(
        self,
        model: str,
        provider,
        system_prompt: str = "",
        memory_size: int = 20,
        max_iterations: int = 20
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.provider = provider
        self.tools: Dict[str, BaseTool] = {}
        self.memory: List[Dict[str, str]] = []
        self.memory_size = memory_size
        self.client = AsyncClient(
            provider=self.provider,
        )
        self.max_iterations = max_iterations

    def update_system_prompt(self, new_prompt: str) -> None:
        """Updates system prompt and reinitializes the agent"""
        self.system_prompt = new_prompt
        self.init()

    def init(self):
        """Initializes or reinitializes the agent with current system prompt"""
        self.clear_memory()
        self.update_memory("system", self._create_system_prompt())

    def register_tool(self, tool_class: Type[BaseTool]) -> None:
        """Регистрирует новый инструмент."""
        tool = tool_class
        self.tools[tool.name] = tool
        self.init()
        
    def _create_tool_description(self) -> str:
        """Создает описание доступных инструментов для промпта."""
        tools_desc = []
        for tool in self.tools.values():
            tool_info = tool.to_dict()
            desc = [
                f"Tool: {tool_info['name']}",
                f"Description: {tool_info['description']}"
            ]
            
            if tool_info['parameters']:
                desc.append("Parameters:")
                for param in tool_info['parameters']:
                    required = "required" if param['required'] else "optional"
                    desc.append(f"  - {param['name']} ({param['type']}, {required}): {param['description']}")
            
            tools_desc.append("\n".join(desc))
        return "\n\n".join(tools_desc)
    
    def clear_memory(self) -> None:
        """Очищает память агента."""
        self.memory = []
        
    def update_memory(self, role: str, content: Union[str, Dict, List, Any]) -> None:
        """Обновляет память агента."""
        if content is None:  # Пропускаем пустые сообщения
            return
            
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
        self.memory.append({"role": role, "content": content})
        if len(self.memory) > self.memory_size:
            self.memory.pop(1) # Удаляем сообщение после сообщения системы

        # logging.debug(f"\n\Добавлено в память\nRole: {role} \nContent: { pprint.pformat(content)}\n\n")
            
    def _create_messages(self, user_input: str) -> List[Dict[str, str]]:
        """Создает список сообщений для отправки модели."""
        
        messages = []
        messages.extend(self.memory)
        if user_input != None:
            messages.append({"role": "user", "content": user_input})
        return messages
        
    def _create_system_prompt(self) -> str:
        """Создает системный промпт с описанием инструментов."""
        tools_desc = self._create_tool_description()
        return f"""{self.system_prompt}
You are an AI assistant with access to the following tools:
## Tools:
{tools_desc}

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
Tool results are stored in memory in the format {{"tool": "tool_name", "result": value}}
Always respond in User language!"""
        
    async def _execute_tool_call(self, tool_call: Dict) -> Any:
        """Выполняет один вызов инструмента."""
        # Получаем первую (и единственную) пару ключ-значение из словаря
        tool_name, tool_params = next(iter(tool_call.items()))
        
        if tool_name not in self.tools:
            raise ValueError(f"Инструмент {tool_name} не найден")
            
        tool = self.tools[tool_name]
        result = await tool.execute(**tool_params)
        self.update_memory("user", {
            "tool": tool_name,
            "result": result
        })
        return result
        
    async def run(self, user_input: str = None) -> str:
        """Запускает агента с заданным запросом."""
        
        iteration_count = 0
        while True:
            if iteration_count >= self.max_iterations:
                return "Превышено максимальное количество итераций выполнения"
                
            iteration_count += 1
            
            messages = self._create_messages(user_input)
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
            except Exception as e:
                logging.error(f"Ошибка при запросе к API: {str(e)}")
                return f"Ошибка при запросе к API: {str(e)}"
            
            response_text = response.choices[0].message.content
            if user_input != None:
                self.update_memory("user", user_input)
            if response_text != None:
                self.update_memory("assistant", response_text)
            
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
                return f"Ошибка: неверный формат ответа от модели: {response_text}"
            except Exception as e:
                logging.error(f"Ошибка при выполнении: {str(e)}")
                self.update_memory("user", f"Ошибка при выполнении: {str(e)}")
                raise e
                return f"Ошибка при выполнении: {str(e)}" 