# Core API Reference

The core module contains the main components of the NexusDI framework.

## Container

::: nexusdi.core.container.Container
    options:
      show_source: false
      heading_level: 3

The main dependency injection container that manages registration, resolution, and lifecycle management.

### Key Methods

#### register(cls_or_func, lifecycle)

Registers a dependency with the container.

**Parameters:**
- `cls_or_func` (Any): The class or function to register
- `lifecycle` (LifeCycle): The lifecycle type (SINGLETON, TRANSIENT, or SCOPED)

```python
from nexusdi.core.container import _container
from nexusdi.core.lifecycle import LifeCycle

_container.register(MyService, LifeCycle.SINGLETON)
```

#### resolve(cls, scope=None)

Resolves a dependency from the container.

**Parameters:**
- `cls` (Type): The type to resolve
- `scope` (Any, optional): The scope for scoped dependencies

**Returns:**
- Any: The resolved instance

```python
service = _container.resolve(MyService)
```

#### clear_scope()

Clears the current scope and removes all scoped instances.

```python
_container.clear_scope()
```

#### get_stats()

Gets statistics about the container.

**Returns:**
- dict[str, int]: Dictionary containing container statistics

```python
stats = _container.get_stats()
print(f"Registered dependencies: {stats['registered_dependencies']}")
```

#### list_registered_dependencies()

Lists all registered dependencies.

**Returns:**
- list[str]: List of registered dependency names with their lifecycles

```python
deps = _container.list_registered_dependencies()
for dep in deps:
    print(dep)
```

### Private Methods

The container also includes several private methods for internal dependency resolution:

- `_resolve_direct(cls, scope)`: Direct resolution without lazy proxies
- `_create_instance(cls_or_func, scope)`: Creates instances with direct dependency resolution
- `_resolve_lazy_dependencies(func, scope)`: Resolves dependencies as lazy proxies
- `_resolve_dependencies(func, scope)`: Resolves dependencies directly

## LifeCycle

::: nexusdi.core.lifecycle.LifeCycle
    options:
      show_source: false
      heading_level: 3

Enumeration defining the different lifecycle types available for dependencies.

### Values

- `SINGLETON`: One instance for the entire application
- `TRANSIENT`: New instance every time it's requested  
- `SCOPED`: One instance per scope (request/thread)

```python
from nexusdi.core.lifecycle import LifeCycle

# Usage in registration
_container.register(MyService, LifeCycle.SINGLETON)
```

## DependencyInfo

::: nexusdi.core.lifecycle.DependencyInfo
    options:
      show_source: false
      heading_level: 3

Internal class that stores information about a registered dependency.

### Attributes

- `cls_or_func`: The class or function being managed
- `lifecycle`: The lifecycle type for this dependency
- `instance`: The singleton instance (if applicable)
- `scoped_instances`: WeakKeyDictionary of scoped instances

## AutoScope

::: nexusdi.core.lifecycle.AutoScope
    options:
      show_source: false
      heading_level: 3

Automatically created scope for scoped dependencies.

### Attributes

- `id`: Unique identifier for the scope
- `thread_id`: Thread ID where the scope was created
- `created_at`: Timestamp of scope creation

```python
from nexusdi.core.lifecycle import AutoScope

scope = AutoScope()
print(f"Scope: {scope}")  # AutoScope(12345678)
```

## LazyProxy

::: nexusdi.core.proxy.LazyProxy
    options:
      show_source: false
      heading_level: 3

Lazy proxy for circular dependency resolution. This proxy delays the resolution of dependencies until they are actually accessed.

### Constructor

```python
LazyProxy(container, target_type, scope=None)
```

**Parameters:**
- `container`: The dependency container
- `target_type` (Type): The target type to be resolved
- `scope` (Any, optional): The scope for scoped dependencies

### Key Methods

#### _resolve()

Resolves the actual instance behind the proxy.

**Returns:**
- Any: The resolved instance

### Magic Methods

The LazyProxy implements various magic methods to behave like the target object:

- `__getattr__`: Delegates attribute access to the resolved instance
- `__setattr__`: Delegates attribute setting to the resolved instance
- `__call__`: Makes the proxy callable if the target is callable
- `__repr__`: String representation showing proxy state
- `__str__`: String conversion of the resolved instance
- `__bool__`: Boolean evaluation of the resolved instance

### Usage Example

```python
from nexusdi.core.proxy import LazyProxy
from nexusdi.core.container import _container

# LazyProxy is typically created internally
proxy = LazyProxy(_container, MyService)

# The proxy behaves like the target object
result = proxy.some_method()  # Resolves and calls method
attribute = proxy.some_attribute  # Resolves and gets attribute
```

## Global Container Instance

The framework provides a global container instance that's used throughout the application:

```python
from nexusdi.core.container import _container

# This is the singleton container instance used by all decorators
service = _container.resolve(MyService)
```

## Context Variables

The core module uses context variables for scope management:

### get_current_request_scope()

Gets the current request scope context variable.

**Returns:**
- contextvars.ContextVar: The current request scope context variable

```python
from nexusdi.core.lifecycle import get_current_request_scope

current_scope = get_current_request_scope().get()
if current_scope:
    print(f"Current scope: {current_scope}")
```

## Thread Safety

All core components are designed to be thread-safe:

- The Container uses threading locks for singleton creation
- Scoped dependencies are isolated per thread/context
- LazyProxy resolution is thread-safe with internal locking

## Error Handling

The core module integrates with the exception system:

```python
from nexusdi.exceptions import DependencyResolutionException

try:
    service = _container.resolve(UnregisteredService)
except DependencyResolutionException as e:
    print(f"Resolution failed: {e.dependency_name}")
```

## Performance Considerations

- **Container Resolution**: Cached for singletons, direct creation for others
- **Lazy Proxies**: Minimal overhead until first access
- **Scoped Management**: WeakKeyDictionary for automatic cleanup
- **Thread Safety**: Minimal locking overhead

## Example Usage

```python
from nexusdi.core.container import _container
from nexusdi.core.lifecycle import LifeCycle

# Manual registration
_container.register(MyService, LifeCycle.SINGLETON)

# Resolution
service = _container.resolve(MyService)

# Statistics
stats = _container.get_stats()
print(f"Container has {stats['registered_dependencies']} dependencies")

# Scope cleanup
_container.clear_scope()
```
