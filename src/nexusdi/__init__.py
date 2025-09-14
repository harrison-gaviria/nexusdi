"""
NexusDI - Dependency Injection Container for Python.

A lightweight and powerful dependency injection framework that supports
singleton, transient, and scoped lifecycles with automatic dependency resolution.
"""

from .core.container import _container
from .decorators.lifecycle import singleton, transient, scoped
from .decorators.injection import service, controller, inject
from .scanning.scanner import initialize

__all__ = [
    "initialize",
    "singleton",
    "transient",
    "scoped",
    "service",
    "controller",
    "inject"
]

def scope_cleanup():
    """
    Clears the current scope and removes all scoped instances.
    """
    _container.clear_scope()