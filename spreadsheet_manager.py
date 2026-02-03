"""
SpreadsheetManager: SQLite-backed spreadsheet storage with CSV export.

Manages multiple spreadsheets as SQLite tables. Each spreadsheet has an
auto-incrementing ID column plus user-defined columns.
"""

import sqlite3
import csv
import re
from pathlib import Path
from typing import Any


class SpreadsheetManager:
    """Manages spreadsheets stored in SQLite with CSV export capability."""

    def __init__(self, db_path: str = "data/spreadsheets.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.current_spreadsheet: str | None = None
        self._init_metadata_table()

    def _init_metadata_table(self):
        """Create metadata table to track spreadsheets and their columns."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS _spreadsheet_meta (
                name TEXT PRIMARY KEY,
                columns TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _sanitize_name(self, name: str) -> str:
        """Convert name to valid SQLite table/column identifier."""
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower().strip())
        if sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized

    def create_spreadsheet(self, name: str, columns: list[str]) -> dict[str, Any]:
        """
        Create a new spreadsheet with the given columns.

        Args:
            name: Human-readable name for the spreadsheet
            columns: List of column names

        Returns:
            Dict with status and spreadsheet info
        """
        table_name = self._sanitize_name(name)

        if self._spreadsheet_exists(table_name):
            return {
                "success": False,
                "error": f"Spreadsheet '{name}' already exists"
            }

        sanitized_columns = [self._sanitize_name(c) for c in columns]

        columns_sql = ", ".join(f'"{col}" TEXT' for col in sanitized_columns)
        self.conn.execute(f'''
            CREATE TABLE "{table_name}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {columns_sql}
            )
        ''')

        self.conn.execute(
            "INSERT INTO _spreadsheet_meta (name, columns) VALUES (?, ?)",
            (table_name, ",".join(sanitized_columns))
        )
        self.conn.commit()

        self.current_spreadsheet = table_name

        return {
            "success": True,
            "spreadsheet": table_name,
            "columns": sanitized_columns,
            "message": f"Created spreadsheet '{name}' with columns: {', '.join(columns)}"
        }

    def _spreadsheet_exists(self, name: str) -> bool:
        """Check if a spreadsheet exists."""
        cursor = self.conn.execute(
            "SELECT name FROM _spreadsheet_meta WHERE name = ?", (name,)
        )
        return cursor.fetchone() is not None

    def get_columns(self, spreadsheet: str | None = None) -> list[str]:
        """Get column names for a spreadsheet (excludes id)."""
        table = spreadsheet or self.current_spreadsheet
        if not table:
            return []

        cursor = self.conn.execute(
            "SELECT columns FROM _spreadsheet_meta WHERE name = ?", (table,)
        )
        row = cursor.fetchone()
        if row:
            return row["columns"].split(",") if row["columns"] else []
        return []

    def add_row(self, data: dict[str, Any], spreadsheet: str | None = None) -> dict[str, Any]:
        """
        Add a row to the spreadsheet.

        Args:
            data: Dict mapping column names to values
            spreadsheet: Target spreadsheet (uses current if None)

        Returns:
            Dict with status and row info
        """
        table = spreadsheet or self.current_spreadsheet
        if not table:
            return {"success": False, "error": "No spreadsheet selected"}

        columns = self.get_columns(table)
        sanitized_data = {}
        for key, value in data.items():
            sanitized_key = self._sanitize_name(key)
            if sanitized_key in columns:
                sanitized_data[sanitized_key] = value

        if not sanitized_data:
            return {"success": False, "error": "No valid columns in data"}

        cols = ", ".join(f'"{c}"' for c in sanitized_data.keys())
        placeholders = ", ".join("?" for _ in sanitized_data)

        cursor = self.conn.execute(
            f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})',
            list(sanitized_data.values())
        )
        self.conn.commit()

        return {
            "success": True,
            "row_id": cursor.lastrowid,
            "message": f"Added row {cursor.lastrowid}"
        }

    def add_column(
        self,
        column_name: str,
        default_value: str = "",
        spreadsheet: str | None = None
    ) -> dict[str, Any]:
        """
        Add a new column to the spreadsheet.

        Args:
            column_name: Name for the new column
            default_value: Default value for existing rows
            spreadsheet: Target spreadsheet (uses current if None)
        """
        table = spreadsheet or self.current_spreadsheet
        if not table:
            return {"success": False, "error": "No spreadsheet selected"}

        sanitized = self._sanitize_name(column_name)
        columns = self.get_columns(table)

        if sanitized in columns:
            return {"success": False, "error": f"Column '{column_name}' already exists"}

        self.conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{sanitized}" TEXT DEFAULT ?',
                         (default_value,))

        columns.append(sanitized)
        self.conn.execute(
            "UPDATE _spreadsheet_meta SET columns = ? WHERE name = ?",
            (",".join(columns), table)
        )
        self.conn.commit()

        return {
            "success": True,
            "column": sanitized,
            "message": f"Added column '{column_name}'"
        }

    def edit_cell(
        self,
        row_id: int,
        column: str,
        value: Any,
        spreadsheet: str | None = None
    ) -> dict[str, Any]:
        """
        Edit a specific cell.

        Args:
            row_id: The row ID to edit
            column: Column name
            value: New value
            spreadsheet: Target spreadsheet (uses current if None)
        """
        table = spreadsheet or self.current_spreadsheet
        if not table:
            return {"success": False, "error": "No spreadsheet selected"}

        sanitized_col = self._sanitize_name(column)
        columns = self.get_columns(table)

        if sanitized_col not in columns:
            return {"success": False, "error": f"Column '{column}' not found"}

        cursor = self.conn.execute(
            f'UPDATE "{table}" SET "{sanitized_col}" = ? WHERE id = ?',
            (value, row_id)
        )
        self.conn.commit()

        if cursor.rowcount == 0:
            return {"success": False, "error": f"Row {row_id} not found"}

        return {
            "success": True,
            "message": f"Updated row {row_id}, column '{column}' to '{value}'"
        }

    def delete_row(self, row_id: int, spreadsheet: str | None = None) -> dict[str, Any]:
        """Delete a row by ID."""
        table = spreadsheet or self.current_spreadsheet
        if not table:
            return {"success": False, "error": "No spreadsheet selected"}

        cursor = self.conn.execute(f'DELETE FROM "{table}" WHERE id = ?', (row_id,))
        self.conn.commit()

        if cursor.rowcount == 0:
            return {"success": False, "error": f"Row {row_id} not found"}

        return {"success": True, "message": f"Deleted row {row_id}"}

    def delete_column(self, column_name: str, spreadsheet: str | None = None) -> dict[str, Any]:
        """
        Delete a column from the spreadsheet.

        Note: SQLite doesn't support DROP COLUMN in older versions,
        so we recreate the table without that column.
        """
        table = spreadsheet or self.current_spreadsheet
        if not table:
            return {"success": False, "error": "No spreadsheet selected"}

        sanitized = self._sanitize_name(column_name)
        columns = self.get_columns(table)

        if sanitized not in columns:
            return {"success": False, "error": f"Column '{column_name}' not found"}

        columns.remove(sanitized)

        temp_table = f"_temp_{table}"
        cols_sql = ", ".join(f'"{c}" TEXT' for c in columns)
        cols_list = ", ".join(f'"{c}"' for c in columns)

        self.conn.execute(f'''
            CREATE TABLE "{temp_table}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {cols_sql}
            )
        ''')
        self.conn.execute(f'''
            INSERT INTO "{temp_table}" (id, {cols_list})
            SELECT id, {cols_list} FROM "{table}"
        ''')
        self.conn.execute(f'DROP TABLE "{table}"')
        self.conn.execute(f'ALTER TABLE "{temp_table}" RENAME TO "{table}"')

        self.conn.execute(
            "UPDATE _spreadsheet_meta SET columns = ? WHERE name = ?",
            (",".join(columns), table)
        )
        self.conn.commit()

        return {"success": True, "message": f"Deleted column '{column_name}'"}

    def get_data(self, spreadsheet: str | None = None) -> dict[str, Any]:
        """
        Get all data from a spreadsheet.

        Returns:
            Dict with columns list and rows list of dicts
        """
        table = spreadsheet or self.current_spreadsheet
        if not table:
            return {"success": False, "error": "No spreadsheet selected", "columns": [], "rows": []}

        columns = self.get_columns(table)
        cursor = self.conn.execute(f'SELECT * FROM "{table}" ORDER BY id')
        rows = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "spreadsheet": table,
            "columns": ["id"] + columns,
            "rows": rows
        }

    def list_spreadsheets(self) -> dict[str, Any]:
        """List all available spreadsheets."""
        cursor = self.conn.execute(
            "SELECT name, columns, created_at FROM _spreadsheet_meta ORDER BY created_at"
        )
        spreadsheets = []
        for row in cursor.fetchall():
            spreadsheets.append({
                "name": row["name"],
                "columns": row["columns"].split(",") if row["columns"] else [],
                "created_at": row["created_at"]
            })

        return {
            "success": True,
            "spreadsheets": spreadsheets,
            "current": self.current_spreadsheet
        }

    def switch_spreadsheet(self, name: str) -> dict[str, Any]:
        """Switch to a different spreadsheet."""
        table = self._sanitize_name(name)

        if not self._spreadsheet_exists(table):
            return {"success": False, "error": f"Spreadsheet '{name}' not found"}

        self.current_spreadsheet = table
        return {
            "success": True,
            "spreadsheet": table,
            "message": f"Switched to spreadsheet '{name}'"
        }

    def export_csv(self, path: str | None = None, spreadsheet: str | None = None) -> dict[str, Any]:
        """
        Export spreadsheet to CSV file.

        Args:
            path: Output file path (defaults to exports/{spreadsheet}.csv)
            spreadsheet: Spreadsheet to export (uses current if None)
        """
        table = spreadsheet or self.current_spreadsheet
        if not table:
            return {"success": False, "error": "No spreadsheet selected"}

        if path is None:
            exports_dir = Path("exports")
            exports_dir.mkdir(exist_ok=True)
            path = str(exports_dir / f"{table}.csv")

        data = self.get_data(table)
        if not data["success"]:
            return data

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data["columns"])
            writer.writeheader()
            writer.writerows(data["rows"])

        return {
            "success": True,
            "path": path,
            "message": f"Exported to {path}"
        }

    def delete_spreadsheet(self, name: str) -> dict[str, Any]:
        """Delete a spreadsheet entirely."""
        table = self._sanitize_name(name)

        if not self._spreadsheet_exists(table):
            return {"success": False, "error": f"Spreadsheet '{name}' not found"}

        self.conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        self.conn.execute("DELETE FROM _spreadsheet_meta WHERE name = ?", (table,))
        self.conn.commit()

        if self.current_spreadsheet == table:
            self.current_spreadsheet = None

        return {"success": True, "message": f"Deleted spreadsheet '{name}'"}

    def close(self):
        """Close database connection."""
        self.conn.close()
