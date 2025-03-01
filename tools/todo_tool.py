from datetime import datetime
import uuid
from typing import Dict, List
from sqlalchemy import Column, String
from sqlalchemy.orm import Session
from AI_Agent import BaseTool, ToolParameter, AI_Agent
from database.db import Base, with_session
import logging

logger = logging.getLogger(__name__)

class TodoItem(Base):
    __tablename__ = 'todos'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)

class CreateTodoTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_todo"
    
    @property
    def description(self) -> str:
        return "Creates a new todo item"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
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
    @property
    def name(self) -> str:
        return "update_todo"
    
    @property
    def description(self) -> str:
        return "Updates an existing todo item"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
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
    @property
    def name(self) -> str:
        return "delete_todo"
    
    @property
    def description(self) -> str:
        return "Deletes a todo by its ID"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="todo_id",
                type="string",
                description="ID of the todo to delete"
            )
        ]
    
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
    @property
    def name(self) -> str:
        return "get_all_todos"
    
    @property
    def description(self) -> str:
        return "Returns all existing todos"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return []
    
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
    def __init__(self, model: str, provider: str):
        self.base_system_prompt = """You are a TODO list management assistant. Always respond in User language!

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
2. Format todo list for easy reading

Always confirm operation result to user."""
        
        self.agent = AI_Agent(
            model=model,
            provider=provider,
            system_prompt=self.base_system_prompt,
            memory_size=20
        )
        
        self.agent.register_tool(CreateTodoTool())
        self.agent.register_tool(UpdateTodoTool())
        self.agent.register_tool(DeleteTodoTool())
        self.agent.register_tool(GetAllTodosTool())
        self.agent.init()

    @property
    def name(self) -> str:
        return "todo_manager"
    
    @property
    def description(self) -> str:
        return """Manages TODO list using natural language commands. Examples:
        - "Create a new task to buy groceries"
        - "Add a todo about calling mom tomorrow"
        - "Update the grocery task"
        - "Delete the task about calling mom"
        - "Show all my todos"
        - "What tasks do I have?" """
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="request",
                type="string",
                description="Natural language request for managing todos"
            )
        ]
    
    async def execute(self, request: str) -> str:
        return await self.agent.run(request) 