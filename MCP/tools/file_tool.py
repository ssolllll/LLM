"""File operation tool for MCP servers."""

import os
import asyncio
import logging
from pathlib import Path
from typing import Any

from .base_tool import BaseTool


class FileTool(BaseTool):
    """Tool for file system operations."""

    def __init__(
        self,
        name: str = "file_operations",
        description: str = "Perform file system operations like read, write, list, and delete files",
        input_schema: dict[str, Any] | None = None,
        title: str | None = "File Operations Tool",
    ) -> None:
        if input_schema is None:
            input_schema = {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list", "delete", "create_dir", "exists"],
                        "description": "The file operation to perform"
                    },
                    "path": {
                        "type": "string",
                        "description": "The file or directory path"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (required for write operation)"
                    },
                    "encoding": {
                        "type": "string",
                        "default": "utf-8",
                        "description": "File encoding (default: utf-8)"
                    }
                },
                "required": ["operation", "path"]
            }
        
        super().__init__(name, description, input_schema, title)

    async def execute(self, arguments: dict[str, Any]) -> Any:
        """Execute file operation."""
        operation = arguments.get("operation")
        path_str = arguments.get("path")
        content = arguments.get("content")
        encoding = arguments.get("encoding", "utf-8")

        if not path_str:
            raise ValueError("Path is required")

        path = Path(path_str)

        try:
            if operation == "read":
                return await self._read_file(path, encoding)
            elif operation == "write":
                if content is None:
                    raise ValueError("Content is required for write operation")
                return await self._write_file(path, content, encoding)
            elif operation == "list":
                return await self._list_directory(path)
            elif operation == "delete":
                return await self._delete_path(path)
            elif operation == "create_dir":
                return await self._create_directory(path)
            elif operation == "exists":
                return await self._check_exists(path)
            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            logging.error(f"File operation failed: {e}")
            return {"error": str(e), "operation": operation, "path": str(path)}

    async def _read_file(self, path: Path, encoding: str) -> dict[str, Any]:
        """Read file content."""
        def _read():
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        
        content = await asyncio.get_event_loop().run_in_executor(None, _read)
        return {
            "success": True,
            "operation": "read",
            "path": str(path),
            "content": content,
            "size": len(content)
        }

    async def _write_file(self, path: Path, content: str, encoding: str) -> dict[str, Any]:
        """Write content to file."""
        def _write():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding=encoding) as f:
                return f.write(content)
        
        bytes_written = await asyncio.get_event_loop().run_in_executor(None, _write)
        return {
            "success": True,
            "operation": "write",
            "path": str(path),
            "bytes_written": bytes_written
        }

    async def _list_directory(self, path: Path) -> dict[str, Any]:
        """List directory contents."""
        def _list():
            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {path}")
            
            if not path.is_dir():
                raise NotADirectoryError(f"Path is not a directory: {path}")
            
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_file": item.is_file(),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return items
        
        items = await asyncio.get_event_loop().run_in_executor(None, _list)
        return {
            "success": True,
            "operation": "list",
            "path": str(path),
            "items": items,
            "count": len(items)
        }

    async def _delete_path(self, path: Path) -> dict[str, Any]:
        """Delete file or directory."""
        def _delete():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                raise FileNotFoundError(f"Path not found: {path}")
        
        await asyncio.get_event_loop().run_in_executor(None, _delete)
        return {
            "success": True,
            "operation": "delete",
            "path": str(path)
        }

    async def _create_directory(self, path: Path) -> dict[str, Any]:
        """Create directory."""
        def _create():
            path.mkdir(parents=True, exist_ok=True)
        
        await asyncio.get_event_loop().run_in_executor(None, _create)
        return {
            "success": True,
            "operation": "create_dir",
            "path": str(path)
        }

    async def _check_exists(self, path: Path) -> dict[str, Any]:
        """Check if path exists."""
        def _exists():
            return {
                "exists": path.exists(),
                "is_file": path.is_file() if path.exists() else None,
                "is_dir": path.is_dir() if path.exists() else None
            }
        
        result = await asyncio.get_event_loop().run_in_executor(None, _exists)
        return {
            "success": True,
            "operation": "exists",
            "path": str(path),
            **result
        }