"""
Tool Registry.

Central registry for all available tools. Handles tool registration,
discovery, and instantiation for agent execution.
"""

from typing import Dict, List, Optional, Type, Any
from alfred.core.tools.base import BaseTool, ToolCategory

# Global registry instance
_registry: Optional["ToolRegistry"] = None


class ToolRegistry:
    """
    Registry for all available tools.

    Provides:
    - Tool registration by name
    - Tool discovery by category
    - Tool instantiation with context
    """

    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._categories: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }

    def register(self, tool_class: Type[BaseTool]) -> Type[BaseTool]:
        """
        Register a tool class.

        Can be used as a decorator:
            @registry.register
            class MyTool(BaseTool):
                ...

        Args:
            tool_class: Tool class to register

        Returns:
            The same tool class (for decorator use)
        """
        name = tool_class.name
        category = tool_class.category

        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        self._tools[name] = tool_class
        self._categories[category].append(name)

        return tool_class

    def get(self, name: str, context: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
        """
        Get an instantiated tool by name.

        Args:
            name: Tool name
            context: Execution context to pass to tool

        Returns:
            Instantiated tool or None if not found
        """
        tool_class = self._tools.get(name)
        if tool_class is None:
            return None
        return tool_class(context=context)

    def get_class(self, name: str) -> Optional[Type[BaseTool]]:
        """Get tool class by name without instantiation."""
        return self._tools.get(name)

    def list_tools(self, category: Optional[ToolCategory] = None) -> List[str]:
        """
        List registered tool names.

        Args:
            category: Optional category filter

        Returns:
            List of tool names
        """
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())

    def get_tools_for_agent(
        self,
        context: Dict[str, Any],
        categories: Optional[List[ToolCategory]] = None,
        include_write: bool = True,
    ) -> List[BaseTool]:
        """
        Get instantiated tools for an agent.

        Args:
            context: Execution context
            categories: Optional list of categories to include
            include_write: Whether to include write operations

        Returns:
            List of instantiated tools
        """
        tools = []

        for name, tool_class in self._tools.items():
            # Filter by category
            if categories and tool_class.category not in categories:
                continue

            # Filter write operations
            if not include_write and tool_class.is_write:
                continue

            tools.append(tool_class(context=context))

        return tools

    def get_tool_definitions(
        self,
        context: Optional[Dict[str, Any]] = None,
        categories: Optional[List[ToolCategory]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get tool definitions for LLM API calls.

        Args:
            context: Execution context
            categories: Optional list of categories to include

        Returns:
            List of tool definitions in OpenAI/Anthropic format
        """
        definitions = []

        for name, tool_class in self._tools.items():
            if categories and tool_class.category not in categories:
                continue

            tool = tool_class(context=context)
            definitions.append(tool.to_tool_definition())

        return definitions

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        # Auto-register built-in tools
        _register_builtin_tools(_registry)
    return _registry


def _register_builtin_tools(registry: ToolRegistry) -> None:
    """Register all built-in tools."""
    # Import tools to trigger registration
    try:
        from alfred.core.tools import tasks
        from alfred.core.tools import habits
        from alfred.core.tools import projects
        from alfred.core.tools import user
        from alfred.core.tools import notifications
    except ImportError:
        # Tools not yet implemented
        pass


# Decorator for easy registration
def register_tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    """
    Decorator to register a tool with the global registry.

    Usage:
        @register_tool
        class MyTool(BaseTool):
            name = "my_tool"
            ...
    """
    registry = get_tool_registry()
    return registry.register(cls)
