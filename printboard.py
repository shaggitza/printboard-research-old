"""
Printboard Research - Simple keyboard PCB layout and 3D model generator

Core components:
- KeyboardGenerator: Main class for generating keyboards
- SwitchLibrary: Defines different switch types and dimensions  
- ControllerLibrary: Defines microcontroller types and pin layouts
- LayoutValidator: Validates keyboard layout configurations
- OutputManager: Handles file generation and export
"""

import json
import math
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class KeyPosition:
    """Represents a single key position with coordinates and properties"""
    row: int
    col: int
    x: float
    y: float
    width: float = 1.0  # Key width in units (1.0 = standard key)
    height: float = 1.0
    rotation: float = 0.0  # Rotation in degrees


@dataclass
class SwitchSpec:
    """Specification for a switch type"""
    name: str
    body_width: float
    body_height: float  
    body_depth: float
    pin_spacing: float
    pin_count: int


@dataclass
class ControllerSpec:
    """Specification for a controller/microcontroller"""
    name: str
    width: float
    height: float
    pin_rows: Dict[str, List[str]]  # "left": [pin1, pin2, ...], "right": [...]
    usable_pins: List[str]


class SwitchLibrary:
    """Library of available switch types"""
    
    SWITCHES = {
        "mx_style": SwitchSpec(
            name="mx_style",
            body_width=14.0,
            body_height=14.0,
            body_depth=5.0,
            pin_spacing=5.08,
            pin_count=2
        ),
        "low_profile": SwitchSpec(
            name="low_profile", 
            body_width=12.5,
            body_height=12.5,
            body_depth=3.5,
            pin_spacing=5.08,
            pin_count=2
        )
    }
    
    @classmethod
    def get_switch(cls, switch_type: str) -> SwitchSpec:
        if switch_type not in cls.SWITCHES:
            raise ValueError(f"Unknown switch type: {switch_type}")
        return cls.SWITCHES[switch_type]
    
    @classmethod 
    def list_switches(cls) -> List[str]:
        return list(cls.SWITCHES.keys())


class ControllerLibrary:
    """Library of available controllers"""
    
    CONTROLLERS = {
        "arduino_pro_micro": ControllerSpec(
            name="arduino_pro_micro",
            width=33.0,
            height=18.0,
            pin_rows={
                "left": ["TX0", "RX1", "GND", "GND", "2", "3", "4", "5", "6", "7", "8", "9"],
                "right": ["RAW", "GND", "RST", "VCC", "A3", "A2", "A1", "A0", "15", "14", "16", "10"]
            },
            usable_pins=["2", "3", "4", "5", "6", "7", "8", "9", "A3", "A2", "A1", "A0", "15", "14", "16", "10"]
        ),
        "tiny_s2": ControllerSpec(
            name="tiny_s2",
            width=25.0,
            height=20.0,
            pin_rows={
                "left": ["35", "37", "36", "14", "9", "8", "38", "33", "RST", "GND", "43", "44"],
                "right": ["BAT", "GND", "5V", "3V3", "4", "5", "6", "7", "17", "18", "0"]
            },
            usable_pins=["35", "37", "36", "14", "9", "8", "38", "33", "43", "44", "4", "5", "6", "7", "17", "18", "0"]
        )
    }
    
    @classmethod
    def get_controller(cls, controller_type: str) -> ControllerSpec:
        if controller_type not in cls.CONTROLLERS:
            raise ValueError(f"Unknown controller type: {controller_type}")
        return cls.CONTROLLERS[controller_type]
    
    @classmethod
    def list_controllers(cls) -> List[str]:
        return list(cls.CONTROLLERS.keys())


class LayoutValidator:
    """Validates keyboard layout configurations"""
    
    @staticmethod
    def validate_layout(config: Dict[str, Any]) -> List[str]:
        """Validate layout config and return list of errors"""
        errors = []
        
        # Required fields
        required_fields = ["name", "keys", "switch_type", "controller"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return errors
        
        # Validate switch type
        try:
            SwitchLibrary.get_switch(config["switch_type"])
        except ValueError as e:
            errors.append(str(e))
        
        # Validate controller
        try:
            ControllerLibrary.get_controller(config["controller"])
        except ValueError as e:
            errors.append(str(e))
        
        # Validate keys structure
        keys = config["keys"]
        if not isinstance(keys, list) or len(keys) == 0:
            errors.append("Keys must be a non-empty list of rows")
        else:
            row_lengths = [len(row) for row in keys]
            if not all(isinstance(row, list) for row in keys):
                errors.append("Each row in keys must be a list")
            elif len(set(row_lengths)) > 1:
                errors.append("All rows must have the same number of keys")
        
        return errors


@dataclass
class KeyboardResult:
    """Result of keyboard generation"""
    layout: Dict[str, Any]
    key_positions: List[KeyPosition]
    scad_content: str
    config_content: str
    
    def save_scad(self, filepath: str):
        """Save OpenSCAD content to file"""
        with open(filepath, 'w') as f:
            f.write(self.scad_content)
    
    def save_config(self, filepath: str):
        """Save configuration as JSON"""
        with open(filepath, 'w') as f:
            f.write(self.config_content)


class KeyboardGenerator:
    """Main class for generating keyboard layouts and 3D models"""
    
    def __init__(self):
        self.key_spacing = 19.05  # Standard key spacing in mm
    
    def generate(self, layout_config: Dict[str, Any]) -> KeyboardResult:
        """Generate keyboard from layout configuration"""
        
        # Validate configuration
        errors = LayoutValidator.validate_layout(layout_config)
        if errors:
            raise ValueError(f"Invalid layout configuration: {', '.join(errors)}")
        
        # Generate key positions
        key_positions = self._calculate_key_positions(layout_config["keys"])
        
        # Generate OpenSCAD content
        scad_content = self._generate_scad(layout_config, key_positions)
        
        # Generate configuration JSON
        config_content = self._generate_config_json(layout_config, key_positions)
        
        return KeyboardResult(
            layout=layout_config,
            key_positions=key_positions,
            scad_content=scad_content,
            config_content=config_content
        )
    
    def _calculate_key_positions(self, keys_matrix: List[List[str]]) -> List[KeyPosition]:
        """Calculate physical positions for all keys"""
        positions = []
        
        for row_idx, row in enumerate(keys_matrix):
            for col_idx, key_type in enumerate(row):
                if key_type and key_type != "empty":
                    # Calculate position (centered at origin)
                    rows = len(keys_matrix)
                    cols = len(row)
                    
                    x = (col_idx - (cols - 1) / 2) * self.key_spacing
                    y = (row_idx - (rows - 1) / 2) * self.key_spacing
                    
                    positions.append(KeyPosition(
                        row=row_idx,
                        col=col_idx,
                        x=x,
                        y=y
                    ))
        
        return positions
    
    def _generate_scad(self, layout: Dict[str, Any], positions: List[KeyPosition]) -> str:
        """Generate OpenSCAD content for the keyboard"""
        switch_spec = SwitchLibrary.get_switch(layout["switch_type"])
        
        scad_lines = [
            "// Generated keyboard layout",
            f"// Name: {layout['name']}",
            f"// Switch: {layout['switch_type']}",
            f"// Controller: {layout['controller']}",
            "",
            "$fn = 50;",
            "",
            "// Switch cutout module",
            "module switch_cutout() {",
            f"    cube([{switch_spec.body_width}, {switch_spec.body_height}, {switch_spec.body_depth}], center=true);",
            "}",
            "",
            "// Main keyboard body",
            "module keyboard() {",
            "    union() {"
        ]
        
        # Add each switch position
        for pos in positions:
            scad_lines.extend([
                f"        translate([{pos.x}, {pos.y}, 0])",
                f"            rotate([0, 0, {pos.rotation}])",
                "                switch_cutout();"
            ])
        
        scad_lines.extend([
            "    }",
            "}",
            "",
            "keyboard();"
        ])
        
        return "\n".join(scad_lines)
    
    def _generate_config_json(self, layout: Dict[str, Any], positions: List[KeyPosition]) -> str:
        """Generate configuration JSON"""
        config_data = {
            "layout": layout,
            "generated_positions": [
                {
                    "row": pos.row,
                    "col": pos.col,
                    "x": pos.x,
                    "y": pos.y,
                    "width": pos.width,
                    "height": pos.height,
                    "rotation": pos.rotation
                }
                for pos in positions
            ],
            "switch_spec": SwitchLibrary.get_switch(layout["switch_type"]).__dict__,
            "controller_spec": ControllerLibrary.get_controller(layout["controller"]).__dict__
        }
        
        return json.dumps(config_data, indent=2)


# Example usage
if __name__ == "__main__":
    # Simple 3x3 test layout
    layout = {
        "name": "test_3x3", 
        "keys": [
            ["key", "key", "key"],
            ["key", "key", "key"],
            ["key", "key", "key"]
        ],
        "switch_type": "mx_style",
        "controller": "arduino_pro_micro"
    }
    
    generator = KeyboardGenerator()
    result = generator.generate(layout)
    
    print(f"Generated keyboard '{layout['name']}' with {len(result.key_positions)} keys")
    print("Available switches:", SwitchLibrary.list_switches())
    print("Available controllers:", ControllerLibrary.list_controllers())