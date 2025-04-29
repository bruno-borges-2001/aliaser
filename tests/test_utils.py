"""
Unit tests for utility functions in utils.py.

This module tests file operations, command validation, and path handling.
"""

from typing import Generator
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.utils import (
    is_command_in_path,
    get_system_commands,
    backup_file,
    safe_write_file,
    expand_user_path,
    is_valid_path,
    get_file_modification_time,
    is_shell_reserved_word,
)


@pytest.fixture
def mock_temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for testing file operations.

    Yields:
        Path: Path to the temporary directory
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@patch("subprocess.run")
def test_is_command_in_path(mock_run: MagicMock) -> None:
    """
    Test checking if a command exists in PATH.

    Args:
        mock_run: Mocked subprocess.run function
    """
    # Setup mock for successful command check
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_run.return_value = mock_process

    # Test with a command that exists
    assert is_command_in_path("valid_command") is True

    # Setup mock for non-existent command
    mock_process.returncode = 1
    mock_run.return_value = mock_process

    # Test with a command that doesn't exist
    assert is_command_in_path("invalid_command") is False

    # Test exception handling
    mock_run.side_effect = Exception("Command failed")
    assert is_command_in_path("error_command") is False


@patch("os.environ")
@patch("os.path.isdir")
@patch("os.listdir")
@patch("os.path.isfile")
@patch("os.access")
def test_get_system_commands(
    mock_access: MagicMock,
    mock_isfile: MagicMock,
    mock_listdir: MagicMock,
    mock_isdir: MagicMock,
    mock_environ: MagicMock,
) -> None:
    """
    Test getting all system commands from PATH.

    Args:
        mock_access: Mocked os.access function
        mock_isfile: Mocked os.path.isfile function
        mock_listdir: Mocked os.listdir function
        mock_isdir: Mocked os.path.isdir function
        mock_environ: Mocked os.environ
    """
    # Mock PATH environment variable
    mock_environ.get.return_value = "/bin:/usr/bin:/usr/local/bin"

    # Mock directory checking
    mock_isdir.side_effect = lambda path: path in ["/bin", "/usr/bin", "/usr/local/bin"]

    # Mock directory contents
    mock_listdir.side_effect = lambda path: {
        "/bin": ["ls", "cd", "grep"],
        "/usr/bin": ["python", "git"],
        "/usr/local/bin": ["node", "npm"],
    }[path]

    # Mock file checking
    mock_isfile.return_value = True

    # Mock executable checking
    mock_access.return_value = True

    # Get system commands
    commands = get_system_commands()

    # Check that all expected commands were found
    expected = {"ls", "cd", "grep", "python", "git", "node", "npm"}
    assert commands == expected

    # Test with permission error
    mock_listdir.side_effect = PermissionError("Permission denied")
    commands = get_system_commands()

    # Check that an empty set is returned
    assert commands == set()


def test_backup_file(mock_temp_dir: Path) -> None:
    """
    Test creating a backup of a file.

    Args:
        mock_temp_dir: Temporary directory path
    """
    # Create a test file
    test_file = mock_temp_dir / "test_file.txt"
    test_file.write_text("Original content")

    # Create a backup
    backup_path = backup_file(test_file)

    # Check that the backup was created with correct content
    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.name == "test_file.txt.bak"
    assert backup_path.read_text() == "Original content"

    # Test with non-existent file
    nonexistent_file = mock_temp_dir / "nonexistent.txt"
    backup_path = backup_file(nonexistent_file)

    # Check that no backup was created
    assert backup_path is None


def test_safe_write_file(mock_temp_dir: Path) -> None:
    """
    Test safely writing content to a file.

    Args:
        mock_temp_dir: Temporary directory path
    """
    # Test writing to a new file
    test_file = mock_temp_dir / "test_file.txt"
    result = safe_write_file(test_file, "Test content")

    # Check that the write was successful
    assert result is True
    assert test_file.exists()
    assert test_file.read_text() == "Test content"

    # Test writing to a file in a subdirectory that doesn't exist
    subdir_file = mock_temp_dir / "subdir" / "test_file.txt"
    result = safe_write_file(subdir_file, "Subdir content")

    # Check that the directory and file were created
    assert result is True
    assert subdir_file.exists()
    assert subdir_file.read_text() == "Subdir content"

    # Test updating an existing file
    result = safe_write_file(test_file, "Updated content")
    assert result is True
    assert test_file.read_text() == "Updated content"


@patch("os.path.expanduser")
def test_expand_user_path(mock_expanduser: MagicMock) -> None:
    """
    Test expanding a user path with tilde.

    Args:
        mock_expanduser: Mocked os.path.expanduser function
    """
    # Mock expanduser to replace ~ with a known path
    mock_expanduser.side_effect = lambda p: p.replace("~", "/home/testuser")

    # Test a path with tilde
    path = expand_user_path("~/documents/file.txt")
    assert str(path) == "/home/testuser/documents/file.txt"

    # Test a path without tilde
    path = expand_user_path("/etc/hosts")
    assert str(path) == "/etc/hosts"


@patch("os.access")
def test_is_valid_path(mock_access: MagicMock, mock_temp_dir: Path) -> None:
    """
    Test checking if a path is valid and accessible.

    Args:
        mock_access: Mocked os.access function
        mock_temp_dir: Temporary directory path
    """
    # Create a test directory
    test_dir = mock_temp_dir / "testdir"
    test_dir.mkdir()

    # Mock access to return True
    mock_access.return_value = True

    # Test a valid path
    test_path = test_dir / "file.txt"
    assert is_valid_path(test_path) is True

    # Mock access to return False
    mock_access.return_value = False

    # Test a path with non-writable parent
    assert is_valid_path(test_path) is False

    # Test exception handling
    mock_access.side_effect = Exception("Access error")
    assert is_valid_path(test_path) is False


def test_get_file_modification_time(mock_temp_dir: Path) -> None:
    """
    Test getting the last modification time of a file.

    Args:
        mock_temp_dir: Temporary directory path
    """
    # Create a test file
    test_file = mock_temp_dir / "test_file.txt"
    test_file.write_text("Test content")

    # Get the actual modification time
    actual_mtime = test_file.stat().st_mtime

    # Get the modification time using our function
    mtime = get_file_modification_time(test_file)

    # Check that the returned time matches the actual time
    assert mtime == actual_mtime

    # Test with non-existent file
    nonexistent_file = mock_temp_dir / "nonexistent.txt"
    mtime = get_file_modification_time(nonexistent_file)

    # Check that 0.0 is returned for non-existent files
    assert mtime == 0.0


def test_is_shell_reserved_word() -> None:
    """
    Test checking if a word is a shell reserved word.
    """
    # Define test reserved words
    reserved_words = {"if", "then", "else", "cd", "ls"}

    # Test with reserved words
    assert is_shell_reserved_word("if", reserved_words) is True
    assert is_shell_reserved_word("cd", reserved_words) is True

    # Test with non-reserved words
    assert is_shell_reserved_word("myalias", reserved_words) is False
    assert is_shell_reserved_word("customcmd", reserved_words) is False

    # Test with empty set
    assert is_shell_reserved_word("if", set()) is False
