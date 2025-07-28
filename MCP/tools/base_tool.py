"""Base tool class for all MCP tools."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all tools."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        title: str | None = None,
    ) -> None:
        self.name: str = name
        self.title: str | None = title
        self.description: str = description
        self.input_schema: dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """Format tool information for LLM.

        Returns:
            A formatted string describing the tool.
        """
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = (
                    f"- {param_name}: {param_info.get('description', 'No description')}"
                )
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        # Build the formatted output with title as a separate field
        output = f"Tool: {self.name}\n"

        # Add human-readable title if available
        if self.title:
            output += f"User-readable title: {self.title}\n"

        output += f"""Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""

        return output

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> Any:
        """Execute the tool with given arguments.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        pass

    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.__class__.__name__}(name={self.name}, title={self.title})"

    def __repr__(self) -> str:
        """Detailed string representation of the tool."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"title='{self.title}', "
            f"description='{self.description[:50]}...')"
        )