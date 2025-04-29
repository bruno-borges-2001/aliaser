from enum import Enum
from typing import Any
from rich import print as rprint
from rich.table import Table
from rich.console import Console

# Rich console for pretty output
console = Console()


class LogLevel(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


MESSAGE_PREFIXES = {
    LogLevel.SUCCESS: "✅",
    LogLevel.ERROR: "❌",
    LogLevel.WARNING: "⚠️",
    LogLevel.INFO: "ℹ️",
}


def log(message: str, level: LogLevel = LogLevel.INFO) -> None:
    if level not in MESSAGE_PREFIXES:
        raise ValueError(f"Invalid log level: {level}")

    rprint(f"{MESSAGE_PREFIXES[level]} {message}")


def log_table(
    title: str | None = None,
    columns: list[dict[str, Any]] | None = None,
    rows: list[list[str]] | None = None,
) -> None:
    table = Table(title=title)
    if columns:
        for column in columns:
            table.add_column(**column)

    if rows:
        for row in rows:
            table.add_row(*row)

    console.print(table)
