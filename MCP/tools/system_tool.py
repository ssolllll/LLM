# """System operations tool for MCP servers."""

# import os
# import sys
# import asyncio
# import logging
# import subprocess
# import platform
# from typing import Any, Dict, List
# from pathlib import Path

# from .base_tool import BaseTool


# class SystemTool(BaseTool):
#     """Tool for system operations like executing commands, environment variables, and system info."""

#     def __init__(
#         self,
#         name: str = "system_operations",
#         description: str = "Perform system operations like executing commands, managing environment variables, and getting system information",
#         input_schema: dict[str, Any] | None = None,
#         title: str | None = "System Operations Tool",
#     ) -> None:
#         if input_schema is None:
#             input_schema = {
#                 "type": "object",
#                 "properties": {
#                     "operation": {
#                         "type": "string",
#                         "enum": ["execute", "get_env", "set_env", "system_info", "process_list", "disk_usage", "memory_info"],
                