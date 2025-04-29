"""
Unit tests for the shell interaction functionality.

This module tests shell detection, config file management,
and alias manipulation without modifying real shell configs.
"""

from typing import Generator
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import shellingham

from app.shell import (
    SECTION_START,
    SECTION_END,
    detect_shell,
    get_shell_config_path,
    add_alias_to_shell,
    remove_alias_from_shell,
    update_alias_in_shell,
    get_all_aliases,
    is_valid_alias_name,
    _ensure_aliaser_section,
    _get_aliaser_section_lines_range,
    _get_alias_format,
    _line_defines_alias,
)


@pytest.fixture
def mock_temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for testing shell config files.

    Yields:
        Path: Path to the temporary directory
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_home_dir(mock_temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Mock the home directory for testing.

    Args:
        mock_temp_dir: Temporary directory path
        monkeypatch: Pytest fixture for patching

    Returns:
        Path: Path to the mock home directory
    """
    # Create a mock home directory
    home_dir = mock_temp_dir / "home"
    home_dir.mkdir(exist_ok=True)

    # Mock Path.home() to return our mock home directory
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    return home_dir


@pytest.fixture
def setup_shell_configs(mock_home_dir: Path) -> dict[str, Path]:
    """
    Set up mock shell configuration files.

    Args:
        mock_home_dir: Mock home directory path

    Returns:
        Dict[str, Path]: Dictionary mapping shell names to config file paths
    """
    # Create mock shell config files
    bashrc = mock_home_dir / ".bashrc"
    bash_profile = mock_home_dir / ".bash_profile"
    zshrc = mock_home_dir / ".zshrc"
    fish_config_dir = mock_home_dir / ".config" / "fish"
    fish_config_dir.mkdir(parents=True, exist_ok=True)
    fish_config = fish_config_dir / "config.fish"

    # Create empty files
    for config_file in [bashrc, bash_profile, zshrc, fish_config]:
        config_file.touch()

    return {
        "bash_bashrc": bashrc,
        "bash_profile": bash_profile,
        "zsh": zshrc,
        "fish": fish_config,
    }


@patch("shellingham.detect_shell")
def test_detect_shell(mock_detect: MagicMock) -> None:
    """
    Test shell detection function.

    Args:
        mock_detect: Mocked shellingham.detect_shell function
    """
    # Test successful detection of supported shell
    mock_detect.return_value = ("zsh", "/bin/zsh")
    assert detect_shell() == "zsh"

    # Test successful detection of another supported shell
    mock_detect.return_value = ("bash", "/bin/bash")
    assert detect_shell() == "bash"

    # Test detection of unsupported shell
    mock_detect.return_value = ("tcsh", "/bin/tcsh")
    with pytest.raises(RuntimeError, match=r"not supported"):
        detect_shell()

    # Test detection failure
    mock_detect.side_effect = shellingham.ShellDetectionFailure()
    with pytest.raises(RuntimeError, match=r"Could not detect your shell"):
        detect_shell()


def test_get_shell_config_path(setup_shell_configs: dict[str, Path]) -> None:
    """
    Test shell configuration path resolution.

    Args:
        mock_home_dir: Mock home directory path
        setup_shell_configs: Dictionary of mock shell config files
    """
    # Test bash with .bash_profile present
    assert get_shell_config_path("bash") == setup_shell_configs["bash_profile"]

    # Test bash with only .bashrc present
    setup_shell_configs["bash_profile"].unlink()
    assert get_shell_config_path("bash") == setup_shell_configs["bash_bashrc"]

    # Test zsh
    assert get_shell_config_path("zsh") == setup_shell_configs["zsh"]

    # Test fish
    assert get_shell_config_path("fish") == setup_shell_configs["fish"]

    # Test unsupported shell
    with pytest.raises(ValueError, match=r"Unsupported shell"):
        get_shell_config_path("tcsh")


def test_ensure_aliaser_section(mock_temp_dir: Path) -> None:
    """
    Test ensuring the aliaser section exists in a shell config file.

    Args:
        mock_temp_dir: Temporary directory path
    """
    # Test with non-existent file
    config_file = mock_temp_dir / "new_config"
    _ensure_aliaser_section(config_file)

    # Check that the file was created with the section
    assert config_file.exists()
    content = config_file.read_text()
    assert SECTION_START in content
    assert SECTION_END in content

    # Test with existing file without section
    config_file = mock_temp_dir / "existing_config"
    config_file.write_text("# Existing configuration\n")
    _ensure_aliaser_section(config_file)

    # Check that the section was added
    content = config_file.read_text()
    assert SECTION_START in content
    assert SECTION_END in content

    # Test with existing file that already has the section
    config_file = mock_temp_dir / "config_with_section"
    config_file.write_text(
        f"# Existing configuration\n{SECTION_START}\n# Managed section\n{SECTION_END}\n"
    )
    _ensure_aliaser_section(config_file)

    # Check that the content didn't change
    content = config_file.read_text()
    assert (
        content == f"# Existing configuration\n{SECTION_START}\n# Managed section\n{SECTION_END}\n"
    )


def test_get_aliaser_section_lines_range(mock_temp_dir: Path) -> None:
    """
    Test getting the aliaser section from a shell config file.

    Args:
        mock_temp_dir: Temporary directory path
    """
    # Create a test config file with a section
    config_file = mock_temp_dir / "config_with_section"
    section_content = f'{SECTION_START}\n# Managed section\nalias test="command"\n{SECTION_END}'
    config_file.write_text(f"# Existing configuration\n{section_content}\n# After section")

    # Get the section
    start_idx, end_idx = _get_aliaser_section_lines_range(config_file)

    # Check that the correct section was found
    # 0-based index, line 0, 1-based index, line 1
    assert start_idx in [0, 1]
    # 0-based index, line 3, 1-based index, line 4
    assert end_idx in [3, 4]

    # Test with a file that doesn't have the section yet
    config_file = mock_temp_dir / "config_without_section"
    config_file.write_text("# Existing configuration\n")


def test_get_alias_format() -> None:
    """
    Test formatting aliases for different shells.

    This tests the _get_alias_format function which creates the appropriate
    alias command string for different shell types.
    """
    # Test bash/zsh format
    alias_cmd = _get_alias_format("bash", "test", "echo 'hello'")
    assert alias_cmd == "alias test=\"echo 'hello'\""

    # Test zsh format (should be the same as bash)
    alias_cmd = _get_alias_format("zsh", "test", "echo 'hello'")
    assert alias_cmd == "alias test=\"echo 'hello'\""

    # Test fish format
    alias_cmd = _get_alias_format("fish", "test", "echo 'hello'")
    assert alias_cmd == "alias test 'echo \\'hello\\''"

    # Test escaping quotes in bash/zsh
    alias_cmd = _get_alias_format("bash", "test", 'echo "quoted"')
    assert alias_cmd == 'alias test="echo \\"quoted\\""'

    # Test unsupported shell
    with pytest.raises(ValueError, match=r"Unsupported shell"):
        _get_alias_format("tcsh", "test", "echo 'hello'")


def test_line_defines_alias() -> None:
    """
    Test detecting if a line defines a specific alias.

    This tests the _line_defines_alias function which checks if a given
    line of text in a config file defines a specific alias.
    """
    # Test bash/zsh style aliases
    assert _line_defines_alias('alias test="command"', "test", "bash")
    assert _line_defines_alias('alias test="command"', "test", "zsh")
    assert not _line_defines_alias('alias other="command"', "test", "zsh")

    # Test with whitespace
    assert _line_defines_alias('  alias   test="command"  ', "test", "bash")

    # Test fish style aliases
    assert _line_defines_alias("alias test 'command'", "test", "fish")
    assert not _line_defines_alias("alias other 'command'", "test", "fish")

    # Test with unsupported shell (should return False)
    assert not _line_defines_alias('alias test="command"', "test", "tcsh")


def test_add_alias_to_shell(mock_temp_dir: Path) -> None:
    """
    Test adding an alias to a shell configuration file.

    Args:
        mock_temp_dir: Temporary directory path
    """
    # Create a test config file
    config_file = mock_temp_dir / "config"
    config_file.write_text(
        f"# Existing configuration\n{SECTION_START}\n"
        f"# Aliases managed by aliaser - DO NOT EDIT THIS SECTION MANUALLY\n"
        f"alias existing=\"echo 'existing'\"\n{SECTION_END}\n"
    )

    # Add a new alias
    result = add_alias_to_shell("zsh", config_file, "test", "echo 'test'")

    # Check that the alias was added
    assert result is True
    content = config_file.read_text()
    assert "alias test=\"echo 'test'\"" in content
    assert "alias existing=\"echo 'existing'\"" in content

    # Try to add an existing alias with the same command
    aliases = get_all_aliases("zsh", config_file)
    result = add_alias_to_shell("zsh", config_file, "existing", "echo 'existing'")

    # Check that the result is False (no change)
    assert result is False
    new_aliases = get_all_aliases("zsh", config_file)
    assert aliases == new_aliases

    # Add an alias with the same name but different command (should update)
    result = add_alias_to_shell("zsh", config_file, "existing", "echo 'updated'")

    # Check that the alias was not updated
    assert result is False
    aliases = get_all_aliases("zsh", config_file)
    assert aliases["existing"] == "echo 'existing'"


def test_remove_alias_from_shell(mock_temp_dir: Path) -> None:
    """
    Test removing an alias from a shell configuration file.

    Args:
        mock_temp_dir: Temporary directory path
    """
    # Create a test config file with aliases
    config_file = mock_temp_dir / "config"
    config_file.write_text(
        f"# Existing configuration\n{SECTION_START}\n"
        f"# Aliases managed by aliaser - DO NOT EDIT THIS SECTION MANUALLY\n"
        f"alias test1=\"echo 'test1'\"\n"
        f"alias test2=\"echo 'test2'\"\n"
        f"{SECTION_END}\n"
    )

    # Remove an existing alias
    result = remove_alias_from_shell("zsh", config_file, "test1")

    # Check that the alias was removed
    assert result is True
    content = config_file.read_text()
    assert "alias test1=\"echo 'test1'\"" not in content
    assert "alias test2=\"echo 'test2'\"" in content

    # Try to remove a non-existent alias
    result = remove_alias_from_shell("zsh", config_file, "nonexistent")

    # Check that the result is False (not found)
    assert result is False


def test_update_alias_in_shell(mock_temp_dir: Path) -> None:
    """
    Test updating an alias in a shell configuration file.

    Args:
        mock_temp_dir: Temporary directory path
    """
    # Create a test config file with aliases
    config_file = mock_temp_dir / "config"
    config_file.write_text(
        f"# Existing configuration\n{SECTION_START}\n"
        f"# Aliases managed by aliaser - DO NOT EDIT THIS SECTION MANUALLY\n"
        f"alias test=\"echo 'original'\"\n"
        f"{SECTION_END}\n"
    )

    # Update an existing alias
    result = update_alias_in_shell("zsh", config_file, "test", "echo 'updated'")

    # Check that the alias was updated
    assert result is True
    aliases = get_all_aliases("zsh", config_file)
    assert aliases["test"] == "echo 'updated'"

    # Try to update a non-existent alias
    result = update_alias_in_shell("zsh", config_file, "nonexistent", "echo 'new'")

    # Check that the result is False (not found)
    assert result is False


def test_get_all_aliases(mock_temp_dir: Path) -> None:
    """
    Test getting all aliases from a shell configuration file.

    Args:
        mock_temp_dir: Temporary directory path
    """
    # Create a test config file with aliases
    config_file = mock_temp_dir / "config"
    config_file.write_text(
        f"# Existing configuration\n{SECTION_START}\n"
        f"# Aliases managed by aliaser - DO NOT EDIT THIS SECTION MANUALLY\n"
        f"alias test1=\"echo 'test1'\"\n"
        f"alias test2=\"echo 'test2'\"\n"
        f"{SECTION_END}\n"
    )

    # Get all aliases
    aliases = get_all_aliases("zsh", config_file)
    assert aliases == {"test1": "echo 'test1'", "test2": "echo 'test2'"}


def test_is_valid_alias_name() -> None:
    """
    Test validating alias names.
    """
    # Test valid alias names
    assert is_valid_alias_name("valid_alias")
    assert is_valid_alias_name("alias_with_underscores")
    assert is_valid_alias_name("alias123")
