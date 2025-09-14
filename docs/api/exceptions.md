# Exceptions API Reference

The exceptions module provides specialized exception classes for handling different error scenarios in the NexusDI framework.

## Base Exception

### NexusDIException

Base exception for all NexusDI related errors.

**Signature:**
```python
class NexusDIException(Exception):
    def __init__(self, message: str, dependency_type: Optional[Type] = None)
```

**Parameters:**
- `message` (str): The error message
- `dependency_type` (Type, optional): The dependency type that caused the error

**Attributes:**
- `dependency_type`: The type that caused the error (if available)

**Example:**
```python
from nexusdi.exceptions import NexusDIException

try:
    # Some NexusDI operation
    pass
except NexusDIException as e:
    print(f"NexusDI error: {e}")
    if e.dependency_type:
        print(f"Related to type: {e.dependency_type.__name__}")
```

## Dependency Resolution Exceptions

### DependencyResolutionException

Exception raised when a dependency cannot be resolved.

**Signature:**
```python
class DependencyResolutionException(NexusDIException):
    def __init__(
        self,
        dependency_name: str,
        dependency_type: Optional[Type] = None,
        missing_dependencies: Optional[List[str]] = None
    )
```

**Parameters:**
- `dependency_name` (str): Name of the dependency that failed to resolve
- `dependency_type` (Type, optional): The dependency type that failed
- `missing_dependencies` (List[str], optional): List of missing dependencies

**Attributes:**
- `dependency_name`: Name of the failed dependency
- `missing_dependencies`: List of missing dependencies

**Example:**
```python
from nexusdi.exceptions import DependencyResolutionException
from nexusdi.core.container import _container

try:
    # Trying to resolve an unregistered dependency
    service = _container.resolve(UnregisteredService)
except DependencyResolutionException as e:
    print(f"Failed to resolve: {e.dependency_name}")
    if e.missing_dependencies:
        print(f"Missing: {', '.join(e.missing_dependencies)}")
    if e.dependency_type:
        print(f"Type: {e.dependency_type.__name__}")
```

**Common Scenarios:**

1. **Unregistered Dependency:**
```python
# UnregisteredService is not decorated or manually registered
@transient
class MyService:
    def __init__(self, unregistered: UnregisteredService):
        self.unregistered = unregistered

# Raises DependencyResolutionException
service = _container.resolve(MyService)
```

2. **Missing Type Hints:**
```python
@inject
def my_function(some_service):  # No type hint
    return some_service.do_something()

# May raise DependencyResolutionException if parameter name doesn't match
```

3. **Complex Dependency Chain:**
```python
@transient
class ServiceA:
    def __init__(self, service_b: ServiceB):
        pass

@transient  
class ServiceB:
    def __init__(self, service_c: UnregisteredServiceC):  # Problem here
        pass

# Raises DependencyResolutionException mentioning ServiceC
service = _container.resolve(ServiceA)
```

### CircularDependencyException

Exception raised when a circular dependency is detected.

**Signature:**
```python
class CircularDependencyException(NexusDIException):
    def __init__(self, dependency_chain: List[str], dependency_type: Optional[Type] = None)
```

**Parameters:**
- `dependency_chain` (List[str]): The chain of dependencies forming the cycle
- `dependency_type` (Type, optional): The dependency type that caused the cycle

**Attributes:**
- `dependency_chain`: List of dependency names forming the circular chain

**Example:**
```python
from nexusdi.exceptions import CircularDependencyException

# This shouldn't happen with NexusDI's lazy proxy system,
# but could occur in edge cases
try:
    # Complex circular dependency that can't be resolved
    service = _container.resolve(ProblematicService)
except CircularDependencyException as e:
    print(f"Circular dependency: {' -> '.join(e.dependency_chain)}")
    print(f"Chain length: {len(e.dependency_chain)}")
```

**Note:** NexusDI typically handles circular dependencies automatically using lazy proxies, so this exception is rare in normal usage.

## Lifecycle Exceptions

### LifecycleException

Exception raised when there's an issue with dependency lifecycle management.

**Signature:**
```python
class LifecycleException(NexusDIException):
    def __init__(
        self,
        message: str,
        dependency_type: Optional[Type] = None,
        lifecycle: Optional[str] = None
    )
```

**Parameters:**
- `message` (str): The lifecycle error message
- `dependency_type` (Type, optional): The dependency type with lifecycle issues
- `lifecycle` (str, optional): The lifecycle type that caused the issue

**Attributes:**
- `lifecycle`: The lifecycle type that caused the issue

**Example:**
```python
from nexusdi.exceptions import LifecycleException

try:
    # Some lifecycle operation that fails
    _container.clear_scope()
except LifecycleException as e:
    print(f"Lifecycle error: {e}")
    if e.lifecycle:
        print(f"Lifecycle type: {e.lifecycle}")
    if e.dependency_type:
        print(f"Related type: {e.dependency_type.__name__}")
```

**Common Scenarios:**

1. **Scope Cleanup Failure:**
```python
@scoped
class ProblematicResource:
    def __init__(self):
        self.file_handle = open("somefile.txt")
    
    def __del__(self):
        # If this fails during cleanup
        raise Exception("Cleanup failed")

# May raise LifecycleException during scope cleanup
try:
    scope_cleanup()
except LifecycleException as e:
    print(f"Scope cleanup failed: {e}")
```

2. **Initialization Failure:**
```python
@singleton
class DatabaseService:
    def __init__(self):
        # If database connection fails
        raise Exception("Database connection failed")

# May be wrapped in LifecycleException
try:
    db = _container.resolve(DatabaseService)
except LifecycleException as e:
    print(f"Service initialization failed: {e}")
```

3. **Invalid Lifecycle State:**
```python
# Trying to use singleton after it should be cleaned up
try:
    # Some operation that violates lifecycle rules
    pass
except LifecycleException as e:
    print(f"Invalid lifecycle operation: {e}")
```

## Exception Hierarchy

```
Exception
└── NexusDIException
    ├── DependencyResolutionException
    ├── CircularDependencyException
    └── LifecycleException
```

## Error Handling Patterns

### Comprehensive Error Handling

```python
from nexusdi.exceptions import (
    NexusDIException,
    DependencyResolutionException,
    CircularDependencyException,
    LifecycleException
)

def safe_resolve(dependency_type):
    try:
        return _container.resolve(dependency_type)
    except DependencyResolutionException as e:
        print(f"Resolution failed for {e.dependency_name}")
        if e.missing_dependencies:
            print(f"Missing: {', '.join(e.missing_dependencies)}")
        return None
    except CircularDependencyException as e:
        print(f"Circular dependency: {' -> '.join(e.dependency_chain)}")
        return None
    except LifecycleException as e:
        print(f"Lifecycle error: {e}")
        return None
    except NexusDIException as e:
        print(f"General NexusDI error: {e}")
        return None
```

### Graceful Degradation

```python
@inject
def robust_function(
    primary_service: PrimaryService,
    fallback_service: Optional[FallbackService] = None
):
    try:
        return primary_service.do_work()
    except DependencyResolutionException:
        if fallback_service:
            return fallback_service.do_work()
        else:
            return "Service unavailable"
```

### Custom Error Messages

```python
def resolve_with_context(dependency_type, context: str):
    try:
        return _container.resolve(dependency_type)
    except DependencyResolutionException as e:
        # Add contextual information
        raise DependencyResolutionException(
            dependency_name=f"{e.dependency_name} (in {context})",
            dependency_type=e.dependency_type,
            missing_dependencies=e.missing_dependencies
        ) from e
```

## Debugging with Exceptions

### Logging Exception Details

```python
import logging
from nexusdi.exceptions import NexusDIException

logger = logging.getLogger(__name__)

def log_di_error(e: NexusDIException):
    logger.error(f"DI Error: {e}")
    if hasattr(e, 'dependency_name'):
        logger.error(f"Dependency: {e.dependency_name}")
    if hasattr(e, 'dependency_chain'):
        logger.error(f"Chain: {' -> '.join(e.dependency_chain)}")
    if e.dependency_type:
        logger.error(f"Type: {e.dependency_type.__name__}")
```

### Exception Context Managers

```python
from contextlib import contextmanager

@contextmanager
def di_error_handler(operation: str):
    try:
        yield
    except NexusDIException as e:
        print(f"Error during {operation}: {e}")
        # Could log, send metrics, etc.
        raise

# Usage
with di_error_handler("service resolution"):
    service = _container.resolve(MyService)
```

## Testing Exception Scenarios

```python
import pytest
from nexusdi.exceptions import DependencyResolutionException

def test_unregistered_dependency():
    with pytest.raises(DependencyResolutionException) as exc_info:
        _container.resolve(UnregisteredService)
    
    assert "UnregisteredService" in str(exc_info.value)
    assert exc_info.value.dependency_name == "UnregisteredService"

def test_missing_type_hints():
    @inject
    def problematic_function(unknown_service):
        return unknown_service
    
    with pytest.raises(DependencyResolutionException):
        problematic_function()
```

## Best Practices

1. **Catch Specific Exceptions**: Handle specific exception types rather than broad catches
2. **Provide Context**: Add meaningful context when re-raising exceptions
3. **Log Details**: Log exception details for debugging
4. **Graceful Degradation**: Provide fallback behavior when possible
5. **Test Error Paths**: Include exception scenarios in your tests
6. **Documentation**: Document expected exceptions in your API

## Performance Impact

- Exception creation has minimal overhead
- Stack traces are preserved for debugging
- No performance impact during normal operation
- Exception handling should be used for exceptional cases, not control flow
