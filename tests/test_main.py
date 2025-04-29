"""
Unit tests for the aliaser CLI commands.

This module tests the core functionality of the aliaser tool
without modifying real shell configuration files.
"""

from typing import Generator
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from app.main import app
from app.logger import MESSAGE_PREFIXES, LogLevel
from app.shell import (
    SECTION_START,
    SECTION_END,
    get_all_aliases,
    add_alias_to_shell,
)


@pytest.fixture
def runner() -> CliRunner:
    """
    Create a Typer CLI test runner.

    Returns:
        CliRunner: A Typer CLI test runner
    """
    return CliRunner()


@pytest.fixture
def mock_shell_config() -> Generator[Path, None, None]:
    """
    Create a temporary shell config file for testing.

    Yields:
        Path: Path to the temporary config file
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary shell config file
        config_path = Path(temp_dir) / ".zshrc"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("# Existing shell configuration\n")
            f.write(f"{SECTION_START}\n")
            f.write("# Aliases managed by aliaser - DO NOT EDIT THIS SECTION MANUALLY\n")
            f.write(f"{SECTION_END}\n")

        yield config_path


@pytest.fixture
def mock_shell_detection() -> Generator[tuple[MagicMock, MagicMock], None, None]:
    """
    Mock the shell detection to return 'zsh' and use the mock config file.

    This prevents the tests from modifying real shell config files.

    Yields:
        Tuple[MagicMock, MagicMock]: Mocked detect_shell and get_shell_config_path functions
    """
    with patch("app.main.detect_shell") as mock_detect:
        mock_detect.return_value = "zsh"
        with patch("app.main.get_shell_config_path") as mock_config:
            # The actual path will be provided by the test
            yield mock_detect, mock_config


@pytest.fixture
def mock_is_valid_alias_name() -> Generator[MagicMock, None, None]:
    """
    Mock the is_valid_alias_name function to always return True except for specific test cases.

    Yields:
        MagicMock: Mocked is_valid_alias_name function
    """
    with patch("app.main.is_valid_alias_name") as mock_valid:
        mock_valid.return_value = True
        yield mock_valid


def test_create_alias(
    runner: CliRunner,
    mock_shell_config: Path,
    mock_shell_detection: tuple[MagicMock, MagicMock],
) -> None:
    """
    Test creating a new alias.

    Args:
        runner: CLI test runner
        mock_shell_config: Path to the mock shell config file
        mock_shell_detection: Mocked shell detection functions
        mock_is_valid_alias_name: Mocked alias name validation function
    """
    # Setup the mock to return our test config path
    _, mock_config = mock_shell_detection
    mock_config.return_value = mock_shell_config

    # Run the create command
    result = runner.invoke(app, ["create", "test_alias", "echo 'test command'"])

    # Check the result
    assert result.exit_code == 0
    assert MESSAGE_PREFIXES[LogLevel.SUCCESS] in result.stdout

    # Verify the alias was added to the config file
    aliases = get_all_aliases("zsh", mock_shell_config)
    assert "test_alias" in aliases
    assert aliases["test_alias"] == "echo 'test command'"


def test_create_existing_alias(
    runner: CliRunner,
    mock_shell_config: Path,
    mock_shell_detection: tuple[MagicMock, MagicMock],
) -> None:
    """
    Test creating an alias that already exists.

    Args:
        runner: CLI test runner
        mock_shell_config: Path to the mock shell config file
        mock_shell_detection: Mocked shell detection functions
        mock_is_valid_alias_name: Mocked alias name validation function
    """
    # Setup the mock to return our test config path
    _, mock_config = mock_shell_detection
    mock_config.return_value = mock_shell_config

    # Add an alias first
    runner.invoke(app, ["create", "existing_alias", "echo 'existing'"])

    result = runner.invoke(app, ["create", "existing_alias", "echo 'new command'"])

    # Check the result - should show notice, not an error
    assert result.exit_code == 0
    assert MESSAGE_PREFIXES[LogLevel.WARNING] in result.stdout

    # Verify the alias still exists with the original command
    aliases = get_all_aliases("zsh", mock_shell_config)
    assert "existing_alias" in aliases
    assert aliases["existing_alias"] == "echo 'existing'"


def test_create_invalid_alias(
    runner: CliRunner,
    mock_shell_config: Path,
    mock_shell_detection: tuple[MagicMock, MagicMock],
    mock_is_valid_alias_name: MagicMock,
) -> None:
    """
    Test creating an alias with an invalid name.

    Args:
        runner: CLI test runner
        mock_shell_config: Path to the mock shell config file
        mock_shell_detection: Mocked shell detection functions
        mock_is_valid_alias_name: Mocked alias name validation function
    """
    # Setup the mock to return our test config path
    _, mock_config = mock_shell_detection
    mock_config.return_value = mock_shell_config

    # Make validation fail
    mock_is_valid_alias_name.return_value = False

    # Run the create command with an invalid alias name
    result = runner.invoke(app, ["create", "ls", "echo 'invalid'"])

    # Check the result
    assert result.exit_code == 1
    assert MESSAGE_PREFIXES[LogLevel.ERROR] in result.stdout
    assert "not a valid alias name" in result.stdout

    # Verify the alias was not added
    aliases = get_all_aliases("zsh", mock_shell_config)
    assert "ls" not in aliases


def test_list_aliases(
    runner: CliRunner,
    mock_shell_config: Path,
    mock_shell_detection: tuple[MagicMock, MagicMock],
) -> None:
    """
    Test listing aliases.

    Args:
        runner: CLI test runner
        mock_shell_config: Path to the mock shell config file
        mock_shell_detection: Mocked shell detection functions
    """
    # Setup the mock to return our test config path
    _, mock_config = mock_shell_detection
    mock_config.return_value = mock_shell_config

    # Add some test aliases
    add_alias_to_shell("zsh", mock_shell_config, "alias1", "command1")
    add_alias_to_shell("zsh", mock_shell_config, "alias2", "command2")

    # Run the list command
    result = runner.invoke(app, ["list"])

    # Check the result
    assert result.exit_code == 0
    assert "alias1" in result.stdout
    assert "alias2" in result.stdout
    assert "command1" in result.stdout
    assert "command2" in result.stdout


def test_list_no_aliases(
    runner: CliRunner,
    mock_shell_config: Path,
    mock_shell_detection: tuple[MagicMock, MagicMock],
) -> None:
    """
    Test listing when no aliases exist.

    Args:
        runner: CLI test runner
        mock_shell_config: Path to the mock shell config file
        mock_shell_detection: Mocked shell detection functions
    """
    # Setup the mock to return our test config path
    _, mock_config = mock_shell_detection
    mock_config.return_value = mock_shell_config

    # Make sure there are no aliases
    with open(mock_shell_config, "w", encoding="utf-8") as f:
        f.write("# Existing shell configuration\n")
        f.write(f"{SECTION_START}\n")
        f.write("# Aliases managed by aliaser - DO NOT EDIT THIS SECTION MANUALLY\n")
        f.write(f"{SECTION_END}\n")

    # Run the list command
    result = runner.invoke(app, ["list"])

    # Check the result
    assert result.exit_code == 0
    assert "No aliases found" in result.stdout


def test_delete_alias(
    runner: CliRunner,
    mock_shell_config: Path,
    mock_shell_detection: tuple[MagicMock, MagicMock],
) -> None:
    """
    Test deleting an alias.

    Args:
        runner: CLI test runner
        mock_shell_config: Path to the mock shell config file
        mock_shell_detection: Mocked shell detection functions
    """
    # Setup the mock to return our test config path
    _, mock_config = mock_shell_detection
    mock_config.return_value = mock_shell_config

    # Add an alias to delete
    add_alias_to_shell("zsh", mock_shell_config, "delete_me", "echo 'delete'")

    # Verify the alias exists
    aliases = get_all_aliases("zsh", mock_shell_config)
    assert "delete_me" in aliases

    # Run the delete command
    result = runner.invoke(app, ["delete", "delete_me"])

    # Check the result
    assert result.exit_code == 0
    assert MESSAGE_PREFIXES[LogLevel.SUCCESS] in result.stdout

    # Verify the alias was removed
    aliases = get_all_aliases("zsh", mock_shell_config)
    assert "delete_me" not in aliases


def test_delete_nonexistent_alias(
    runner: CliRunner,
    mock_shell_config: Path,
    mock_shell_detection: tuple[MagicMock, MagicMock],
) -> None:
    """
    Test deleting an alias that doesn't exist.

    Args:
        runner: CLI test runner
        mock_shell_config: Path to the mock shell config file
        mock_shell_detection: Mocked shell detection functions
    """
    # Setup the mock to return our test config path
    _, mock_config = mock_shell_detection
    mock_config.return_value = mock_shell_config

    # Run the delete command for a non-existent alias
    result = runner.invoke(app, ["delete", "nonexistent"])

    # Check the result
    assert result.exit_code == 0
    assert MESSAGE_PREFIXES[LogLevel.ERROR] in result.stdout
    assert "not found" in result.stdout


def test_update_alias(
    runner: CliRunner,
    mock_shell_config: Path,
    mock_shell_detection: tuple[MagicMock, MagicMock],
) -> None:
    """
    Test updating an alias.

    Args:
        runner: CLI test runner
        mock_shell_config: Path to the mock shell config file
        mock_shell_detection: Mocked shell detection functions
    """
    # Setup the mock to return our test config path
    _, mock_config = mock_shell_detection
    mock_config.return_value = mock_shell_config

    # Add an alias to update
    add_alias_to_shell("zsh", mock_shell_config, "update_me", "echo 'original'")

    # Verify the alias exists with the original command
    aliases = get_all_aliases("zsh", mock_shell_config)
    assert "update_me" in aliases
    assert aliases["update_me"] == "echo 'original'"

    # Run the update command
    result = runner.invoke(app, ["update", "update_me", "echo 'updated'"])

    # Check the result
    assert result.exit_code == 0
    assert MESSAGE_PREFIXES[LogLevel.SUCCESS] in result.stdout

    # Verify the alias was updated
    aliases = get_all_aliases("zsh", mock_shell_config)
    assert "update_me" in aliases
    assert aliases["update_me"] == "echo 'updated'"


def test_update_nonexistent_alias(
    runner: CliRunner,
    mock_shell_config: Path,
    mock_shell_detection: tuple[MagicMock, MagicMock],
) -> None:
    """
    Test updating an alias that doesn't exist.

    Args:
        runner: CLI test runner
        mock_shell_config: Path to the mock shell config file
        mock_shell_detection: Mocked shell detection functions
    """
    # Setup the mock to return our test config path
    _, mock_config = mock_shell_detection
    mock_config.return_value = mock_shell_config

    # Run the update command for a non-existent alias
    result = runner.invoke(app, ["update", "nonexistent", "echo 'new'"])

    # Check the result
    assert result.exit_code == 0
    assert MESSAGE_PREFIXES[LogLevel.ERROR] in result.stdout
    assert "not found" in result.stdout


def test_shell_detection_error(
    runner: CliRunner,
    mock_shell_detection: tuple[MagicMock, MagicMock],
) -> None:
    """
    Test error handling when shell detection fails.

    Args:
        runner: CLI test runner
        mock_shell_detection: Mocked shell detection functions
    """
    # Make shell detection fail
    mock_detect, _ = mock_shell_detection
    mock_detect.side_effect = RuntimeError("Shell detection failed")

    # Run any command
    result = runner.invoke(app, ["list"])

    # Check the result
    assert result.exit_code == 1
    assert MESSAGE_PREFIXES[LogLevel.ERROR] in result.stdout
    assert "Shell detection failed" in result.stdout
