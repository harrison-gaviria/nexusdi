"""
Core components of the NexusDI framework.

Contains the main container, lifecycle management, and proxy classes.
"""

from .container import Container, _container
from .lifecycle import LifeCycle
from .proxy import LazyProxy

__all__ = ["Container", "_container", "LifeCycle", "LazyProxy"]