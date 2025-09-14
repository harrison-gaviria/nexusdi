"""
Main dependency injection container implementation.
"""

import threading
import sys
import inspect
import typing
from typing import Any, Dict, Type, Callable, Optional, Set, get_type_hints

from .lifecycle import LifeCycle, DependencyInfo, AutoScope, get_current_request_scope
from ..exceptions.errors import DependencyResolutionException, CircularDependencyException, LifecycleException
from .proxy import LazyProxy


class Container:
    """
    Main dependency injection container.

    Singleton container that manages dependency registration, resolution,
    and lifecycle management. Supports circular dependencies through lazy proxies.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not getattr(self, '_initialized', False):
            self._dependencies: Dict[Type, DependencyInfo] = {}
            self._resolving: Set[Type] = set()
            self._circular_dependencies: Set[Type] = set()
            self._initialized = True

    def _get_or_create_auto_scope(self) -> AutoScope:
        """
        Gets or creates an automatic scope for scoped dependencies.

        Returns:
            AutoScope: The current or new auto scope
        """
        current_scope = get_current_request_scope().get()
        if current_scope is None:
            current_scope = AutoScope()
            get_current_request_scope().set(current_scope)
        return current_scope

    def register(self, cls_or_func: Any, lifecycle: LifeCycle = LifeCycle.TRANSIENT):
        """
        Registers a dependency with the container.

        Args:
            cls_or_func (Any): The class or function to register
            lifecycle (LifeCycle, optional): The lifecycle type. Defaults to TRANSIENT.
        """
        key = cls_or_func if isinstance(cls_or_func, type) else type(cls_or_func)
        self._dependencies[key] = DependencyInfo(cls_or_func, lifecycle)

    def resolve(self, cls: Type, scope: Optional[Any] = None) -> Any:
        """
        Resolves a dependency from the container.

        Args:
            cls (Type): The type to resolve
            scope (Any, optional): The scope for scoped dependencies

        Returns:
            Any: The resolved instance
        """
        if cls not in self._dependencies:
            try:
                return self._resolve_direct(cls, scope)
            except Exception:
                return LazyProxy(self, cls, scope)

        dep_info = self._dependencies[cls]

        if dep_info.lifecycle == LifeCycle.SINGLETON:
            if dep_info.instance is None:
                dep_info.instance = self._create_instance_with_lazy_deps(dep_info.cls_or_func, scope)
            return dep_info.instance

        elif dep_info.lifecycle == LifeCycle.SCOPED:
            current_scope = scope or self._get_or_create_auto_scope()
            if current_scope not in dep_info.scoped_instances:
                dep_info.scoped_instances[current_scope] = self._create_instance_with_lazy_deps(dep_info.cls_or_func, scope)
            return dep_info.scoped_instances[current_scope]

        else:
            return self._create_instance_with_lazy_deps(dep_info.cls_or_func, scope)

    def _resolve_direct(self, cls: Type, scope: Optional[Any] = None) -> Any:
        """
        Resolves a dependency directly without lazy proxies.

        Args:
            cls (Type): The type to resolve
            scope (Any, optional): The scope for scoped dependencies

        Returns:
            Any: The resolved instance

        Raises:
            ValueError: If the dependency cannot be resolved
        """
        if cls in self._resolving:
            return LazyProxy(self, cls, scope)

        if cls not in self._dependencies:
            try:
                return self._create_instance(cls, scope)
            except Exception as e:
                raise DependencyResolutionException(
                    dependency_name=cls.__name__,
                    dependency_type=cls
                ) from e

        self._resolving.add(cls)
        try:
            dep_info = self._dependencies[cls]
            if dep_info.lifecycle == LifeCycle.SINGLETON:
                if dep_info.instance is None:
                    dep_info.instance = self._create_instance_with_lazy_deps(dep_info.cls_or_func, scope)
                return dep_info.instance
            elif dep_info.lifecycle == LifeCycle.SCOPED:
                current_scope = scope or self._get_or_create_auto_scope()
                if current_scope not in dep_info.scoped_instances:
                    dep_info.scoped_instances[current_scope] = self._create_instance_with_lazy_deps(dep_info.cls_or_func, scope)
                return dep_info.scoped_instances[current_scope]
            else:
                return self._create_instance_with_lazy_deps(dep_info.cls_or_func, scope)
        finally:
            self._resolving.discard(cls)

    def _create_instance_with_lazy_deps(self, cls_or_func: Any, scope: Optional[Any] = None) -> Any:
        """
        Creates an instance using lazy dependency resolution.

        Args:
            cls_or_func (Any): The class or function to instantiate
            scope (Any, optional): The scope for scoped dependencies

        Returns:
            Any: The created instance
        """
        if not isinstance(cls_or_func, type):
            return cls_or_func

        instance = cls_or_func.__new__(cls_or_func)

        if hasattr(cls_or_func, '_nexusdi_container_resolve_init'):
            instance._nexusdi_container_resolve_init()
        else:
            original_init = getattr(cls_or_func, '_nexusdi_original_init', cls_or_func.__init__)
            try:
                dependencies = self._resolve_lazy_dependencies(original_init, scope)
                original_init(instance, **dependencies)
            except TypeError as e:
                if "missing" in str(e) or "unexpected keyword" in str(e):
                    sig = inspect.signature(original_init)
                    minimal_deps = {}
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                        if param.default is not inspect.Parameter.empty:
                            continue
                        if param_name in dependencies:
                            minimal_deps[param_name] = dependencies[param_name]
                    try:
                        original_init(instance, **minimal_deps)
                    except Exception:
                        try:
                            original_init(instance)
                        except Exception:
                            pass
                else:
                    raise
            except Exception:
                try:
                    cls_or_func.__init__(instance)
                except Exception:
                    pass
        return instance

    def _create_instance(self, cls_or_func: Any, scope: Optional[Any] = None) -> Any:
        """
        Creates an instance with direct dependency resolution.

        Args:
            cls_or_func (Any): The class or function to instantiate
            scope (Any, optional): The scope for scoped dependencies

        Returns:
            Any: The created instance
        """
        if not isinstance(cls_or_func, type):
            return cls_or_func

        self._resolving.add(cls_or_func)
        try:
            original_init = getattr(cls_or_func, '_nexusdi_original_init', cls_or_func.__init__)
            dependencies = self._resolve_dependencies(original_init, scope)
            instance = cls_or_func.__new__(cls_or_func)
            try:
                original_init(instance, **dependencies)
            except TypeError as e:
                if "missing" in str(e):
                    sig = inspect.signature(original_init)
                    for param in sig.parameters.values():
                        if param.name not in dependencies and param.default is inspect.Parameter.empty:
                            dependencies[param.name] = None
                    original_init(instance, **dependencies)
                else:
                    raise
            return instance
        finally:
            self._resolving.discard(cls_or_func)

    def _resolve_lazy_dependencies(self, func: Callable, scope: Optional[Any] = None) -> dict[str, Any]:
        """
        Resolves dependencies as lazy proxies for a function.

        Args:
            func (Callable): The function to resolve dependencies for
            scope (Any, optional): The scope for scoped dependencies

        Returns:
            dict[str, Any]: Dictionary of parameter names to lazy proxies
        """
        dependencies = {}
        try:
            hints = self._get_type_hints_safe(func)
            sig = inspect.signature(func)

            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                if param_name in hints:
                    param_type = hints[param_name]
                    param_type = self._extract_type(param_type)

                    if param_type:
                        dependencies[param_name] = LazyProxy(self, param_type, scope)
                elif param.default is not inspect.Parameter.empty:
                    continue
                else:
                    found_dep = self._find_dependency_by_name(param_name)
                    if found_dep:
                        dependencies[param_name] = LazyProxy(self, found_dep, scope)

        except Exception:
            sig = inspect.signature(func)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                if param.default is inspect.Parameter.empty:
                    found_dep = self._find_dependency_by_name(param_name)
                    if found_dep:
                        dependencies[param_name] = LazyProxy(self, found_dep, scope)

        return dependencies

    def _resolve_dependencies(self, func: Callable, scope: Optional[Any] = None) -> dict[str, Any]:
        """
        Resolves dependencies directly for a function.

        Args:
            func (Callable): The function to resolve dependencies for
            scope (Any, optional): The scope for scoped dependencies

        Returns:
            dict[str, Any]: Dictionary of parameter names to resolved instances

        Raises:
            ValueError: If a required dependency cannot be resolved
        """
        dependencies = {}
        sig = inspect.signature(func)
        try:
            hints = self._get_type_hints_safe(func)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                if param_name in hints:
                    param_type = self._extract_type(hints[param_name])
                    if param_type:
                        try:
                            dependencies[param_name] = self._resolve_direct(param_type, scope)
                        except Exception:
                            found_dep = self._find_dependency_by_name(param_name)
                            if found_dep:
                                dependencies[param_name] = self._resolve_direct(found_dep, scope)
                else:
                    found_dep = self._find_dependency_by_name(param_name)
                    if found_dep:
                        dependencies[param_name] = self._resolve_direct(found_dep, scope)
        except Exception:
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                if param_name not in dependencies:
                    found_dep = self._find_dependency_by_name(param_name)
                    if found_dep:
                        dependencies[param_name] = self._resolve_direct(found_dep, scope)

        for param_name, param in sig.parameters.items():
            if (param_name != 'self' and
            param.default is inspect.Parameter.empty and
            param_name not in dependencies):
                raise DependencyResolutionException(
                    dependency_name=param_name,
                    missing_dependencies=[param_name]
                )

        return dependencies

    def _get_type_hints_safe(self, func: Callable) -> dict[str, Any]:
        """
        Safely gets type hints for a function.

        Args:
            func (Callable): The function to get type hints for

        Returns:
            dict[str, Any]: Dictionary of parameter names to types
        """
        try:
            module = sys.modules.get(func.__module__)
            if module:
                return get_type_hints(func, globalns=module.__dict__)
            else:
                return get_type_hints(func)
        except (NameError, AttributeError, TypeError):
            return {}

    def _find_dependency_by_name(self, param_name: str) -> Optional[Type]:
        """
        Finds a dependency by parameter name using various naming conventions.

        Args:
            param_name (str): The parameter name to search for

        Returns:
            Optional[Type]: The found dependency type or None
        """
        for dep_type in self._dependencies.keys():
            if dep_type.__name__.lower() == param_name.lower():
                return dep_type

        variations = [
            param_name.lower(),
            param_name.lower().replace('_', ''),
            param_name.lower().replace('service', ''),
            param_name.lower().replace('repository', ''),
            param_name.lower().replace('provider', ''),
            param_name.lower().replace('manager', '')
        ]

        for dep_type in self._dependencies.keys():
            type_name = dep_type.__name__.lower()
            for variation in variations:
                if variation == type_name or variation in type_name:
                    return dep_type

        return None

    def _extract_type(self, hint) -> Optional[Type]:
        """
        Extracts the actual type from a type hint.

        Args:
            hint: The type hint to extract from

        Returns:
            Optional[Type]: The extracted type or None
        """
        if isinstance(hint, type):
            return hint

        if hasattr(typing, 'get_origin') and typing.get_origin(hint) is typing.Union:
            args = typing.get_args(hint)
            if len(args) == 2 and type(None) in args:
                return next((arg for arg in args if arg is not type(None)), None)

        return None

    def clear_scope(self) -> None:
        """
        Clears the current scope and removes all scoped instances.

        This method should be called to clean up scoped dependencies
        when a scope (like a request) ends.

        Raises:
            LifecycleException: If there's an error cleaning up scoped instances
        """
        current_scope = get_current_request_scope().get()
        if current_scope is None:
            return

        try:
            for dep_info in self._dependencies.values():
                if dep_info.lifecycle == LifeCycle.SCOPED:
                    if current_scope in dep_info.scoped_instances:
                        try:
                            dep_info.scoped_instances.pop(current_scope, None)
                        except Exception as e:
                            raise LifecycleException(
                                message=f"Failed to clean up scoped instance of {dep_info.cls_or_func.__name__}",
                                dependency_type=dep_info.cls_or_func,
                                lifecycle="SCOPED"
                            ) from e

            get_current_request_scope().set(None)
        except LifecycleException:
            raise
        except Exception as e:
            raise LifecycleException(
                message="Failed to clear current scope",
                lifecycle="SCOPED"
            ) from e

    def get_stats(self) -> dict[str, int]:
        """
        Gets statistics about the container.

        Returns:
            dict[str, int]: Dictionary containing container statistics
        """
        return {
            'registered_dependencies': len(self._dependencies),
            'circular_dependencies_detected': len(self._circular_dependencies),
            'singleton_instances': sum(1 for dep in self._dependencies.values()
                if dep.lifecycle == LifeCycle.SINGLETON and dep.instance is not None)
        }

    def list_registered_dependencies(self) -> list[str]:
        """
        Lists all registered dependencies.

        Returns:
            list[str]: List of registered dependency names with their lifecycles
        """
        dependencies: list[str] = []
        for dep_type, dep_info in self._dependencies.items():
            dependencies.append(f"  - {dep_type.__name__} ({dep_info.lifecycle.value})")

        return dependencies


_container = Container()
