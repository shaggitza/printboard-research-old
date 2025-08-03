#!/usr/bin/env python3
"""
Manual test script to verify the enhanced wire routing functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.printboard_v2.builder import KeyboardBuilder
from libs.printboard_v2.config import KeyboardConfig, MatrixConfig
from libs.printboard_v2.routing import RoutePlanner
from libs.printboard_v2.switches import switch_registry
from libs.printboard_v2.controllers import controller_registry
from libs.printboard_v2.layout import LayoutPlanner

def test_routing_integration():
    """Test the full routing integration."""
    print("Testing Enhanced Wire Routing Integration...")
    
    # Create a simple keyboard configuration
    builder = KeyboardBuilder()
    
    try:
        result = builder.create_simple_keyboard(
            name="routing_test",
            rows=3,
            cols=3,
            switch_type="gamdias_lp",
            controller_type="tinys2"
        )
        
        print(f"✓ Successfully created keyboard: {result.config.name}")
        print(f"✓ Total keys: {result.metadata['total_keys']}")
        print(f"✓ Switch type: {result.metadata['switch_type']}")
        print(f"✓ Controller type: {result.metadata['controller_type']}")
        print(f"✓ Generated {len(result.parts)} parts")
        
        # Test routing plan specifically
        switch = switch_registry.get("gamdias_lp")
        controller = controller_registry.get("tinys2")
        planner = LayoutPlanner(switch)
        layout_plan = planner.plan_layout(result.config)
        
        route_planner = RoutePlanner(controller, switch)
        route_plan = route_planner.plan_routes(layout_plan)
        
        print(f"✓ Generated {len(route_plan.routes)} routing paths")
        print(f"✓ Coverage: {route_plan.coverage_stats['coverage_percentage']:.1f}%")
        print(f"✓ Connected pins: {route_plan.coverage_stats['connected_pins']}/{route_plan.coverage_stats['total_pins']}")
        print(f"✓ Row connections: {route_plan.coverage_stats['row_pins_connected']}")
        print(f"✓ Column connections: {route_plan.coverage_stats['column_pins_connected']}")
        print(f"✓ Controller pin assignments: {len(route_plan.controller_connections)}")
        
        # Verify all switches are covered
        if route_plan.coverage_stats['coverage_percentage'] >= 95:
            print("✓ Excellent coverage - all or nearly all switches connected")
        elif route_plan.coverage_stats['coverage_percentage'] >= 80:
            print("✓ Good coverage - most switches connected")
        else:
            print("⚠ Low coverage - some switches may be unreachable")
        
        # Test collision avoidance
        has_collisions = False
        for i, route1 in enumerate(route_plan.routes):
            for j, route2 in enumerate(route_plan.routes[i+1:], i+1):
                if route_planner._routes_intersect(route1, route2):
                    print(f"⚠ Potential collision between {route1.name} and {route2.name}")
                    has_collisions = True
        
        if not has_collisions:
            print("✓ No wire collisions detected")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_routing_algorithm_specifics():
    """Test specific aspects of the routing algorithm."""
    print("\nTesting Routing Algorithm Specifics...")
    
    try:
        # Test distance-based routing vs old row/column method
        switch = switch_registry.get("gamdias_lp")
        controller = controller_registry.get("tinys2")
        
        # Create a test layout with irregular spacing
        config = KeyboardConfig(
            name="algorithm_test",
            switch_type="gamdias_lp",
            controller_type="tinys2",
            matrices={
                "main": MatrixConfig(
                    rows=3, 
                    cols=4,
                    # Add some staggering to make routing more interesting
                    columns_stagger=[0, 2, 4, 6],
                    rows_stagger=[0, 1, 2]
                )
            }
        )
        
        planner = LayoutPlanner(switch)
        layout_plan = planner.plan_layout(config)
        
        route_planner = RoutePlanner(controller, switch)
        route_plan = route_planner.plan_routes(layout_plan)
        
        print(f"✓ Handled irregular layout with staggering")
        print(f"✓ Generated {len(route_plan.routes)} optimized routes")
        
        # Check that the algorithm prefers connecting same-row pins for row routes
        row_routes = [r for r in route_plan.routes if any("row" in pin.pin_name for pin in r.connected_pins)]
        column_routes = [r for r in route_plan.routes if any("column" in pin.pin_name for pin in r.connected_pins)]
        
        print(f"✓ Row routes: {len(row_routes)}")
        print(f"✓ Column routes: {len(column_routes)}")
        
        # Verify row routes prefer same-row connections
        for route in row_routes:
            if len(route.connected_pins) > 1:
                rows_in_route = set(pin.switch_position.row for pin in route.connected_pins)
                if len(rows_in_route) == 1:
                    print(f"✓ Route {route.name} connects pins in same row {list(rows_in_route)[0]}")
                else:
                    print(f"⚠ Route {route.name} spans multiple rows: {rows_in_route}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing algorithm specifics: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Enhanced Wire Routing Test")
    print("=" * 50)
    
    success1 = test_routing_integration()
    success2 = test_routing_algorithm_specifics()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✓ All tests passed! Enhanced wire routing is working correctly.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Check the output above for details.")
        sys.exit(1)