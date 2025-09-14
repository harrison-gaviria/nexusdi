# Basic Examples

This section provides practical examples to help you get started with NexusDI.

## Simple Service Example

```python
from nexusdi import singleton, transient, inject, initialize

@singleton
class DatabaseService:
    def __init__(self):
        self.connection = "postgresql://localhost/myapp"
    
    def query(self, sql: str):
        return f"Executing: {sql} on {self.connection}"

@transient
class UserService:
    def __init__(self, db: DatabaseService):
        self.db = db
    
    def get_user(self, user_id: int):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

@inject
def handle_user_request(user_service: UserService, user_id: int):
    return user_service.get_user(user_id)

# Initialize and use
initialize()
result = handle_user_request(user_id=123)
print(result)  # "Executing: SELECT * FROM users WHERE id = 123 on postgresql://localhost/myapp"
```

## Configuration and Logging Example

```python
from nexusdi import singleton, transient, initialize
import logging

@singleton
class ConfigService:
    def __init__(self):
        self.settings = {
            'debug': True,
            'database_url': 'postgresql://localhost/myapp',
            'log_level': 'INFO'
        }
    
    def get(self, key: str, default=None):
        return self.settings.get(key, default)

@singleton
class LoggerService:
    def __init__(self, config: ConfigService):
        self.config = config
        logging.basicConfig(level=config.get('log_level'))
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)

@transient
class EmailService:
    def __init__(self, config: ConfigService, logger: LoggerService):
        self.config = config
        self.logger = logger
    
    def send_email(self, to: str, subject: str):
        self.logger.info(f"Sending email to {to}: {subject}")
        if self.config.get('debug'):
            print(f"DEBUG: Email sent to {to}")
        return f"Email sent to {to}"

# Usage
initialize()

email_service = _container.resolve(EmailService)
email_service.send_email("user@example.com", "Welcome!")
```

## Repository Pattern Example

```python
from nexusdi import singleton, transient, initialize
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: int):
        pass
    
    @abstractmethod
    def save(self, user):
        pass

@transient
class DatabaseUserRepository(IUserRepository):
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def find_by_id(self, user_id: int):
        return {"id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}
    
    def save(self, user):
        print(f"Saving user: {user}")
        return user

@transient
class UserBusinessLogic:
    def __init__(self, user_repo: DatabaseUserRepository, email_service: EmailService):
        self.user_repo = user_repo
        self.email_service = email_service
    
    def create_user(self, name: str, email: str):
        user = {"name": name, "email": email, "id": 123}
        saved_user = self.user_repo.save(user)
        self.email_service.send_email(email, "Account Created")
        return saved_user

# Usage
initialize()
business_logic = _container.resolve(UserBusinessLogic)
user = business_logic.create_user("John Doe", "john@example.com")
```

## Caching Example

```python
from nexusdi import singleton, transient, initialize
import time

@singleton
class CacheService:
    def __init__(self):
        self.cache = {}
        self.ttl = 300  # 5 minutes
    
    def get(self, key: str):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value):
        self.cache[key] = (value, time.time())

@transient
class DataService:
    def __init__(self, cache: CacheService, db: DatabaseService):
        self.cache = cache
        self.db = db
    
    def get_expensive_data(self, key: str):
        # Check cache first
        cached_data = self.cache.get(key)
        if cached_data:
            return cached_data
        
        # Expensive operation
        data = self.db.query(f"SELECT * FROM expensive_table WHERE key = '{key}'")
        self.cache.set(key, data)
        return data

# Usage
initialize()
data_service = _container.resolve(DataService)
result = data_service.get_expensive_data("user_123")
```

## Event System Example

```python
from nexusdi import singleton, transient, initialize

@singleton
class EventBus:
    def __init__(self):
        self.listeners = {}
    
    def subscribe(self, event_type: str, callback):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def publish(self, event_type: str, data):
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                callback(data)

@singleton
class NotificationService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe('user_created', self.send_welcome_email)
    
    def send_welcome_email(self, user_data):
        print(f"Sending welcome email to {user_data['email']}")

@transient
class UserService:
    def __init__(self, event_bus: EventBus, user_repo: DatabaseUserRepository):
        self.event_bus = event_bus
        self.user_repo = user_repo
    
    def create_user(self, name: str, email: str):
        user = {"name": name, "email": email}
        saved_user = self.user_repo.save(user)
        
        # Publish event
        self.event_bus.publish('user_created', saved_user)
        return saved_user

# Usage
initialize()
user_service = _container.resolve(UserService)
user = user_service.create_user("Alice", "alice@example.com")
```

## Testing Example

```python
import pytest
from nexusdi import singleton, transient, _container, initialize

# Production services
@singleton
class DatabaseService:
    def query(self, sql: str):
        return f"Real database result: {sql}"

@transient
class UserService:
    def __init__(self, db: DatabaseService):
        self.db = db
    
    def get_user(self, user_id: int):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Test setup
class MockDatabaseService:
    def query(self, sql: str):
        return f"Mock result: {sql}"

def test_user_service():
    # Override dependency for testing
    _container.register(MockDatabaseService, LifeCycle.SINGLETON)
    _container._dependencies[DatabaseService] = _container._dependencies[MockDatabaseService]
    
    user_service = _container.resolve(UserService)
    result = user_service.get_user(123)
    
    assert "Mock result" in result
    assert "SELECT * FROM users WHERE id = 123" in result

# Run test
initialize()
test_user_service()
```

## Common Patterns

### Factory Pattern

```python
@singleton
class ServiceFactory:
    def __init__(self, config: ConfigService):
        self.config = config
    
    def create_email_service(self):
        provider = self.config.get('email_provider', 'smtp')
        if provider == 'smtp':
            return SMTPEmailService()
        elif provider == 'sendgrid':
            return SendGridEmailService()
        else:
            raise ValueError(f"Unknown email provider: {provider}")

@transient
class EmailSender:
    def __init__(self, factory: ServiceFactory):
        self.email_service = factory.create_email_service()
```

### Strategy Pattern

```python
@transient
class PaymentProcessor:
    def __init__(self, config: ConfigService):
        self.config = config
        self.strategies = {
            'credit_card': CreditCardPayment(),
            'paypal': PayPalPayment(),
            'bank_transfer': BankTransferPayment()
        }
    
    def process(self, amount: float, method: str):
        strategy = self.strategies.get(method)
        if not strategy:
            raise ValueError(f"Unsupported payment method: {method}")
        return strategy.process(amount)
```

These examples demonstrate common patterns and use cases for NexusDI in real applications. Each example shows how to properly structure your dependencies and use the injection system effectively.