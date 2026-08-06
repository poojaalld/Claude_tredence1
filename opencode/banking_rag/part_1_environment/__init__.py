"""
Part 1: Environment Setup and Project Skeleton
This module handles application configuration and logger setup.
"""

from .config import settings, Settings
from .logger import log

__all__ = ["settings", "Settings", "log"]
