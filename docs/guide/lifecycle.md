# Lifecycle Management

NexusDI provides three distinct lifecycle types for managing your dependencies. Understanding when and how to use each lifecycle is crucial for building efficient applications.

## Singleton Lifecycle

Singleton dependencies are created once and reused throughout the application's lifetime. They're perfect for expensive-to-create objects that maintain state.

### Usage

```python
from nexusdi import singleton

@singleton
class DatabaseConnectionPool:
    def __init__(self):
        print("Creating expensive database connection pool...")
        self.connections = self._create_pool()
        self.max_connections = 10
    
    def _create_pool(self):
        # Expensive initialization
        return ["connection_1", "connection_2", "connection_3"]
    
    def get_connection(self):
        return self.connections[0]  # Simplified logic
```

### Characteristics

- **Single Instance**: Only one instance exists per application
- **Lazy Creation**: Created when first requested
- **Thread-Safe**: Safe to use across multiple threads
- **Memory Efficient**: Reuses the same instance

### Best Practices

```python
@singleton
class ConfigurationService:
    def __init__(self):
        # Load configuration once at startup
        self.settings = self._load_from_file()
        self.cache = {}
    
    def get_setting(self, key: str, default=None):
        return self.settings.get(key, default)
    
    def _load_from_file(self):
        # Expensive I/O operation done once
        return {"database_url": "postgres://...", "api_key": "secret"}

# Multiple resolutions return the same instance
config1 = _container.resolve(ConfigurationService)
config2 = _container.resolve(ConfigurationService)
assert config1 is config2  # True - same instance
```

## Transient Lifecycle

Transient dependencies are created fresh every time they're requested. Use them for stateless services or when you need isolated instances.

### Usage

```python
from nexusdi import transient

@transient
class EmailSender:
    def __init__(self, config: ConfigurationService):
        self.config = config
        self.sent_count = 0  # Each instance has its own counter
    
    def send_email(self, to: str, subject: str, body: str):
        self.sent_count += 1
        print(f"Sending email #{self.sent_count} to {to}")
        # Email sending logic
```

### Characteristics

- **New Instance**: Fresh instance every time
- **No State Sharing**: Each instance is independent
- **Memory Overhead**: More memory usage than singletons
- **Isolation**: Perfect for avoiding shared state issues

### Best Practices

```python
@transient
class DataProcessor:
    def __init__(self, logger: LoggingService):
        self.logger = logger
        self.processed_items = []  # Instance-specific state
    
    def process(self, data):
        # Each processor handles its own data
        self.processed_items.append(data)
        self.logger.info(f"Processed {len(self.processed_items)} items")
        return self._transform_data(data)
    
    def _transform_data(self, data):
        # Processing logic
        return data.upper()

# Each resolution creates a new instance
processor1 = _container.resolve(DataProcessor)
processor2 = _container.resolve(DataProcessor)
assert processor1 is not processor2  # True - different instances
```

## Scoped Lifecycle

Scoped dependencies are created once per scope and reused within that scope. This is particularly useful for web applications where you want one instance per request.

### Usage

```python
from nexusdi import scoped

@scoped
class RequestContext:
    def __init__(self):
        self.request_id = None
        self.user_id = None
        self.start_time = time.time()
        self.data = {}
    
    def set_request_info(self, request_id: str, user_id: int):
        self.request_id = request_id
        self.user_id = user_id
    
    def add_data(self, key: str, value):
        self.data[key] = value

@scoped
class AuditService:
    def __init__(self, context: RequestContext):
        self.context = context
        self.audit_entries = []
    
    def log_action(self, action: str):
        entry = {
            "request_id": self.context.request_id,
            "user_id": self.context.user_id,
            "action": action,
            "timestamp": time.time()
        }
        self.audit_entries.append(entry)
```

### Scope Management

```python
from nexusdi import scope_cleanup

def handle_request(request_id: str, user_id: int):
    try:
        # Set up request context
        context = _container.resolve(RequestContext)
        context.set_request_info(request_id, user_id)
        
        # Use scoped services - they'll share the same context
        audit = _container.resolve(AuditService)
        user_service = _container.resolve(UserService)  # Also uses RequestContext
        
        # Process the request
        audit.log_action("request_started")
        result = user_service.process_user_data(user_id)
        audit.log_action("request_completed")
        
        return result
    
    finally:
        # Clean up scoped instances
        scope_cleanup()
```

### Automatic Scope Creation

```python
# NexusDI automatically creates scopes when needed
@scoped
class SessionData:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now()

# First access creates a new scope
session1 = _container.resolve(SessionData)

# Second access in same thread/context returns same instance
session2 = _container.resolve(SessionData)
assert session1 is session2  # True - same scope

# After scope cleanup, new scope is created
scope_cleanup()
session3 = _container.resolve(SessionData)
assert session1 is not session3  # True - new scope
```

## Manual Binding

You can register dependencies without modifying their constructors using bind decorators:

```python
from nexusdi import bind_singleton, bind_transient, bind_scoped

# Third-party classes that you can't modify
class ExternalService:
    def __init__(self):
        self.name = "external"

# Bind without modifying the class
bind_singleton(ExternalService)

# Now you can inject it
@transient
class MyService:
    def __init__(self, external: ExternalService):
        self.external = external
```

## Lifecycle Comparison

| Aspect | Singleton | Transient | Scoped |
|--------|-----------|-----------|---------|
| **Creation** | Once per application | Every resolution | Once per scope |
| **Memory** | Low | High | Medium |
| **Thread Safety** | Shared state concerns | Isolated | Scope-isolated |
| **Use Cases** | Config, DB pools, Caches | Processors, Commands | Request data, User context |
| **Cleanup** | Application shutdown | Immediate GC | Scope end |

## Advanced Patterns

### Conditional Lifecycles

```python
import os
from nexusdi import singleton, transient

def cache_service_factory():
    if os.getenv("USE_REDIS") == "true":
        @singleton
        class RedisCache:
            def __init__(self):
                self.client = redis.Redis()
        return RedisCache
    else:
        @transient
        class MemoryCache:
            def __init__(self):
                self.data = {}
        return MemoryCache

CacheService = cache_service_factory()
```

### Lifecycle Validation

```python
from nexusdi.exceptions import LifecycleException

@singleton
class ExpensiveResource:
    def __init__(self):
        self.connections = []
        self.is_initialized = False
    
    def initialize(self):
        if self.is_initialized:
            raise LifecycleException("Resource already initialized")
        self.is_initialized = True
```

## Testing with Different Lifecycles

```python
import pytest
from nexusdi import _container, scope_cleanup

def test_singleton_behavior():
    # Singletons return same instance
    service1 = _container.resolve(ConfigurationService)
    service2 = _container.resolve(ConfigurationService)
    assert service1 is service2

def test_transient_behavior():
    # Transients return different instances
    processor1 = _container.resolve(DataProcessor)
    processor2 = _container.resolve(DataProcessor)
    assert processor1 is not processor2

def test_scoped_behavior():
    # Same scope returns same instance
    context1 = _container.resolve(RequestContext)
    context2 = _container.resolve(RequestContext)
    assert context1 is context2
    
    # New scope returns different instance
    scope_cleanup()
    context3 = _container.resolve(RequestContext)
    assert context1 is not context3
```

## Performance Considerations

### Memory Usage

- **Singletons**: Most memory efficient for heavy objects
- **Transients**: Can cause memory bloat if not carefully managed
- **Scoped**: Balance between isolation and efficiency

### Resolution Speed

- **Singletons**: Fastest after first creation (cached)
- **Transients**: Slowest (creates new instance each time)
- **Scoped**: Fast within scope, slower on scope changes

### Best Practices

1. Use **singletons** for expensive, stateful resources
2. Use **transients** for lightweight, stateless services
3. Use **scoped** for request-specific data and context
4. Always clean up scoped dependencies
5. Be cautious with singleton state in multi-threaded applications

## Next Steps

- [Dependency Injection](injection.md) - Learn advanced injection patterns
- [Scoped Dependencies](scoped.md) - Deep dive into scoped lifecycle
- [Examples](../examples/basic.md) - See lifecycle patterns in action
