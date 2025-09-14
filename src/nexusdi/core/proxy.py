"""
Lazy proxy implementation for circular dependency resolution.
"""

import threading
from typing import Any, Optional, Type
from ..exceptions.errors import DependencyResolutionException


class LazyProxy:
    """
    Lazy proxy for circular dependency resolution.

    This proxy delays the resolution of dependencies until they are actually
    accessed, allowing for circular dependencies to be resolved.

    Args:
        container: The dependency container
        target_type (Type): The target type to be resolved
        scope (Any, optional): The scope for scoped dependencies
    """

    def __init__(self, container, target_type: Type, scope: Optional[Any] = None) -> None:
        object.__setattr__(self, '_container', container)
        object.__setattr__(self, '_target_type', target_type)
        object.__setattr__(self, '_scope', scope)
        object.__setattr__(self, '_resolved_instance', None)
        object.__setattr__(self, '_is_resolved', False)
        object.__setattr__(self, '_lock', threading.Lock())

    def _resolve(self) -> Any:
        """
        Resolves the actual instance behind the proxy.

        Returns:
            Any: The resolved instance
        """
        if not object.__getattribute__(self, '_is_resolved'):
            with object.__getattribute__(self, '_lock'):
                if not object.__getattribute__(self, '_is_resolved'):
                    container = object.__getattribute__(self, '_container')
                    target_type = object.__getattribute__(self, '_target_type')
                    scope = object.__getattribute__(self, '_scope')

                    try:
                        resolved = container._resolve_direct(target_type, scope)
                        object.__setattr__(self, '_resolved_instance', resolved)
                    except Exception:
                        resolved = target_type.__new__(target_type)
                        resolved._nexusdi_initialized = True
                        object.__setattr__(self, '_resolved_instance', resolved)
                    object.__setattr__(self, '_is_resolved', True)

        return object.__getattribute__(self, '_resolved_instance')

    def __getattr__(self, name):
        instance = self._resolve()
        return getattr(instance, name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            instance = self._resolve()
            setattr(instance, name, value)

    def __call__(self, *args, **kwargs):
        instance = self._resolve()
        return instance(*args, **kwargs)

    def __repr__(self):
        if object.__getattribute__(self, '_is_resolved'):
            instance = object.__getattribute__(self, '_resolved_instance')
            return f"<LazyProxy[resolved] -> {repr(instance)}>"
        else:
            target_type = object.__getattribute__(self, '_target_type')
            return f"<LazyProxy[unresolved] -> {target_type.__name__}>"

    def __str__(self):
        instance = self._resolve()
        return str(instance)

    def __bool__(self):
        instance = self._resolve()
        return bool(instance)

    def __len__(self):
        instance = self._resolve()
        return len(instance)

    def __iter__(self):
        instance = self._resolve()
        return iter(instance)
