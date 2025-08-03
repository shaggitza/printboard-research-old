"""
Switch registry and interface for V2 API

Provides a clean plugin architecture for switch types.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import importlib
from solid import *
from solid.utils import *


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
    def get_3d_model(self, **kwargs) -> Any:
        """Get 3D model geometry for the switch."""
        pass
    
    @abstractmethod
    def get_spacing_x(self) -> float:
        """Get horizontal spacing between switches."""
        pass
    
    @abstractmethod
    def get_spacing_y(self) -> float:
        """Get vertical spacing between switches.""" 
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
    
    def get_3d_model(self, **kwargs) -> Any:
        """Create switch body 3D model."""
        # Create a simplified but representative switch body
        # This is a basic box-like switch body for Gamdias LP
        switch_body_x = 14.5
        switch_body_y = 14.5
        switch_body_height = 2.0
        switch_total_height = 8.0
        
        # Main switch housing
        main_body = cube([switch_body_x, switch_body_y, switch_body_height], center=True)
        
        # Switch stem area (where the key cap sits)
        stem_size = 12.0
        stem_height = 6.0
        stem_body = up(switch_body_height/2 + stem_height/2)(
            cube([stem_size, stem_size, stem_height], center=True)
        )
        
        # Create pin holes (simplified)
        pin_hole_size = 1.0
        pin1_hole = translate([-4.7, -5.0, 0])(
            cylinder(d=pin_hole_size, h=switch_total_height, center=True)
        )
        pin2_hole = translate([5.0, 8.0, 0])(
            cylinder(d=pin_hole_size, h=switch_total_height, center=True)
        )
        
        # Combine all parts
        switch_complete = main_body + stem_body - pin1_hole - pin2_hole
        
        return switch_complete
    
    def get_spacing_x(self) -> float:
        """Get horizontal spacing between switches."""
        return 18.5  # Standard key unit spacing
    
    def get_spacing_y(self) -> float:
        """Get vertical spacing between switches."""
        return 18.5  # Standard key unit spacing


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