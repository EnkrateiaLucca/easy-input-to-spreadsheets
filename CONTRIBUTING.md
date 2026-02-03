# Contributing to Easy Input to Spreadsheets

Thanks for your interest in contributing! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [Claude Code CLI](https://claude.ai/code) installed
- `ANTHROPIC_API_KEY` environment variable set

### Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/easy-input-to-spreadsheets.git
   cd easy-input-to-spreadsheets
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync --dev

   # Or using pip
   pip install -e ".[dev]"
   ```

3. **Run the application**
   ```bash
   uv run spreadsheet_agent.py
   ```

## Project Structure

```
easy-input-to-spreadsheets/
├── src/easy_input_to_spreadsheets/
│   ├── __init__.py
│   ├── spreadsheet_agent.py   # Main entry point
│   ├── spreadsheet_manager.py # SQLite + CSV storage
│   ├── tools.py               # Claude Agent SDK tools
│   ├── voice_input.py         # Voice recording + transcription
│   └── display.py             # Rich terminal rendering
├── tests/                     # Test files
├── data/                      # SQLite databases (gitignored)
├── exports/                   # CSV exports (gitignored)
├── pyproject.toml             # Project configuration
└── README.md
```

## Making Changes

### Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking

We use [mypy](https://mypy.readthedocs.io/) for static type checking:

```bash
mypy src/
```

### Running Tests

```bash
pytest
```

### Commit Messages

We follow conventional commit messages:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example: `feat: add support for Excel export`

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes** and ensure:
   - Code passes linting (`ruff check .`)
   - Code is formatted (`ruff format .`)
   - Types are correct (`mypy src/`)
   - Tests pass (`pytest`)

3. **Push and create a PR**
   ```bash
   git push origin feat/your-feature-name
   ```

4. **PR Guidelines**
   - Provide a clear description of the changes
   - Link any related issues
   - Include screenshots/demos for UI changes
   - Keep PRs focused and reasonably sized

## Adding New Tools

To add a new spreadsheet tool:

1. Define the tool function in `tools.py` using the `@tool` decorator:
   ```python
   @tool(
       "tool_name",
       "Description of what the tool does",
       {"param1": str, "param2": int}
   )
   async def tool_name_tool(args: dict[str, Any]) -> dict[str, Any]:
       # Implementation
       pass
   ```

2. Add the tool to `create_spreadsheet_server()` and `SPREADSHEET_TOOL_NAMES`

3. Update the system prompt in `spreadsheet_agent.py` to describe the new tool

4. Add tests for the new functionality

## Reporting Issues

When reporting bugs, please include:

- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Any error messages or logs

## Questions?

Feel free to open an issue for any questions about contributing!
