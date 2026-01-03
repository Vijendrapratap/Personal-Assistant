"""
Background Scheduler for Alfred
Uses APScheduler for scheduled jobs like morning briefings, evening reviews, and habit reminders.
"""

from .scheduler import AlfredScheduler, get_scheduler

__all__ = ['AlfredScheduler', 'get_scheduler']
