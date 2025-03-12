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
