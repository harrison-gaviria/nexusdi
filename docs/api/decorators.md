# Decorators API Reference

The decorators module provides the main interface for dependency injection through Python decorators.

## Lifecycle Decorators

### @singleton

Decorates a class to be registered as a singleton dependency.

**Signature:**
```python
def singleton(cls: Type) -> Type
```

**Parameters:**
- `cls` (Type): The class to register as singleton

**Returns:**
- Type: The decorated class with patched constructor

**Example:**
```python
from nexusdi import singleton

@singleton
class DatabaseService:
    def __init__(self):
        self.connection = "database_connection"
    
    def query(self, sql: str):
        return f"Result: {sql}"

# Usage - same instance returned every time
service1 = _container.resolve(DatabaseService)
service2 = _container.resolve(DatabaseService)
assert service1 is service2  # True
```

### @transient

Decorates a class to be registered as a transient dependency.

**Signature:**
```python
def transient(cls: Type) -> Type
```

**Parameters:**
- `cls` (Type): The class to register as transient

**Returns:**
- Type: The decorated class with patched constructor

**Example:**
```python
from nexusdi import transient

@transient
class EmailSender:
    def __init__(self, config: ConfigService):
        self.config = config
        self.sent_count = 0
    
    def send_email(self, to: str, message: str):
        self.sent_count += 1
        print(f"Sending email #{self.sent_count}")

# Usage - new instance each time
sender1 = _container.resolve(EmailSender)
sender2 = _container.resolve(EmailSender)
assert sender1 is not sender2  # True
```

### @scoped

Decorates a class to be registered as a scoped dependency.

**Signature:**
```python
def scoped(cls: Type) -> Type
```

**Parameters:**
- `cls` (Type): The class to register as scoped

**Returns:**
- Type: The decorated class with patched constructor

**Example:**
```python
from nexusdi import scoped, scope_cleanup

@scoped
class RequestContext:
    def __init__(self):
        self.request_id = None
        self.user_data = {}
    
    def set_request_id(self, request_id: str):
        self.request_id = request_id

# Usage - same instance within scope
context1 = _container.resolve(RequestContext)
context2 = _container.resolve(RequestContext)
assert context1 is context2  # True - same scope

scope_cleanup()  # End scope
context3 = _container.resolve(RequestContext)
assert context1 is not context3  # True - new scope
```

## Binding Decorators

These decorators register classes without modifying their constructors, useful for third-party classes.

### @bind_singleton

Binds a class as singleton without patching its constructor.

**Signature:**
```python
def bind_singleton(cls: Type) -> Type
```

**Example:**
```python
from nexusdi import bind_singleton

# Third-party class you can't modify
class ExternalService:
    def __init__(self, api_key: str):
        self.api_key = api_key

# Bind it as singleton
bind_singleton(ExternalService)

# Manual instantiation required
external = ExternalService("my-api-key")
```

### @bind_transient

Binds a class as transient without patching its constructor.

**Signature:**
```python
def bind_transient(cls: Type) -> Type
```

### @bind_scoped

Binds a class as scoped without patching its constructor.

**Signature:**
```python
def bind_scoped(cls: Type) -> Type
```

## Injection Decorators

### @inject

Decorates a function to inject dependencies into its parameters.

**Signature:**
```python
def inject(func: Callable) -> Callable
```

**Parameters:**
- `func` (Callable): The function to decorate

**Returns:**
- Callable: The decorated function with dependency injection

**Example:**
```python
from nexusdi import inject

@inject
def process_data(
    data_processor: DataProcessor, 
    logger: LoggingService,
    data: str
) -> str:
    logger.info("Processing data")
    return data_processor.process(data)

# Usage - dependencies automatically injected
result = process_data(data="my_data")
```

**Features:**
- Resolves dependencies based on parameter names and type hints
- Preserves function signature and annotations
- Handles missing dependencies gracefully
- Supports mixed injected and regular parameters

### @service

Semantic alias for @transient. Decorates a class as a service.

**Signature:**
```python
def service(cls: Type) -> Type
```

**Example:**
```python
from nexusdi import service

@service
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def get_user(self, user_id: int):
        return self.user_repo.find_by_id(user_id)

# Equivalent to @transient
```

### @controller

Semantic alias for @transient. Decorates a class as a controller.

**Signature:**
```python
def controller(cls: Type) -> Type
```

**Example:**
```python
from nexusdi import controller

@controller
class UserController:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    def get_user_endpoint(self, user_id: int):
        return {"user": self.user_service.get_user(user_id)}

# Equivalent to @transient
```

## Implementation Details

### Constructor Patching

The lifecycle decorators (`@singleton`, `@transient`, `@scoped`) patch the class constructor to enable dependency injection:

```python
# Before patching
class MyService:
    def __init__(self, dependency: SomeDependency):
        self.dependency = dependency

# After patching with @singleton
class MyService:
    def __init__(self, dependency: SomeDependency = <LazyProxy>):
        # Dependencies are automatically resolved
        self.dependency = dependency
    
    # Additional attributes added:
    # - _nexusdi_original_init: Original constructor
    # - _nexusdi_lifecycle: Lifecycle type
    # - _nexusdi_container_resolve_init: Container resolution method
```

### Dependency Resolution Strategy

The decorators use a multi-step resolution strategy:

1. **Type Hints**: Primary method using `__annotations__`
2. **Parameter Names**: Fallback matching by parameter name
3. **Lazy Proxies**: For circular dependencies
4. **Graceful Fallback**: Falls back to original constructor if injection fails

### Error Handling

```python
from nexusdi.exceptions import DependencyResolutionException, LifecycleException

@inject
def my_function(missing_service: UnregisteredService):
    return "This will raise DependencyResolutionException"

try:
    result = my_function()
except DependencyResolutionException as e:
    print(f"Failed to resolve: {e.dependency_name}")
```

## Advanced Usage

### Multiple Decorators

```python
from nexusdi import singleton, inject

@singleton
class CacheService:
    def __init__(self):
        self.cache = {}

@inject
def cached_operation(cache: CacheService, key: str, value: str):
    cache.cache[key] = value
    return f"Cached {key}={value}"
```

### Custom Parameter Names

```python
@transient
class OrderService:
    def __init__(self, user_service, email_service):
        # Resolved by parameter name matching
        self.user_service = user_service  # Matches UserService
        self.email_service = email_service  # Matches EmailService
```

### Circular Dependencies

```python
@singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self.service_b = service_b  # LazyProxy initially

@singleton  
class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a  # Circular dependency resolved

# Both services can be resolved successfully
a = _container.resolve(ServiceA)
b = _container.resolve(ServiceB)
```

### Testing Decorators

```python
import pytest
from unittest.mock import Mock
from nexusdi import singleton, inject

@singleton
class TestService:
    def __init__(self):
        self.value = "original"

@inject
def test_function(service: TestService):
    return service.value

def test_dependency_injection():
    # Test that injection works
    result = test_function()
    assert result == "original"

def test_with_mocked_dependency(mocker):
    # Mock the dependency
    mock_service = Mock()
    mock_service.value = "mocked"
    
    # Replace in container for testing
    _container.register(TestService, lambda: mock_service)
    
    result = test_function()
    assert result == "mocked"
```

## Performance Notes

- **Decorator Overhead**: Minimal runtime overhead after first resolution
- **Signature Preservation**: Function signatures and annotations are preserved
- **Lazy Resolution**: Dependencies resolved only when accessed
- **Caching**: Singleton instances cached for performance

## Best Practices

1. **Use Type Hints**: Always provide type hints for reliable resolution
2. **Choose Appropriate Lifecycle**: Match lifecycle to use case
3. **Avoid Heavy Constructor Logic**: Keep constructors light
4. **Test with Mocks**: Use dependency injection for better testing
5. **Handle Circular Dependencies**: Use forward references when needed
