"""
Tasks API - Task and reminder management
"""

from fastmcp import FastMCP
from datetime import datetime
from typing import Annotated, Optional
import json
import logging

logger = logging.getLogger(__name__)


class TasksAPI:
    """Task management tools"""
    
    def __init__(self, mcp: FastMCP):
        """
        Initialize TasksAPI and register tools with the MCP instance.
        
        Args:
            mcp: FastMCP instance to register tools with
        """
        self.mcp = mcp
        self.tasks_store = {}  # In-memory task storage
        self._register_tools()
    
    def _register_tools(self):
        """Register all task-related tools with the MCP instance."""
        self.mcp.tool()(self.create_task)
        self.mcp.tool()(self.list_tasks)
        self.mcp.tool()(self.update_task)
        self.mcp.tool()(self.delete_task)
    
    def create_task(
        self,
        title: Annotated[str, "Task title or name"],
        description: Annotated[Optional[str], "Detailed description of the task"] = "",
        priority: Annotated[str, "Task priority: 'low', 'medium', or 'high'"] = "medium",
        due_date: Annotated[Optional[str], "Due date in YYYY-MM-DD format"] = None
    ) -> dict:
        """
        Create a new task or reminder.
        
        Tasks are stored in memory and will be lost when the server restarts.
        For production use, integrate with a database or task management system.
        
        Args:
            title: The task title (required)
            description: Detailed description (optional)
            priority: Priority level - "low", "medium", or "high"
            due_date: Due date in YYYY-MM-DD format (optional)
        
        Returns:
            Dictionary containing the created task details
        
        Example:
            >>> create_task("Buy groceries", "Milk, eggs, bread", "high", "2024-01-20")
            {
                "id": "task_1705323045.123",
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "priority": "high",
                "due_date": "2024-01-20",
                "status": "pending",
                "created_at": "2024-01-15T14:30:45.123456"
            }
        """
        task_id = f"task_{datetime.now().timestamp()}"
        
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Store task
        self.tasks_store[task_id] = task
        
        logger.info(f"Task created: {task_id} - {title}")
        
        return task
    
    def list_tasks(
        self,
        status: Annotated[Optional[str], "Filter by status: 'pending', 'in_progress', 'completed', or 'all'"] = "all",
        priority: Annotated[Optional[str], "Filter by priority: 'low', 'medium', 'high', or 'all'"] = "all"
    ) -> dict:
        """
        List all tasks with optional filtering.
        
        Args:
            status: Filter by status - "pending", "in_progress", "completed", or "all"
            priority: Filter by priority - "low", "medium", "high", or "all"
        
        Returns:
            Dictionary containing list of tasks and count
        
        Example:
            >>> list_tasks(status="pending", priority="high")
            {
                "tasks": [...],
                "count": 5,
                "filters": {"status": "pending", "priority": "high"}
            }
        """
        tasks = list(self.tasks_store.values())
        
        # Apply filters
        if status != "all":
            tasks = [t for t in tasks if t["status"] == status]
        
        if priority != "all":
            tasks = [t for t in tasks if t["priority"] == priority]
        
        # Sort by created_at (newest first)
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "tasks": tasks,
            "count": len(tasks),
            "filters": {
                "status": status,
                "priority": priority
            }
        }
    
    def update_task(
        self,
        task_id: Annotated[str, "Task ID to update"],
        status: Annotated[Optional[str], "New status: 'pending', 'in_progress', 'completed'"] = None,
        priority: Annotated[Optional[str], "New priority: 'low', 'medium', 'high'"] = None,
        description: Annotated[Optional[str], "New description"] = None
    ) -> dict:
        """
        Update an existing task.
        
        Args:
            task_id: ID of the task to update
            status: New status (optional)
            priority: New priority (optional)
            description: New description (optional)
        
        Returns:
            Updated task dictionary or error message
        
        Example:
            >>> update_task("task_123", status="completed")
            {
                "id": "task_123",
                "status": "completed",
                "updated_at": "2024-01-15T15:30:00.000000"
            }
        """
        if task_id not in self.tasks_store:
            return {
                "error": f"Task not found: {task_id}",
                "success": False
            }
        
        task = self.tasks_store[task_id]
        
        # Update fields
        if status is not None:
            task["status"] = status
        if priority is not None:
            task["priority"] = priority
        if description is not None:
            task["description"] = description
        
        task["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Task updated: {task_id}")
        
        return {
            "success": True,
            "task": task
        }
    
    def delete_task(
        self,
        task_id: Annotated[str, "Task ID to delete"]
    ) -> dict:
        """
        Delete a task.
        
        Args:
            task_id: ID of the task to delete
        
        Returns:
            Success status and message
        
        Example:
            >>> delete_task("task_123")
            {
                "success": True,
                "message": "Task deleted successfully",
                "task_id": "task_123"
            }
        """
        if task_id not in self.tasks_store:
            return {
                "error": f"Task not found: {task_id}",
                "success": False
            }
        
        task = self.tasks_store.pop(task_id)
        
        logger.info(f"Task deleted: {task_id}")
        
        return {
            "success": True,
            "message": "Task deleted successfully",
            "task_id": task_id,
            "deleted_task": task
        }

