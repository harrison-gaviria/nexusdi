# Advanced Examples

Complex patterns and advanced usage scenarios for NexusDI.

## Circular Dependencies

### Service Layer with Circular References

```python
from nexusdi import singleton

@singleton
class UserService:
    def __init__(self, order_service: 'OrderService'):
        self.order_service = order_service
    
    def get_user_orders(self, user_id: int):
        return self.order_service.find_by_user(user_id)

@singleton
class OrderService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    def find_by_user(self, user_id: int):
        # Access user_service through lazy proxy
        user = self.user_service.get_user_info(user_id)
        return f"Orders for {user}"

# Usage - circular dependencies are automatically resolved
initialize()
user_service = _container.resolve(UserService)
orders = user_service.get_user_orders(123)
```

### Complex Circular Chain

```python
@singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB', service_c: 'ServiceC'):
        self.service_b = service_b
        self.service_c = service_c
    
    def method_a(self):
        return f"A -> {self.service_b.method_b()}"

@singleton
class ServiceB:
    def __init__(self, service_c: 'ServiceC', service_a: ServiceA):
        self.service_c = service_c
        self.service_a = service_a
    
    def method_b(self):
        return f"B -> {self.service_c.method_c()}"

@singleton
class ServiceC:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a
    
    def method_c(self):
        return "C executed"
```

## Multi-Tenant Architecture

```python
from nexusdi import scoped, singleton, transient
import threading

@scoped
class TenantContext:
    def __init__(self):
        self.tenant_id = None
        self.database_url = None
        self.config = {}
    
    def set_tenant(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.database_url = f"postgresql://tenant_{tenant_id}.db"
        self.config = self._load_tenant_config(tenant_id)
    
    def _load_tenant_config(self, tenant_id: str):
        return {"tenant": tenant_id, "features": ["feature1", "feature2"]}

@transient
class TenantAwareService:
    def __init__(self, tenant_context: TenantContext):
        self.tenant_context = tenant_context
    
    def process_data(self, data):
        tenant_id = self.tenant_context.tenant_id
        return f"Processing {data} for tenant {tenant_id}"

class TenantMiddleware:
    @inject
    def __call__(self, request, tenant_context: TenantContext):
        tenant_id = request.headers.get('X-Tenant-ID')
        tenant_context.set_tenant(tenant_id)
        return f"Request processed for tenant {tenant_id}"
```

## Plugin Architecture

```python
from abc import ABC, abstractmethod
from nexusdi import singleton, transient

class IPlugin(ABC):
    @abstractmethod
    def execute(self, data):
        pass

@singleton
class PluginRegistry:
    def __init__(self):
        self.plugins = []
    
    def register(self, plugin: IPlugin):
        self.plugins.append(plugin)
    
    def execute_all(self, data):
        results = []
        for plugin in self.plugins:
            results.append(plugin.execute(data))
        return results

@transient
class EmailPlugin(IPlugin):
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def execute(self, data):
        return self.email_service.send_email(data['email'], data['subject'])

@transient
class LoggingPlugin(IPlugin):
    def __init__(self, logger: LoggerService):
        self.logger = logger
    
    def execute(self, data):
        self.logger.info(f"Processing: {data}")
        return f"Logged: {data}"

@transient
class PluginManager:
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._register_plugins()
    
    def _register_plugins(self):
        # Auto-register plugins
        email_plugin = _container.resolve(EmailPlugin)
        logging_plugin = _container.resolve(LoggingPlugin)
        
        self.registry.register(email_plugin)
        self.registry.register(logging_plugin)
```

## Factory Pattern with DI

```python
@singleton
class ServiceFactory:
    def __init__(self, config: ConfigService):
        self.config = config
    
    def create_payment_processor(self, payment_type: str):
        if payment_type == "credit_card":
            return _container.resolve(CreditCardProcessor)
        elif payment_type == "paypal":
            return _container.resolve(PayPalProcessor)
        else:
            raise ValueError(f"Unknown payment type: {payment_type}")

@transient
class CreditCardProcessor:
    def __init__(self, bank_service: BankService):
        self.bank_service = bank_service
    
    def process(self, amount: float):
        return self.bank_service.charge_card(amount)

@transient
class PayPalProcessor:
    def __init__(self, paypal_api: PayPalAPI):
        self.paypal_api = paypal_api
    
    def process(self, amount: float):
        return self.paypal_api.process_payment(amount)

@transient
class PaymentService:
    def __init__(self, factory: ServiceFactory):
        self.factory = factory
    
    def process_payment(self, payment_type: str, amount: float):
        processor = self.factory.create_payment_processor(payment_type)
        return processor.process(amount)
```

## Command Pattern with DI

```python
from abc import ABC, abstractmethod
from nexusdi import singleton, transient
from typing import List

class ICommand(ABC):
    @abstractmethod
    def execute(self):
        pass

@transient
class CreateUserCommand(ICommand):
    def __init__(self, user_service: UserService, username: str, email: str):
        self.user_service = user_service
        self.username = username
        self.email = email
    
    def execute(self):
        return self.user_service.create_user(self.username, self.email)

@transient
class SendEmailCommand(ICommand):
    def __init__(self, email_service: EmailService, to: str, subject: str):
        self.email_service = email_service
        self.to = to
        self.subject = subject
    
    def execute(self):
        return self.email_service.send_email(self.to, self.subject)

@singleton
class CommandInvoker:
    def __init__(self):
        self.commands: List[ICommand] = []
    
    def add_command(self, command: ICommand):
        self.commands.append(command)
    
    def execute_all(self):
        results = []
        for command in self.commands:
            results.append(command.execute())
        return results

# Usage
def create_user_workflow(username: str, email: str):
    invoker = _container.resolve(CommandInvoker)
    
    # Create commands with DI
    create_cmd = CreateUserCommand(
        _container.resolve(UserService), 
        username, 
        email
    )
    email_cmd = SendEmailCommand(
        _container.resolve(EmailService),
        email,
        "Welcome!"
    )
    
    invoker.add_command(create_cmd)
    invoker.add_command(email_cmd)
    
    return invoker.execute_all()
```

## Observer Pattern with Events

```python
from typing import List, Callable
from nexusdi import singleton, transient

@singleton
class EventManager:
    def __init__(self):
        self.listeners = {}
    
    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def publish(self, event_type: str, data):
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                callback(data)

@singleton
class EmailNotificationHandler:
    def __init__(self, email_service: EmailService, event_manager: EventManager):
        self.email_service = email_service
        event_manager.subscribe('user_created', self.handle_user_created)
        event_manager.subscribe('order_placed', self.handle_order_placed)
    
    def handle_user_created(self, user_data):
        self.email_service.send_email(
            user_data['email'], 
            "Welcome!",
            f"Welcome {user_data['name']}"
        )
    
    def handle_order_placed(self, order_data):
        self.email_service.send_email(
            order_data['user_email'],
            "Order Confirmation",
            f"Order {order_data['id']} confirmed"
        )

@transient
class UserService:
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
    
    def create_user(self, name: str, email: str):
        user = {"id": 123, "name": name, "email": email}
        self.event_manager.publish('user_created', user)
        return user
```

## Decorator Chain Pattern

```python
from functools import wraps
from nexusdi import singleton, transient

@singleton
class SecurityService:
    def check_permissions(self, user_id: int, action: str):
        return True  # Simplified

@singleton
class AuditService:
    def log_action(self, user_id: int, action: str):
        print(f"User {user_id} performed {action}")

@transient
class DecoratedService:
    def __init__(self, security: SecurityService, audit: AuditService):
        self.security = security
        self.audit = audit
    
    def secure_and_audit(self, action: str):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                user_id = kwargs.get('user_id', 1)
                
                # Security check
                if not self.security.check_permissions(user_id, action):
                    raise PermissionError("Access denied")
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Audit log
                self.audit.log_action(user_id, action)
                
                return result
            return wrapper
        return decorator

# Usage
@transient
class BusinessService:
    def __init__(self, decorator_service: DecoratedService):
        self.decorator = decorator_service
    
    @property
    def secure_operation(self):
        return self.decorator.secure_and_audit("sensitive_operation")
    
    @secure_operation
    def perform_sensitive_operation(self, data, user_id: int):
        return f"Performed operation with {data}"
```

## Async/Await Pattern

```python
import asyncio
from nexusdi import singleton, transient

@singleton
class AsyncDatabaseService:
    async def query(self, sql: str):
        await asyncio.sleep(0.1)  # Simulate async I/O
        return f"Async result: {sql}"

@singleton
class AsyncCacheService:
    def __init__(self):
        self.cache = {}
    
    async def get(self, key: str):
        await asyncio.sleep(0.01)
        return self.cache.get(key)
    
    async def set(self, key: str, value):
        await asyncio.sleep(0.01)
        self.cache[key] = value

@transient
class AsyncUserService:
    def __init__(self, db: AsyncDatabaseService, cache: AsyncCacheService):
        self.db = db
        self.cache = cache
    
    async def get_user(self, user_id: int):
        cache_key = f"user_{user_id}"
        cached_user = await self.cache.get(cache_key)
        
        if cached_user:
            return cached_user
        
        user_data = await self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
        await self.cache.set(cache_key, user_data)
        
        return user_data

# Usage with async context
async def async_example():
    initialize()
    user_service = _container.resolve(AsyncUserService)
    user = await user_service.get_user(123)
    print(user)

# Run async example
# asyncio.run(async_example())
```

## Custom Lifecycle Implementation

```python
from nexusdi.core.lifecycle import LifeCycle
from nexusdi.core.container import _container
import time

class TimedLifecycle:
    """Custom lifecycle that expires instances after a specified time."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.instances = {}
        self.timestamps = {}
    
    def get_instance(self, cls_type):
        now = time.time()
        
        # Check if instance exists and is still valid
        if cls_type in self.instances:
            if now - self.timestamps[cls_type] < self.ttl_seconds:
                return self.instances[cls_type]
            else:
                # Instance expired, remove it
                del self.instances[cls_type]
                del self.timestamps[cls_type]
        
        # Create new instance
        instance = _container._create_instance_with_lazy_deps(cls_type)
        self.instances[cls_type] = instance
        self.timestamps[cls_type] = now
        
        return instance

# Usage of custom lifecycle
timed_lifecycle = TimedLifecycle(ttl_seconds=60)

class TimedService:
    def __init__(self):
        self.created_at = time.time()
    
    def get_age(self):
        return time.time() - self.created_at

# Register with custom lifecycle
_container.register(TimedService, LifeCycle.SINGLETON)
# Override the resolution behavior (simplified example)
```

## Memory-Efficient Large Object Handling

```python
import weakref
from nexusdi import singleton, transient

@singleton
class ResourcePool:
    def __init__(self):
        self._pool = weakref.WeakValueDictionary()
        self._stats = {"created": 0, "reused": 0}
    
    def get_resource(self, resource_id: str):
        if resource_id in self._pool:
            self._stats["reused"] += 1
            return self._pool[resource_id]
        
        resource = ExpensiveResource(resource_id)
        self._pool[resource_id] = resource
        self._stats["created"] += 1
        return resource
    
    def get_stats(self):
        return self._stats.copy()

class ExpensiveResource:
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self.large_data = [i for i in range(100000)]  # Simulate large object
    
    def process(self, data):
        return f"Processing {data} with resource {self.resource_id}"

@transient
class ResourceManager:
    def __init__(self, pool: ResourcePool):
        self.pool = pool
    
    def process_with_resource(self, resource_id: str, data):
        resource = self.pool.get_resource(resource_id)
        return resource.process(data)
```

## Testing with Complex Dependencies

```python
import pytest
from unittest.mock import Mock, patch
from nexusdi import singleton, transient, _container, initialize

# Production services
@singleton
class ExternalApiService:
    def call_api(self, endpoint: str):
        return f"Real API call to {endpoint}"

@singleton
class DatabaseService:
    def query(self, sql: str):
        return f"Real DB query: {sql}"

@transient
class BusinessLogic:
    def __init__(self, api: ExternalApiService, db: DatabaseService):
        self.api = api
        self.db = db
    
    def complex_operation(self, data):
        api_result = self.api.call_api("/process")
        db_result = self.db.query("SELECT * FROM processed")
        return f"Business logic: {api_result} + {db_result} + {data}"

# Test setup with mocks
@pytest.fixture
def mock_container():
    # Create mock services
    mock_api = Mock(spec=ExternalApiService)
    mock_api.call_api.return_value = "Mock API response"
    
    mock_db = Mock(spec=DatabaseService)
    mock_db.query.return_value = "Mock DB response"
    
    # Override container dependencies
    original_api_dep = _container._dependencies.get(ExternalApiService)
    original_db_dep = _container._dependencies.get(DatabaseService)
    
    _container._dependencies[ExternalApiService] = Mock()
    _container._dependencies[ExternalApiService].instance = mock_api
    _container._dependencies[DatabaseService] = Mock()
    _container._dependencies[DatabaseService].instance = mock_db
    
    yield
    
    # Restore original dependencies
    if original_api_dep:
        _container._dependencies[ExternalApiService] = original_api_dep
    if original_db_dep:
        _container._dependencies[DatabaseService] = original_db_dep

def test_complex_business_logic(mock_container):
    business_logic = _container.resolve(BusinessLogic)
    result = business_logic.complex_operation("test_data")
    
    assert "Mock API response" in result
    assert "Mock DB response" in result
    assert "test_data" in result

# Performance testing
def test_performance_with_di():
    initialize()
    
    import time
    start_time = time.time()
    
    # Resolve multiple times to test caching
    for _ in range(1000):
        service = _container.resolve(BusinessLogic)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"1000 resolutions took {duration:.4f} seconds")
    assert duration < 1.0  # Should be fast due to singleton caching
```

These advanced examples demonstrate sophisticated patterns like circular dependencies, multi-tenancy, plugin architectures, and complex testing scenarios that showcase NexusDI's flexibility and power.