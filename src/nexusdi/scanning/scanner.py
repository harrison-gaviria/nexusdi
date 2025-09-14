"""
Component scanning implementation for automatic discovery.
"""

import sys
import importlib
import pkgutil
from typing import Set, Any

from ..exceptions.errors import NexusDIException


class ComponentScanner:
    """
    Scans modules and packages for decorated components.

    Automatically discovers classes and functions decorated with
    NexusDI decorators across the application.
    """

    def __init__(self) -> None:
        self._scanned_modules: Set[str] = set()
        self._decorated_classes: Set[type] = set()
        self._decorated_functions: Set[Any] = set()

    def scan_all_modules(self) -> None:
        """
        Scans all currently loaded modules for decorated components.

        This method searches through all modules in sys.modules
        and identifies NexusDI decorated classes and functions.
        """
        for module_name in list(sys.modules.keys()):
            if module_name not in self._scanned_modules:
                try:
                    module = sys.modules[module_name]
                    if module:
                        self._scan_module(module)
                except Exception:
                    pass

    def scan_package(self, package_name: str) -> None:
        """
        Scans a specific package and its subpackages for components.

        Args:
            package_name (str): The name of the package to scan
        """
        try:
            package = importlib.import_module(package_name)
            self._scan_module(package)

            if hasattr(package, '__path__'):
                for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
                    try:
                        submodule = importlib.import_module(modname)
                        self._scan_module(submodule)
                        if ispkg:
                            self.scan_package(modname)
                    except Exception:
                        continue
        except Exception:
            pass

    def get_decorated_components(self) -> dict[str, Any]:
        """
        Returns all discovered decorated components.

        Returns:
            dict[str, Any]: Dictionary containing discovered classes and functions
        """
        return {
            'classes': self._decorated_classes,
            'functions': self._decorated_functions
        }


    def _scan_module(self, module: Any) -> None:
        """
        Scans a single module for decorated components.

        Args:
            module (Any): The module to scan
        """
        if not hasattr(module, '__name__'):
            return

        module_name = module.__name__
        if module_name in self._scanned_modules:
            return

        self._scanned_modules.add(module_name)

        try:
            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    continue

                try:
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        hasattr(attr, '_nexusdi_original_init')):
                        self._decorated_classes.add(attr)
                    elif (callable(attr) and
                        hasattr(attr, '__wrapped__') and
                        hasattr(attr, '__name__')):
                        self._decorated_functions.add(attr)

                except Exception:
                    continue
        except Exception:
            pass


def initialize(scan_packages: list[Any] = None) -> None:
    """
    Initializes the dependency injection system.

    Scans for decorated components and sets up the container.
    Should be called once at application startup.

    Args:
        scan_packages (list[Any], optional): List of package names to scan.
        If None, scans all loaded modules.

    Raises:
        NexusDIException: If initialization fails
    """
    try:
        scanner = ComponentScanner()
        scanner.scan_all_modules()
        if scan_packages:
            for package_name in scan_packages:
                if not isinstance(package_name, str):
                    raise NexusDIException(f"Package name must be string, got {type(package_name).__name__}")
                scanner.scan_package(package_name)

        scanner.get_decorated_components()
    except Exception as e:
        raise NexusDIException("Failed to initialize NexusDI system") from e
