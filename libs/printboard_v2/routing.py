"""
Route planning for V2 API

Handles electrical routing between switches and controllers.
Separated from layout planning for cleaner architecture.
"""

import math
import random
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

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
class SwitchPin:
    """Represents a switch pin in routing context."""
    switch_position: KeyPosition
    pin_name: str  # "row" or "column"
    world_position: Tuple[float, float, float]  # Absolute position in world coordinates
    connection_type: str  # "matrix"


@dataclass
class Route:
    """An electrical route between components."""
    name: str
    points: List[RoutePoint]
    route_type: str  # "wire", "controller"
    connected_pins: List[SwitchPin]
    wire_radius: float = 0.85  # Half of 1.7mm diameter steel wire


@dataclass
class RoutePlan:
    """Complete routing plan for a keyboard."""
    routes: List[Route]
    controller_connections: Dict[str, List[Route]]
    coverage_stats: Dict[str, Any]  # Statistics about routing coverage


class RoutePlanner:
    """Plans electrical routing for keyboards using distance-based algorithm."""
    
    def __init__(self, controller: ControllerInterface, switch: SwitchInterface):
        self.controller = controller
        self.switch = switch
        self.wire_radius = 0.85  # Half of 1.7mm diameter steel wire
        self.collision_margin = 1.0  # Additional margin to avoid collisions
    
    def plan_routes(self, layout_plan: LayoutPlan) -> RoutePlan:
        """Plan complete routing for a keyboard layout using enhanced distance-based algorithm."""
        
        # Extract switch pins from layout plan
        switch_pins = self._extract_switch_pins(layout_plan)
        
        # Separate pins by connection type (row vs column)
        row_pins = [pin for pin in switch_pins if pin.pin_name == "row"]
        column_pins = [pin for pin in switch_pins if pin.pin_name == "column"]
        
        # Plan routes using distance-based algorithm
        row_routes = self._plan_distance_based_routes(row_pins, "row")
        column_routes = self._plan_distance_based_routes(column_pins, "column")
        
        all_routes = row_routes + column_routes
        
        # Check for and resolve collisions
        all_routes = self._resolve_collisions(all_routes)
        
        # Plan controller connections
        controller_connections = self._plan_controller_connections(all_routes)
        
        # Calculate coverage statistics
        coverage_stats = self._calculate_coverage(switch_pins, all_routes)
        
        return RoutePlan(
            routes=all_routes,
            controller_connections=controller_connections,
            coverage_stats=coverage_stats
        )
    
    def _extract_switch_pins(self, layout_plan: LayoutPlan) -> List[SwitchPin]:
        """Extract switch pin positions from layout plan."""
        switch_pins = []
        
        for key_position in layout_plan.keys:
            # Get pin specifications from switch
            for pin_spec in self.switch.specs.pins:
                if pin_spec.connection_type == "matrix":
                    # Calculate world position of pin
                    pin_x_local, pin_y_local, pin_z_local = pin_spec.position
                    
                    # Apply switch rotation if any
                    if key_position.angle != 0:
                        cos_angle = math.cos(math.radians(key_position.angle))
                        sin_angle = math.sin(math.radians(key_position.angle))
                        
                        # Rotate pin position around switch center
                        rotated_x = pin_x_local * cos_angle - pin_y_local * sin_angle
                        rotated_y = pin_x_local * sin_angle + pin_y_local * cos_angle
                        pin_x_local, pin_y_local = rotated_x, rotated_y
                    
                    # Transform to world coordinates (use centered switch position like modeling engine)
                    # The modeling engine centers switches by adding switch_size/2, so we need to do the same
                    switch_center_x = key_position.x + self.switch.get_spacing_x() / 2
                    switch_center_y = key_position.y + self.switch.get_spacing_y() / 2
                    
                    world_x = switch_center_x + pin_x_local
                    world_y = switch_center_y + pin_y_local
                    world_z = key_position.z + pin_z_local
                    
                    switch_pin = SwitchPin(
                        switch_position=key_position,
                        pin_name=pin_spec.name,
                        world_position=(world_x, world_y, world_z),
                        connection_type=pin_spec.connection_type
                    )
                    switch_pins.append(switch_pin)
        
        return switch_pins
    
    def _plan_distance_based_routes(self, pins: List[SwitchPin], route_type: str) -> List[Route]:
        """Plan routes using distance-based algorithm that connects closest pins."""
        if not pins:
            return []
        
        routes = []
        unconnected_pins = pins.copy()
        
        # Try multiple runs to find the best routing
        best_routes = None
        best_score = float('inf')
        
        for run in range(10):  # Reduced from 100 for performance
            current_routes = self._single_distance_routing_run(unconnected_pins.copy(), route_type)
            score = self._score_routing(current_routes, pins)
            
            if score < best_score:
                best_score = score
                best_routes = current_routes
        
        return best_routes if best_routes else []
    
    def _single_distance_routing_run(self, available_pins: List[SwitchPin], route_type: str) -> List[Route]:
        """Single run of distance-based routing algorithm."""
        routes = []
        connected_pins = set()
        
        while available_pins:
            # Start with a random unconnected pin
            start_pin = random.choice(available_pins)
            available_pins.remove(start_pin)
            connected_pins.add(id(start_pin))
            
            # Build a route starting from this pin
            route_pins = [start_pin]
            route_points = [RoutePoint(*start_pin.world_position)]
            
            # Find closest pins to connect
            current_pin = start_pin
            while True:
                closest_pin = self._find_closest_connectable_pin(
                    current_pin, available_pins, route_type
                )
                
                if closest_pin is None:
                    break
                
                # Add pin to route
                route_pins.append(closest_pin)
                route_points.append(RoutePoint(*closest_pin.world_position))
                
                # Remove from available and mark as connected
                available_pins.remove(closest_pin)
                connected_pins.add(id(closest_pin))
                current_pin = closest_pin
            
            # Create route if we have more than one pin
            if len(route_pins) > 1:
                # Add connection point to edge for controller routing
                edge_point = self._get_edge_connection_point(route_points, route_type)
                route_points.append(edge_point)
                
                route = Route(
                    name=f"{route_type}_route_{len(routes)}",
                    points=route_points,
                    route_type="wire",
                    connected_pins=route_pins,
                    wire_radius=self.wire_radius
                )
                routes.append(route)
        
        return routes
    
    def _find_closest_connectable_pin(self, current_pin: SwitchPin, 
                                     available_pins: List[SwitchPin], 
                                     route_type: str) -> Optional[SwitchPin]:
        """Find the closest pin that can be connected based on routing rules."""
        if not available_pins:
            return None
        
        current_x, current_y, current_z = current_pin.world_position
        
        # Calculate distances to all available pins
        distances = []
        for pin in available_pins:
            pin_x, pin_y, pin_z = pin.world_position
            
            # Check if this pin is connectable based on routing type
            if route_type == "row":
                # For row routing, prefer pins in the same row
                if current_pin.switch_position.row == pin.switch_position.row:
                    priority_bonus = 0
                else:
                    priority_bonus = 100  # Penalty for different rows
            elif route_type == "column":
                # For column routing, prefer pins in the same column
                if current_pin.switch_position.col == pin.switch_position.col:
                    priority_bonus = 0
                else:
                    priority_bonus = 100  # Penalty for different columns
            else:
                priority_bonus = 0
            
            # Calculate Euclidean distance
            distance = math.sqrt(
                (pin_x - current_x) ** 2 + 
                (pin_y - current_y) ** 2 + 
                (pin_z - current_z) ** 2
            ) + priority_bonus
            
            distances.append((distance, pin))
        
        # Sort by distance and pick the closest
        distances.sort(key=lambda x: x[0])
        
        # Check if the closest pin is within reasonable distance
        closest_distance, closest_pin = distances[0]
        max_reasonable_distance = self.switch.get_spacing_x() * 2  # Max 2 switch widths
        
        if closest_distance > max_reasonable_distance:
            return None
        
        return closest_pin
    
    def _get_edge_connection_point(self, route_points: List[RoutePoint], route_type: str) -> RoutePoint:
        """Get connection point at the edge for controller routing."""
        if not route_points:
            return RoutePoint(0, 0, 0)
        
        # Get the last point in the route
        last_point = route_points[-1]
        
        # For row routes, connect to left edge (x=0)
        # For column routes, connect to top edge (y=0)
        if route_type == "row":
            return RoutePoint(0, last_point.y, last_point.z)
        else:  # column
            return RoutePoint(last_point.x, 0, last_point.z)
    
    def _score_routing(self, routes: List[Route], all_pins: List[SwitchPin]) -> float:
        """Score a routing solution (lower is better)."""
        if not routes:
            return float('inf')
        
        # Count connected pins
        connected_pins = set()
        for route in routes:
            for pin in route.connected_pins:
                connected_pins.add(id(pin))
        
        # Penalty for unconnected pins
        unconnected_penalty = (len(all_pins) - len(connected_pins)) * 1000
        
        # Penalty for total wire length
        total_length = 0
        for route in routes:
            for i in range(len(route.points) - 1):
                p1, p2 = route.points[i], route.points[i + 1]
                length = math.sqrt(
                    (p2.x - p1.x) ** 2 + 
                    (p2.y - p1.y) ** 2 + 
                    (p2.z - p1.z) ** 2
                )
                total_length += length
        
        # Penalty for number of routes (prefer fewer routes)
        route_count_penalty = len(routes) * 10
        
        return unconnected_penalty + total_length + route_count_penalty
    
    def _resolve_collisions(self, routes: List[Route]) -> List[Route]:
        """Resolve collisions between wire routes."""
        # For now, implement basic collision detection
        # In a more sophisticated implementation, we could adjust route paths
        
        # Check for wire intersections and adjust z-levels to avoid collisions
        for i, route1 in enumerate(routes):
            for j, route2 in enumerate(routes[i + 1:], i + 1):
                if self._routes_intersect(route1, route2):
                    # Offset one route in Z direction to avoid collision
                    for point in route2.points:
                        point.z += (route1.wire_radius + route2.wire_radius + self.collision_margin)
        
        return routes
    
    def _routes_intersect(self, route1: Route, route2: Route) -> bool:
        """Check if two routes intersect in 2D plane."""
        # Check if any line segments from route1 intersect with any from route2
        for i in range(len(route1.points) - 1):
            for j in range(len(route2.points) - 1):
                p1_start, p1_end = route1.points[i], route1.points[i + 1]
                p2_start, p2_end = route2.points[j], route2.points[j + 1]
                
                # Check if the line segments intersect using bounding box check first
                if self._segments_intersect(p1_start, p1_end, p2_start, p2_end):
                    return True
        return False
    
    def _segments_intersect(self, p1_start: RoutePoint, p1_end: RoutePoint, 
                           p2_start: RoutePoint, p2_end: RoutePoint) -> bool:
        """Check if two line segments intersect in 2D."""
        # Simple bounding box check first
        min_x1, max_x1 = min(p1_start.x, p1_end.x), max(p1_start.x, p1_end.x)
        min_y1, max_y1 = min(p1_start.y, p1_end.y), max(p1_start.y, p1_end.y)
        min_x2, max_x2 = min(p2_start.x, p2_end.x), max(p2_start.x, p2_end.x)
        min_y2, max_y2 = min(p2_start.y, p2_end.y), max(p2_start.y, p2_end.y)
        
        # Expand by wire radius
        margin = self.wire_radius + self.collision_margin
        
        if (max_x1 + margin < min_x2 - margin or max_x2 + margin < min_x1 - margin or
            max_y1 + margin < min_y2 - margin or max_y2 + margin < min_y1 - margin):
            return False
        
        # If bounding boxes overlap, check for actual intersection
        # For simplicity, we'll use distance between line segments
        return self._line_segment_distance(p1_start, p1_end, p2_start, p2_end) < margin
    
    def _line_segment_distance(self, p1_start: RoutePoint, p1_end: RoutePoint,
                              p2_start: RoutePoint, p2_end: RoutePoint) -> float:
        """Calculate minimum distance between two line segments."""
        # Simplified implementation - check distance between midpoints
        mid1_x, mid1_y = (p1_start.x + p1_end.x) / 2, (p1_start.y + p1_end.y) / 2
        mid2_x, mid2_y = (p2_start.x + p2_end.x) / 2, (p2_start.y + p2_end.y) / 2
        
        return math.sqrt((mid2_x - mid1_x) ** 2 + (mid2_y - mid1_y) ** 2)
    
    def _calculate_coverage(self, all_pins: List[SwitchPin], routes: List[Route]) -> Dict[str, Any]:
        """Calculate routing coverage statistics."""
        connected_pins = set()
        for route in routes:
            for pin in route.connected_pins:
                connected_pins.add(id(pin))
        
        row_pins = [pin for pin in all_pins if pin.pin_name == "row"]
        column_pins = [pin for pin in all_pins if pin.pin_name == "column"]
        
        connected_row_pins = len([pin for pin in row_pins if id(pin) in connected_pins])
        connected_column_pins = len([pin for pin in column_pins if id(pin) in connected_pins])
        
        return {
            "total_pins": len(all_pins),
            "connected_pins": len(connected_pins),
            "coverage_percentage": (len(connected_pins) / len(all_pins) * 100) if all_pins else 0,
            "row_pins_connected": connected_row_pins,
            "column_pins_connected": connected_column_pins,
            "total_routes": len(routes)
        }
    
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