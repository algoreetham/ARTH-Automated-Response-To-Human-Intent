"""Base classes and registry for ARTH tools.
Defines the standard tool interface compatible with Ollama function/tool calling.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class Tool(ABC):
    """Abstract base class for all ARTH tools."""

    name: str
    description: str
    parameters: Dict[str, Any]
    is_sensitive: bool = False
    is_risky: bool = False

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool action."""
        pass

    @abstractmethod
    def describe_action(self, **kwargs) -> str:
        """Return a clear, plain-language description of what this action will do.
        Used by the PermissionEngine before execution.
        Example: 'move 12 files from Downloads to Notes'
        """
        pass

    def to_ollama_schema(self) -> Dict[str, Any]:
        """Format the tool schema for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Central registry for discovering, registering, and invoking ARTH tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_ollama_tools_schema(self) -> List[Dict[str, Any]]:
        """Generate the full tools schema list for Ollama chat requests."""
        return [tool.to_ollama_schema() for tool in self._tools.values()]
