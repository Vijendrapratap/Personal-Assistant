"""
Alfred Integrations Framework

A plugin-based system for connecting Alfred to external services
like calendars, email, task managers, and more.
"""

from alfred.integrations.base import (
    BaseIntegration,
    CalendarIntegration,
    EmailIntegration,
    TaskManagerIntegration,
    IntegrationStatus,
    IntegrationConfig,
    IntegrationError,
)
from alfred.integrations.manager import IntegrationManager

__all__ = [
    "BaseIntegration",
    "CalendarIntegration",
    "EmailIntegration",
    "TaskManagerIntegration",
    "IntegrationStatus",
    "IntegrationConfig",
    "IntegrationError",
    "IntegrationManager",
]
