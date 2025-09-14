"""
Custom exception classes for NexusDI framework.
"""

from typing import Type, List, Optional


class NexusDIException(Exception):
    """
    Base exception for all NexusDI related errors.

    Args:
        message (str): The error message
        dependency_type (Type, optional): The dependency type that caused the error
    """

    def __init__(self, message: str, dependency_type: Optional[Type] = None):
        self.dependency_type = dependency_type
        super().__init__(message)


class DependencyResolutionException(NexusDIException):
    """
    Exception raised when a dependency cannot be resolved.

    Args:
        dependency_name (str): Name of the dependency that failed to resolve
        dependency_type (Type, optional): The dependency type that failed
        missing_dependencies (List[str], optional): List of missing dependencies
    """

    def __init__(
        self,
        dependency_name: str,
        dependency_type: Optional[Type] = None,
        missing_dependencies: Optional[List[str]] = None
    ):
        self.dependency_name = dependency_name
        self.missing_dependencies = missing_dependencies or []

        message = f"Could not resolve dependency: {dependency_name}"
        if self.missing_dependencies:
            message += f". Missing dependencies: {', '.join(self.missing_dependencies)}"

        super().__init__(message, dependency_type)


class CircularDependencyException(NexusDIException):
    """
    Exception raised when a circular dependency is detected.

    Args:
        dependency_chain (List[str]): The chain of dependencies forming the cycle
        dependency_type (Type, optional): The dependency type that caused the cycle
    """

    def __init__(self, dependency_chain: List[str], dependency_type: Optional[Type] = None):
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(dependency_chain)
        message = f"Circular dependency detected: {chain_str}"
        super().__init__(message, dependency_type)


class LifecycleException(NexusDIException):
    """
    Exception raised when there's an issue with dependency lifecycle management.

    Args:
        message (str): The lifecycle error message
        dependency_type (Type, optional): The dependency type with lifecycle issues
        lifecycle (str, optional): The lifecycle type that caused the issue
    """

    def __init__(
        self,
        message: str,
        dependency_type: Optional[Type] = None,
        lifecycle: Optional[str] = None
    ):
        self.lifecycle = lifecycle
        if lifecycle:
            message = f"Lifecycle error ({lifecycle}): {message}"
        super().__init__(message, dependency_type)
