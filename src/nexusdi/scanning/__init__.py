"""
Component scanning functionality.

Automatically discovers and registers decorated components across modules.
"""

from .scanner import ComponentScanner, initialize

__all__ = ["ComponentScanner", "initialize"]
