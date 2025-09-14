# Basic Concepts

Understanding these core concepts will help you effectively use NexusDI in your applications.

## Dependency Injection

Dependency injection is a design pattern where objects receive their dependencies from external sources rather than creating them internally. This promotes loose coupling, better testability, and more maintainable code.

### Without Dependency Injection

```python
class EmailService:
    def __init__(self):
        # Tight coupling - hard to test and change
        self.smtp_client = SMTPClient("smtp.example.com", 587)
    
    def send_email(self, to: str, message: str):
        self.smtp_client.send(to, message)

class UserService:
    def __init__(self):
        # Creating dependencies internally
        self.email_service = EmailService()
```

### With Dependency Injection

```python
from nexusdi import singleton, transient

@singleton
class EmailService:
    def __init__(self, smtp_client: SMTPClient):
        # Dependency is injected
        self.smtp_client = smtp_client
    
    def send_email(self, to: str, message: str):
        self.smtp_client.send(to, message)

@transient
class UserService:
    def __init__(self, email_service: EmailService):
        # Dependency is injected
        self.email_service = email_service
```

## Dependency Container

The dependency container is the central registry that manages all your dependencies. It knows how to create instances, manage their lifecycles, and resolve their dependencies.

```python
from nexusdi.core.container import _container

# The container automatically handles registration when you use decorators
# You can also manually resolve dependencies
user_service = _container.resolve(UserService)
```

## Lifecycles

NexusDI supports three lifecycle types:

### Singleton

One instance for the entire application lifetime.

```python
from nexusdi import singleton

@singleton
class DatabaseConnection:
    def __init__(self):
        self.connection = self._create_connection()
    
    def _create_connection(self):
        # Expensive operation - only done once
        return "database_connection"
```

**Use cases**: Database connections, configuration services, caches, loggers.

### Transient

A new instance is created every time it's requested.

```python
from nexusdi import transient

@transient
class EmailSender:
    def __init__(self, config: ConfigService):
        self.config = config
    
    def send(self, message: str):
        # Each call gets a fresh instance
        pass
```

**Use cases**: Stateless services, data processors, short-lived operations.

### Scoped

One instance per scope (typically per request or thread).

```python
from nexusdi import scoped

@scoped
class UserContext:
    def __init__(self):
        self.user_id = None
        self.permissions = []
    
    def set_user(self, user_id: int):
        self.user_id = user_id
        self.permissions = self._load_permissions(user_id)
```

**Use cases**: Request-specific data, user contexts, temporary state.

## Type Resolution

NexusDI uses multiple strategies to resolve dependencies:

### 1. Type Hints (Recommended)

```python
@transient
class UserService:
    def __init__(self, db: DatabaseService, email: EmailService):
        # Types are resolved from type hints
        self.db = db
        self.email = email
```

### 2. Parameter Name Matching

```python
@transient
class OrderService:
    def __init__(self, user_service, email_service):
        # Matched by parameter names
        self.user_service = user_service
        self.email_service = email_service
```

### 3. Manual Registration

```python
from nexusdi import bind_singleton

# Manually bind interfaces to implementations
bind_singleton(IUserRepository)  # Must be registered somewhere
```

## Lazy Loading and Circular Dependencies

NexusDI handles circular dependencies using lazy proxies:

```python
@singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self.service_b = service_b  # Lazy proxy until actually used

@singleton
class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a  # Circular dependency resolved
```

The proxy automatically resolves the actual instance when you access it:

```python
service_a = _container.resolve(ServiceA)
# service_a.service_b is a LazyProxy
result = service_a.service_b.some_method()  # Now resolves to actual ServiceB
```

## Component Scanning

NexusDI can automatically discover decorated classes across your application:

```python
from nexusdi import initialize

# Scan all loaded modules
initialize()

# Or scan specific packages
initialize(scan_packages=["myapp.services", "myapp.repositories"])
```

## Scopes and Cleanup

For scoped dependencies, you should clean up at the end of each scope:

```python
from nexusdi import scope_cleanup

def handle_request():
    try:
        # Use scoped dependencies
        result = process_request()
        return result
    finally:
        # Clean up scoped instances
        scope_cleanup()
```

## Error Handling

NexusDI provides specific exceptions for different error scenarios:

```python
from nexusdi.exceptions import (
    DependencyResolutionException,
    CircularDependencyException,
    LifecycleException
)

try:
    service = _container.resolve(UnregisteredService)
except DependencyResolutionException as e:
    print(f"Failed to resolve: {e.dependency_name}")
```

## Best Practices

1. **Use Type Hints**: Always provide type hints for better resolution
2. **Favor Composition**: Inject dependencies rather than inheriting
3. **Keep Constructors Simple**: Don't do heavy work in `__init__`
4. **Initialize Early**: Call `initialize()` at application startup
5. **Clean Up Scopes**: Always clean up scoped dependencies
6. **Test with Mocks**: Use dependency injection for better testing

## Next Steps

Now that you understand the basic concepts, dive deeper into specific areas:

- [Lifecycle Management](../guide/lifecycle.md) - Detailed lifecycle guide
- [Dependency Injection](../guide/injection.md) - Advanced injection patterns
- [Component Scanning](../guide/scanning.md) - Automatic component discovery
