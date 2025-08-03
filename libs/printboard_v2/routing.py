"""
Route planning for V2 API

Handles electrical routing between switches and controllers.
Separated from layout planning for cleaner architecture.
Includes improved tube routing with collision detection.
"""

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import math
from shapely.geometry import LineString
import random

from .layout import LayoutPlan, KeyPosition
from .controllers import ControllerInterface
from .switches import SwitchInterface


@dataclass
class RoutePoint:
    """A point in a routing path."""
    x: float
    y: float
    z: float


@dataclass
class Route:
    """An electrical route between components."""
    name: str
    points: List[RoutePoint]
    route_type: str  # "row", "column", "controller"
    start_key: KeyPosition = None
    end_key: KeyPosition = None
    connected_keys: List[KeyPosition] = None
    
    def __post_init__(self):
        if self.connected_keys is None:
            self.connected_keys = []


@dataclass
class TubeRoute:
    """A physical tube route for electrical connection."""
    route: Route
    tube_radius: float = 0.85  # Default tube radius (1.7mm diameter)
    
    def get_line_segments(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """Get 2D line segments for collision detection."""
        segments = []
        for i in range(len(self.route.points) - 1):
            p1 = self.route.points[i]
            p2 = self.route.points[i + 1]
            segments.append(((p1.x, p1.y), (p2.x, p2.y)))
        return segments


@dataclass
class RoutePlan:
    """Complete routing plan for a keyboard."""
    routes: List[Route]
    tube_routes: List[TubeRoute]
    controller_connections: Dict[str, List[Route]]


class TubeRoutePlanner:
    """Plans tube routing for electrical connections with collision avoidance."""
    
    def __init__(self, switch: SwitchInterface, controller: ControllerInterface):
        self.switch = switch
        self.controller = controller
        self.collision_distance = 2.0  # Minimum distance between tubes
        
    def plan_tube_routes(self, layout_plan: LayoutPlan) -> List[TubeRoute]:
        """Plan tube routes starting from pin1 for each switch on the same plane."""
        switch_points = self._extract_switch_points(layout_plan)
        
        # Plan routes using closest-neighbor algorithm
        tube_routes = []
        
        # Group switches by row (for row routing)
        row_groups = self._group_keys_by_row(layout_plan.keys)
        
        for row_num, row_keys in row_groups.items():
            if len(row_keys) > 1:
                # Sort by column position
                row_keys.sort(key=lambda k: k.x)
                
                # Create route for this row starting from pin1
                route_points = []
                connected_keys = []
                
                for key in row_keys:
                    # Get pin1 position for this key (row connection)
                    pin_pos = self._get_pin_position(key, 'row')
                    route_points.append(RoutePoint(pin_pos[0], pin_pos[1], pin_pos[2]))
                    connected_keys.append(key)
                
                # Extend route to edge for controller connection
                if route_points:
                    last_point = route_points[-1]
                    # Extend to left edge (x=0)
                    edge_point = RoutePoint(0, last_point.y, last_point.z)
                    route_points.append(edge_point)
                
                route = Route(
                    name=f"row_{row_num}",
                    points=route_points,
                    route_type="row",
                    start_key=row_keys[0],
                    end_key=row_keys[-1],
                    connected_keys=connected_keys
                )
                
                tube_route = TubeRoute(route=route)
                tube_routes.append(tube_route)
        
        # Apply collision avoidance
        tube_routes = self._avoid_collisions(tube_routes)
        
        return tube_routes
    
    def _extract_switch_points(self, layout_plan: LayoutPlan) -> Dict[str, List[Dict]]:
        """Extract switch pin positions for routing."""
        points = {'row': [], 'column': []}
        
        for key in layout_plan.keys:
            # Get pin positions for this key
            row_pin_pos = self._get_pin_position(key, 'row')
            col_pin_pos = self._get_pin_position(key, 'column')
            
            points['row'].append({
                'key': key,
                'position': row_pin_pos,
                'row': key.row,
                'col': key.col
            })
            
            points['column'].append({
                'key': key,
                'position': col_pin_pos,
                'row': key.row,
                'col': key.col
            })
        
        return points
    
    def _get_pin_position(self, key: KeyPosition, pin_type: str) -> Tuple[float, float, float]:
        """Get the 3D position of a specific pin for a key."""
        # Get pin specifications from switch
        pin_info = None
        for pin in self.switch.specs.pins:
            if pin.name == pin_type:
                pin_info = pin
                break
        
        if not pin_info:
            # Default pin position
            pin_offset = (0, 0, 5.3)
        else:
            pin_offset = pin_info.position
        
        # Apply key rotation if any
        if key.angle != 0:
            # Rotate pin position around key center
            cos_angle = math.cos(math.radians(key.angle))
            sin_angle = math.sin(math.radians(key.angle))
            
            rotated_x = pin_offset[0] * cos_angle - pin_offset[1] * sin_angle
            rotated_y = pin_offset[0] * sin_angle + pin_offset[1] * cos_angle
            pin_offset = (rotated_x, rotated_y, pin_offset[2])
        
        # Add to key position
        pin_x = key.x + pin_offset[0]
        pin_y = key.y + pin_offset[1]
        pin_z = key.z + pin_offset[2]
        
        return (pin_x, pin_y, pin_z)
    
    def _group_keys_by_row(self, keys: List[KeyPosition]) -> Dict[int, List[KeyPosition]]:
        """Group keys by row number."""
        row_groups = {}
        for key in keys:
            if key.row not in row_groups:
                row_groups[key.row] = []
            row_groups[key.row].append(key)
        return row_groups
    
    def _avoid_collisions(self, tube_routes: List[TubeRoute]) -> List[TubeRoute]:
        """Apply collision avoidance to tube routes."""
        # Simple collision avoidance: offset routes vertically if they get too close
        for i, route1 in enumerate(tube_routes):
            for j, route2 in enumerate(tube_routes[i+1:], i+1):
                if self._routes_collide(route1, route2):
                    # Offset the second route slightly
                    self._offset_route(route2, 0, 2.0, 0)  # Offset by 2mm in Y
        
        return tube_routes
    
    def _routes_collide(self, route1: TubeRoute, route2: TubeRoute) -> bool:
        """Check if two tube routes collide."""
        segments1 = route1.get_line_segments()
        segments2 = route2.get_line_segments()
        
        for seg1 in segments1:
            for seg2 in segments2:
                line1 = LineString(seg1)
                line2 = LineString(seg2)
                
                if line1.distance(line2) < self.collision_distance:
                    return True
        
        return False
    
    def _offset_route(self, tube_route: TubeRoute, dx: float, dy: float, dz: float):
        """Offset all points in a route by the given amounts."""
        for point in tube_route.route.points:
            point.x += dx
            point.y += dy
            point.z += dz


class RoutePlanner:
    """Plans electrical routing for keyboards."""
    
    def __init__(self, controller: ControllerInterface):
        self.controller = controller
    
    def plan_routes(self, layout_plan: LayoutPlan, switch: SwitchInterface) -> RoutePlan:
        """Plan complete routing for a keyboard layout."""
        
        # Create tube routing planner
        tube_planner = TubeRoutePlanner(switch, self.controller)
        
        # Plan tube routes with collision avoidance
        tube_routes = tube_planner.plan_tube_routes(layout_plan)
        
        # Extract basic routes from tube routes
        routes = [tube_route.route for tube_route in tube_routes]
        
        # Plan controller connections
        controller_connections = self._plan_controller_connections(routes)
        
        return RoutePlan(
            routes=routes,
            tube_routes=tube_routes,
            controller_connections=controller_connections
        )
    
    
    def _plan_controller_connections(self, routes: List[Route]) -> Dict[str, List[Route]]:
        """Plan connections from routes to controller pins."""
        
        # Simple assignment for now - could be optimized
        connections = {}
        
        usable_pins = self.controller.specs.usable_pins
        pin_index = 0
        
        for route in routes:
            if pin_index < len(usable_pins):
                pin_num = usable_pins[pin_index]
                if pin_num not in connections:
                    connections[pin_num] = []
                connections[pin_num].append(route)
                pin_index += 1
        
        return connections