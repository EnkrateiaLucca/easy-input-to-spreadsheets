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

#### Option 1: Install as a tool (Recommended)

```bash
# Install globally with uv
uv tool install easy-input-to-spreadsheets

# Run from anywhere
easy-spreadsheets
```

#### Option 2: Run without installing

```bash
# Run directly with uvx (no installation needed)
uvx easy-input-to-spreadsheets
```

#### Option 3: Install with pip

```bash
# Install from PyPI
pip install easy-input-to-spreadsheets

# Run
easy-spreadsheets
```

#### Option 4: Development setup

```bash
# Clone the repository
git clone https://github.com/EnkrateiaLucca/easy-input-to-spreadsheets.git
cd easy-input-to-spreadsheets

# Install in development mode
pip install -e ".[dev]"

# Or run directly with uv
uv run easy-spreadsheets
```

### Optional: Voice Input Setup

Voice input requires **ffmpeg** and **whisper.cpp**. Follow these steps:

#### 1. Install ffmpeg

```bash
brew install ffmpeg
```

#### 2. Build whisper.cpp

```bash
# Clone and build whisper.cpp in your home directory
cd ~
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
cmake -B build
cmake --build build -j --config Release
```

#### 3. Download a model

```bash
# Download the base English model (recommended for speed)
cd ~/whisper.cpp
sh ./models/download-ggml-model.sh base.en
```

Available models (speed vs accuracy trade-off):
- `tiny.en` - Fastest, least accurate
- `base.en` - Good balance (recommended)
- `small.en` - More accurate, slower
- `medium.en` / `large` - Most accurate, slowest

#### 4. Verify installation

The app auto-detects whisper.cpp if installed in `~/whisper.cpp`. For custom locations, set environment variables:

```bash
export WHISPER_CPP_PATH=/path/to/whisper-cli
export WHISPER_CPP_MODEL=/path/to/ggml-base.en.bin
```

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
├── src/easy_input_to_spreadsheets/
│   ├── __init__.py          # Package version & exports
│   ├── cli.py               # CLI entry point
│   ├── agent.py             # Main agent & REPL loop
│   ├── manager.py           # SQLite + CSV storage layer
│   ├── tools.py             # Claude Agent SDK tool definitions
│   ├── voice_input.py       # Voice recording + whisper.cpp
│   └── display.py           # Rich terminal rendering
├── .github/workflows/       # CI/CD (test + publish)
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
- Build whisper.cpp in `~/whisper.cpp` (see Voice Input Setup above)
- Download a model: `sh ./models/download-ggml-model.sh base.en`
- Or set `WHISPER_CPP_PATH` and `WHISPER_CPP_MODEL` environment variables

**"No spreadsheet selected"**
- Create a spreadsheet first: `"create a new spreadsheet called tasks"`
- Or switch to an existing one: `"switch to expenses"`

## License

MIT - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with the [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/sdk-overview)
- Terminal rendering by [Rich](https://github.com/Textualize/rich)
- Voice transcription by [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
