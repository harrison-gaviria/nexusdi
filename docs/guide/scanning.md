# Component Scanning

NexusDI can automatically discover decorated components across your application without manual registration.

## Basic Scanning

Initialize NexusDI with automatic component discovery:

```python
from nexusdi import initialize

# Scan all loaded modules
initialize()

# Or scan specific packages
initialize(scan_packages=["myapp.services", "myapp.repositories"])
```

## Manual Scanning

Use the ComponentScanner directly for more control:

```python
from nexusdi.scanning.scanner import ComponentScanner

scanner = ComponentScanner()

# Scan all loaded modules
scanner.scan_all_modules()

# Scan specific packages
scanner.scan_package("myapp.services")
scanner.scan_package("myapp.controllers")

# Get discovered components
components = scanner.get_decorated_components()
print(f"Found {len(components['classes'])} classes")
print(f"Found {len(components['functions'])} functions")
```

## Package Structure

Organize your code for effective scanning:

```
myapp/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   └── email_service.py
├── repositories/
│   ├── __init__.py
│   └── user_repository.py
└── controllers/
    ├── __init__.py
    └── user_controller.py
```

## Decorated Components

The scanner automatically finds:

### Classes with Lifecycle Decorators

```python
# services/user_service.py
from nexusdi import singleton, transient

@singleton
class ConfigService:
    def __init__(self):
        self.config = {}

@transient
class UserService:
    def __init__(self, config: ConfigService):
        self.config = config
```

### Functions with @inject

```python
# controllers/user_controller.py
from nexusdi import inject

@inject
def get_user_handler(user_service: UserService, user_id: int):
    return user_service.get_user(user_id)
```

## Application Startup

Initialize scanning at application startup:

```python
# main.py
from nexusdi import initialize

def main():
    # Initialize dependency injection
    initialize(scan_packages=[
        "myapp.services",
        "myapp.repositories",
        "myapp.controllers"
    ])

    # Start your application
    start_application()

if __name__ == "__main__":
    main()
```

## Web Framework Integration

### Flask Example

```python
from flask import Flask
from nexusdi import initialize, inject

app = Flask(__name__)

@app.before_first_request
def setup_di():
    initialize(scan_packages=["myapp"])

@app.route("/users/<int:user_id>")
@inject
def get_user(user_service: UserService, user_id: int):
    return user_service.get_user(user_id)
```

### FastAPI Example

```python
from fastapi import FastAPI
from nexusdi import initialize, inject

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    initialize(scan_packages=["myapp"])

@app.get("/users/{user_id}")
@inject
async def get_user(user_service: UserService, user_id: int):
    return user_service.get_user(user_id)
```

## Error Handling

Handle scanning errors gracefully:

```python
from nexusdi.exceptions import NexusDIException

try:
    initialize(scan_packages=["myapp"])
except NexusDIException as e:
    print(f"Scanning failed: {e}")
    # Handle error or use fallback
```

## Best Practices

1. Call `initialize()` once at application startup
2. Scan only necessary packages to avoid overhead
3. Use consistent package structure
4. Import modules that contain decorated components
5. Handle initialization errors appropriately

## Performance Notes

- Scanning happens once at startup
- Already loaded modules are scanned faster
- Package scanning imports modules as needed
- Minimal runtime overhead after initialization
