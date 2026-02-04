# Best Practices Guide: Lessons from simonw/claude-code-transcripts

This guide compares our repo structure with Simon Willison's `claude-code-transcripts` project and outlines improvements to adopt.

## Summary of Gaps

| Area | claude-code-transcripts | easy-input-to-spreadsheets | Priority |
|------|------------------------|---------------------------|----------|
| Package layout | `src/` layout | Flat modules in root | High |
| CLI entry point | Defined in pyproject.toml | None (run via `python file.py`) | High |
| CI testing | Matrix: 5 Python × 3 OS | None | High |
| PyPI publishing | Automated on release | Manual/none | Medium |
| Tests directory | `tests/` with pytest | `tests/` exists but no CI | Medium |

---

## 1. Adopt `src/` Package Layout

**Why:** The `src/` layout prevents accidental imports of local modules during development and is the modern Python packaging standard.

**Current structure:**
```
easy-input-to-spreadsheets/
├── spreadsheet_agent.py
├── spreadsheet_manager.py
├── tools.py
├── display.py
└── voice_input.py
```

**Target structure:**
```
easy-input-to-spreadsheets/
└── src/
    └── easy_input_to_spreadsheets/
        ├── __init__.py
        ├── cli.py              # Entry point (main())
        ├── agent.py            # SpreadsheetAgent class
        ├── manager.py          # SpreadsheetManager class
        ├── tools.py
        ├── display.py
        └── voice_input.py
```

**Changes to pyproject.toml:**
```toml
[project.scripts]
easy-spreadsheets = "easy_input_to_spreadsheets.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/easy_input_to_spreadsheets"]
```

---

## 2. Add GitHub Actions CI

**Why:** Automated testing catches regressions before merge and validates cross-platform compatibility.

**Create `.github/workflows/test.yml`:**
```yaml
name: Test

on: [push, pull_request]

permissions:
  contents: read

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: pyproject.toml
      - run: pip install -e ".[dev]"
      - run: pytest
        env:
          PYTHONUTF8: 1
```

*Note: Windows excluded since voice_input.py uses macOS-specific `avfoundation`.*

---

## 3. Add PyPI Publishing Workflow

**Why:** Automated releases reduce human error and ensure consistent package builds.

**Create `.github/workflows/publish.yml`:**
```yaml
name: Publish

on:
  release:
    types: [created]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest

  deploy:
    runs-on: ubuntu-latest
    needs: [test]
    environment: release
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

---

## 4. Define CLI Entry Point

**Why:** Allows `pip install` to create a runnable command, enabling `uvx easy-spreadsheets` or `pipx install`.

**Add to pyproject.toml:**
```toml
[project.scripts]
easy-spreadsheets = "easy_input_to_spreadsheets.cli:main"
```

**Users can then run:**
```bash
# Install globally
uv tool install easy-input-to-spreadsheets

# Or run without installing
uvx easy-input-to-spreadsheets
```

---

## 5. Implementation Checklist

1. [ ] Create `src/easy_input_to_spreadsheets/` directory structure
2. [ ] Move and rename modules (agent.py, manager.py, etc.)
3. [ ] Create `cli.py` with `main()` entry point wrapping the async run
4. [ ] Update imports throughout the codebase
5. [ ] Update pyproject.toml with `[project.scripts]` and build config
6. [ ] Create `.github/workflows/test.yml`
7. [ ] Create `.github/workflows/publish.yml`
8. [ ] Configure PyPI trusted publishing in GitHub repo settings
9. [ ] Test with `uv run pytest` and `uv run easy-spreadsheets`
10. [ ] Tag a release to trigger publish workflow

---

## Key Takeaways

- **Installable CLI** = broader adoption (users run `uvx easy-spreadsheets`, not `python script.py`)
- **CI matrix testing** = confidence in cross-version compatibility
- **Automated publishing** = consistent releases without manual PyPI uploads
- **`src/` layout** = cleaner separation, standard packaging practice
