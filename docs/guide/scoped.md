# Scoped Dependencies

Scoped dependencies live for the duration of a specific scope, typically a web request or processing context.

## Basic Scoped Usage

```python
from nexusdi import scoped, scope_cleanup
import time

@scoped
class RequestContext:
    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.user_id = None

    def set_user(self, user_id: int):
        self.user_id = user_id

@scoped
class AuditLogger:
    def __init__(self, context: RequestContext):
        self.context = context
        self.events = []

    def log_event(self, event: str):
        self.events.append({
            "event": event,
            "request_id": self.context.request_id,
            "user_id": self.context.user_id,
            "timestamp": time.time()
        })
```

## Scope Lifecycle

Within the same scope, dependencies are reused:

```python
def handle_request(user_id: int):
    try:
        # First resolution creates the scope
        context = _container.resolve(RequestContext)
        context.set_user(user_id)

        # Second resolution returns same instance
        audit = _container.resolve(AuditLogger)
        audit.log_event("request_started")

        # Third resolution also returns same context
        another_context = _container.resolve(RequestContext)
        assert context is another_context  # Same instance

        # Process request...
        result = process_user_data(user_id)
        audit.log_event("request_completed")

        return result

    finally:
        # Clean up scoped instances
        scope_cleanup()
```

## Web Application Integration

### Flask Integration

```python
from flask import Flask, g
from nexusdi import scoped, scope_cleanup, _container

app = Flask(__name__)

@scoped
class RequestData:
    def __init__(self):
        self.request_start = time.time()
        self.user_id = None

@app.before_request
def before_request():
    # Scoped dependencies are automatically created per request
    request_data = _container.resolve(RequestData)
    g.request_data = request_data

@app.teardown_request
def teardown_request(exception):
    # Clean up scoped dependencies
    scope_cleanup()

@app.route('/users/<int:user_id>')
def get_user(user_id):
    request_data = _container.resolve(RequestData)
    request_data.user_id = user_id
    # Process user...
    return f"User {user_id}"
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

@asynccontextmanager
async def request_scope():
    try:
        yield
    finally:
        scope_cleanup()

app = FastAPI()

@app.middleware("http")
async def scope_middleware(request, call_next):
    async with request_scope():
        response = await call_next(request)
        return response

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    request_data = _container.resolve(RequestData)
    request_data.user_id = user_id
    return {"user_id": user_id}
```

## Thread-Based Scopes

Each thread gets its own scope:

```python
import threading
from nexusdi import scoped, _container

@scoped
class ThreadData:
    def __init__(self):
        self.thread_id = threading.get_ident()
        self.data = {}

def worker(worker_id: int):
    # Each thread gets its own ThreadData instance
    thread_data = _container.resolve(ThreadData)
    thread_data.data['worker_id'] = worker_id

    # Same instance within the thread
    same_data = _container.resolve(ThreadData)
    assert thread_data is same_data

    print(f"Worker {worker_id} on thread {thread_data.thread_id}")

# Start multiple threads
threads = []
for i in range(3):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

## Automatic Scope Management

NexusDI automatically creates scopes when needed:

```python
@scoped
class SessionData:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        print(f"Created session: {self.session_id}")

# First access creates new scope
session1 = _container.resolve(SessionData)

# Second access returns same instance
session2 = _container.resolve(SessionData)
assert session1 is session2

# After cleanup, new scope is created
scope_cleanup()
session3 = _container.resolve(SessionData)
assert session1 is not session3
```

## Error Handling in Scoped Dependencies

```python
from nexusdi.exceptions import LifecycleException

@scoped
class DatabaseTransaction:
    def __init__(self):
        self.transaction = self._begin_transaction()

    def _begin_transaction(self):
        # Could fail during initialization
        return "transaction_handle"

    def commit(self):
        print("Transaction committed")

    def rollback(self):
        print("Transaction rolled back")

def process_with_transaction():
    try:
        tx = _container.resolve(DatabaseTransaction)
        # Do work...
        tx.commit()
    except Exception as e:
        tx = _container.resolve(DatabaseTransaction)
        tx.rollback()
        raise
    finally:
        scope_cleanup()
```

## Scoped vs Singleton vs Transient

```python
from nexusdi import singleton, transient, scoped

@singleton
class AppConfig:  # Shared across entire app
    def __init__(self):
        self.database_url = "postgresql://..."

@scoped
class UserSession:  # One per request/scope
    def __init__(self, config: AppConfig):
        self.config = config
        self.logged_in_user = None

@transient
class EmailSender:  # New instance each time
    def __init__(self, session: UserSession):
        self.session = session
```

## Best Practices

1. Always call `scope_cleanup()` when scope ends
2. Use scoped dependencies for request-specific data
3. Avoid heavy initialization in scoped constructors
4. Consider thread safety for multi-threaded applications
5. Clean up resources properly in scope cleanup

## Common Patterns

### Request Processing Pipeline

```python
@scoped
class RequestProcessor:
    def __init__(self):
        self.steps = []

    def add_step(self, step: str):
        self.steps.append(step)

    def get_summary(self):
        return f"Processed {len(self.steps)} steps"

def process_pipeline():
    processor = _container.resolve(RequestProcessor)
    processor.add_step("validation")
    processor.add_step("processing")
    processor.add_step("response")
    return processor.get_summary()
```

### Context Managers

```python
from contextlib import contextmanager

@contextmanager
def request_context():
    try:
        yield _container.resolve(RequestContext)
    finally:
        scope_cleanup()

# Usage
with request_context() as ctx:
    ctx.set_user(123)
    # Use scoped dependencies...
# Automatic cleanup when exiting context
```
