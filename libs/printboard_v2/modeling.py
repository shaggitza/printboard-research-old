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
    
    def generate_routing_tubes(self, layout_plan, switch: SwitchInterface, controller) -> Any:
        """Generate 3D routing tubes for connections."""
        from .routing import RoutePlanner
        from .layout import LayoutPlan
        from .controllers import ControllerInterface
        from solid import union, translate, cylinder, hull
        
        # Plan the routes
        route_planner = RoutePlanner(controller)
        route_plan = route_planner.plan_routes(layout_plan, switch)
        
        # Generate tube geometry for each route
        tubes_union = union()()
        
        for tube_route in route_plan.tube_routes:
            # Create tube geometry
            tube_geometry = self._create_tube_geometry(tube_route)
            tubes_union += tube_geometry
        
        return tubes_union
    
    def _create_tube_geometry(self, tube_route) -> Any:
        """Create 3D tube geometry for a single route."""
        from solid import cylinder, hull, union, translate
        
        # Create tube segments between consecutive points
        tube_union = union()()
        
        points = tube_route.route.points
        radius = tube_route.tube_radius
        
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            
            # Create tube segment between p1 and p2
            # Use hull of two cylinders to create smooth tube
            cyl1 = translate([p1.x, p1.y, p1.z])(
                cylinder(r=radius, h=0.1)
            )
            cyl2 = translate([p2.x, p2.y, p2.z])(
                cylinder(r=radius, h=0.1)
            )
            
            segment = hull()(cyl1, cyl2)
            tube_union += segment
        
        return tube_union
    
    def create_keyboard_parts(self, config: KeyboardConfig, layout_plan) -> List[Dict[str, Any]]:
        """Create keyboard parts as 3D cavity geometry for switch mounting."""
        from .switches import switch_registry
        from .controllers import controller_registry
        
        parts = []
        
        # Get the switch and controller types
        switch = switch_registry.get(config.switch_type)
        if not switch:
            raise ValueError(f"Unknown switch type: {config.switch_type}")
            
        controller = controller_registry.get(config.controller_type)
        if not controller:
            raise ValueError(f"Unknown controller type: {config.controller_type}")
        
        # Generate matrix parts (switch mounting cavities)
        for matrix_name, matrix_config in config.matrices.items():
            matrix_geometry = self.generate_matrix_3d(matrix_config, switch, matrix_name)
            
            # Add routing tubes using the complete layout plan
            routing_geometry = self.generate_routing_tubes(layout_plan, switch, controller)
            
            # Combine matrix cavities and routing
            combined_geometry = matrix_geometry + routing_geometry
            
            parts.append({
                "name": f"{matrix_name}_switch_holes",
                "shape": combined_geometry
            })
        
        return parts