# NexusDI

[![PyPI version](https://badge.fury.io/py/nexusdi.svg)](https://badge.fury.io/py/nexusdi)
[![Python versions](https://img.shields.io/pypi/pyversions/nexusdi.svg)](https://pypi.org/project/nexusdi/)
[![PyPI - Status](https://img.shields.io/pypi/status/nexusdi)](https://pypi.org/project/nexusdi/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A lightweight and powerful dependency injection framework for Python**

NexusDI provides elegant dependency injection with support for multiple lifecycles, automatic dependency resolution, component scanning, and circular dependency handling via lazy proxies.

---

## ✨ Key Features

- **🔄 Multiple Lifecycles**: Singleton, transient, and scoped dependencies
- **⚡ Automatic Resolution**: Type-hint based dependency resolution
- **♻️ Circular Dependencies**: Lazy proxies to handle complex graphs
- **🔍 Component Scanning**: Auto-discovery of decorated components
- **🧵 Thread-Safe**: Reliable for concurrent applications
- **💡 Lightweight**: Minimal overhead with maximum flexibility

---

## 🚀 Quick Example

```python
from nexusdi import singleton, transient, inject, initialize

@singleton
class DatabaseService:
    def __init__(self):
        self.connection = "database_connection"

@transient
class UserRepository:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service

    def get_user(self, user_id: int):
        return f"User {user_id} from {self.db.connection}"

@inject
def get_user_data(user_repo: UserRepository, user_id: int = 1):
    return user_repo.get_user(user_id)

# Initialize the DI system
initialize()

# Dependencies are automatically injected
result = get_user_data(user_id=123)
print(result)  # "User 123 from database_connection"
```

## 📦 Installation

Install NexusDI with pip:

```bash
pip install nexusdi
```

Or with poetry:

```bash
poetry add nexusdi
```

## 🎯 Core Concepts

### Lifecycles

* `singleton`: A single instance for the application lifetime
* `transient`: A new instance per request
* `scoped`: Shared within a defined scope

### Injection

* Use `@inject` on functions to resolve dependencies automatically

### Scanning

* Decorate classes to enable **automatic component discovery**

### Circular Dependencies

* NexusDI resolves circular graphs via **lazy proxies**

---

## 🔗 Quick Links

* [Getting Started](https://harrison-gaviria.github.io/nexusdi/getting-started/installation/) – Install and set up NexusDI
* [User Guide](https://harrison-gaviria.github.io/nexusdi/guide/lifecycle/) – Explore lifecycles, injection, and more
* [API Reference](https://harrison-gaviria.github.io/nexusdi/api/core/) – Complete API documentation
* [Examples](https://harrison-gaviria.github.io/nexusdi/examples/basic/) – See practical usage examples

---


## 🤝 Contributing

Contributions are welcome!
Please feel free to open an [issue](https://github.com/harrison-gaviria/nexusdi/issues) or submit a Pull Request.
For major changes, start a discussion first in [GitHub Discussions](https://github.com/harrison-gaviria/nexusdi/discussions).

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](https://github.com/harrison-gaviria/nexusdi/blob/main/LICENSE) file for details.

---

## 👤 Author

**Harrison Alonso Arroyave Gaviria**

* GitHub: [@harrison-gaviria](https://github.com/harrison-gaviria)
* LinkedIn: [Harrison Alonso Arroyave Gaviria](https://www.linkedin.com/in/harrison-alonso-arroyave-gaviria-4ba07b358)
* Email: [harrisonarroyaveg@gmail.com](mailto:harrisonarroyaveg@gmail.com)

```
