"""
Display module: Rich terminal rendering for spreadsheets.

Provides beautiful table output and styled feedback messages.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from typing import Any


console = Console()


def render_spreadsheet(
    data: dict[str, Any],
    title: str | None = None,
    show_empty_message: bool = True
) -> None:
    """
    Render a spreadsheet as a rich table.

    Args:
        data: Dict with 'columns' and 'rows' keys from SpreadsheetManager.get_data()
        title: Optional title override (defaults to spreadsheet name)
        show_empty_message: Show message if no rows exist
    """
    if not data.get("success", False):
        show_error(data.get("error", "Failed to retrieve data"))
        return

    columns = data.get("columns", [])
    rows = data.get("rows", [])
    spreadsheet_name = data.get("spreadsheet", "Spreadsheet")

    table = Table(
        title=title or spreadsheet_name,
        show_header=True,
        header_style="bold white on dark_blue",
        border_style="bright_blue",
        box=box.ROUNDED,
        row_styles=["", "on grey11"],
        padding=(0, 1),
        collapse_padding=True,
        show_lines=False,
        title_style="bold cyan",
        caption_style="dim",
    )

    # Calculate column widths based on content
    for col in columns:
        if col == "id":
            table.add_column("ID", style="dim cyan", width=4, justify="center")
        elif col in ("notes", "description", "task_description"):
            table.add_column(
                col.replace("_", " ").title(),
                style="white",
                max_width=40,
                overflow="ellipsis",
                no_wrap=False,
            )
        else:
            table.add_column(
                col.replace("_", " ").title(),
                style="bright_white",
                max_width=25,
                overflow="ellipsis",
            )

    if rows:
        for row in rows:
            values = []
            for col in columns:
                val = row.get(col, "")
                cell_val = str(val) if val is not None else ""
                # Add subtle styling for empty cells
                if not cell_val:
                    cell_val = "[dim]—[/dim]"
                values.append(cell_val)
            table.add_row(*values)
    elif show_empty_message:
        table.add_row(*["[dim]—[/dim]" for _ in columns])

    console.print()
    console.print(table)
    console.print()

    if not rows and show_empty_message:
        console.print("[dim italic]  (no rows yet)[/dim italic]")
        console.print()


def render_spreadsheet_list(data: dict[str, Any]) -> None:
    """Render list of available spreadsheets."""
    if not data.get("success", False):
        show_error(data.get("error", "Failed to list spreadsheets"))
        return

    spreadsheets = data.get("spreadsheets", [])
    current = data.get("current")

    if not spreadsheets:
        show_info("No spreadsheets exist yet. Create one with a command like 'create a new expense tracker'")
        return

    table = Table(
        title="Available Spreadsheets",
        show_header=True,
        header_style="bold white on dark_blue",
        border_style="bright_blue",
        box=box.ROUNDED,
        row_styles=["", "on grey11"],
        padding=(0, 1),
        title_style="bold cyan",
    )
    table.add_column("Name", style="bright_white")
    table.add_column("Columns", style="dim", max_width=50, overflow="ellipsis")
    table.add_column("Active", justify="center", width=6)

    for sheet in spreadsheets:
        name = sheet["name"]
        cols = ", ".join(sheet["columns"][:5])
        if len(sheet["columns"]) > 5:
            cols += f" [dim](+{len(sheet['columns']) - 5})[/dim]"
        is_current = "[bold green]●[/bold green]" if name == current else "[dim]○[/dim]"
        table.add_row(name, cols, is_current)

    console.print()
    console.print(table)
    console.print()


def show_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[green bold]>[/green bold] {message}")


def show_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[red bold]![/red bold] [red]{message}[/red]")


def show_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[blue bold]i[/blue bold] {message}")


def show_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[yellow bold]![/yellow bold] [yellow]{message}[/yellow]")


def show_voice_status(status: str) -> None:
    """Display voice input status."""
    if status == "recording":
        console.print("[bold magenta]Recording...[/bold magenta] (speak now, silence to stop)")
    elif status == "transcribing":
        console.print("[bold cyan]Transcribing...[/bold cyan]")
    elif status == "done":
        console.print("[green]Done[/green]")


def show_transcription(text: str) -> None:
    """Display transcribed text."""
    console.print(f'[dim]Heard:[/dim] "[italic]{text}[/italic]"')


def show_welcome() -> None:
    """Display welcome message."""
    welcome = Text()
    welcome.append("Spreadsheet Agent", style="bold cyan")
    welcome.append(" Ready\n", style="white")
    welcome.append("Type commands in natural language or use ", style="dim")
    welcome.append("!voice", style="bold yellow")
    welcome.append(" for voice input", style="dim")

    panel = Panel(
        welcome,
        border_style="blue",
        padding=(0, 2)
    )
    console.print()
    console.print(panel)
    console.print()


def show_help() -> None:
    """Display help information."""
    help_text = """
[bold cyan]Natural Language Commands:[/bold cyan]
  "create a spreadsheet for tracking expenses"
  "add a row: coffee, 5 dollars, today"
  "change row 2 price to 10"
  "delete row 3"
  "add a column called notes"
  "show me the spreadsheet"

[bold cyan]Special Commands:[/bold cyan]
  [yellow]!voice[/yellow]    - Record voice command
  [yellow]!show[/yellow]     - Display current spreadsheet
  [yellow]!list[/yellow]     - List all spreadsheets
  [yellow]!export[/yellow]   - Export to CSV
  [yellow]!help[/yellow]     - Show this help
  [yellow]!quit[/yellow]     - Exit
"""
    console.print(help_text)


def show_thinking() -> None:
    """Display thinking indicator."""
    console.print("[dim]Thinking...[/dim]", end="\r")


def clear_line() -> None:
    """Clear the current line."""
    console.print(" " * 50, end="\r")


def get_prompt() -> str:
    """Get styled prompt string."""
    return "[bold blue]>[/bold blue] "
