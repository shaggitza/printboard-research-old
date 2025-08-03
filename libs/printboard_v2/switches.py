"""
Switch registry and interface for V2 API

Provides a clean plugin architecture for switch types.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import importlib


@dataclass
class SwitchPin:
    """Represents a switch pin configuration."""
    name: str
    position: Tuple[float, float, float]  # x, y, z relative to switch center
    connection_type: str  # "matrix", "diode", etc.


@dataclass
class SwitchSpecs:
    """Physical specifications for a switch type."""
    body_size: Tuple[float, float, float]  # x, y, z dimensions
    key_size: Tuple[float, float] = (18.5, 18.5)  # Standard key unit size
    pins: List[SwitchPin] = None
    
    def __post_init__(self):
        if self.pins is None:
            self.pins = []


class SwitchInterface(ABC):
    """Abstract interface for switch types."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Switch type name."""
        pass
    
    @property
    @abstractmethod
    def specs(self) -> SwitchSpecs:
        """Physical specifications."""
        pass
    
    @abstractmethod
    def create_body(self, **kwargs) -> Any:
        """Create 3D body geometry for the switch."""
        pass
    
    @abstractmethod
    def create_empty(self, width: float = None, **kwargs) -> Any:
        """Create empty switch for variable key sizes."""
        pass


class GamdiasLPSwitch(SwitchInterface):
    """Gamdias Low Profile switch implementation."""
    
    @property
    def name(self) -> str:
        return "gamdias_lp"
    
    @property
    def specs(self) -> SwitchSpecs:
        return SwitchSpecs(
            body_size=(14.5, 14.5, 8.0),
            key_size=(18.5, 18.5),
            pins=[
                SwitchPin(
                    name="column",
                    position=(-4.7, -5.0, 2.6),
                    connection_type="matrix"
                ),
                SwitchPin(
                    name="row", 
                    position=(5.0, 8.0, 3.2),
                    connection_type="matrix"
                )
            ]
        )
    
    def create_body(self, **kwargs) -> Any:
        """Create switch body using legacy implementation."""
        # Import legacy switch for backward compatibility
        from ..switches import gamdias_lp as legacy_switch
        return legacy_switch.switch_body
    
    def create_empty(self, width: float = None, **kwargs) -> Any:
        """Create empty switch for variable key sizes."""
        from ..switches import gamdias_lp as legacy_switch
        from .. import printboard as kb
        
        if width is None:
            width = 18.5
        
        return kb.empty_sw(
            legacy_switch, 
            body=legacy_switch.switch_body, 
            pins=legacy_switch.pins, 
            x=width
        )


class SwitchRegistry:
    """Registry for managing switch types."""
    
    def __init__(self):
        self._switches: Dict[str, SwitchInterface] = {}
        self._register_default_switches()
    
    def _register_default_switches(self):
        """Register default switch types."""
        self.register(GamdiasLPSwitch())
    
    def register(self, switch: SwitchInterface):
        """Register a new switch type."""
        self._switches[switch.name] = switch
    
    def get(self, name: str) -> SwitchInterface:
        """Get a switch by name."""
        if name not in self._switches:
            raise ValueError(f"Unknown switch type: {name}")
        return self._switches[name]
    
    def list_switches(self) -> List[str]:
        """List available switch types."""
        return list(self._switches.keys())
    
    def is_registered(self, name: str) -> bool:
        """Check if a switch type is registered."""
        return name in self._switches


# Global registry instance
switch_registry = SwitchRegistry()