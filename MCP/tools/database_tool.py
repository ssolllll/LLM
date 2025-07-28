"""Database operations tool for MCP servers."""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base_tool import BaseTool


class DatabaseTool(BaseTool):
    """Tool for database operations including SQLite, JSON, and CSV operations."""

    def __init__(
        self,
        name: str = "database_operations",
        description: str = "Perform database operations on SQLite, JSON files, and CSV files",
        input_schema: dict[str, Any] | None = None,
        title: str | None = "Database Operations Tool",
    ) -> None:
        if input_schema is None:
            input_schema = {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["query", "execute", "create_table", "insert", "update", "delete", "read_json", "write_json", "read_csv", "write_csv"],
                        "description": "The database operation to perform"
                    },
                    "db_type": {
                        "type": "string",
                        "enum": ["sqlite", "json", "csv"],
                        "description": "Database type"
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Path to database file"
                    },
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (for SQLite)"
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Table name"
                    },
                    "data": {
                        "type": ["object", "array"],
                        "description": "Data to insert/update"
                    },
                    "conditions": {
                        "type": "object",
                        "description": "Conditions for update/delete operations"
                    },
                    "columns": {
                        "type": "array",
                        "description": "Column definitions for table creation"
                    }
                },
                "required": ["operation", "db_type", "db_path"]
            }
        
        super().__init__(name, description, input_schema, title)

    async def execute(self, arguments: dict[str, Any]) -> Any:
        """Execute database operation."""
        operation = arguments.get("operation")
        db_type = arguments.get("db_type")
        db_path = arguments.get("db_path")

        if not db_path:
            raise ValueError("Database path is required")

        try:
            if db_type == "sqlite":
                return await self._handle_sqlite_operation(operation, db_path, arguments)
            elif db_type == "json":
                return await self._handle_json_operation(operation, db_path, arguments)
            elif db_type == "csv":
                return await self._handle_csv_operation(operation, db_path, arguments)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")

        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            return {"error": str(e), "operation": operation, "db_type": db_type, "db_path": db_path}

    async def _handle_sqlite_operation(self, operation: str, db_path: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle SQLite operations."""
        try:
            import sqlite3
        except ImportError:
            raise ImportError("sqlite3 module is required for SQLite operations")

        def _execute_sqlite():
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()

            try:
                if operation == "query":
                    query = arguments.get("query")
                    if not query:
                        raise ValueError("Query is required for query operation")
                    
                    cursor.execute(query)
                    rows = [dict(row) for row in cursor.fetchall()]
                    return {
                        "success": True,
                        "operation": "query",
                        "rows": rows,
                        "count": len(rows)
                    }

                elif operation == "execute":
                    query = arguments.get("query")
                    if not query:
                        raise ValueError("Query is required for execute operation")
                    
                    cursor.execute(query)
                    conn.commit()
                    return {
                        "success": True,
                        "operation": "execute",
                        "rows_affected": cursor.rowcount
                    }

                elif operation == "create_table":
                    table_name = arguments.get("table_name")
                    columns = arguments.get("columns")
                    if not table_name or not columns:
                        raise ValueError("Table name and columns are required")
                    
                    columns_sql = ", ".join(columns)
                    query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
                    cursor.execute(query)
                    conn.commit()
                    return {
                        "success": True,
                        "operation": "create_table",
                        "table_name": table_name
                    }

                elif operation == "insert":
                    table_name = arguments.get("table_name")
                    data = arguments.get("data")
                    if not table_name or not data:
                        raise ValueError("Table name and data are required")
                    
                    if isinstance(data, dict):
                        data = [data]
                    
                    for row in data:
                        columns = ", ".join(row.keys())
                        placeholders = ", ".join(["?" for _ in row.keys()])
                        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                        cursor.execute(query, list(row.values()))
                    
                    conn.commit()
                    return {
                        "success": True,
                        "operation": "insert",
                        "rows_inserted": len(data)
                    }

                else:
                    raise ValueError(f"Unsupported SQLite operation: {operation}")

            finally:
                conn.close()

        return await asyncio.get_event_loop().run_in_executor(None, _execute_sqlite)

    async def _handle_json_operation(self, operation: str, db_path: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle JSON file operations."""
        def _execute_json():
            path = Path(db_path)
            
            if operation == "read_json":
                if not path.exists():
                    return {"success": True, "operation": "read_json", "data": None}
                
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return {
                    "success": True,
                    "operation": "read_json",
                    "data": data,
                    "size": len(json.dumps(data))
                }

            elif operation == "write_json":
                data = arguments.get("data")
                if data is None:
                    raise ValueError("Data is required for write_json operation")
                
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                return {
                    "success": True,
                    "operation": "write_json",
                    "path": str(path),
                    "size": len(json.dumps(data))
                }

            else:
                raise ValueError(f"Unsupported JSON operation: {operation}")

        return await asyncio.get_event_loop().run_in_executor(None, _execute_json)

    async def _handle_csv_operation(self, operation: str, db_path: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle CSV file operations."""
        try:
            import csv
        except ImportError:
            raise ImportError("csv module is required for CSV operations")

        def _execute_csv():
            path = Path(db_path)
            
            if operation == "read_csv":
                if not path.exists():
                    return {"success": True, "operation": "read_csv", "data": []}
                
                rows = []
                with open(path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        rows.append(dict(row))
                
                return {
                    "success": True,
                    "operation": "read_csv",
                    "data": rows,
                    "count": len(rows)
                }

            elif operation == "write_csv":
                data = arguments.get("data")
                if not data:
                    raise ValueError("Data is required for write_csv operation")
                
                if isinstance(data, dict):
                    data = [data]
                
                if not data:
                    raise ValueError("Data cannot be empty")
                
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    if data:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
                
                return {
                    "success": True,
                    "operation": "write_csv",
                    "path": str(path),
                    "rows_written": len(data)
                }

            else:
                raise ValueError(f"Unsupported CSV operation: {operation}")

        return await asyncio.get_event_loop().run_in_executor(None, _execute_csv)