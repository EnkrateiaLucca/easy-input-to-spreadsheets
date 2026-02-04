"""
Easy Input to Spreadsheets - Voice/text natural language interface for spreadsheets.

Powered by the Claude Agent SDK.
"""

__version__ = "0.1.0"

from easy_input_to_spreadsheets.agent import SpreadsheetAgent
from easy_input_to_spreadsheets.manager import SpreadsheetManager

__all__ = ["SpreadsheetAgent", "SpreadsheetManager", "__version__"]
