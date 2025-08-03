"""
Controller registry and interface for V2 API

Provides a clean plugin architecture for controller types.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class ControllerPin:
    """Represents a controller pin."""
    number: int
    name: str
    usable: bool = True
    position: Tuple[float, float] = (0.0, 0.0)  # x, y relative to controller


@dataclass
class ControllerSpecs:
    """Physical specifications for a controller."""
    name: str
    footprint_size: Tuple[float, float]  # x, y dimensions
    pin_pitch: float
    pins: Dict[str, List[ControllerPin]]  # "left", "right" sides
    
    @property
    def usable_pins(self) -> List[int]:
        """Get list of usable pin numbers."""
        usable = []
        for side_pins in self.pins.values():
            for pin in side_pins:
                if pin.usable:
                    usable.append(pin.number)
        return usable


class ControllerInterface(ABC):
    """Abstract interface for controller types."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Controller type name."""
        pass
    
    @property
    @abstractmethod
    def specs(self) -> ControllerSpecs:
        """Physical specifications."""
        pass
    
    @abstractmethod
    def create_footprint(self, **kwargs) -> Any:
        """Create 3D footprint geometry for the controller."""
        pass
    
    @abstractmethod
    def get_pin_mapping(self) -> Dict[int, str]:
        """Get pin number to name mapping."""
        pass


class TinyS2Controller(ControllerInterface):
    """TinyS2 controller implementation."""
    
    @property
    def name(self) -> str:
        return "tinys2"
    
    @property  
    def specs(self) -> ControllerSpecs:
        left_pins = [
            ControllerPin(35, "D24", True, (0, 0)),
            ControllerPin(37, "D25", True, (0, 2.54)),
            ControllerPin(36, "D23", True, (0, 5.08)),
            ControllerPin(14, "D16", True, (0, 7.62)),
            ControllerPin(9, "D11", True, (0, 10.16)),
            ControllerPin(8, "D10", True, (0, 12.70)),
            ControllerPin(38, "D21", True, (0, 15.24)),
            ControllerPin(33, "D20", True, (0, 17.78)),
            ControllerPin(-1, "RST", False, (0, 20.32)),
            ControllerPin(-2, "GND", False, (0, 22.86)),
            ControllerPin(43, "D1", True, (0, 25.40)),
            ControllerPin(44, "D0", True, (0, 27.94))
        ]
        
        right_pins = [
            ControllerPin(-3, "BAT", False, (16, 0)),
            ControllerPin(-4, "GND", False, (16, 2.54)),
            ControllerPin(-5, "5V", False, (16, 5.08)),
            ControllerPin(-6, "3V3", False, (16, 7.62)),
            ControllerPin(4, "D6", True, (16, 10.16)),
            ControllerPin(5, "D19", True, (16, 12.70)),
            ControllerPin(6, "D18", True, (16, 15.24)),
            ControllerPin(7, "D9", True, (16, 17.78)),
            ControllerPin(17, "D14", True, (16, 20.32)),
            ControllerPin(18, "D15", True, (16, 22.86)),
            ControllerPin(0, "D4", True, (16, 25.40))
        ]
        
        return ControllerSpecs(
            name="TinyS2",
            footprint_size=(16.0, 27.94),
            pin_pitch=2.54,
            pins={"left": left_pins, "right": right_pins}
        )
    
    def create_footprint(self, **kwargs) -> Any:
        """Create controller footprint using legacy implementation."""
        from ..controllers import tinys2 as legacy_controller
        return legacy_controller.controller_footprint
    
    def get_pin_mapping(self) -> Dict[int, str]:
        """Get pin number to name mapping."""
        mapping = {}
        for side_pins in self.specs.pins.values():
            for pin in side_pins:
                if pin.usable:
                    mapping[pin.number] = pin.name
        return mapping


class ControllerRegistry:
    """Registry for managing controller types."""
    
    def __init__(self):
        self._controllers: Dict[str, ControllerInterface] = {}
        self._register_default_controllers()
    
    def _register_default_controllers(self):
        """Register default controller types."""
        self.register(TinyS2Controller())
    
    def register(self, controller: ControllerInterface):
        """Register a new controller type."""
        self._controllers[controller.name] = controller
    
    def get(self, name: str) -> ControllerInterface:
        """Get a controller by name."""
        if name not in self._controllers:
            raise ValueError(f"Unknown controller type: {name}")
        return self._controllers[name]
    
    def list_controllers(self) -> List[str]:
        """List available controller types."""
        return list(self._controllers.keys())
    
    def is_registered(self, name: str) -> bool:
        """Check if a controller type is registered."""
        return name in self._controllers


# Global registry instance
controller_registry = ControllerRegistry()