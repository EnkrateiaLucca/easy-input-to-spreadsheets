# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "claude-agent-sdk",
#     "rich",
#     "anthropic",
#     "matplotlib"
# ]
# ///
"""
Spreadsheet Agent: Voice/text-based natural language interface for spreadsheets.

Uses the Claude Agent SDK to interpret commands and manipulate spreadsheets
stored in SQLite with CSV export capability.

Usage:
    uv run spreadsheet_agent.py

Commands:
    - Natural language: "create a spreadsheet for expenses", "add row: coffee, 5"
    - !voice  - Record voice command (requires ffmpeg + transcribe)
    - !show   - Display current spreadsheet
    - !list   - List all spreadsheets
    - !export - Export to CSV
    - !help   - Show help
    - !quit   - Exit
"""

import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
from rich.console import Console

from spreadsheet_manager import SpreadsheetManager
from tools import set_manager, create_spreadsheet_server, SPREADSHEET_TOOL_NAMES
from display import (
    show_welcome,
    show_help,
    show_error,
    show_info,
    show_success,
    render_spreadsheet,
    render_spreadsheet_list,
    console,
)
from voice_input import get_voice_input, check_voice_available


SYSTEM_PROMPT = """You are a spreadsheet assistant. You help users create and manage spreadsheets through natural language commands.

IMPORTANT: You have access to spreadsheet tools that you MUST use to perform operations. Do not just describe what you would do - actually call the tools to do it.

Available operations via tools:
- create_spreadsheet: Create new spreadsheets with custom columns
- add_row: Add rows with data (format: "column:value, column:value")
- add_column: Add new columns
- edit_cell: Modify specific cells by row ID and column name
- delete_row: Remove rows by ID
- delete_column: Remove columns by name
- display: Show current spreadsheet state
- list_spreadsheets: Show all available spreadsheets
- switch_spreadsheet: Change to a different spreadsheet
- export_csv: Export to CSV file
- plot_data: Create visualizations (bar, line, scatter, pie, histogram). If no parameters given, analyze the data and create the most appropriate chart automatically.

Interpret user commands (even vague ones) and call the appropriate tools.

Examples of how to interpret commands:
- "make a new table for tracking expenses" → create_spreadsheet with name "expenses" and columns like "description, amount, category, date"
- "add coffee 5 dollars" → add_row with "description:coffee, amount:5"
- "change row 2 price to 10" → edit_cell with row_id=2, column="price", value="10"
- "show me the data" → display
- "remove the notes column" → delete_column with column_name="notes"
- "plot the data" or "visualize this" → plot_data (auto-selects best chart type)
- "show me a bar chart of sales by category" → plot_data with plot_type="bar", x_column="category", y_column="sales"
- "create a pie chart" → plot_data with plot_type="pie"

When a user describes data to add, infer which columns the values belong to based on the current spreadsheet structure.

Always call the display tool after modifications so users see the result. If no spreadsheet exists yet, suggest creating one first."""


class SpreadsheetAgent:
    """Main agent class that handles the REPL and Claude SDK integration."""

    def __init__(self, db_path: str = "data/spreadsheets.db"):
        self.manager = SpreadsheetManager(db_path)
        set_manager(self.manager)
        self.voice_available, self.voice_error = check_voice_available()
        self.client: ClaudeSDKClient | None = None

    async def setup_client(self):
        """Initialize the Claude SDK client with spreadsheet tools."""
        spreadsheet_server = create_spreadsheet_server()

        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            mcp_servers={"spreadsheet": spreadsheet_server},
            allowed_tools=SPREADSHEET_TOOL_NAMES,
            permission_mode="bypassPermissions",
        )

        self.client = ClaudeSDKClient(options=options)
        await self.client.connect()

    async def process_command(self, command: str) -> bool:
        """
        Process a user command through Claude.

        Returns True if should continue, False if should exit.
        """
        if not command.strip():
            return True

        # Handle special commands
        if command.startswith("!"):
            return await self.handle_special_command(command)

        # Send to Claude for interpretation
        if not self.client:
            show_error("Client not initialized")
            return True

        try:
            console.print("[dim]Processing...[/dim]")

            await self.client.query(command)

            # Process response
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            # Only show text that's not just tool call confirmations
                            text = block.text.strip()
                            if text and not text.startswith("I'll") and len(text) > 20:
                                console.print(f"\n[cyan]{text}[/cyan]")

        except Exception as e:
            show_error(f"Error processing command: {e}")

        return True

    async def handle_special_command(self, command: str) -> bool:
        """Handle special ! commands."""
        cmd = command.lower().strip()

        if cmd in ("!quit", "!exit", "!q"):
            return False

        elif cmd in ("!help", "!h"):
            show_help()

        elif cmd in ("!show", "!display", "!d"):
            data = self.manager.get_data()
            if data["success"]:
                render_spreadsheet(data)
            else:
                show_info("No spreadsheet selected. Create one first.")

        elif cmd in ("!list", "!ls"):
            result = self.manager.list_spreadsheets()
            render_spreadsheet_list(result)

        elif cmd.startswith("!export"):
            parts = cmd.split(maxsplit=1)
            filename = parts[1] if len(parts) > 1 else None
            result = self.manager.export_csv(filename)
            if result["success"]:
                show_success(result["message"])
            else:
                show_error(result["error"])

        elif cmd in ("!voice", "!v"):
            if not self.voice_available:
                show_error(f"Voice input not available. {self.voice_error}")
                return True

            text = get_voice_input()
            if text:
                console.print()
                return await self.process_command(text)

        else:
            show_error(f"Unknown command: {cmd}")
            show_info("Type !help for available commands")

        return True

    async def run(self):
        """Main REPL loop."""
        show_welcome()

        if not self.voice_available:
            show_info(f"Voice input disabled: {self.voice_error}")

        # Check for existing spreadsheets
        existing = self.manager.list_spreadsheets()
        if existing["spreadsheets"]:
            show_info(f"Found {len(existing['spreadsheets'])} existing spreadsheet(s)")
            render_spreadsheet_list(existing)

            # Auto-select the first one if none selected
            if not self.manager.current_spreadsheet:
                first = existing["spreadsheets"][0]["name"]
                self.manager.switch_spreadsheet(first)
                show_info(f"Auto-selected '{first}'")

        try:
            await self.setup_client()

            running = True
            while running:
                try:
                    console.print()
                    user_input = console.input("[bold blue]>[/bold blue] ")
                    running = await self.process_command(user_input)

                except KeyboardInterrupt:
                    console.print("\n[dim]Use !quit to exit[/dim]")
                    continue

                except EOFError:
                    break

        except Exception as e:
            show_error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.client:
                await self.client.disconnect()
            self.manager.close()
            console.print("\n[dim]Goodbye![/dim]")


async def main():
    """Entry point."""
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    if script_dir != Path.cwd():
        import os
        os.chdir(script_dir)

    agent = SpreadsheetAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
