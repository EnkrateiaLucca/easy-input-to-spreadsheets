# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice/text-based natural language interface for managing spreadsheets, powered by the Claude Agent SDK. Users speak or type commands like "create a spreadsheet for expenses" and Claude interprets and executes them via custom MCP tools.

## Running the Application

```bash
# Primary method (auto-installs dependencies)
uv run spreadsheet_agent.py

# Or with pip
pip install -r requirements.txt && python spreadsheet_agent.py
```

## Development Commands

```bash
# Install dev dependencies
uv sync --dev

# Linting and formatting
ruff check .              # Check for issues
ruff check --fix .        # Auto-fix issues
ruff format .             # Format code

# Type checking
mypy .                    # Run against all files

# Run tests
pytest                    # Run all tests
pytest tests/test_file.py # Run specific test file
pytest -k "test_name"     # Run tests matching pattern
```

## Architecture

### Data Flow
```
User Input → SpreadsheetAgent.process_command() → Claude SDK → MCP Tools → SpreadsheetManager → SQLite
                                                                    ↓
                                                              display.py (Rich output)
```

### Key Components

**spreadsheet_agent.py** - Entry point and REPL loop
- `SpreadsheetAgent` class manages Claude SDK client lifecycle
- `SYSTEM_PROMPT` defines how Claude interprets natural language commands
- Special `!` commands handled locally without going through Claude

**tools.py** - MCP tool definitions using Claude Agent SDK patterns
- Tools use `@tool(name, description, schema)` decorator
- All tools are async and return `{"content": [...], "is_error": bool}` format
- `SPREADSHEET_TOOL_NAMES` list uses `mcp__spreadsheet__<tool>` naming convention
- Global `_manager` instance set via `set_manager()` at startup

**spreadsheet_manager.py** - SQLite storage layer
- Each spreadsheet = SQLite table with auto-increment `id` column
- `_spreadsheet_meta` table tracks spreadsheet names and column schemas
- `_sanitize_name()` converts user input to valid SQLite identifiers
- `current_spreadsheet` tracks active table for operations

**display.py** - Rich terminal rendering
- Exports `console` (Rich Console instance) used throughout
- `render_spreadsheet()` creates styled tables with alternating row colors
- `show_*` functions for consistent message formatting

**voice_input.py** - macOS voice recording + whisper.cpp transcription
- Uses ffmpeg with `avfoundation` device for audio capture (16kHz mono WAV)
- `find_whisper_cli()` auto-discovers whisper-cli in common paths or via `WHISPER_CPP_PATH`
- `find_whisper_model()` auto-discovers model files or via `WHISPER_CPP_MODEL`
- Default search paths: `~/whisper.cpp/build/bin/whisper-cli`, `~/whisper.cpp/models/ggml-*.bin`

### Tool Development Pattern

To add a new spreadsheet tool:

1. Define in `tools.py`:
```python
@tool("tool_name", "Description", {"param": str})
async def tool_name_tool(args: dict[str, Any]) -> dict[str, Any]:
    manager = get_manager()
    # ... implementation
    return {"content": [{"type": "text", "text": "result"}]}
```

2. Add to `create_spreadsheet_server()` tools list
3. Add `mcp__spreadsheet__tool_name` to `SPREADSHEET_TOOL_NAMES`
4. Update `SYSTEM_PROMPT` in `spreadsheet_agent.py`

## Data Storage

- SQLite database: `data/spreadsheets.db`
- CSV exports: `exports/` directory
- Generated plots: `plots/` directory (auto-created)

## Voice Input Requirements (Optional)

- **ffmpeg**: `brew install ffmpeg`
- **whisper.cpp**: Build from source at `~/whisper.cpp`
  ```bash
  cd ~ && git clone https://github.com/ggml-org/whisper.cpp.git
  cd whisper.cpp && cmake -B build && cmake --build build -j --config Release
  sh ./models/download-ggml-model.sh base.en
  ```
- **Environment variables** (for non-standard paths):
  - `WHISPER_CPP_PATH`: Path to `whisper-cli` executable
  - `WHISPER_CPP_MODEL`: Path to model `.bin` file
