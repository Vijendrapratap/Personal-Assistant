"""
Base Tool Definition.

All tools inherit from BaseTool and provide a standardized interface
for the agent executor to call.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class ToolCategory(str, Enum):
    """Categories of tools."""
    USER = "user"           # User context and preferences
    TASKS = "tasks"         # Task management
    PROJECTS = "projects"   # Project management
    HABITS = "habits"       # Habit tracking
    CALENDAR = "calendar"   # Calendar operations
    EMAIL = "email"         # Email operations
    NOTES = "notes"         # Notes and documentation
    SEARCH = "search"       # Web and knowledge search
    NOTIFICATIONS = "notifications"  # Push notifications
    CONNECTORS = "connectors"  # External service connectors
    SYSTEM = "system"       # System operations


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: Dict[str, Any] = {
            "type": self.type,
            "description": self.description,
        }
        if self.enum:
            schema["enum"] = self.enum
        if self.default is not None:
            schema["default"] = self.default
        return schema


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        """Convert result to string for LLM context."""
        if not self.success:
            return f"Error: {self.error}"

        if self.data is None:
            return "Success (no data returned)"

        if isinstance(self.data, str):
            return self.data

        if isinstance(self.data, (dict, list)):
            return json.dumps(self.data, indent=2, default=str)

        return str(self.data)

    @classmethod
    def ok(cls, data: Any = None, **metadata) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata) -> "ToolResult":
        """Create a failed result."""
        return cls(success=False, error=error, metadata=metadata)


class ToolError(Exception):
    """Exception raised by tools."""

    def __init__(self, message: str, recoverable: bool = True):
        self.message = message
        self.recoverable = recoverable
        super().__init__(message)


class BaseTool(ABC):
    """
    Abstract base class for all tools.

    Tools are the actions that agents can take. Each tool:
    - Has a unique name
    - Has a description for the LLM
    - Defines its parameters as JSON Schema
    - Implements an execute method
    """

    # Tool metadata (override in subclasses)
    name: str = "base_tool"
    description: str = "Base tool description"
    category: ToolCategory = ToolCategory.SYSTEM

    # Whether this tool requires user authentication
    requires_auth: bool = True

    # Whether this tool can modify data
    is_write: bool = False

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize tool with optional context.

        Args:
            context: Execution context (user_id, storage, etc.)
        """
        self.context = context or {}

    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """
        Define the parameters this tool accepts.

        Returns:
            List of ToolParameter definitions
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given arguments.

        Args:
            **kwargs: Tool arguments

        Returns:
            ToolResult with success/failure and data
        """
        pass

    def get_json_schema(self) -> Dict[str, Any]:
        """
        Get the JSON Schema for this tool's parameters.

        Returns:
            JSON Schema dict compatible with OpenAI/Anthropic tool format
        """
        parameters = self.get_parameters()

        properties = {}
        required = []

        for param in parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def to_tool_definition(self) -> Dict[str, Any]:
        """
        Convert to LLM tool definition format.

        Returns:
            Dict compatible with OpenAI/Anthropic tool calling
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_json_schema(),
            }
        }

    def validate_args(self, **kwargs) -> Optional[str]:
        """
        Validate arguments against parameter definitions.

        Returns:
            Error message if validation fails, None if valid
        """
        parameters = self.get_parameters()
        param_map = {p.name: p for p in parameters}

        # Check required parameters
        for param in parameters:
            if param.required and param.name not in kwargs:
                return f"Missing required parameter: {param.name}"

        # Check enum values
        for name, value in kwargs.items():
            if name in param_map:
                param = param_map[name]
                if param.enum and value not in param.enum:
                    return f"Invalid value for {name}: {value}. Must be one of: {param.enum}"

        return None

    async def safe_execute(self, **kwargs) -> ToolResult:
        """
        Execute with validation and error handling.

        Args:
            **kwargs: Tool arguments

        Returns:
            ToolResult (always returns, never raises)
        """
        # Validate arguments
        validation_error = self.validate_args(**kwargs)
        if validation_error:
            return ToolResult.fail(validation_error)

        # Execute with error handling
        try:
            return await self.execute(**kwargs)
        except ToolError as e:
            return ToolResult.fail(e.message)
        except Exception as e:
            return ToolResult.fail(f"Unexpected error: {str(e)}")

    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
