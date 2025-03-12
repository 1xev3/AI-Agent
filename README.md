# 🤖 Agent Framework

A flexible framework for building AI agents with tools and database support. This framework allows you to create AI assistants that can use various tools and maintain conversation history.

## Content
- [Features](#features)
- [Installation](#installation)
- [Architecture](#architecture)
- [Creating Custom Tools](#creating-custom-tools)
- [Using the Framework](#using-the-framework)

## Features

- 🤖 Modular agent architecture
- 🛠 Extensible tool system
- 💾 Database integration for persistence
- 📝 Message history management
- ⚡️ Async support
- 🔌 Pluggable LLM providers
- 🔄 Context management (TODO)

## Installation

```bash
pip install -r requirements.txt
```

## Architecture

The framework consists of several core components:

- **Agent**: Main class that coordinates tools and message handling
- **Tools**: Modular components that provide specific functionality
- **Message Storage**: Manages conversation history
- **Database**: Handles persistence of data
- **LLM Client**: Interface for language model providers

## Creating Custom Tools

You can create custom tools by inheriting from `BaseTool`:

```python
class CustomTool(BaseTool):
    name = "custom_tool"
    description = "Description of what the tool does"
    parameters = [
        ToolParameter(
            name="param1",
            type="string",
            description="Parameter description"
        )
    ]
    async def execute(self, kwargs) -> Any:
        # Tool implementation
        pass
```

## Using the Framework

Here's a basic example of how to use the framework:

```python
import asyncio
import logging
from datetime import datetime

from settings import settings

# Import the framework
from AgentForge import Agent, G4FClient, MessageStorage, db
from AgentForge.tools import ReminderAgentTool, TodoAgentTool, SearchAgentTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Initialize the database
    db.init_db(settings.DATABASE_URL)
    
    # Create a client for working with LLM
    from g4f.Provider import Blackbox
    client = G4FClient(model="llama-3.1-8b", provider=Blackbox)
    
    # Create a message storage
    message_storage = MessageStorage(max_size=20)
    
    # Create an agent
    agent = Agent(
        client=client,
        message_storage=message_storage,
        who_am_i=f"You are an AI assistant. Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        tools=[
            ReminderAgentTool(), 
            TodoAgentTool(), 
            SearchAgentTool()
        ]
    )
    
    # Start the agent
    while True:
        user_input = input("Enter your request (quit to exit): ")
        if user_input.lower() in ["exit", "quit", "выход"]:
            break
            
        # Update the time in the system prompt
        agent.update_who_am_i(f"You are an AI assistant. Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Start the agent
        result = await agent.run(user_input)
        print(f"AI Answer:\n{result}")

if __name__ == "__main__":
    asyncio.run(main())
```