# Circular Dependencies

NexusDI automatically handles circular dependencies using lazy proxies, allowing services to reference each other without causing resolution errors.

## Basic Circular Dependencies

```python
from nexusdi import singleton

@singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):  # Forward reference
        self.service_b = service_b

    def method_a(self):
        return f"A calls B: {self.service_b.method_b()}"

@singleton
class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a

    def method_b(self):
        return "B executed"

    def call_a(self):
        return f"B calls A: {self.service_a.method_a()}"
```

## How It Works

NexusDI uses lazy proxies to break circular references:

```python
# When ServiceA is resolved:
# 1. ServiceA creation starts
# 2. ServiceB needed -> LazyProxy created for ServiceB
# 3. ServiceA gets LazyProxy, not actual ServiceB
# 4. When ServiceB method is called, proxy resolves to actual ServiceB

service_a = _container.resolve(ServiceA)
# service_a.service_b is a LazyProxy until first access
result = service_a.method_a()  # Now resolves ServiceB
```

## Complex Circular Chains

Handle multiple services in circular relationship:

```python
@singleton
class UserService:
    def __init__(self, order_service: 'OrderService', notification_service: 'NotificationService'):
        self.order_service = order_service
        self.notification_service = notification_service

    def create_user(self, name: str):
        user = {"name": name, "id": 123}
        self.notification_service.send_welcome(user)
        return user

@singleton
class OrderService:
    def __init__(self, user_service: UserService, payment_service: 'PaymentService'):
        self.user_service = user_service
        self.payment_service = payment_service

    def create_order(self, user_id: int):
        # Can access user_service normally
        return f"Order for user {user_id}"

@singleton
class PaymentService:
    def __init__(self, order_service: OrderService):
        self.order_service = order_service

    def process_payment(self):
        return "Payment processed"

@singleton
class NotificationService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def send_welcome(self, user):
        return f"Welcome {user['name']}"
```

## Proxy Behavior

Lazy proxies behave like the target object:

```python
@singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self.service_b = service_b

    def test_proxy(self):
        # All these work with the proxy
        result = self.service_b.get_data()           # Method call
        value = self.service_b.some_attribute        # Attribute access
        self.service_b.some_attribute = "new_value"  # Attribute setting
        length = len(self.service_b)                 # Special methods
        return str(self.service_b)                   # String conversion

@singleton
class ServiceB:
    def __init__(self):
        self.some_attribute = "initial"
        self.data = [1, 2, 3]

    def get_data(self):
        return self.data

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return f"ServiceB with {len(self.data)} items"
```

## Mixed Lifecycles in Circular Dependencies

```python
@singleton
class ConfigService:
    def __init__(self, cache_service: 'CacheService'):
        self.cache_service = cache_service
        self.settings = {"debug": True}

    def get_setting(self, key):
        # Check cache first
        cached = self.cache_service.get(key)
        if cached:
            return cached
        return self.settings.get(key)

@transient  # Different lifecycle
class CacheService:
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self.cache = {}

    def get(self, key):
        if self.config_service.get_setting("debug"):
            print(f"Cache lookup: {key}")
        return self.cache.get(key)
```

## Error Handling with Circular Dependencies

```python
from nexusdi.exceptions import CircularDependencyException

@singleton
class ProblematicServiceA:
    def __init__(self, service_b: 'ProblematicServiceB'):
        # If circular dependency can't be resolved
        self.service_b = service_b

# In rare cases where lazy proxies can't resolve:
try:
    service = _container.resolve(ProblematicServiceA)
except CircularDependencyException as e:
    print(f"Circular dependency: {' -> '.join(e.dependency_chain)}")
```

## Best Practices

### Use Forward References

```python
from __future__ import annotations  # Python 3.7+

@singleton
class ServiceA:
    def __init__(self, service_b: ServiceB):  # No quotes needed
        self.service_b = service_b
```

### Lazy Initialization Pattern

```python
@singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self._service_b = service_b

    @property
    def service_b(self):
        # Lazy access through property
        return self._service_b

    def do_work(self):
        # Service B only resolved when actually needed
        return self.service_b.get_data()
```

### Interface Segregation

Break circular dependencies by introducing interfaces:

```python
from abc import ABC, abstractmethod

class INotificationService(ABC):
    @abstractmethod
    def send_notification(self, message: str):
        pass

@singleton
class UserService:
    def __init__(self, notification: INotificationService):
        self.notification = notification

@singleton
class NotificationService(INotificationService):
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def send_notification(self, message: str):
        return f"Sent: {message}"
```

## Debugging Circular Dependencies

Check proxy resolution:

```python
@singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self.service_b = service_b
        print(f"ServiceA got: {repr(self.service_b)}")  # Shows LazyProxy

    def use_service_b(self):
        result = self.service_b.method()  # Triggers resolution
        print(f"After use: {repr(self.service_b)}")  # Shows actual object
        return result
```

## Performance Considerations

- Proxy creation has minimal overhead
- First access triggers resolution
- Subsequent access is direct (no proxy overhead)
- Circular resolution happens once per singleton

## Common Patterns

### Event System with Circular References

```python
@singleton
class EventBus:
    def __init__(self, logger: 'Logger'):
        self.logger = logger
        self.listeners = {}

    def emit(self, event: str, data):
        self.logger.log(f"Event: {event}")
        # Notify listeners...

@singleton
class Logger:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    def log(self, message: str):
        print(f"LOG: {message}")
        # Could emit log events back to event bus if needed
```

### Repository-Service Pattern

```python
@singleton
class UserRepository:
    def __init__(self, audit_service: 'AuditService'):
        self.audit_service = audit_service

    def save_user(self, user):
        # Save user and audit the action
        self.audit_service.log_action("user_saved", user)
        return user

@singleton
class AuditService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def log_action(self, action: str, entity):
        # Log the action (without creating infinite loops)
        print(f"Audit: {action} for {entity}")
```
