# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Install: `uv pip install -e .`
- Run server: `uv run backlog-manager`
- Run tests: `python -m pytest tests/`
- Run single test: `python -m pytest tests/test_backlog_manager.py::test_name -v`

## Code Style Guidelines
- Python 3.12+ compatible code
- Use type hints for function parameters and return values
- Follow PEP 8 naming conventions (snake_case for functions/variables)
- Docstrings: Use Google-style formatting with Args/Returns sections
- Error handling: Use try/except blocks with specific error messages
- Imports: Group standard library, third-party, and local imports
- Enums for status values (TaskStatus, IssueStatus)
- Async/await for all MCP tool implementations
- Context management using FastMCP's Context objects
- JSON-based data structures for file storage