"""
Automation module for AI platform interactions.

This module provides automation capabilities for various AI platforms
including ChatGPT, Claude, Gemini, and others.
"""

from .base_handler import BaseAIHandler
from .browser_manager import BrowserManager
from .chatgpt_handler import ChatGPTHandler
from .retry_manager import RetryManager, retry_on_failure
from .automation_controller import AutomationController, ProcessingStatus, ProcessingTask

__all__ = [
    'BaseAIHandler',
    'BrowserManager', 
    'ChatGPTHandler',
    'RetryManager',
    'retry_on_failure',
    'AutomationController',
    'ProcessingStatus',
    'ProcessingTask'
]