"""
3D modeling module for V2 API

Handles 3D geometry generation without dependencies on legacy code.
"""

from typing import List, Dict, Any
from solid2 import *
import math
from math import cos, radians, sin, pi
import numpy as np
from euclid3 import Point3

from .config import KeyboardConfig, MatrixConfig
from .switches import SwitchInterface


def circle_points(radius: float, segments: int = 50) -> List[List[float]]:
    """Generate points for a circle cross-section."""
    points = []
    for i in range(segments):
        angle = 2 * pi * i / segments
        x = radius * cos(angle)
        y = radius * sin(angle)
        points.append([x, y])
    return points


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
        """Generate 3D routing tubes for connections using the new V2 routing algorithm."""
        from .routing import RoutePlanner
        
        # Create route planner and plan routes
        planner = RoutePlanner(controller, switch)
        route_plan = planner.plan_routes(layout_plan)
        
        # Generate 3D tubes from routes
        tubes_union = union()()
        
        for route in route_plan.routes:
            if len(route.points) < 2:
                continue
                
            # Create tube geometry
            tube_geometry = self._create_tube_from_points(route.points, route.wire_radius)
            tubes_union += tube_geometry
        
        return tubes_union
    
    def _create_tube_from_points(self, points: List, wire_radius: float) -> Any:
        """Create a 3D tube from a series of points."""
        if len(points) < 2:
            return union()()
        
        # Create circular cross-section for the wire
        wire_circle = circle_points(wire_radius)
        
        # Convert RoutePoint objects to Point3 objects for SolidPython
        path_points = []
        for point in points:
            # Handle both RoutePoint objects and tuples
            if hasattr(point, 'x'):
                path_points.append(Point3(point.x, point.y, point.z))
            else:
                path_points.append(Point3(*point))
        
        # Create smooth path if we have more than 2 points
        if len(path_points) > 2:
            path_points = self._smooth_path(path_points)
        
        # Extrude the circle along the path
        try:
            return extrude_along_path(wire_circle, path_points)
        except:
            # Fallback to simple cylinder connections if extrude_along_path fails
            tube_union = union()()
            for i in range(len(path_points) - 1):
                p1, p2 = path_points[i], path_points[i + 1]
                # Calculate distance and orientation between points
                dx, dy, dz = p2.x - p1.x, p2.y - p1.y, p2.z - p1.z
                length = math.sqrt(dx*dx + dy*dy + dz*dz)
                
                if length > 0:
                    # Create cylinder segment
                    cyl = cylinder(r=wire_radius, h=length, center=True)
                    
                    # Rotate and translate to connect the points
                    if dz != 0 or dx != 0 or dy != 0:
                        # Calculate rotation angles
                        pitch = math.atan2(math.sqrt(dx*dx + dy*dy), dz)
                        yaw = math.atan2(dy, dx) if dx != 0 or dy != 0 else 0
                        
                        cyl = rotate([math.degrees(pitch), 0, math.degrees(yaw)])(cyl)
                    
                    # Translate to midpoint
                    mid_x, mid_y, mid_z = (p1.x + p2.x)/2, (p1.y + p2.y)/2, (p1.z + p2.z)/2
                    cyl = translate([mid_x, mid_y, mid_z])(cyl)
                    
                    tube_union += cyl
            
            return tube_union
    
    def _smooth_path(self, path_points: List, num_interpolated: int = 10) -> List:
        """Create a smooth path through the given points using simple linear interpolation."""
        if len(path_points) <= 2:
            return path_points
        
        smooth_points = []
        
        for i in range(len(path_points) - 1):
            p1, p2 = path_points[i], path_points[i + 1]
            
            # Add the current point
            smooth_points.append(p1)
            
            # Add interpolated points
            for j in range(1, num_interpolated):
                t = j / num_interpolated
                interp_x = p1.x + t * (p2.x - p1.x)
                interp_y = p1.y + t * (p2.y - p1.y)
                interp_z = p1.z + t * (p2.z - p1.z)
                smooth_points.append(Point3(interp_x, interp_y, interp_z))
        
        # Add the final point
        smooth_points.append(path_points[-1])
        
        return smooth_points
    
    def create_keyboard_parts(self, config: KeyboardConfig, layout_plan=None) -> List[Dict[str, Any]]:
        """Create keyboard parts as 3D cavity geometry for switch mounting."""
        from .switches import switch_registry
        from .controllers import controller_registry
        from .layout import LayoutPlanner
        
        parts = []
        
        # Get the switch type
        switch = switch_registry.get(config.switch_type)
        if not switch:
            raise ValueError(f"Unknown switch type: {config.switch_type}")
        
        # Get the controller type
        controller = controller_registry.get(config.controller_type)
        if not controller:
            raise ValueError(f"Unknown controller type: {config.controller_type}")
        
        # Generate layout plan if not provided
        if layout_plan is None:
            planner = LayoutPlanner(switch)
            layout_plan = planner.plan_layout(config)
        
        # Generate matrix parts (switch mounting cavities)
        for matrix_name, matrix_config in config.matrices.items():
            matrix_geometry = self.generate_matrix_3d(matrix_config, switch, matrix_name)
            
            # Add routing tubes using the new algorithm
            routing_geometry = self.generate_routing_tubes(layout_plan, switch, controller)
            
            # Combine matrix cavities and routing
            combined_geometry = matrix_geometry + routing_geometry
            
            parts.append({
                "name": f"{matrix_name}_switch_holes",
                "shape": combined_geometry
            })
        
        return parts