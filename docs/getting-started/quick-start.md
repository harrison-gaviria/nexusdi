# Quick Start Guide

This guide will get you up and running with NexusDI in just a few minutes.

## Basic Setup

First, import the necessary decorators and functions:

```python
from nexusdi import singleton, transient, scoped, inject, initialize
```

## Step 1: Define Your Dependencies

Use decorators to mark your classes with their desired lifecycle:

```python
@singleton
class ConfigService:
    def __init__(self):
        self.database_url = "postgresql://localhost:5432/myapp"
        self.api_key = "secret-api-key"

@transient
class EmailService:
    def __init__(self, config: ConfigService):
        self.config = config
    
    def send_email(self, to: str, subject: str, body: str):
        print(f"Sending email to {to}: {subject}")
        # Email sending logic here

@transient
class UserService:
    def __init__(self, config: ConfigService, email_service: EmailService):
        self.config = config
        self.email_service = email_service
    
    def create_user(self, username: str, email: str):
        # User creation logic
        user = {"id": 1, "username": username, "email": email}
        
        # Send welcome email
        self.email_service.send_email(
            to=email,
            subject="Welcome!",
            body=f"Welcome to our app, {username}!"
        )
        
        return user
```

## Step 2: Use Dependency Injection

You can inject dependencies into functions using the `@inject` decorator:

```python
@inject
def create_new_user(user_service: UserService, username: str, email: str):
    return user_service.create_user(username, email)
```

Or resolve dependencies manually:

```python
from nexusdi.core.container import _container

def manual_resolution():
    user_service = _container.resolve(UserService)
    return user_service.create_user("john_doe", "john@example.com")
```

## Step 3: Initialize the System

Before using your dependencies, initialize NexusDI:

```python
# Initialize the dependency injection system
initialize()

# Now you can use your functions
user = create_new_user(username="alice", email="alice@example.com")
print(f"Created user: {user}")
```

## Complete Example

Here's a complete working example:

```python
from nexusdi import singleton, transient, inject, initialize

# Define services
@singleton
class DatabaseService:
    def __init__(self):
        print("DatabaseService initialized (singleton)")
        self.connection = "database_connection_pool"
    
    def query(self, sql: str):
        return f"Result from {self.connection}: {sql}"

@transient
class UserRepository:
    def __init__(self, db_service: DatabaseService):
        print("UserRepository initialized (transient)")
        self.db = db_service
    
    def find_by_id(self, user_id: int):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

@transient
class UserService:
    def __init__(self, user_repo: UserRepository):
        print("UserService initialized (transient)")
        self.user_repo = user_repo
    
    def get_user_info(self, user_id: int):
        return self.user_repo.find_by_id(user_id)

# Use dependency injection
@inject
def get_user_details(user_service: UserService, user_id: int):
    return user_service.get_user_info(user_id)

# Initialize and run
if __name__ == "__main__":
    initialize()
    
    # Call the function multiple times
    print("First call:")
    result1 = get_user_details(user_id=123)
    print(f"Result: {result1}")
    
    print("\nSecond call:")
    result2 = get_user_details(user_id=456)
    print(f"Result: {result2}")
```

## Key Points

- **Singleton**: `DatabaseService` is created once and reused
- **Transient**: `UserRepository` and `UserService` are created new each time
- **Automatic Resolution**: Dependencies are automatically injected based on type hints
- **Initialize**: Always call `initialize()` before using dependency injection

## What's Next?

Now that you've seen the basics, explore more advanced features:

- [Basic Concepts](concepts.md) - Understand the core concepts
- [Lifecycle Management](../guide/lifecycle.md) - Learn about different lifecycles
- [Scoped Dependencies](../guide/scoped.md) - Handle request-scoped dependencies
- [Component Scanning](../guide/scanning.md) - Automatically discover components
