# Dependency Injection

NexusDI provides multiple ways to inject dependencies into your classes and functions.

## Function Injection

Use `@inject` to automatically inject dependencies into function parameters:

```python
from nexusdi import inject, singleton, transient

@singleton
class DatabaseService:
    def get_data(self):
        return "database_data"

@transient
class EmailService:
    def send_email(self, message):
        return f"Sent: {message}"

@inject
def process_user(db_service: DatabaseService, email_service: EmailService, user_id: int):
    data = db_service.get_data()
    email_service.send_email(f"Processing user {user_id}")
    return f"Processed {user_id} with {data}"

# Call with only the non-injected parameter
result = process_user(user_id=123)
```

## Constructor Injection

Dependencies are automatically injected into class constructors:

```python
@transient
class UserService:
    def __init__(self, database: DatabaseService, email: EmailService):
        self.database = database
        self.email = email

    def create_user(self, username):
        # Both database and email are automatically injected
        user_data = self.database.get_data()
        self.email.send_email(f"Welcome {username}")
        return f"User {username} created"
```

## Type Resolution

NexusDI resolves dependencies using multiple strategies:

### 1. Type Hints (Primary)

```python
@transient
class OrderService:
    def __init__(self, user_service: UserService, email_service: EmailService):
        # Resolved by type hints
        self.user_service = user_service
        self.email_service = email_service
```

### 2. Parameter Name Matching

```python
@transient
class PaymentService:
    def __init__(self, database_service, email_service):
        # Resolved by parameter name matching
        self.database = database_service
        self.email = email_service
```

## Manual Resolution

You can manually resolve dependencies:

```python
from nexusdi.core.container import _container

def manual_example():
    user_service = _container.resolve(UserService)
    return user_service.create_user("manual_user")
```

## Mixed Parameters

Functions can have both injected and regular parameters:

```python
@inject
def complex_operation(
    db: DatabaseService,     # Injected
    email: EmailService,     # Injected
    user_id: int,           # Regular parameter
    send_notification: bool = True  # Regular parameter with default
):
    data = db.get_data()
    if send_notification:
        email.send_email(f"Operation for user {user_id}")
    return data

# Call with regular parameters only
result = complex_operation(user_id=456, send_notification=False)
```

## Semantic Decorators

Use semantic aliases for better code readability:

```python
from nexusdi import service, controller

@service
class UserService:  # Same as @transient
    def __init__(self, database: DatabaseService):
        self.database = database

@controller
class UserController:  # Same as @transient
    def __init__(self, user_service: UserService):
        self.user_service = user_service
```

## Error Handling

Handle injection failures gracefully:

```python
from nexusdi.exceptions import DependencyResolutionException

@inject
def safe_operation(unknown_service: UnknownService):
    return unknown_service.do_something()

try:
    result = safe_operation()
except DependencyResolutionException as e:
    print(f"Failed to inject: {e.dependency_name}")
```

## Best Practices

1. Always use type hints for reliable resolution
2. Keep constructor parameters focused on dependencies
3. Use semantic decorators (@service, @controller) for clarity
4. Handle injection failures appropriately
5. Avoid complex logic in constructors
