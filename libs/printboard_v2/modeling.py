"""
3D modeling module for V2 API

Handles 3D geometry generation without dependencies on legacy code.
"""

from typing import List, Dict, Any
from solid import *
from solid.utils import *
from solid.objects import *
import math
from math import cos, radians, sin, pi
import numpy as np

from .config import KeyboardConfig, MatrixConfig
from .switches import SwitchInterface


class ModelingEngine:
    """Handles 3D geometry generation for keyboards."""
    
    def __init__(self):
        self.shape_rad = 15
        self.segments = 50
    
    def generate_matrix_3d(self, matrix_config: MatrixConfig, switch: SwitchInterface, matrix_name: str = "main") -> Any:
        """Generate 3D cavity geometry for switch mounting holes in a keyboard matrix."""
        # Plan the switch positions
        switch_positions = self._plan_switch_positions(matrix_config, switch)
        
        # Create the union of all switch mounting cavities
        matrix_union = union()()
        
        for position in switch_positions:
            switch_cavity = switch.get_3d_model()  # Now returns mounting cavity
            
            # Apply transformations: translation, then rotation
            transformed_cavity = translate([position['x'], position['y'], 0])(
                rotate([0, 0, position['rotation']])(
                    switch_cavity
                )
            )
            
            matrix_union += transformed_cavity
        
        return matrix_union
    
    def _plan_switch_positions(self, matrix_config: MatrixConfig, switch: SwitchInterface) -> List[Dict[str, Any]]:
        """Plan the positions of switches in the matrix."""
        positions = []
        
        switch_spacing_x = switch.get_spacing_x()
        switch_spacing_y = switch.get_spacing_y()
        
        for row in range(matrix_config.rows):
            for col in range(matrix_config.cols):
                # Calculate base position
                x = col * switch_spacing_x
                y = row * switch_spacing_y
                
                # Apply row stagger if specified
                if matrix_config.rows_stagger and row < len(matrix_config.rows_stagger):
                    x += matrix_config.rows_stagger[row]
                
                # Apply column stagger if specified  
                if matrix_config.columns_stagger and col < len(matrix_config.columns_stagger):
                    y += matrix_config.columns_stagger[col]
                
                # Apply matrix offset
                x += matrix_config.offset[0]
                y += matrix_config.offset[1]
                
                # Calculate rotation (start with matrix rotation)
                rotation = matrix_config.rotation_angle
                
                # Apply row angles if specified
                if matrix_config.rows_angle and row < len(matrix_config.rows_angle):
                    rotation += matrix_config.rows_angle[row]
                
                # Apply column angles if specified
                if matrix_config.columns_angle and col < len(matrix_config.columns_angle):
                    rotation += matrix_config.columns_angle[col]
                
                positions.append({
                    'x': x,
                    'y': y,
                    'rotation': rotation,
                    'row': row,
                    'col': col
                })
        
        return positions
    
    def generate_routing_tubes(self, matrix_config: MatrixConfig, switch: SwitchInterface) -> Any:
        """Generate 3D routing tubes for connections."""
        # For now, return empty geometry - routing is complex and can be added later
        # This allows V2 to work without the complex routing logic from V1
        return union()()
    
    def create_keyboard_parts(self, config: KeyboardConfig) -> List[Dict[str, Any]]:
        """Create keyboard parts as 3D cavity geometry for switch mounting."""
        from .switches import switch_registry
        
        parts = []
        
        # Get the switch type
        switch = switch_registry.get(config.switch_type)
        if not switch:
            raise ValueError(f"Unknown switch type: {config.switch_type}")
        
        # Generate matrix parts (switch mounting cavities)
        for matrix_name, matrix_config in config.matrices.items():
            matrix_geometry = self.generate_matrix_3d(matrix_config, switch, matrix_name)
            
            # Add routing tubes
            routing_geometry = self.generate_routing_tubes(matrix_config, switch)
            
            # Combine matrix cavities and routing
            combined_geometry = matrix_geometry + routing_geometry
            
            parts.append({
                "name": f"{matrix_name}_switch_holes",
                "shape": combined_geometry
            })
        
        return parts