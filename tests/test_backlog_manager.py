import pytest
import os
import json
import tempfile
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to the path so we can import the backlog_manager package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from backlog_manager.main import (
    BacklogContext, 
    initialize_issue, 
    add_task, 
    list_tasks, 
    update_task_status
)

load_dotenv()

class MockContext:
    def __init__(self, tasks_file):
        self.request_context = MockRequestContext(tasks_file)

class MockRequestContext:
    def __init__(self, tasks_file):
        self.lifespan_context = BacklogContext(tasks_file=tasks_file)

@pytest.fixture
def temp_tasks_file():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        yield f.name
    # Clean up the file after the test
    os.unlink(f.name)

@pytest.mark.asyncio
async def test_initialize_issue(temp_tasks_file):
    ctx = MockContext(temp_tasks_file)
    result = await initialize_issue(ctx, "Test Issue", "This is a test issue description")
    
    assert "Successfully initialized issue: Test Issue" in result
    
    # Verify the file was created with the right content
    with open(temp_tasks_file, "r") as f:
        data = json.load(f)
    
    assert "issues" in data
    assert "Test Issue" in data["issues"]
    assert data["issues"]["Test Issue"]["description"] == "This is a test issue description"
    assert data["issues"]["Test Issue"]["tasks"] == {}

@pytest.mark.asyncio
async def test_add_task(temp_tasks_file):
    ctx = MockContext(temp_tasks_file)
    
    # First, initialize an issue
    await initialize_issue(ctx, "Test Issue", "This is a test issue")
    
    # Then add a task
    result = await add_task(ctx, "Test Task", "This is a test task")
    
    assert "Successfully added task: Test Task" in result
    
    # Verify the task was added
    with open(temp_tasks_file, "r") as f:
        data = json.load(f)
    
    assert "Test Issue" in data["issues"]
    assert len(data["issues"]["Test Issue"]["tasks"]) == 1
    
    # Get the task ID from the tasks
    task_id = list(data["issues"]["Test Issue"]["tasks"].keys())[0]
    task = data["issues"]["Test Issue"]["tasks"][task_id]
    
    assert task["title"] == "Test Task"
    assert task["description"] == "This is a test task"
    assert task["status"] == "New"

@pytest.mark.asyncio
async def test_list_tasks(temp_tasks_file):
    ctx = MockContext(temp_tasks_file)
    
    # Initialize issue and add tasks
    await initialize_issue(ctx, "Test Issue", "This is a test issue")
    await add_task(ctx, "Task 1", "Description 1")
    await add_task(ctx, "Task 2", "Description 2")
    
    # List all tasks
    result = await list_tasks(ctx)
    
    assert "Tasks for issue: Test Issue" in result
    assert "Issue description: This is a test issue" in result
    assert "Task 1" in result
    assert "Description 1" in result
    assert "Task 2" in result
    assert "Description 2" in result

@pytest.mark.asyncio
async def test_update_task_status(temp_tasks_file):
    ctx = MockContext(temp_tasks_file)
    
    # Initialize issue and add a task
    await initialize_issue(ctx, "Test Issue", "This is a test issue")
    await add_task(ctx, "Test Task", "This is a test task")
    
    # Get the task ID
    with open(temp_tasks_file, "r") as f:
        data = json.load(f)
    
    task_id = list(data["issues"]["Test Issue"]["tasks"].keys())[0]
    
    # Update the task status
    result = await update_task_status(ctx, task_id, "InWork")
    
    assert "Successfully updated task" in result
    assert "from 'New' to 'InWork'" in result
    
    # Verify the status was updated
    with open(temp_tasks_file, "r") as f:
        data = json.load(f)
    
    assert data["issues"]["Test Issue"]["tasks"][task_id]["status"] == "InWork"

@pytest.mark.asyncio
async def test_list_tasks_with_status_filter(temp_tasks_file):
    ctx = MockContext(temp_tasks_file)
    
    # Initialize issue and add tasks with different statuses
    await initialize_issue(ctx, "Test Issue", "This is a test issue")
    await add_task(ctx, "Task 1", "Description 1")
    await add_task(ctx, "Task 2", "Description 2")
    
    # Get task IDs
    with open(temp_tasks_file, "r") as f:
        data = json.load(f)
    
    task_ids = list(data["issues"]["Test Issue"]["tasks"].keys())
    
    # Update one task status
    await update_task_status(ctx, task_ids[0], "InWork")
    
    # List tasks with status filter
    result = await list_tasks(ctx, status="InWork")
    
    assert "Tasks for issue: Test Issue" in result
    assert "Task 1" in result
    assert "Task 2" not in result

@pytest.mark.asyncio
async def test_invalid_status(temp_tasks_file):
    ctx = MockContext(temp_tasks_file)
    
    # Initialize issue and add a task
    await initialize_issue(ctx, "Test Issue", "This is a test issue")
    await add_task(ctx, "Test Task", "This is a test task")
    
    # Get the task ID
    with open(temp_tasks_file, "r") as f:
        data = json.load(f)
    
    task_id = list(data["issues"]["Test Issue"]["tasks"].keys())[0]
    
    # Try to update with an invalid status
    result = await update_task_status(ctx, task_id, "Invalid")
    
    assert "Error: Invalid status" in result