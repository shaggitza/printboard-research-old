"""
Route planning for V2 API

Handles electrical routing between switches and controllers.
Separated from layout planning for cleaner architecture.
"""

from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

from .layout import LayoutPlan, KeyPosition
from .controllers import ControllerInterface


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


@dataclass
class RoutePlan:
    """Complete routing plan for a keyboard."""
    routes: List[Route]
    controller_connections: Dict[str, List[Route]]


class RoutePlanner:
    """Plans electrical routing for keyboards."""
    
    def __init__(self, controller: ControllerInterface):
        self.controller = controller
    
    def plan_routes(self, layout_plan: LayoutPlan) -> RoutePlan:
        """Plan complete routing for a keyboard layout."""
        
        # For V2 initial implementation, we'll keep it simple
        # The legacy system handles the complex routing algorithm
        
        # Extract key positions and group by row/column
        rows_routes = self._plan_row_routes(layout_plan)
        column_routes = self._plan_column_routes(layout_plan)
        
        all_routes = rows_routes + column_routes
        
        # Plan controller connections
        controller_connections = self._plan_controller_connections(all_routes)
        
        return RoutePlan(
            routes=all_routes,
            controller_connections=controller_connections
        )
    
    def _plan_row_routes(self, layout_plan: LayoutPlan) -> List[Route]:
        """Plan routes connecting keys in rows."""
        routes = []
        
        # Group keys by row within each matrix
        for matrix_name in layout_plan.matrices.keys():
            matrix_keys = layout_plan.get_keys_for_matrix(matrix_name)
            
            # Group by row
            row_groups = {}
            for key in matrix_keys:
                if key.row not in row_groups:
                    row_groups[key.row] = []
                row_groups[key.row].append(key)
            
            # Create route for each row
            for row_num, row_keys in row_groups.items():
                if len(row_keys) > 1:
                    # Sort by column
                    row_keys.sort(key=lambda k: k.col)
                    
                    # Create route points
                    points = []
                    for key in row_keys:
                        points.append(RoutePoint(key.x, key.y, key.z))
                    
                    route = Route(
                        name=f"{matrix_name}_row_{row_num}",
                        points=points,
                        route_type="row",
                        start_key=row_keys[0],
                        end_key=row_keys[-1]
                    )
                    routes.append(route)
        
        return routes
    
    def _plan_column_routes(self, layout_plan: LayoutPlan) -> List[Route]:
        """Plan routes connecting keys in columns."""
        routes = []
        
        # Group keys by column within each matrix
        for matrix_name in layout_plan.matrices.keys():
            matrix_keys = layout_plan.get_keys_for_matrix(matrix_name)
            
            # Group by column
            column_groups = {}
            for key in matrix_keys:
                if key.col not in column_groups:
                    column_groups[key.col] = []
                column_groups[key.col].append(key)
            
            # Create route for each column
            for col_num, col_keys in column_groups.items():
                if len(col_keys) > 1:
                    # Sort by row
                    col_keys.sort(key=lambda k: k.row)
                    
                    # Create route points
                    points = []
                    for key in col_keys:
                        points.append(RoutePoint(key.x, key.y, key.z))
                    
                    route = Route(
                        name=f"{matrix_name}_col_{col_num}",
                        points=points,
                        route_type="column", 
                        start_key=col_keys[0],
                        end_key=col_keys[-1]
                    )
                    routes.append(route)
        
        return routes
    
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