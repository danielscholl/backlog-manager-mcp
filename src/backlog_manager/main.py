from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
from enum import Enum
import asyncio
import json
import os
import uuid
from pathlib import Path

load_dotenv()

# Default file paths
DEFAULT_TASKS_FILE = "tasks.json"

# Task and Issue statuses
class TaskStatus(str, Enum):
    NEW = "New"
    IN_WORK = "InWork"
    DONE = "Done"

class IssueStatus(str, Enum):
    NEW = "New"
    IN_WORK = "InWork"
    DONE = "Done"

@dataclass
class BacklogContext:
    """Context for the Backlog Manager MCP server."""
    tasks_file: str
    active_issue: str = None

@asynccontextmanager
async def backlog_lifespan(server: FastMCP) -> AsyncIterator[BacklogContext]:
    """
    Manages the Backlog Manager lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        BacklogContext: The context containing the tasks file path
    """
    tasks_file = os.getenv("TASKS_FILE", DEFAULT_TASKS_FILE)
    
    try:
        yield BacklogContext(tasks_file=tasks_file)
    finally:
        pass

# Initialize FastMCP server
# Get port, defaulting to 8050 if not set or if empty
port_str = os.getenv("PORT")
port = int(port_str) if port_str and port_str.strip() else 8050

mcp = FastMCP(
    "backlog-manager",
    description="MCP server for managing issues and tasks with file-based storage",
    lifespan=backlog_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=port
)

def _load_tasks(file_path: str) -> dict:
    """
    Load tasks from a JSON file.
    
    Args:
        file_path: Path to the tasks file
        
    Returns:
        dict: Dictionary containing issues and tasks data
    """
    try:
        if not os.path.exists(file_path):
            return {"issues": {}}
        
        with open(file_path, "r") as f:
            data = json.load(f)
            
            # Ensure issues key exists
            if "issues" not in data:
                data = {"issues": {}}
            
            return data
    except Exception as e:
        print(f"Error loading tasks: {str(e)}")
        return {"issues": {}}

def _save_tasks(file_path: str, data: dict) -> None:
    """
    Save tasks to a JSON file.
    
    Args:
        file_path: Path to the tasks file
        data: Dictionary containing tasks data
    """
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving tasks: {str(e)}")

@mcp.tool()
async def create_issue(ctx: Context, name: str, description: str = "", status: str = IssueStatus.NEW) -> str:
    """Create a new issue for task management.
    
    This tool creates a new issue in the backlog manager. If the issue already
    exists, it will return an error.
    
    Args:
        ctx: The MCP server provided context
        name: The name of the issue to create
        description: A detailed description of the issue
        status: The status of the issue (New, InWork, or Done)
    """
    try:
        tasks_file = ctx.request_context.lifespan_context.tasks_file
        data = _load_tasks(tasks_file)
        
        if name in data["issues"]:
            return f"Error: Issue '{name}' already exists."
        
        # Validate status if provided
        if status not in [s.value for s in IssueStatus]:
            return f"Error: Invalid status '{status}'. Valid values are: {', '.join([s.value for s in IssueStatus])}"
        
        data["issues"][name] = {
            "description": description,
            "status": status,
            "tasks": {}
        }
        _save_tasks(tasks_file, data)
        
        # Set the created issue as active
        ctx.request_context.lifespan_context.active_issue = name
        
        return f"Successfully created issue: {name} with status: {status}"
    except Exception as e:
        return f"Error creating issue: {str(e)}"

@mcp.tool()
async def list_issues(ctx: Context) -> str:
    """List all available issues.
    
    This tool shows all issues in the backlog manager.
    
    Args:
        ctx: The MCP server provided context
    """
    try:
        tasks_file = ctx.request_context.lifespan_context.tasks_file
        data = _load_tasks(tasks_file)
        
        if not data["issues"]:
            return "No issues found. Use 'create_issue' to create a new issue."
        
        active_issue = ctx.request_context.lifespan_context.active_issue
        
        result = ["Available issues:"]
        for issue_name, issue_data in data["issues"].items():
            task_count = len(issue_data["tasks"])
            active_marker = " (active)" if issue_name == active_issue else ""
            description_preview = issue_data.get("description", "")[:30]
            if description_preview and len(issue_data.get("description", "")) > 30:
                description_preview += "..."
            
            # Handle missing status for backward compatibility
            status = issue_data.get("status", IssueStatus.NEW)
            
            result.append(f"- {issue_name}{active_marker}: Status: {status}, Tasks: {task_count}")
            if description_preview:
                result.append(f"  Description: {description_preview}")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error listing issues: {str(e)}"

@mcp.tool()
async def select_issue(ctx: Context, name: str) -> str:
    """Select an issue to work with.
    
    This tool sets the active issue for subsequent task operations.
    
    Args:
        ctx: The MCP server provided context
        name: The name of the issue to select
    """
    try:
        tasks_file = ctx.request_context.lifespan_context.tasks_file
        data = _load_tasks(tasks_file)
        
        if name not in data["issues"]:
            return f"Error: Issue '{name}' not found."
        
        ctx.request_context.lifespan_context.active_issue = name
        return f"Selected issue: {name}"
    except Exception as e:
        return f"Error selecting issue: {str(e)}"

@mcp.tool()
async def initialize_issue(ctx: Context, name: str, description: str = "", status: str = IssueStatus.NEW) -> str:
    """Initialize or reset an issue for task management.
    
    This tool creates a new issue or resets an existing one. It will create a tasks
    file with the provided issue name and an empty task list.
    
    Args:
        ctx: The MCP server provided context
        name: The name of the issue to initialize
        description: A detailed description of the issue
        status: The status of the issue (New, InWork, or Done)
    """
    try:
        tasks_file = ctx.request_context.lifespan_context.tasks_file
        data = _load_tasks(tasks_file)
        
        # Validate status if provided
        if status not in [s.value for s in IssueStatus]:
            return f"Error: Invalid status '{status}'. Valid values are: {', '.join([s.value for s in IssueStatus])}"
        
        # Clear existing tasks if issue exists
        data["issues"][name] = {
            "description": description,
            "status": status,
            "tasks": {}
        }
        
        _save_tasks(tasks_file, data)
        
        # Set this issue as active
        ctx.request_context.lifespan_context.active_issue = name
        
        return f"Successfully initialized issue: {name} with status: {status}"
    except Exception as e:
        return f"Error initializing issue: {str(e)}"

@mcp.tool()
async def add_task(ctx: Context, title: str, description: str = "") -> str:
    """Add a new task to the backlog.
    
    This tool adds a new task to the active issue backlog with a unique identifier.
    Tasks are created with the default 'New' status.
    
    Args:
        ctx: The MCP server provided context
        title: The title of the task (required)
        description: A detailed description of the task (optional)
    """
    try:
        tasks_file = ctx.request_context.lifespan_context.tasks_file
        active_issue = ctx.request_context.lifespan_context.active_issue
        
        if not active_issue:
            return "Error: No active issue. Please select an issue using 'select_issue' first."
        
        data = _load_tasks(tasks_file)
        
        if active_issue not in data["issues"]:
            return f"Error: Issue '{active_issue}' not found."
        
        task_id = str(uuid.uuid4())[:8]  # Generate a short unique ID
        
        data["issues"][active_issue]["tasks"][task_id] = {
            "title": title,
            "description": description,
            "status": TaskStatus.NEW
        }
        
        _save_tasks(tasks_file, data)
        return f"Successfully added task: {title} (ID: {task_id}) to issue '{active_issue}'"
    except Exception as e:
        return f"Error adding task: {str(e)}"

@mcp.tool()
async def list_tasks(ctx: Context, status: str = None) -> str:
    """List all tasks in the active issue backlog, optionally filtered by status.
    
    This tool shows all tasks in the active issue backlog. You can filter the tasks
    by providing a status value (New, InWork, or Done).
    
    Args:
        ctx: The MCP server provided context
        status: Optional status to filter tasks by (New, InWork, or Done)
    """
    try:
        tasks_file = ctx.request_context.lifespan_context.tasks_file
        active_issue = ctx.request_context.lifespan_context.active_issue
        
        if not active_issue:
            return "Error: No active issue. Please select an issue using 'select_issue' first."
        
        data = _load_tasks(tasks_file)
        
        if active_issue not in data["issues"]:
            return f"Error: Issue '{active_issue}' not found."
        
        issue_data = data["issues"][active_issue]
        issue_tasks = issue_data["tasks"]
        
        if len(issue_tasks) == 0:
            return f"No tasks found in issue '{active_issue}'."
        
        # Validate status if provided
        if status and status not in [s.value for s in TaskStatus]:
            return f"Error: Invalid status '{status}'. Valid values are: {', '.join([s.value for s in TaskStatus])}"
        
        # Build the task list
        result = [f"Tasks for issue: {active_issue}"]
        
        # Add issue description if available
        if issue_data.get("description"):
            result.append(f"Issue description: {issue_data['description']}")
        
        for task_id, task in issue_tasks.items():
            # Skip if filtering by status and this task doesn't match
            if status and task["status"] != status:
                continue
                
            result.append(f"\nID: {task_id}")
            result.append(f"Title: {task['title']}")
            result.append(f"Status: {task['status']}")
            
            if task["description"]:
                result.append(f"Description: {task['description']}")
        
        if len(result) == 1 or (len(result) == 2 and issue_data.get("description")):  # Only has the issue name and possibly description
            return f"No tasks found with status '{status}'" if status else "No tasks found"
            
        return "\n".join(result)
    except Exception as e:
        return f"Error listing tasks: {str(e)}"

@mcp.tool()
async def update_task_status(ctx: Context, task_id: str, status: str) -> str:
    """Update the status of a task in the active issue.
    
    This tool changes the status of an existing task. Valid status values are:
    New, InWork, and Done.
    
    Args:
        ctx: The MCP server provided context
        task_id: The ID of the task to update
        status: The new status (New, InWork, or Done)
    """
    try:
        tasks_file = ctx.request_context.lifespan_context.tasks_file
        active_issue = ctx.request_context.lifespan_context.active_issue
        
        if not active_issue:
            return "Error: No active issue. Please select an issue using 'select_issue' first."
        
        data = _load_tasks(tasks_file)
        
        if active_issue not in data["issues"]:
            return f"Error: Issue '{active_issue}' not found."
        
        issue_tasks = data["issues"][active_issue]["tasks"]
        
        if task_id not in issue_tasks:
            return f"Error: Task with ID '{task_id}' not found in issue '{active_issue}'."
        
        # Validate status
        if status not in [s.value for s in TaskStatus]:
            return f"Error: Invalid status '{status}'. Valid values are: {', '.join([s.value for s in TaskStatus])}"
        
        # Update task status
        old_status = issue_tasks[task_id]["status"]
        issue_tasks[task_id]["status"] = status
        _save_tasks(tasks_file, data)
        
        return f"Successfully updated task '{issue_tasks[task_id]['title']}' (ID: {task_id}) status from '{old_status}' to '{status}'."
    except Exception as e:
        return f"Error updating task: {str(e)}"


@mcp.tool()
async def update_issue_status(ctx: Context, name: str, status: str) -> str:
    """Update the status of an issue.
    
    This tool changes the status of an existing issue. Valid status values are:
    New, InWork, and Done.
    
    Args:
        ctx: The MCP server provided context
        name: The name of the issue to update
        status: The new status (New, InWork, or Done)
    """
    try:
        tasks_file = ctx.request_context.lifespan_context.tasks_file
        data = _load_tasks(tasks_file)
        
        if name not in data["issues"]:
            return f"Error: Issue '{name}' not found."
        
        # Validate status
        if status not in [s.value for s in IssueStatus]:
            return f"Error: Invalid status '{status}'. Valid values are: {', '.join([s.value for s in IssueStatus])}"
        
        # Update issue status
        old_status = data["issues"][name].get("status", IssueStatus.NEW)
        data["issues"][name]["status"] = status
        _save_tasks(tasks_file, data)
        
        return f"Successfully updated issue '{name}' status from '{old_status}' to '{status}'."
    except Exception as e:
        return f"Error updating issue: {str(e)}"

async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()

def run_cli():
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())