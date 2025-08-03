"""
Switch registry and interface for V2 API

Provides a clean plugin architecture for switch types.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import importlib
from solid2 import *
from math import cos, sin, pi, tau
import glob

SEGMENTS = 50


def quarter_torus(outer_radius, tube_radius, angle=90):
    """Create a quarter torus shape for diode routing."""
    # Define the path (a quarter circle)
    path = []
    segments = SEGMENTS
    for i in range(segments + 1):
        theta = (angle * pi / 180) * i / segments
        x = outer_radius * cos(theta)
        y = outer_radius * sin(theta)
        path.append([x, y, 0])

    # Define the shape to be extruded (a circle)
    shape = []
    for i in range(segments + 1):
        theta = (2 * pi) * i / segments
        x = tube_radius * cos(theta)
        y = tube_radius * sin(theta)
        shape.append([x, y])

    # Extrude the shape along the path
    return extrude_along_path(shape_pts=shape, path_pts=path)


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
    """Gamdias Low Profile switch implementation with detailed V1-compatible geometry."""
    
    def __init__(self):
        """Initialize switch with V1-compatible configuration."""
        self.conf = {
            "side_leg_height": 1.63,
            "side_leg_width": 3.3,
            "side_leg_distance_cylinders": 1.4,
            "side_leg_width_spacer": 3,
            "mid_leg_height": 4.35,
            "mid_leg_diameter": 4,
            "mid_to_side_horizontal": 4.2,
            "pin_hole_x": 1.7,
            "pin_hole_y": 1.2,
            "pin_cone_d": 1,
            "pin_cone_d1": 3, 
            "pin_cone_h": 3,
            "pin_diode_vertical": -5.2,
            "pin_clean_vertical": -5,
            "pin_to_center_horizontal": -4.7,
            "pin_contact_height": 2.6,
            "switch_body_x": 14.5,
            "switch_body_y": 14.5,
            "switch_body_height": 2,
            "switch_body_wedge_edge": 14,
            "switch_body_wedge_height": 0.7,
            "switch_sizes_x": 18.5,
            "switch_sizes_y": 18.5,
            "switch_sizes_height": 8,
        }
        
        self.pins = [
            {
                "name": "column",
                "dist_to_center": {
                    "x": self.conf['pin_to_center_horizontal'],
                    "y": -self.conf['pin_clean_vertical'],
                    "z": self.conf['pin_contact_height'] + self.conf['switch_body_height'] + self.conf['switch_body_wedge_height']
                },
                "connection": "matrix"
            },
            {
                "name": "row",
                "dist_to_center": {
                    "x": 5,
                    "y": 8,
                    "z": 3 + self.conf['pin_contact_height'] + self.conf['switch_body_height'] + self.conf['switch_body_wedge_height'] + 0.6
                },
                "connection": "matrix"
            }
        ]
    
    @property
    def name(self) -> str:
        return "gamdias_lp"
    
    @property
    def specs(self) -> SwitchSpecs:
        return SwitchSpecs(
            body_size=(self.conf['switch_body_x'], self.conf['switch_body_y'], self.conf['switch_sizes_height']),
            key_size=(self.conf['switch_sizes_x'], self.conf['switch_sizes_y']),
            pins=[
                SwitchPin(
                    name=pin["name"],
                    position=(pin["dist_to_center"]["x"], pin["dist_to_center"]["y"], pin["dist_to_center"]["z"]),
                    connection_type=pin["connection"]
                ) for pin in self.pins
            ]
        )
    
    def _create_leg_side(self) -> Any:
        """Create side leg component."""
        leg_side = cube([self.conf['side_leg_width'], self.conf['side_leg_width_spacer'], self.conf['side_leg_height']], center=True)
        leg_side += forward(-self.conf['side_leg_distance_cylinders'])(
            cylinder(d=self.conf['side_leg_width'], h=self.conf['side_leg_height'], center=True)
        )
        leg_side += forward(self.conf['side_leg_distance_cylinders'])(
            cylinder(d=self.conf['side_leg_width'], h=self.conf['side_leg_height'], center=True)
        )
        return leg_side
    
    def _create_leg_center(self) -> Any:
        """Create center leg component."""
        return cylinder(d=self.conf['mid_leg_diameter'], h=self.conf['mid_leg_height'], center=True)
    
    def _create_switch_footprint(self) -> Any:
        """Create the main switch footprint with legs."""
        leg_side = self._create_leg_side()
        leg_center = self._create_leg_center()
        
        footprint = up(self.conf['side_leg_height']/2)(
            left(-self.conf['mid_to_side_horizontal'])(leg_side)
        )
        footprint += up(self.conf['mid_leg_height']/2)(leg_center)
        footprint += up(self.conf['side_leg_height']/2)(
            left(self.conf['mid_to_side_horizontal'])(leg_side)
        )
        
        return footprint
    
    def _create_pin_hole(self) -> Any:
        """Create pin hole component."""
        pin_hole = up(self.conf['mid_leg_height']/2)(
            cube([self.conf['pin_hole_x'], self.conf['pin_hole_y'], self.conf['mid_leg_height']], center=True)
        )
        pin_hole += cylinder(
            d=self.conf['pin_cone_d'], 
            d1=self.conf['pin_cone_d1'], 
            h=self.conf['pin_cone_h']
        )
        return pin_hole
    
    def _create_switch_pin_holes(self) -> Any:
        """Create switch pin holes."""
        pin_hole = self._create_pin_hole()
        
        switch_pin_holes = back(self.conf['pin_clean_vertical'])(
            right(self.conf['pin_to_center_horizontal'])(
                rotate([0, 0, 90])(pin_hole)
            )
        )
        switch_pin_holes += back(self.conf['pin_diode_vertical'])(pin_hole)
        
        return switch_pin_holes
    
    def _create_switch_body_lock(self) -> Any:
        """Create switch body lock mechanism."""
        switch_body_lock = down(self.conf['switch_body_height']/2)(
            cube([self.conf['switch_body_x'], self.conf['switch_body_y'], self.conf['switch_body_height']], center=True)
        )
        switch_body_lock += down(self.conf['switch_body_height'] + self.conf['switch_body_wedge_height']/2)(
            cube([self.conf['switch_body_wedge_edge'], self.conf['switch_body_wedge_edge'], self.conf['switch_body_wedge_height']], center=True)
        )
        
        return switch_body_lock
    
    def _create_diode_slot(self) -> Any:
        """Create diode slot with complex routing."""
        arc_diode_hole = quarter_torus(self.conf['mid_leg_height']/2, 1.7/2)
        arc_diode_end = cylinder(d=1.7, h=1.5, center=True)
        arc_diode_end = rotate([90, 0, 0])(arc_diode_end)
        arc_diode_end = back(0.7)(arc_diode_end)
        arc_diode_end = right(2.17)(arc_diode_end)
        
        diode_body_hole = cube([8, 4, 4], center=True)
        diode_clearance = cube([16, 2, 4], center=True)
        diode_second_leg_hole = cube([10, 2, 2], center=True)
        diode_second_leg_hole = back(1)(left(5)(down(3)(diode_second_leg_hole)))
        
        diode_slot = arc_diode_hole + arc_diode_end + forward(1.5)(left(4)(diode_body_hole)) + forward(-1)(left(0)(diode_clearance)) + diode_second_leg_hole
        
        diode_slot = rotate([-90, 180, 0])(diode_slot)
        diode_slot = forward(self.conf['pin_diode_vertical'])(diode_slot)
        diode_slot = right(2)(diode_slot)
        diode_slot = down(5)(diode_slot)
        diode_slot = down(3)(diode_slot)
        
        return diode_slot
    
    def get_3d_model(self, **kwargs) -> Any:
        """Get the complete detailed switch body exactly like V1.
        
        Returns the same complex switch body as V1 with all components:
        legs, pins, body lock, and positioning.
        """
        # Create all components
        switch_footprint = self._create_switch_footprint()
        switch_pin_holes = self._create_switch_pin_holes()
        switch_body_lock = self._create_switch_body_lock()
        
        # Combine components and apply V1-compatible transformations
        switch_body = rotate([0, 180, 180])(
            up(self.conf['switch_body_wedge_height'] + self.conf['switch_body_height'])(
                switch_footprint + switch_pin_holes + switch_body_lock
            )
        )
        
        return switch_body
    
    def get_spacing_x(self) -> float:
        """Get horizontal spacing between switches."""
        return self.conf['switch_sizes_x']
    
    def get_spacing_y(self) -> float:
        """Get vertical spacing between switches."""
        return self.conf['switch_sizes_y']


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