"""
CLI entry point for Easy Input to Spreadsheets.

This module provides the main() function that serves as the console script
entry point, allowing the tool to be run as `easy-spreadsheets` after installation.
"""

import asyncio
import sys


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    from easy_input_to_spreadsheets.agent import SpreadsheetAgent

    try:
        agent = SpreadsheetAgent()
        asyncio.run(agent.run())
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
