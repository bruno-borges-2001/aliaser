"""
Aliaser - A command-line tool for managing shell aliases.

This module contains the main CLI implementation using Typer.
"""

import sys
from pathlib import Path
from typing import Any
import typer

# Import internal modules
from app.logger import LogLevel, log, log_table
from app.shell import (
    detect_shell,
    get_all_aliases,
    run_shell_command,
    add_alias_to_shell,
    is_valid_alias_name,
    update_alias_in_shell,
    get_shell_config_path,
    remove_alias_from_shell,
)

# Create Typer app instance
app = typer.Typer(
    help="Create and manage shell aliases in a structured way.",
    add_completion=True,
)


@app.command("create")
def create_alias(
    alias: str = typer.Argument(..., help="Name of the alias to create."),
    command: str = typer.Argument(..., help="Command to associate with the alias."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing aliases."),
    reload: bool = typer.Option(True, "--reload", "-r", help="Reload the shell configuration."),
) -> None:
    """
    Create a new alias in your shell configuration file.

    The alias will be added to a section managed by aliaser.
    If the alias already exists, it will be overwritten if the `--force` flag is passed.
    Ignored if not
    """
    try:
        # Detect the shell and get config path
        shell_name = detect_shell()
        config_path = get_shell_config_path(shell_name)

        # Validate the alias name
        if not is_valid_alias_name(alias):
            log(
                f"'{alias}' is not a valid alias name. "
                f"It may be a reserved word or existing command.",
                LogLevel.ERROR,
            )
            sys.exit(1)

        # Add the alias
        result = add_alias_to_shell(shell_name, config_path, alias, command, force)

        if result:
            log(
                f"Alias '[bold]{alias}[/bold]' created for command '[bold]{command}[/bold]'",
                LogLevel.SUCCESS,
            )
            if not reload:
                log(
                    f"Reload your shell configuration with: [bold]source {config_path}[/bold]",
                    LogLevel.INFO,
                )
            else:
                run_shell_command(f"source {config_path}")
        else:
            # Alias already exists
            log(
                f"Alias '[bold]{alias}[/bold]' already exists.",
                LogLevel.WARNING,
            )

    except Exception as e:
        log(str(e), LogLevel.ERROR)
        sys.exit(1)


@app.command("list")
def list_aliases() -> None:
    """
    List all aliases managed by aliaser.
    """
    try:
        # Detect the shell and get config path
        shell_name = detect_shell()
        config_path = get_shell_config_path(shell_name)

        # Get all aliases
        aliases = get_all_aliases(shell_name, config_path)

        if not aliases:
            log("No aliases found. Add some with 'aliaser create'.", LogLevel.WARNING)
            return

        # Create a table for display
        columns: list[dict[str, Any]] = [
            {"header": "Alias", "style": "cyan", "no_wrap": True},
            {"header": "Command", "style": "green"},
        ]
        rows = [[alias, cmd] for alias, cmd in aliases.items()]

        log_table(columns=columns, rows=rows)

    except Exception as e:
        log(str(e), LogLevel.ERROR)
        sys.exit(1)


@app.command("delete")
def delete_alias(
    alias: str = typer.Argument(..., help="Name of the alias to delete."),
    reload: bool = typer.Option(False, "--reload", "-r", help="Reload the shell configuration."),
) -> None:
    """
    Delete an existing alias from your shell configuration file.
    """
    try:
        # Detect the shell and get config path
        shell_name = detect_shell()
        config_path = get_shell_config_path(shell_name)

        # Remove the alias
        result = remove_alias_from_shell(shell_name, config_path, alias)

        if result:
            log(
                f"Alias '[bold]{alias}[/bold]' deleted.",
                LogLevel.SUCCESS,
            )
            if not reload:
                log(
                    f"Reload your shell configuration with: [bold]source {config_path}[/bold]",
                    LogLevel.INFO,
                )
            else:
                run_shell_command(f"source {config_path}")
        else:
            log(
                f"Alias '[bold]{alias}[/bold]' not found.",
                LogLevel.ERROR,
            )

    except Exception as e:
        log(str(e), LogLevel.ERROR)
        sys.exit(1)


@app.command("update")
def update_alias(
    alias: str = typer.Argument(..., help="Name of the alias to update."),
    command: str = typer.Argument(..., help="New command to associate with the alias."),
    reload: bool = typer.Option(False, "--reload", "-r", help="Reload the shell configuration."),
) -> None:
    """
    Update an existing alias with a new command.
    """
    try:
        # Detect the shell and get config path
        shell_name = detect_shell()
        config_path = get_shell_config_path(shell_name)

        # Update the alias
        result = update_alias_in_shell(shell_name, config_path, alias, command)

        if result:
            log(
                f"Alias '[bold]{alias}[/bold]' updated to '[bold]{command}[/bold]'",
                LogLevel.SUCCESS,
            )
            if not reload:
                log(
                    f"Reload your shell configuration with: [bold]source {config_path}[/bold]",
                    LogLevel.INFO,
                )
            else:
                run_shell_command(f"source {config_path}")
        else:
            log(
                f"Alias '[bold]{alias}[/bold]' not found.",
                LogLevel.ERROR,
            )

    except Exception as e:
        log(str(e), LogLevel.ERROR)
        sys.exit(1)


@app.command("export")
def export_aliases() -> None:
    """
    Export all aliases to a file. The file will be saved in the current directory.
    The file will be named `aliases.txt` and be overwritten if it already exists.
    The file will contain all the aliases in the format `alias_name=command`.
    After the file is created, the user will be prompted with a link to the file.
    """
    try:
        # Detect the shell and get config path
        shell_name = detect_shell()
        config_path = get_shell_config_path(shell_name)

        # Get all aliases
        aliases = get_all_aliases(shell_name, config_path)

        # Write aliases to file
        with open("aliases.txt", "w", encoding="utf-8") as f:
            for alias, command in aliases.items():
                f.write(f"{alias}={command}\n")

            log(
                f"Aliases exported successfully to '[bold]{Path('aliases.txt').absolute()}[/bold]'",
                LogLevel.SUCCESS,
            )

    except Exception as e:
        log(str(e), LogLevel.ERROR)
        sys.exit(1)


@app.command("import")
def import_aliases(
    path: Path = typer.Argument(..., help="Path to the file containing the aliases."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing aliases."),
) -> None:
    """
    Import aliases from a file. The path to the file will be passed as an argument.
    The command will receive an optional argument `--force` or `-f` to overwrite
    existing aliases.
    It will be read line by line and each line will be parsed as `alias_name=command`.
    If the alias already exists, it will be overwritten if the `--force` flag is passed.
    Ignored if not
    """
    try:
        # Detect the shell and get config path
        shell_name = detect_shell()
        config_path = get_shell_config_path(shell_name)

        # Get the path to the aliases file
        if not path.exists():
            log(
                f"File '[bold]{path}[/bold]' does not exist.",
                LogLevel.ERROR,
            )
            sys.exit(1)

        # Read and parse the aliases file
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Get existing aliases
        existing_aliases = get_all_aliases(shell_name, config_path)

        # Track if any aliases were imported
        imported_count = 0

        # Process each line
        for line in lines:
            line = line.strip()
            if not line or "=" not in line:
                continue

            # Parse alias and command
            alias, command = line.split("=", 1)
            alias = alias.strip()
            command = command.strip()

            # Skip if alias exists and no force flag
            if not force and alias in existing_aliases:
                log(
                    f"Alias '[bold]{alias}[/bold]' already exists - skipping.",
                    LogLevel.WARNING,
                )
                continue

            # Add the alias
            try:
                if add_alias_to_shell(shell_name, config_path, alias, command, force):
                    log(
                        f"Alias '[bold]{alias}[/bold] [blue]({command})[/blue]'"
                        + "imported successfully.",
                        LogLevel.SUCCESS,
                    )
                    imported_count += 1
            except RuntimeError as e:
                log(
                    f"Failed to import alias '[bold]{alias}[/bold]': {str(e)}",
                    LogLevel.ERROR,
                )

        if imported_count > 0:
            log(
                f"Successfully imported [bold]{imported_count}[/bold]"
                + f"alias{'es' if imported_count > 1 else ''}.",
                LogLevel.SUCCESS,
            )
        else:
            log("No new aliases were imported.", LogLevel.INFO)

    except Exception as e:
        log(str(e), LogLevel.ERROR)
        sys.exit(1)


@app.command("clear")
def clear_aliases(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt."),
    reload: bool = typer.Option(False, "--reload", "-r", help="Reload the shell configuration."),
) -> None:
    """
    Remove all aliases managed by aliaser.
    Requires confirmation unless --force flag is used.
    """
    try:
        # Detect the shell and get config path
        shell_name = detect_shell()
        config_path = get_shell_config_path(shell_name)

        # Get current aliases
        aliases = get_all_aliases(shell_name, config_path)

        if not aliases:
            log("No aliases found to remove.", LogLevel.INFO)
            return

        # Get confirmation unless force flag is used
        if not force:
            num_aliases = len(aliases)
            confirm = typer.confirm(
                f"Are you sure you want to remove all {num_aliases}"
                + f"alias{'es' if num_aliases > 1 else ''}?"
            )
            if not confirm:
                log("Operation cancelled.", LogLevel.INFO)
                return

        # Remove all aliases one by one
        for alias in aliases:
            if remove_alias_from_shell(shell_name, config_path, alias):
                log(
                    f"Removed alias '[bold]{alias}[/bold]'",
                    LogLevel.SUCCESS,
                )

        if not reload:
            log(
                f"Reload your shell configuration with: [bold]source {config_path}[/bold]",
                LogLevel.INFO,
            )
        else:
            run_shell_command(f"source {config_path}")

    except Exception as e:
        log(str(e), LogLevel.ERROR)
        sys.exit(1)


@app.command("source")
def source_aliases() -> None:
    """
    Source the aliases file.
    """
    try:
        # Detect the shell and get config path
        shell_name = detect_shell()
        config_path = get_shell_config_path(shell_name)

        run_shell_command(f"source {config_path}")
    except Exception as e:
        log(str(e), LogLevel.ERROR)
        sys.exit(1)


if __name__ == "__main__":
    app()
