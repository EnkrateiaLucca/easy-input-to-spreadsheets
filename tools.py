"""
Spreadsheet tools for the Claude Agent SDK.

Defines custom tools that Claude can call to manipulate spreadsheets.
Uses the @tool decorator and create_sdk_mcp_server() pattern.
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any
from pathlib import Path
import subprocess
import sys

from spreadsheet_manager import SpreadsheetManager
from display import (
    render_spreadsheet,
    render_spreadsheet_list,
    show_success,
    show_error,
    show_info,
)


# Global manager instance - will be set by the main agent
_manager: SpreadsheetManager | None = None


def set_manager(manager: SpreadsheetManager):
    """Set the global spreadsheet manager instance."""
    global _manager
    _manager = manager


def get_manager() -> SpreadsheetManager:
    """Get the spreadsheet manager, raising if not initialized."""
    if _manager is None:
        raise RuntimeError("SpreadsheetManager not initialized")
    return _manager


@tool(
    "create_spreadsheet",
    "Create a new spreadsheet with specified columns. Use this when the user wants to start a new table or spreadsheet.",
    {"name": str, "columns": str}  # columns is comma-separated string
)
async def create_spreadsheet_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Create a new spreadsheet with the given name and columns."""
    manager = get_manager()

    name = args["name"]
    columns_str = args["columns"]
    columns = [c.strip() for c in columns_str.split(",") if c.strip()]

    if not columns:
        return {
            "content": [{"type": "text", "text": "Error: No columns specified"}],
            "is_error": True
        }

    result = manager.create_spreadsheet(name, columns)

    if result["success"]:
        show_success(result["message"])
        data = manager.get_data()
        render_spreadsheet(data)
        return {
            "content": [{
                "type": "text",
                "text": f"Created spreadsheet '{name}' with columns: {', '.join(columns)}. The spreadsheet is now displayed."
            }]
        }
    else:
        show_error(result["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {result['error']}"}],
            "is_error": True
        }


@tool(
    "add_row",
    "Add a new row to the current spreadsheet. Provide data as column:value pairs.",
    {"data": str}  # Format: "column1:value1, column2:value2"
)
async def add_row_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Add a row with the given data."""
    manager = get_manager()

    data_str = args["data"]
    data = {}

    for pair in data_str.split(","):
        if ":" in pair:
            key, value = pair.split(":", 1)
            data[key.strip()] = value.strip()

    if not data:
        return {
            "content": [{"type": "text", "text": "Error: No valid data provided. Use format 'column:value, column:value'"}],
            "is_error": True
        }

    result = manager.add_row(data)

    if result["success"]:
        show_success(result["message"])
        spreadsheet_data = manager.get_data()
        render_spreadsheet(spreadsheet_data)
        return {
            "content": [{
                "type": "text",
                "text": f"Added row {result['row_id']}. The updated spreadsheet is now displayed."
            }]
        }
    else:
        show_error(result["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {result['error']}"}],
            "is_error": True
        }


@tool(
    "add_column",
    "Add a new column to the current spreadsheet.",
    {"column_name": str, "default_value": str}
)
async def add_column_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Add a new column to the spreadsheet."""
    manager = get_manager()

    result = manager.add_column(
        args["column_name"],
        args.get("default_value", "")
    )

    if result["success"]:
        show_success(result["message"])
        data = manager.get_data()
        render_spreadsheet(data)
        return {
            "content": [{
                "type": "text",
                "text": f"Added column '{args['column_name']}'. The updated spreadsheet is now displayed."
            }]
        }
    else:
        show_error(result["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {result['error']}"}],
            "is_error": True
        }


@tool(
    "edit_cell",
    "Edit a specific cell in the spreadsheet by row ID and column name.",
    {"row_id": int, "column": str, "value": str}
)
async def edit_cell_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Edit a specific cell."""
    manager = get_manager()

    result = manager.edit_cell(
        args["row_id"],
        args["column"],
        args["value"]
    )

    if result["success"]:
        show_success(result["message"])
        data = manager.get_data()
        render_spreadsheet(data)
        return {
            "content": [{
                "type": "text",
                "text": f"Updated row {args['row_id']}, column '{args['column']}' to '{args['value']}'. The updated spreadsheet is now displayed."
            }]
        }
    else:
        show_error(result["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {result['error']}"}],
            "is_error": True
        }


@tool(
    "delete_row",
    "Delete a row from the spreadsheet by its ID.",
    {"row_id": int}
)
async def delete_row_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Delete a row by ID."""
    manager = get_manager()

    result = manager.delete_row(args["row_id"])

    if result["success"]:
        show_success(result["message"])
        data = manager.get_data()
        render_spreadsheet(data)
        return {
            "content": [{
                "type": "text",
                "text": f"Deleted row {args['row_id']}. The updated spreadsheet is now displayed."
            }]
        }
    else:
        show_error(result["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {result['error']}"}],
            "is_error": True
        }


@tool(
    "delete_column",
    "Delete a column from the spreadsheet by name.",
    {"column_name": str}
)
async def delete_column_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Delete a column by name."""
    manager = get_manager()

    result = manager.delete_column(args["column_name"])

    if result["success"]:
        show_success(result["message"])
        data = manager.get_data()
        render_spreadsheet(data)
        return {
            "content": [{
                "type": "text",
                "text": f"Deleted column '{args['column_name']}'. The updated spreadsheet is now displayed."
            }]
        }
    else:
        show_error(result["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {result['error']}"}],
            "is_error": True
        }


@tool(
    "display",
    "Display the current spreadsheet. Use this to show the user the current state of the data.",
    {}
)
async def display_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Display the current spreadsheet."""
    manager = get_manager()

    data = manager.get_data()

    if data["success"]:
        render_spreadsheet(data)
        row_count = len(data["rows"])
        col_count = len(data["columns"]) - 1  # Exclude 'id' column
        return {
            "content": [{
                "type": "text",
                "text": f"Displayed spreadsheet '{data['spreadsheet']}' with {row_count} rows and {col_count} columns."
            }]
        }
    else:
        show_error(data["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {data['error']}"}],
            "is_error": True
        }


@tool(
    "list_spreadsheets",
    "List all available spreadsheets in the database.",
    {}
)
async def list_spreadsheets_tool(args: dict[str, Any]) -> dict[str, Any]:
    """List all spreadsheets."""
    manager = get_manager()

    result = manager.list_spreadsheets()
    render_spreadsheet_list(result)

    count = len(result["spreadsheets"])
    current = result.get("current", "none")

    return {
        "content": [{
            "type": "text",
            "text": f"Found {count} spreadsheet(s). Current: {current or 'none selected'}"
        }]
    }


@tool(
    "switch_spreadsheet",
    "Switch to a different spreadsheet by name.",
    {"name": str}
)
async def switch_spreadsheet_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Switch to a different spreadsheet."""
    manager = get_manager()

    result = manager.switch_spreadsheet(args["name"])

    if result["success"]:
        show_success(result["message"])
        data = manager.get_data()
        render_spreadsheet(data)
        return {
            "content": [{
                "type": "text",
                "text": f"Switched to spreadsheet '{args['name']}'. The spreadsheet is now displayed."
            }]
        }
    else:
        show_error(result["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {result['error']}"}],
            "is_error": True
        }


@tool(
    "export_csv",
    "Export the current spreadsheet to a CSV file.",
    {"filename": str}
)
async def export_csv_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Export to CSV."""
    manager = get_manager()

    filename = args.get("filename", "")
    if filename and not filename.endswith(".csv"):
        filename += ".csv"

    path = f"exports/{filename}" if filename else None
    result = manager.export_csv(path)

    if result["success"]:
        show_success(result["message"])
        return {
            "content": [{
                "type": "text",
                "text": f"Exported spreadsheet to {result['path']}"
            }]
        }
    else:
        show_error(result["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {result['error']}"}],
            "is_error": True
        }


@tool(
    "plot_data",
    "Create a visualization/plot of the spreadsheet data. If no parameters specified, analyze the data and create the most appropriate visualization. Supports bar, line, scatter, pie, and histogram charts.",
    {"plot_type": str, "x_column": str, "y_column": str, "title": str, "output_file": str}
)
async def plot_data_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Create a plot/visualization of the current spreadsheet data.

    Parameters are all optional - if not provided, the tool will analyze the data
    and create the most sensible visualization.
    """
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt

    manager = get_manager()
    data = manager.get_data()

    if not data["success"]:
        show_error(data["error"])
        return {
            "content": [{"type": "text", "text": f"Error: {data['error']}"}],
            "is_error": True
        }

    rows = data["rows"]
    columns = data["columns"]
    spreadsheet_name = data["spreadsheet"]

    if not rows:
        show_error("No data to plot. Add some rows first.")
        return {
            "content": [{"type": "text", "text": "Error: No data to plot. The spreadsheet is empty."}],
            "is_error": True
        }

    # Get parameters (all optional)
    plot_type = args.get("plot_type", "").lower().strip()
    x_column = args.get("x_column", "").strip()
    y_column = args.get("y_column", "").strip()
    title = args.get("title", "").strip()
    output_file = args.get("output_file", "").strip()

    # Filter out 'id' from plottable columns
    plottable_cols = [c for c in columns if c != "id"]

    if not plottable_cols:
        show_error("No plottable columns found.")
        return {
            "content": [{"type": "text", "text": "Error: No plottable columns in the spreadsheet."}],
            "is_error": True
        }

    # Helper function to check if a column has numeric data
    def is_numeric_column(col: str) -> bool:
        for row in rows:
            val = row.get(col, "")
            if val:
                try:
                    float(str(val).replace(",", "").replace("$", ""))
                    return True
                except (ValueError, TypeError):
                    pass
        return False

    # Helper to extract numeric values
    def get_numeric_values(col: str) -> list[float]:
        values = []
        for row in rows:
            val = row.get(col, "")
            if val:
                try:
                    num = float(str(val).replace(",", "").replace("$", ""))
                    values.append(num)
                except (ValueError, TypeError):
                    values.append(0.0)
            else:
                values.append(0.0)
        return values

    # Identify numeric and categorical columns
    numeric_cols = [c for c in plottable_cols if is_numeric_column(c)]
    categorical_cols = [c for c in plottable_cols if c not in numeric_cols]

    # Auto-select plot type and columns if not specified
    if not plot_type:
        if len(numeric_cols) >= 2:
            plot_type = "scatter"
        elif len(numeric_cols) == 1 and categorical_cols:
            plot_type = "bar"
        elif len(numeric_cols) == 1:
            plot_type = "histogram"
        elif categorical_cols:
            plot_type = "bar"  # Count-based bar chart
        else:
            plot_type = "bar"

    # Auto-select columns if not specified
    if not x_column:
        if categorical_cols:
            x_column = categorical_cols[0]
        elif numeric_cols:
            x_column = numeric_cols[0]
        else:
            x_column = plottable_cols[0]

    if not y_column and plot_type not in ("histogram", "pie"):
        if numeric_cols:
            # Pick a numeric column different from x if possible
            y_candidates = [c for c in numeric_cols if c != x_column]
            y_column = y_candidates[0] if y_candidates else (numeric_cols[0] if numeric_cols else "")

    # Generate title if not provided
    if not title:
        title = f"{spreadsheet_name.replace('_', ' ').title()}"
        if plot_type == "histogram":
            title += f" - {x_column.replace('_', ' ').title()} Distribution"
        elif y_column:
            title += f" - {y_column.replace('_', ' ').title()} by {x_column.replace('_', ' ').title()}"

    # Create figure with nice styling
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    try:
        if plot_type == "bar":
            x_values = [str(row.get(x_column, "")) or "—" for row in rows]
            if y_column and is_numeric_column(y_column):
                y_values = get_numeric_values(y_column)
            else:
                # Count occurrences
                from collections import Counter
                counts = Counter(x_values)
                x_values = list(counts.keys())
                y_values = list(counts.values())
                y_column = "count"

            colors = plt.cm.viridis([i / len(x_values) for i in range(len(x_values))])
            bars = ax.bar(range(len(x_values)), y_values, color=colors)
            ax.set_xticks(range(len(x_values)))
            ax.set_xticklabels(x_values, rotation=45, ha='right')
            ax.set_ylabel(y_column.replace('_', ' ').title())
            ax.set_xlabel(x_column.replace('_', ' ').title())

            # Add value labels on bars
            for bar, val in zip(bars, y_values):
                height = bar.get_height()
                ax.annotate(f'{val:.1f}' if isinstance(val, float) else str(val),
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)

        elif plot_type == "line":
            x_values = list(range(len(rows)))
            x_labels = [str(row.get(x_column, i)) for i, row in enumerate(rows)]
            y_values = get_numeric_values(y_column) if y_column else [i for i in range(len(rows))]

            ax.plot(x_values, y_values, marker='o', linewidth=2, markersize=6, color='#2196F3')
            ax.fill_between(x_values, y_values, alpha=0.3, color='#2196F3')
            ax.set_xticks(x_values)
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
            ax.set_ylabel(y_column.replace('_', ' ').title() if y_column else 'Value')
            ax.set_xlabel(x_column.replace('_', ' ').title())

        elif plot_type == "scatter":
            if not y_column:
                y_column = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
            x_values = get_numeric_values(x_column)
            y_values = get_numeric_values(y_column)

            scatter = ax.scatter(x_values, y_values, c=range(len(x_values)), cmap='viridis',
                                s=100, alpha=0.7, edgecolors='white', linewidth=1)
            ax.set_xlabel(x_column.replace('_', ' ').title())
            ax.set_ylabel(y_column.replace('_', ' ').title())
            plt.colorbar(scatter, label='Row Index')

        elif plot_type == "pie":
            x_values = [str(row.get(x_column, "")) or "Unknown" for row in rows]
            if y_column and is_numeric_column(y_column):
                y_values = get_numeric_values(y_column)
                # Aggregate by x_values
                from collections import defaultdict
                agg = defaultdict(float)
                for x, y in zip(x_values, y_values):
                    agg[x] += y
                labels = list(agg.keys())
                sizes = list(agg.values())
            else:
                from collections import Counter
                counts = Counter(x_values)
                labels = list(counts.keys())
                sizes = list(counts.values())

            colors = plt.cm.Set3([i / len(labels) for i in range(len(labels))])
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                              colors=colors, startangle=90,
                                              explode=[0.02] * len(labels))
            ax.axis('equal')

        elif plot_type == "histogram":
            values = get_numeric_values(x_column)
            n, bins, patches = ax.hist(values, bins='auto', color='#4CAF50',
                                       edgecolor='white', alpha=0.7)
            ax.set_xlabel(x_column.replace('_', ' ').title())
            ax.set_ylabel('Frequency')

            # Color gradient
            for i, patch in enumerate(patches):
                patch.set_facecolor(plt.cm.viridis(i / len(patches)))

        else:
            show_error(f"Unknown plot type: {plot_type}")
            return {
                "content": [{"type": "text", "text": f"Error: Unknown plot type '{plot_type}'. Supported types: bar, line, scatter, pie, histogram"}],
                "is_error": True
            }

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()

        # Generate output path
        if not output_file:
            plots_dir = Path("plots")
            plots_dir.mkdir(exist_ok=True)
            output_file = str(plots_dir / f"{spreadsheet_name}_{plot_type}.png")
        elif not output_file.endswith(('.png', '.jpg', '.pdf', '.svg')):
            output_file += '.png'

        # Ensure directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        # Save the plot
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        show_success(f"Created {plot_type} chart: {output_file}")

        # Open the plot file
        if sys.platform == "darwin":
            subprocess.run(["open", output_file], check=False)
        elif sys.platform == "win32":
            subprocess.run(["start", output_file], shell=True, check=False)
        else:
            subprocess.run(["xdg-open", output_file], check=False)

        show_info("Plot opened in default viewer")

        return {
            "content": [{
                "type": "text",
                "text": f"Created {plot_type} chart and saved to {output_file}. The plot has been opened for viewing. X-axis: {x_column}, Y-axis: {y_column or 'N/A'}"
            }]
        }

    except Exception as e:
        plt.close(fig)
        show_error(f"Failed to create plot: {e}")
        return {
            "content": [{"type": "text", "text": f"Error creating plot: {e}"}],
            "is_error": True
        }


def create_spreadsheet_server():
    """Create the MCP server with all spreadsheet tools."""
    return create_sdk_mcp_server(
        name="spreadsheet",
        version="1.0.0",
        tools=[
            create_spreadsheet_tool,
            add_row_tool,
            add_column_tool,
            edit_cell_tool,
            delete_row_tool,
            delete_column_tool,
            display_tool,
            list_spreadsheets_tool,
            switch_spreadsheet_tool,
            export_csv_tool,
            plot_data_tool,
        ]
    )


# List of tool names for allowed_tools configuration
SPREADSHEET_TOOL_NAMES = [
    "mcp__spreadsheet__create_spreadsheet",
    "mcp__spreadsheet__add_row",
    "mcp__spreadsheet__add_column",
    "mcp__spreadsheet__edit_cell",
    "mcp__spreadsheet__delete_row",
    "mcp__spreadsheet__delete_column",
    "mcp__spreadsheet__display",
    "mcp__spreadsheet__list_spreadsheets",
    "mcp__spreadsheet__switch_spreadsheet",
    "mcp__spreadsheet__export_csv",
    "mcp__spreadsheet__plot_data",
]
