"""
Lifecycle decorators for dependency registration.
"""

import functools
import inspect
from typing import Type

from ..core.container import _container
from ..core.lifecycle import LifeCycle
from ..exceptions.errors import LifecycleException, DependencyResolutionException


def _patch_class_init(cls: Type, lifecycle: LifeCycle) -> Type:
    """
    Patches a class constructor to support dependency injection.

    Args:
        cls (Type): The class to patch
        lifecycle (LifeCycle): The lifecycle type for the class

    Returns:
        Type: The patched class
    """
    original_init = cls.__init__
    cls._nexusdi_original_init = original_init
    cls._nexusdi_lifecycle = lifecycle

    @functools.wraps(original_init)
    def patched_init(self, *args, **kwargs) -> None:
        if hasattr(self, '_nexusdi_initialized'):
            return

        try:
            dependencies = _container._resolve_lazy_dependencies(original_init)
            final_kwargs = {**dependencies, **kwargs}
            original_init(self, **final_kwargs)
        except DependencyResolutionException:
            try:
                original_init(self, *args, **kwargs)
            except Exception as fallback_error:
                raise LifecycleException(
                    message=f"Failed to initialize {cls.__name__} with dependency injection and fallback",
                    dependency_type=cls,
                    lifecycle=lifecycle.value
                ) from fallback_error
        except Exception as e:
            try:
                original_init(self, *args, **kwargs)
            except Exception as fallback_error:
                raise LifecycleException(
                    message=f"Failed to initialize {cls.__name__}",
                    dependency_type=cls,
                    lifecycle=lifecycle.value
                ) from e
        self._nexusdi_initialized = True

    def container_resolve_init(self) -> None:
        if not hasattr(self, '_nexusdi_initialized'):
            try:
                dependencies = _container._resolve_lazy_dependencies(original_init)
                original_init(self, **dependencies)
            except Exception:
                pass
            finally:
                self._nexusdi_initialized = True

    patched_init.__signature__ = inspect.signature(original_init)
    patched_init.__annotations__ = getattr(original_init, '__annotations__', {})

    cls.__init__ = patched_init
    cls._nexusdi_container_resolve_init = container_resolve_init

    return cls


def singleton(cls: Type) -> Type:
    """
    Decorates a class to be registered as a singleton dependency.

    Singleton dependencies are created once and reused throughout
    the application lifetime.

    Args:
        cls (Type): The class to register as singleton

    Returns:
        Type: The decorated class
    """
    _container.register(cls, LifeCycle.SINGLETON)
    return _patch_class_init(cls, LifeCycle.SINGLETON)


def bind_singleton(cls: Type) -> Type:
    """
    Binds a class as singleton without patching its constructor.

    Args:
        cls (Type): The class to bind as singleton

    Returns:
        Type: The class (unmodified)
    """
    _container.register(cls, LifeCycle.SINGLETON)
    return cls


def bind_transient(cls: Type) -> Type:
    """
    Binds a class as transient without patching its constructor.

    Args:
        cls (Type): The class to bind as transient

    Returns:
        Type: The class (unmodified)
    """
    _container.register(cls, LifeCycle.TRANSIENT)
    return cls


def bind_scoped(cls: Type) -> Type:
    """
    Binds a class as scoped without patching its constructor.

    Args:
        cls (Type): The class to bind as scoped

    Returns:
        Type: The class (unmodified)
    """
    _container.register(cls, LifeCycle.SCOPED)
    return cls


def transient(cls: Type) -> Type:
    """
    Decorates a class to be registered as a transient dependency.

    Transient dependencies are created new every time they are requested.

    Args:
        cls (Type): The class to register as transient

    Returns:
        Type: The decorated class
    """
    _container.register(cls, LifeCycle.TRANSIENT)
    return _patch_class_init(cls, LifeCycle.TRANSIENT)


def scoped(cls: Type) -> Type:
    """
    Decorates a class to be registered as a scoped dependency.

    Scoped dependencies are created once per scope (request/thread)
    and reused within that scope.

    Args:
        cls (Type): The class to register as scoped

    Returns:
        Type: The decorated class
    """
    _container.register(cls, LifeCycle.SCOPED)
    return _patch_class_init(cls, LifeCycle.SCOPED)
