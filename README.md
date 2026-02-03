# Easy Input to Spreadsheets

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Agent SDK](https://img.shields.io/badge/powered%20by-Claude%20Agent%20SDK-purple.svg)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/sdk-overview)

A voice/text-based natural language interface for managing spreadsheets, powered by the **Claude Agent SDK**.

Speak or type commands like *"create a spreadsheet for expenses"* or *"add coffee, 5 dollars"* and watch Claude interpret and execute them in real-time.

## Features

- **Natural Language Interface** - Create and manage spreadsheets using plain English
- **Voice Input** - Record commands via microphone (requires ffmpeg + whisper.cpp)
- **Smart Visualization** - Generate charts and plots from your data automatically
- **SQLite Storage** - Persistent data storage with CSV export
- **Rich Terminal UI** - Beautiful table rendering with the Rich library

## Quick Start

### Prerequisites

- Python 3.12+
- [Claude Code CLI](https://claude.ai/code) installed
- `ANTHROPIC_API_KEY` environment variable set

### Installation

```bash
# Clone the repository
git clone https://github.com/EnkrateiaLucca/easy-input-to-spreadsheets.git
cd easy-input-to-spreadsheets

# Run with uv (auto-installs dependencies)
uv run spreadsheet_agent.py
```

Or with pip:

```bash
pip install claude-agent-sdk rich anthropic matplotlib
python spreadsheet_agent.py
```

### Optional: Voice Input

For voice commands, install:
- ffmpeg: `brew install ffmpeg`
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) with `transcribe` command in PATH

## Usage

### Natural Language Commands

Just type what you want to do:

```
> create a spreadsheet for tracking my reading list

> add dune by frank herbert, status reading

> change row 1 status to finished

> add a column called notes

> show me the spreadsheet

> create a pie chart of status

> export to reading_list.csv
```

### Special Commands

| Command | Description |
|---------|-------------|
| `!voice` / `!v` | Record voice input |
| `!show` / `!d` | Display current spreadsheet |
| `!list` / `!ls` | List all spreadsheets |
| `!export [name]` | Export to CSV |
| `!help` / `!h` | Show help |
| `!quit` / `!q` | Exit |

### Visualization

Generate charts with natural language:

```
> visualize this data
> create a bar chart of sales by category
> show me a pie chart of payment methods
> plot amount over time as a line chart
```

Supported chart types: `bar`, `line`, `scatter`, `pie`, `histogram`

## Example Session

```
┌─────────────────────────────────────────────┐
│ Spreadsheet Agent Ready                     │
│ Type commands in natural language or use    │
│ !voice for voice input                      │
└─────────────────────────────────────────────┘

> create an expense tracker with date, description, amount, category

✓ Created spreadsheet 'expense_tracker'
┌────┬──────┬─────────────┬────────┬──────────┐
│ ID │ Date │ Description │ Amount │ Category │
└────┴──────┴─────────────┴────────┴──────────┘

> add today, morning coffee, 4.50, food

✓ Added row 1
┌────┬───────┬────────────────┬────────┬──────────┐
│ ID │ Date  │ Description    │ Amount │ Category │
├────┼───────┼────────────────┼────────┼──────────┤
│  1 │ today │ morning coffee │ 4.50   │ food     │
└────┴───────┴────────────────┴────────┴──────────┘

> show me a pie chart of spending by category

✓ Created pie chart: expense_tracker_pie.png
```

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   You speak/    │────▶│  Claude Agent   │────▶│   Spreadsheet   │
│   type command  │     │  interprets it  │     │   operations    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                        ┌─────────────────┐              │
                        │  Rich terminal  │◀─────────────┘
                        │    display      │
                        └─────────────────┘
```

1. **You speak or type** a natural language command
2. **Claude interprets** the command using the Agent SDK
3. **Tools execute** the actual spreadsheet operations (SQLite)
4. **Results display** immediately in a rich terminal table

The agent maintains conversation context, so commands like *"add another one"* or *"change that to 10"* work naturally.

## Project Structure

```
easy-input-to-spreadsheets/
├── spreadsheet_agent.py     # Main entry point & REPL
├── spreadsheet_manager.py   # SQLite + CSV storage layer
├── tools.py                 # Claude Agent SDK tool definitions
├── voice_input.py           # Voice recording + transcription
├── display.py               # Rich terminal rendering
├── pyproject.toml           # Project configuration
├── data/                    # SQLite databases
└── exports/                 # CSV exports
```

## Data Storage

- **SQLite**: All spreadsheets are stored in `data/spreadsheets.db`
- **CSV Export**: Use `!export filename` to export any spreadsheet
- **Multiple Spreadsheets**: Create and switch between different tables

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Troubleshooting

**"Claude Code not found"**
- Install Claude Code CLI: `curl -fsSL https://claude.ai/install.sh | bash`

**"Voice input not available"**
- Install ffmpeg: `brew install ffmpeg`
- Ensure `transcribe` command is in your PATH (whisper.cpp)

**"No spreadsheet selected"**
- Create a spreadsheet first: `"create a new spreadsheet called tasks"`
- Or switch to an existing one: `"switch to expenses"`

## License

MIT - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with the [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/sdk-overview)
- Terminal rendering by [Rich](https://github.com/Textualize/rich)
- Voice transcription by [whisper.cpp](https://github.com/ggerganov/whisper.cpp)
