"""
Alfred Agent System

A multi-agent architecture where specialized agents handle different aspects
of the personal assistant experience.
"""

from alfred.core.agents.base import (
    BaseAgent,
    AgentType,
    AgentResult,
    AgentContext as BaseAgentContext,
    AgentCapability,
)
from alfred.core.agents.executor import (
    AgentExecutor,
    AgentContext,
    ExecutionResult,
    ExecutionStep,
)
from alfred.core.agents.context import (
    ContextBuilder,
    UserContext,
    KnowledgeContext,
    EnvironmentContext,
    ConversationContext,
)

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentType",
    "AgentResult",
    "AgentCapability",
    # Executor
    "AgentExecutor",
    "AgentContext",
    "ExecutionResult",
    "ExecutionStep",
    # Context building
    "ContextBuilder",
    "UserContext",
    "KnowledgeContext",
    "EnvironmentContext",
    "ConversationContext",
]
