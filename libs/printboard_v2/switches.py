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
        """Get 3D mounting cavity geometry for the switch.
        
        Returns the negative space (hole/cavity) where the switch will be mounted,
        not the solid switch body itself.
        """
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
        """Create switch mounting cavity (negative space for switch installation)."""
        # Create the cavity/hole where the switch will be mounted
        # This is slightly larger than the actual switch for clearance
        
        # Main switch cavity - slightly larger than switch body for clearance
        cavity_clearance = 0.2  # 0.2mm clearance on each side
        switch_cavity_x = 14.5 + (2 * cavity_clearance)
        switch_cavity_y = 14.5 + (2 * cavity_clearance) 
        switch_cavity_depth = 2.2  # Slightly deeper than switch body
        
        # Main mounting cavity
        main_cavity = cube([switch_cavity_x, switch_cavity_y, switch_cavity_depth], center=True)
        
        # Stem cavity (where the key cap mechanism goes)
        stem_clearance = 0.1
        stem_cavity_size = 12.0 + (2 * stem_clearance)
        stem_cavity_depth = 6.2  # Slightly deeper than stem
        stem_cavity = up(switch_cavity_depth/2 + stem_cavity_depth/2)(
            cube([stem_cavity_size, stem_cavity_size, stem_cavity_depth], center=True)
        )
        
        # Pin cavities (holes for the electrical pins)
        pin_cavity_diameter = 1.2  # Slightly larger than pin for clearance
        pin_cavity_depth = 10.0  # Deep enough for pins
        
        pin1_cavity = translate([-4.7, -5.0, 0])(
            cylinder(d=pin_cavity_diameter, h=pin_cavity_depth, center=True)
        )
        pin2_cavity = translate([5.0, 8.0, 0])(
            cylinder(d=pin_cavity_diameter, h=pin_cavity_depth, center=True)
        )
        
        # Combine all cavities
        complete_cavity = main_cavity + stem_cavity + pin1_cavity + pin2_cavity
        
        return complete_cavity
    
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