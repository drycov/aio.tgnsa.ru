"""
This module provides exports for the bot setup and lifecycle management functions.
"""

from .bot_module import setup_bot, start_bot, graceful_shutdown

__all__ = ["setup_bot", "start_bot", "graceful_shutdown"]
