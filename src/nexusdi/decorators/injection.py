"""
Injection decorators for functions and semantic aliases.
"""

import functools
import inspect
from typing import Callable, Type

from ..core.container import _container
from .lifecycle import transient
from ..exceptions.errors import DependencyResolutionException


def inject(func: Callable) -> Callable:
    """
    Decorates a function to inject dependencies into its parameters.

    Dependencies are resolved based on parameter names and type hints.

    Args:
        func (Callable): The function to decorate

    Returns:
        Callable: The decorated function with dependency injection
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            dependencies = _container._resolve_lazy_dependencies(func)
            final_kwargs = {**dependencies, **kwargs}
            return func(*args, **final_kwargs)
        except Exception as e:
            raise DependencyResolutionException(
                dependency_name=f"function '{func.__name__}'",
            ) from e

    wrapper.__signature__ = inspect.signature(func)
    wrapper.__annotations__ = getattr(func, '__annotations__', {})
    wrapper._nexusdi_decorated = True
    return wrapper


def service(cls: Type) -> Type:
    """
    Decorates a class as a service (alias for transient).

    Args:
        cls (Type): The service class

    Returns:
        Type: The decorated class
    """
    return transient(cls)


def controller(cls: Type) -> Type:
    """
    Decorates a class as a controller (alias for transient).

    Args:
        cls (Type): The controller class

    Returns:
        Type: The decorated class
    """
    return transient(cls)
