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
        """Plan the positions of switches in the matrix using V1-compatible logic."""
        positions = []
        
        switch_size_x = switch.get_spacing_x()  # 18.5 for gamdias_lp
        switch_size_y = switch.get_spacing_y()  # 18.5 for gamdias_lp
        
        # V1-style position tracking
        last_position_x_offset = 0
        last_position_y_offset = {}
        offset_x, offset_y = matrix_config.offset
        
        for row in range(matrix_config.rows):
            for col in range(matrix_config.cols):
                # V1-style position calculation: accumulate positions + center offset
                move_x = last_position_x_offset + offset_x + switch_size_x / 2
                move_y = last_position_y_offset.get(col, 0) + offset_y + switch_size_y / 2
                
                # Apply staggering using V1 logic (subtract, not add)
                if matrix_config.rows_stagger and row < len(matrix_config.rows_stagger):
                    stagger = matrix_config.rows_stagger[row]
                    move_x -= stagger
                
                if matrix_config.columns_stagger and col < len(matrix_config.columns_stagger):
                    stagger = matrix_config.columns_stagger[col]
                    move_y -= stagger
                
                # Calculate rotation angles like V1
                rotation = matrix_config.rotation_angle
                
                if matrix_config.rows_angle and row < len(matrix_config.rows_angle):
                    rotation += matrix_config.rows_angle[row]
                
                if matrix_config.columns_angle and col < len(matrix_config.columns_angle):
                    rotation += matrix_config.columns_angle[col]
                
                positions.append({
                    'x': move_x,
                    'y': move_y,
                    'rotation': rotation,
                    'row': row,
                    'col': col
                })
                
                # Update position offsets for next element (V1 style)
                last_position_x_offset += switch_size_x
                if matrix_config.padding_keys and col < len(matrix_config.padding_keys):
                    padding = matrix_config.padding_keys[col]
                    last_position_x_offset += padding
                
                # Track column heights
                if col not in last_position_y_offset:
                    last_position_y_offset[col] = 0
                last_position_y_offset[col] += switch_size_y
            
            # Reset for next row
            last_position_x_offset = 0
        
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