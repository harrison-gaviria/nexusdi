"""
Lifecycle management for dependencies.
"""

from enum import Enum
import threading
import time
import uuid
import contextvars

_current_request_scope = contextvars.ContextVar('current_request_scope', default=None)


class LifeCycle(Enum):
    """
    Dependency lifecycle enumeration.

    Defines the different lifecycle types available for dependencies:
    - SINGLETON: One instance for the entire application
    - TRANSIENT: New instance every time it's requested
    - SCOPED: One instance per scope (request/thread)
    """
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class AutoScope:
    """
    Automatically created scope for scoped dependencies.

    Args:
        None
    """

    def __init__(self) -> None:
        self.id = str(uuid.uuid4())
        self.thread_id = threading.get_ident()
        self.created_at = time.time()

    def __str__(self):
        return f"AutoScope({self.id[:8]})"


class DependencyInfo:
    """
    Information about a registered dependency.

    Args:
        cls_or_func (Any): The class or function to be managed
        lifecycle (LifeCycle): The lifecycle type for this dependency
    """

    def __init__(self, cls_or_func, lifecycle: LifeCycle) -> None:
        self.cls_or_func = cls_or_func
        self.lifecycle = lifecycle
        self.instance = None
        import weakref
        self.scoped_instances = weakref.WeakKeyDictionary()


def get_current_request_scope():
    """
    Gets the current request scope context variable.

    Returns:
        contextvars.ContextVar: The current request scope context variable
    """
    return _current_request_scope
