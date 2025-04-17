import json
import os
from pathlib import Path

def get_tasks_file_path(tasks_file: str) -> str:
    """
    Get the absolute path to the tasks file.
    
    Args:
        tasks_file: Relative or absolute path to the tasks file
        
    Returns:
        str: Absolute path to the tasks file
    """
    if os.path.isabs(tasks_file):
        return tasks_file
    
    return os.path.abspath(tasks_file)

def validate_directory(directory: str) -> bool:
    """
    Validate that a directory exists and is writable.
    
    Args:
        directory: Path to the directory
        
    Returns:
        bool: True if the directory is valid, False otherwise
    """
    try:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True)
        
        # Check if we can write to it
        test_file = path / ".test"
        test_file.touch()
        test_file.unlink()
        
        return True
    except Exception:
        return False