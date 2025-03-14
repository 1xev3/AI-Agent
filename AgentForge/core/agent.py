# Standard library imports
import json
import logging
from typing import Dict, List, Type, Any, Union

# Local imports
from .client import AIClient
from .message_storage import MessageStorage 
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
"""

class Agent:
    def __init__(
        self,
        agent_id: str,
        client: AIClient,
        message_storage: MessageStorage = None,
        tools: Dict[str, BaseTool] = None,
        who_am_i: str = "You are an AI assistant",
        max_iterations: int = 20,
    ):
        self.who_am_i = who_am_i
        self.tools: Dict[str, BaseTool] = {}
        self.client = client
        self.message_storage = message_storage or MessageStorage(max_size=20)
        self.max_iterations = max_iterations
        self.agent_id = agent_id

        self.update_system_prompt(self._create_system_prompt())

        if tools:
            for tool in tools:
                self.register_tool(tool)

    def get_id(self) -> str:
        """Returns the agent's ID."""
        return self.agent_id
    
    def set_id(self, new_id: str) -> None:
        """Sets the agent's ID."""
        self.agent_id = new_id

    def register_tool(self, tool: BaseTool) -> None:
        """Registers a new tool."""
        self.tools[tool.name] = tool
        tool._register_internal(self)
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

    def _create_all_tools_description(self) -> str:
        """Creates a description of available tools for the prompt."""
        tools_desc = []
        for tool in self.tools.values():
            tool_info = tool.to_string()
            tools_desc.append(tool_info)
        return "\n".join(tools_desc)
    
    def clear_memory(self) -> None:
        """Clears the agent's memory."""
        self.message_storage.clear_messages()
        
    def update_memory(self, role: str, content: Union[str, Dict, List, Any]) -> None:
        """Updates the agent's memory."""
        if content is None:  # Skip empty messages
            return
        self.message_storage.add_message(role, content)
        
    def _create_system_prompt(self) -> str:
        """Creates system prompt with tools description."""
        return SYSTEM_PROMPT_TEMPLATE.format(
            who_am_i=self.who_am_i,
            tools_description=self._create_all_tools_description()
        )
        
    async def _execute_tool_call(self, tool_call: Dict) -> Any:
        """Executes a single tool call."""
        tool_name, tool_params = next(iter(tool_call.items()))
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
            
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
                return "Maximum number of iterations exceeded"
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
                    return f"Error: bad answer from model: {response_text}"
                
            except Exception as e:
                logging.error(f"Error: {str(e)}")
                self.message_storage.add_message("user", f"Error: {str(e)}")
                raise e 