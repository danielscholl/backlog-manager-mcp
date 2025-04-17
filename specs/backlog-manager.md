# Specification for Backlog Manager (MCP)
> We are building a MCP Server tool for a task management system with a file-based approach and focusing on core functionality.

## Overview

The Backlog Manager is an MCP server designed to help AI assistants and other clients track and manage issues and tasks. It provides a simple, file-based task management system with status tracking capabilities, built using Anthropic's MCP protocol to enable seamless integration with AI agents and other MCP-compatible clients.

## Implementation details

- First, READ ai_docs/* to understand a sample mcp server.
- Mirror the work done inside `of ai_docs/mcp-mem0.xml`. Here we have a complete example of how to build a mcp server. We also have a complete codebase structure that we want to replicate. With some slight tweaks - see `Codebase Structure` below.
- Be sure to use load_dotenv() in the tests.
- Don't mock any tests - run real commands and expect them to pass case insensitive.
- Document the usage of the MCP server in the README.md

## Codebase Structure

- Follow the codebase Structure provided in the mcp-mem0 sample.

## Core Tool Commands to Implement (MVP)

### Issue Management
- `create_issue` - Create a new issue with name, description, and optional status
- `list_issues` - Show all available issues with their status and task count
- `select_issue` - Set the active issue for subsequent task operations
- `initialize_issue` - Create or reset an issue (replacing any existing data)
- `update_issue_status` - Update the status of an existing issue

### Task Management
- `add_task` - Add a new task to the active issue
- `list_tasks` - List all tasks in the active issue (with optional status filtering)
- `update_task_status` - Update status of a task (New|InWork|Done)

## Server Configuration

- The server should support both SSE and stdio transport options through environment variables
- Configuration should be provided through environment variables with sensible defaults:
  - TRANSPORT: Either 'sse' or 'stdio' (defaults to SSE if not specified)
  - HOST: Host to bind to if using SSE transport (default: 0.0.0.0)
  - PORT: Port to listen on if using SSE transport (default: 8050)
  - TASKS_FILE: Path to the tasks file (default: tasks.json)

## Data Structure

- The task data should be stored in a JSON file with the following structure:
  ```json
  {
    "issues": {
      "issue_name": {
        "description": "string",
        "status": "string",
        "tasks": {
          "task_id": {
            "title": "string",
            "description": "string",
            "status": "string"
          }
        }
      }
    }
  }
  ```
- Issues are identified by name (e.g., "login-system", "dashboard-redesign")
- Each issue has a description explaining the problem or feature
- Each issue has a status (New, InWork, Done)
- Multiple issues can be managed simultaneously
- Task IDs should be generated as shorter unique identifiers (8 characters)
- Task statuses should be defined as an enum with values: "New", "InWork", "Done"

## Error Handling

- Tools should validate inputs and provide clear error messages
- Errors should be returned as descriptive string messages
- Common error scenarios to handle:
  - Issue not found
  - No active issue selected
  - Invalid status values
  - Duplicate issue names
  - Task not found
  - File access errors

## API Reference

### Issue Management Tools

| Tool | Description | Parameters | Returns |
|------|-------------|------------|---------|
| `create_issue` | Create a new issue | `name` (string), `description` (string, optional), `status` (string, optional) | Success or error message |
| `list_issues` | Show all available issues | None | Formatted list of issues |
| `select_issue` | Set the active issue | `name` (string) | Success or error message |
| `initialize_issue` | Create or reset an issue | `name` (string), `description` (string, optional), `status` (string, optional) | Success or error message |
| `update_issue_status` | Update issue status | `name` (string), `status` (string) | Success or error message |

### Task Management Tools

| Tool | Description | Parameters | Returns |
|------|-------------|------------|---------|
| `add_task` | Add task to active issue | `title` (string), `description` (string, optional) | Success or error message |
| `list_tasks` | List tasks in active issue | `status` (string, optional) | Formatted list of tasks |
| `update_task_status` | Update task status | `task_id` (string), `status` (string) | Success or error message |

## Common User Workflows

### Basic Workflow
1. Create a new issue
2. Add tasks to the issue
3. Update task status as work progresses
4. Mark the issue as done when all tasks are completed

### PRD to Backlog Workflow
1. Read a PRD document
2. Create issues for main components or features
3. Break down each issue into specific tasks
4. Review and organize the backlog

## MCP Integration Details

- Include a .mcp.json file for quick setup with MCP clients
- Document multiple ways to integrate with common MCP clients including:
  - SSE transport configuration
  - stdio transport configuration
  - Docker container integration
- Note that this is an MCP server without traditional CLI functionality (no --help flag)

## Future Enhancements

Potential future improvements for consideration:
- Support for task priorities
- Task dependencies tracking
- Deadline/due date management
- Assignee tracking
- Labels and categories for issues
- Export/import functionality
- Metrics and reporting

## Validation (close the loop)

- Run `uv run pytest <path_to_test>` to validate the tests are passing - do this iteratively as you build out the tests.
- After code is written, run `uv run pytest` to validate all tests are passing.
- To validate the server, start it with `uv run backlog-manager` and connect with an MCP client
- Success criteria:
  - All tests pass
  - Server starts correctly with both transport options
  - All tools function as expected with valid input
  - Error handling works correctly with invalid input
  - JSON data structure maintains integrity