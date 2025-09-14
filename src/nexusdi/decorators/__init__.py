"""
Decorators for dependency injection.

Contains lifecycle decorators (singleton, transient, scoped) and
injection decorators (inject, service, controller).
"""

from .lifecycle import singleton, transient, scoped, bind_singleton, bind_transient, bind_scoped
from .injection import inject, service, controller

__all__ = [
    "singleton", "transient", "scoped",
    "bind_singleton", "bind_transient", "bind_scoped",
    "inject", "service", "controller"
]
