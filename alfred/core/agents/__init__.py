"""
Alfred Agent System

A multi-agent architecture where specialized agents handle different aspects
of the personal assistant experience.
"""

from alfred.core.agents.base import (
    BaseAgent,
    AgentType,
    AgentResult,
    AgentContext,
    AgentCapability,
)

__all__ = [
    "BaseAgent",
    "AgentType",
    "AgentResult",
    "AgentContext",
    "AgentCapability",
]
