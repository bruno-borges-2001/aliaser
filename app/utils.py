"""
Utility functions for the aliaser tool.

This module contains helper functions for file operations,
command validation, and path handling.
"""

from typing import Optional
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import platform


def is_command_in_path(command: str) -> bool:
    """
    Check if a command exists in the system PATH.

    Args:
        command (str): The command to check

    Returns:
        bool: True if the command exists in PATH
    """
    # Different approach based on the platform
    if platform.system() == "Windows":
        cmd = ["where", command]
    else:
        cmd = ["which", command]

    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def get_system_commands() -> set[str]:
    """
    Get a set of all commands available in the system PATH.

    Returns:
        Set[str]: Set of command names
    """
    commands = set()

    # Get the PATH environment variable
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)

    # Find all executable files in PATH directories
    for path_dir in path_dirs:
        if not os.path.isdir(path_dir):
            continue

        try:
            for item in os.listdir(path_dir):
                item_path = os.path.join(path_dir, item)
                if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
                    commands.add(item)
        except (FileNotFoundError, PermissionError):
            continue

    return commands


def backup_file(file_path: Path) -> Optional[Path]:
    """
    Create a backup of a file before modifying it.

    Args:
        file_path (Path): Path to the file to backup

    Returns:
        Optional[Path]: Path to the backup file, or None if backup failed
    """
    if not file_path.exists():
        return None

    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception:
        return None


def safe_write_file(file_path: Path, content: str) -> bool:
    """
    Safely write content to a file using a temporary file.

    Args:
        file_path (Path): Path to the file to write
        content (str): Content to write

    Returns:
        bool: True if the write was successful
    """
    # Create the directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a temporary file in the same directory
    temp_file = None
    try:
        fd, temp_path = tempfile.mkstemp(dir=file_path.parent)
        temp_file = os.fdopen(fd, "w")
        temp_file.write(content)
        temp_file.close()
        temp_file = None

        # Ensure permissions match original file if it exists
        if file_path.exists():
            shutil.copymode(file_path, temp_path)

        # Rename the temporary file to the target file
        os.replace(temp_path, file_path)
        return True

    except Exception:
        return False

    finally:
        if temp_file is not None:
            temp_file.close()


def expand_user_path(path: str) -> Path:
    """
    Expand a path that may contain a tilde (~) to an absolute path.

    Args:
        path (str): The path to expand

    Returns:
        Path: The expanded path
    """
    return Path(os.path.expanduser(path))


def is_valid_path(path: Path) -> bool:
    """
    Check if a path is valid and accessible.

    Args:
        path (Path): The path to check

    Returns:
        bool: True if the path is valid and accessible
    """
    try:
        # Check if the parent directory exists and is writable
        parent = path.parent
        return parent.exists() and os.access(parent, os.W_OK)
    except Exception:
        return False


def get_file_modification_time(file_path: Path) -> float:
    """
    Get the last modification time of a file.

    Args:
        file_path (Path): Path to the file

    Returns:
        float: Last modification time (timestamp)
    """
    if not file_path.exists():
        return 0.0

    return file_path.stat().st_mtime


def is_shell_reserved_word(word: str, reserved_words: set[str]) -> bool:
    """
    Check if a word is a shell reserved word.

    Args:
        word (str): The word to check
        reserved_words (Set[str]): Set of reserved words

    Returns:
        bool: True if the word is reserved
    """
    return word in reserved_words
