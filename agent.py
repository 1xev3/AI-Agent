import json
from typing import Dict, List, Type, Optional, Any, Union
from g4f.client import AsyncClient
from tools import BaseTool
import logging
import pprint

class Agent:
    def __init__(
        self,
        model: str,
        provider,
        system_prompt: str = "",
        memory_size: int = 20
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
        
    def register_tool(self, tool_class: Type[BaseTool]) -> None:
        """Регистрирует новый инструмент."""
        tool = tool_class()
        self.tools[tool.name] = tool
        
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
    
    def _clear_memory(self) -> None:
        """Очищает память агента."""
        self.memory = []
        
    def _update_memory(self, role: str, content: Union[str, Dict, List, Any]) -> None:
        """Обновляет память агента."""
        if content is None:  # Пропускаем пустые сообщения
            return
            
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
        self.memory.append({"role": role, "content": content})
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)

        logging.debug(f"\n\Добавлено в память\nRole: {role} \nContent: { pprint.pformat(content)}\n\n")
            
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
Ты - AI ассистент, который может использовать предоставленные инструменты для выполнения задач. 
Анализируй запрос пользователя и выбирай подходящий инструмент.
Поддерживай контекст разговора и используй результаты предыдущих вызовов из истории.

Доступные инструменты:
{tools_desc}

У тебя есть два варианта ответа:

1. Если нужно выполнить инструменты:
{{
    "actions": [
        {{
            "tool": "название_инструмента",
            // Если у инструмента есть параметры
            "params": {{
                "параметр1": "значение1",
                ...
            }}
        }},
        ...
    ],
    "thoughts": "Объясни свои мысли и план действий"
}}

2. Если задача выполнена и нужно вернуть результат:
{{
    "final_answer": "Твой ответ пользователю",
}}

Результаты всех вызовов инструментов сохраняются в твоей памяти в формате:
{{"tool": "название_инструмента", "result": значение}}

Используй эти результаты для принятия решений и формирования параметров следующих вызовов."""
        
    async def _execute_tool_call(self, tool_call: Dict) -> Any:
        """Выполняет один вызов инструмента."""
        tool_name = tool_call["tool"]
        tool_params = tool_call.get("params", {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Инструмент {tool_name} не найден")
            
        tool = self.tools[tool_name]
        result = await tool.execute(**tool_params)
        # Сохраняем результат выполнения инструмента в память
        self._update_memory("user", {
            "tool": tool_name,
            "result": result
        })
        return result
        
    async def run(self, user_input: str = None) -> str:
        """Запускает агента с заданным запросом."""

        self._clear_memory()
        self._update_memory("system", self._create_system_prompt())
        
        while True:
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
                self._update_memory("user", user_input)
            if response_text != None:
                self._update_memory("assistant", response_text)
            
            try:
                decision = json.loads(response_text)
                
                # Если есть финальный ответ, возвращаем его
                if "final_answer" in decision:
                    return f"{decision['final_answer']}"
                
                # Иначе выполняем инструменты
                if "actions" in decision:

                    for tool_call in decision["actions"]:
                        await self._execute_tool_call(tool_call)
                    
                    # Продолжаем цикл с новым контекстом
                    user_input = None #"Продолжи выполнение задачи с учетом полученных результатов."
                    continue
                    
            except json.JSONDecodeError:
                return f"Ошибка: неверный формат ответа от модели: {response_text}"
            except Exception as e:
                logging.error(f"Ошибка при выполнении: {str(e)}")
                return f"Ошибка при выполнении: {str(e)}" 