# Standard library imports
import logging
import uuid
from typing import Dict, List

# Third party imports
from sqlalchemy.orm import Session

# Local imports
from AI_Agent import BaseTool, ToolParameter, AI_Agent, AI_Client, AIMessageStorage
from database.db import with_session
from database.models import TodoItem

logger = logging.getLogger(__name__)

WHO_AM_I = """You are a TODO list management assistant. Always respond in User language!

For creating a todo:
1. Extract title and description from user request
2. Use create_todo tool with extracted data

For updating a todo:
1. First use get_all_todos to get list of all todos
2. Find todo whose title best matches user request
3. Use update_todo with ID of found todo and new data

For deleting a todo:
1. First use get_all_todos to get list of all todos
2. Find todo whose title best matches user request
3. Use delete_todo with ID of found todo

For viewing todos:
1. Use get_all_todos
2. Format todo list for easy reading"""



class CreateTodoTool(BaseTool):
    name = "create_todo"
    description = "Creates a new todo item"
    parameters = [
        ToolParameter(
            name="title",
            type="string",
            description="Title of the todo item"
        ),
        ToolParameter(
            name="description",
            type="string",
            description="Detailed description of the todo item"
        )
    ]
    returns = "Result of action"

    @with_session
    async def execute(self, title: str, description: str, session: Session) -> Dict:
        todo_id = f"todo_{uuid.uuid4().hex[:8]}"
        
        todo = TodoItem(
            id=todo_id,
            title=title,
            description=description
        )
        session.add(todo)
        logger.info(f"Todo created: {todo.id} - {todo.title}")
        
        return {
            "id": todo.id,
            "title": todo.title,
            "description": todo.description
        }

class UpdateTodoTool(BaseTool):
    name = "update_todo"
    description = "Updates an existing todo item"
    parameters = [
        ToolParameter(
            name="todo_id",
            type="string",
            description="ID of the todo to update"
        ),
        ToolParameter(
            name="title",
            type="string",
            description="New title of the todo item"
        ),
        ToolParameter(
            name="description",
            type="string",
            description="New description of the todo item"
        )
    ]
    returns = "Result of action"
    
    @with_session
    async def execute(self, todo_id: str, title: str, description: str, session: Session) -> Dict:
        todo = session.query(TodoItem).filter_by(id=todo_id).first()
        if todo:
            todo.title = title
            todo.description = description
            logger.info(f"Todo updated: {todo_id} - {todo.title}")
            return {
                "success": True,
                "message": f"Todo '{todo.title}' updated",
                "todo": {
                    "id": todo.id,
                    "title": todo.title,
                    "description": todo.description
                }
            }
        
        logger.info(f"Todo not found for update: {todo_id}")
        return {
            "success": False,
            "message": f"No todo found with ID {todo_id}"
        }

class DeleteTodoTool(BaseTool):
    name = "delete_todo"
    description = "Deletes a todo by its ID"
    parameters = [
        ToolParameter(
            name="todo_id",
            type="string",
            description="ID of the todo to delete"
        )
    ]
    returns = "Result of action"
    
    @with_session
    async def execute(self, todo_id: str, session: Session) -> Dict:
        todo = session.query(TodoItem).filter_by(id=todo_id).first()
        if todo:
            title = todo.title
            session.delete(todo)
            logger.info(f"Todo deleted: {todo_id} - {title}")
            return {
                "success": True,
                "message": f"Todo '{title}' deleted"
            }
        logger.info(f"Todo not found for delete: {todo_id}")
        return {
            "success": False,
            "message": f"No todo found with ID {todo_id}"
        }

class GetAllTodosTool(BaseTool):
    name = "get_all_todos"
    description = "Returns all existing todos"
    parameters = []
    returns = "List of todos"
    
    @with_session
    async def execute(self, session: Session) -> List[Dict]:
        todos = session.query(TodoItem).all()
        logger.info(f"Todos retrieved: {len(todos)}")
        return [{
            "id": t.id,
            "title": t.title,
            "description": t.description
        } for t in todos]

class TodoAgentTool(BaseTool):
    name = "todo_manager"
    parameters = [
        ToolParameter(
            name="request",
            type="string",
            description="Natural language request for managing todos"
        )
    ]
    description = """Manages TODO list using natural language commands"""
    returns = "Result of action"

    def __init__(self, client: AI_Client):        
        self.agent = AI_Agent(
            client=client,
            message_storage=AIMessageStorage(), #will be updated AI Agent
            who_am_i=WHO_AM_I
        )
        
        self.agent.register_tool(CreateTodoTool())
        self.agent.register_tool(UpdateTodoTool())
        self.agent.register_tool(DeleteTodoTool())
        self.agent.register_tool(GetAllTodosTool())
    
    async def execute(self, request: str) -> str:
        return await self.agent.run(request) 