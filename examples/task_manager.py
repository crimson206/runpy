#!/usr/bin/env python3
"""
Task Manager Example - Pydantic Models with Runpy

This example demonstrates how to use Pydantic models with Runpy for
structured data input and validation.
"""

from runpycli import Runpy
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# Create Runpy instance
cli = Runpy(name="tasks", version="2.0.0")

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(BaseModel):
    """Task model with validation"""
    title: str = Field(..., min_length=1, max_length=100, description="Task title")
    description: Optional[str] = Field(None, max_length=500, description="Task description")
    priority: Priority = Field(Priority.MEDIUM, description="Task priority level")
    due_date: Optional[datetime] = Field(None, description="Due date and time")
    tags: List[str] = Field(default_factory=list, description="List of tags")
    completed: bool = Field(False, description="Whether task is completed")

class TaskFilter(BaseModel):
    """Filter criteria for tasks"""
    priority: Optional[Priority] = Field(None, description="Filter by priority")
    tag: Optional[str] = Field(None, description="Filter by tag")
    completed: Optional[bool] = Field(None, description="Filter by completion status")

# In-memory task storage (in real app, this would be a database)
tasks_db: List[dict] = []
next_id = 1

@cli.register
def add_task(task: Task) -> dict:
    """Add a new task to the task list
    
    Creates a new task with the provided details including title, description,
    priority, due date, and tags. The task is automatically assigned a unique ID.
    
    Args:
        task: Task object containing all task details
        
    Returns:
        Dictionary with status, message, and the created task
        
    Example:
        tasks add-task --task '{"title": "Buy groceries", "priority": "high"}'
    """
    global next_id
    
    task_dict = task.model_dump()
    task_dict["id"] = next_id
    task_dict["created_at"] = datetime.now().isoformat()
    
    tasks_db.append(task_dict)
    next_id += 1
    
    return {
        "status": "success",
        "message": f"Task '{task.title}' added successfully",
        "task": task_dict
    }

@cli.register
def list_tasks(filters: Optional[TaskFilter] = None) -> dict:
    """List all tasks with optional filtering"""
    filtered_tasks = tasks_db.copy()
    
    if filters:
        if filters.priority:
            filtered_tasks = [t for t in filtered_tasks if t.get("priority") == filters.priority.value]
        if filters.tag:
            filtered_tasks = [t for t in filtered_tasks if filters.tag in t.get("tags", [])]
        if filters.completed is not None:
            filtered_tasks = [t for t in filtered_tasks if t.get("completed") == filters.completed]
    
    return {
        "total_tasks": len(tasks_db),
        "filtered_tasks": len(filtered_tasks),
        "tasks": filtered_tasks
    }

@cli.register
def complete_task(task_id: int) -> dict:
    """Mark a task as completed"""
    for task in tasks_db:
        if task["id"] == task_id:
            task["completed"] = True
            task["completed_at"] = datetime.now().isoformat()
            return {
                "status": "success",
                "message": f"Task {task_id} marked as completed",
                "task": task
            }
    
    return {
        "status": "error",
        "message": f"Task with ID {task_id} not found"
    }

@cli.register
def delete_task(task_id: int) -> dict:
    """Delete a task by ID"""
    global tasks_db
    
    for i, task in enumerate(tasks_db):
        if task["id"] == task_id:
            deleted_task = tasks_db.pop(i)
            return {
                "status": "success",
                "message": f"Task '{deleted_task['title']}' deleted successfully",
                "deleted_task": deleted_task
            }
    
    return {
        "status": "error",
        "message": f"Task with ID {task_id} not found"
    }

@cli.register
def get_stats() -> dict:
    """Get task statistics"""
    total = len(tasks_db)
    completed = len([t for t in tasks_db if t.get("completed", False)])
    pending = total - completed
    
    priority_counts = {}
    for priority in Priority:
        priority_counts[priority.value] = len([t for t in tasks_db if t.get("priority") == priority.value])
    
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "completion_rate": round((completed / total * 100) if total > 0 else 0, 2),
        "priority_breakdown": priority_counts
    }

if __name__ == "__main__":
    cli.app()