# Scanning API Reference

The scanning module provides automatic discovery and registration of decorated components across your application.

## ComponentScanner

::: nexusdi.scanning.scanner.ComponentScanner
    options:
      show_source: false
      heading_level: 3

The main class responsible for discovering decorated components in modules and packages.

### Constructor

```python
ComponentScanner()
```

Creates a new component scanner instance. Each scanner maintains its own state of scanned modules and discovered components.

**Attributes:**
- `_scanned_modules`: Set of already scanned module names
- `_decorated_classes`: Set of discovered decorated classes
- `_decorated_functions`: Set of discovered decorated functions

### Methods

#### scan_all_modules()

Scans all currently loaded modules for decorated components.

**Signature:**
```python
def scan_all_modules(self) -> None
```

**Description:**
This method searches through all modules in `sys.modules` and identifies NexusDI decorated classes and functions. It's useful for discovering components that have already been imported.

**Example:**
```python
from nexusdi.scanning.scanner import ComponentScanner

scanner = ComponentScanner()
scanner.scan_all_modules()

components = scanner.get_decorated_components()
print(f"Found {len(components['classes'])} decorated classes")
print(f"Found {len(components['functions'])} decorated functions")
```

**Behavior:**
- Scans all modules in `sys.modules`
- Skips modules that have already been scanned
- Silently ignores modules that can't be scanned
- Only processes modules that are actually loaded

#### scan_package(package_name)

Scans a specific package and its subpackages for components.

**Signature:**
```python
def scan_package(self, package_name: str) -> None
```

**Parameters:**
- `package_name` (str): The name of the package to scan

**Description:**
Recursively scans a package and all its subpackages, importing modules as needed to discover decorated components.

**Example:**
```python
scanner = ComponentScanner()

# Scan a specific package
scanner.scan_package("myapp.services")

# Scan multiple packages
scanner.scan_package("myapp.repositories")
scanner.scan_package("myapp.controllers")
```

**Behavior:**
- Imports the package if not already loaded
- Recursively scans all subpackages
- Handles import errors gracefully
- Only scans Python packages (with `__path__` attribute)

#### get_decorated_components()

Returns all discovered decorated components.

**Signature:**
```python
def get_decorated_components(self) -> dict[str, Any]
```

**Returns:**
- `dict[str, Any]`: Dictionary containing discovered classes and functions

**Return Structure:**
```python
{
    'classes': set,      # Set of decorated classes
    'functions': set     # Set of decorated functions
}
```

**Example:**
```python
components = scanner.get_decorated_components()

print("Decorated Classes:")
for cls in components['classes']:
    lifecycle = getattr(cls, '_nexusdi_lifecycle', 'unknown')
    print(f"  - {cls.__name__} ({lifecycle.value if hasattr(lifecycle, 'value') else lifecycle})")

print("Decorated Functions:")
for func in components['functions']:
    print(f"  - {func.__name__}")
```

### Private Methods

#### _scan_module(module)

Scans a single module for decorated components.

**Signature:**
```python
def _scan_module(self, module: Any) -> None
```

**Parameters:**
- `module` (Any): The module to scan

**Detection Logic:**
- **Classes**: Looks for `_nexusdi_original_init` attribute (added by lifecycle decorators)
- **Functions**: Looks for `__wrapped__` and `__name__` attributes (added by `@inject` decorator)

## Global Functions

### initialize(scan_packages=None)

Initializes the dependency injection system with automatic component scanning.

**Signature:**
```python
def initialize(scan_packages: list[Any] = None) -> None
```

**Parameters:**
- `scan_packages` (list[Any], optional): List of package names to scan. If None, scans all loaded modules.

**Raises:**
