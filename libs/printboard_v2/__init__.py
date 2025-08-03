"""
Printboard V2 - Clean keyboard generation API

This module provides a cleaner, more modular architecture for keyboard generation
while maintaining backward compatibility with the original API.

Key improvements:
- Separated concerns: layout planning, switch construction, routing
- Plugin architecture for switches and controllers  
- Builder pattern for clean keyboard construction
- Immutable configuration objects
- Dependency injection
"""

from .builder import KeyboardBuilder
from .layout import LayoutPlanner
from .switches import SwitchRegistry
from .controllers import ControllerRegistry
from .config import KeyboardConfig, MatrixConfig

__version__ = "2.0.0"

__all__ = [
    "KeyboardBuilder",
    "LayoutPlanner", 
    "SwitchRegistry",
    "ControllerRegistry",
    "KeyboardConfig",
    "MatrixConfig"
]