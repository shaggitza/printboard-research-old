"""
Tests for the enhanced V2 routing system.
"""

import unittest
import math
from typing import Dict
from unittest.mock import Mock

from libs.printboard_v2.routing import RoutePlanner, SwitchPin, Route, RoutePoint
from libs.printboard_v2.layout import LayoutPlan, KeyPosition
from libs.printboard_v2.switches import SwitchPin as SwitchPinSpec, SwitchSpecs, SwitchInterface
from libs.printboard_v2.controllers import ControllerInterface, ControllerSpecs, ControllerPin


class MockSwitch(SwitchInterface):
    """Mock switch for testing."""
    
    @property
    def name(self) -> str:
        return "test_switch"
    
    @property
    def specs(self) -> SwitchSpecs:
        return SwitchSpecs(
            body_size=(10, 10, 5),
            key_size=(18.5, 18.5),
            pins=[
                SwitchPinSpec(name="row", position=(-2.0, 0.0, 2.0), connection_type="matrix"),
                SwitchPinSpec(name="column", position=(2.0, 0.0, 2.0), connection_type="matrix")
            ]
        )
    
    def get_3d_model(self, **kwargs):
        return None
    
    def get_spacing_x(self) -> float:
        return 18.5
    
    def get_spacing_y(self) -> float:
        return 18.5


class MockController(ControllerInterface):
    """Mock controller for testing."""
    
    @property
    def name(self) -> str:
        return "test_controller"
    
    @property
    def specs(self) -> ControllerSpecs:
        return ControllerSpecs(
            name="Test Controller",
            footprint_size=(20, 10),
            pin_pitch=2.54,
            pins={
                "left": [ControllerPin(i, f"D{i}", True, (0, i*2.54)) for i in range(1, 6)],
                "right": [ControllerPin(i, f"D{i}", True, (20, i*2.54)) for i in range(6, 11)]
            }
        )
    
    def create_footprint(self, **kwargs):
        return None
    
    def get_pin_mapping(self) -> Dict[int, str]:
        return {i: f"D{i}" for i in range(1, 11)}


class TestRoutePlanner(unittest.TestCase):
    """Test the enhanced routing planner."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.switch = MockSwitch()
        self.controller = MockController()
        self.planner = RoutePlanner(self.controller, self.switch)
    
    def test_extract_switch_pins(self):
        """Test extracting switch pins from layout plan."""
        # Create a simple 2x2 layout
        keys = [
            KeyPosition(row=0, col=0, x=0, y=0, z=0),
            KeyPosition(row=0, col=1, x=18.5, y=0, z=0),
            KeyPosition(row=1, col=0, x=0, y=18.5, z=0),
            KeyPosition(row=1, col=1, x=18.5, y=18.5, z=0)
        ]
        
        layout_plan = LayoutPlan(
            keys=keys,
            matrices={"main": (37, 37)},
            total_bounds=(0, 0, 37, 37)
        )
        
        pins = self.planner._extract_switch_pins(layout_plan)
        
        # Should have 8 pins total (2 per switch * 4 switches)
        self.assertEqual(len(pins), 8)
        
        # Check that we have both row and column pins
        row_pins = [pin for pin in pins if pin.pin_name == "row"]
        column_pins = [pin for pin in pins if pin.pin_name == "column"]
        
        self.assertEqual(len(row_pins), 4)
        self.assertEqual(len(column_pins), 4)
        
        # Check pin positions are calculated correctly
        first_key_row_pin = next(pin for pin in row_pins if pin.switch_position.row == 0 and pin.switch_position.col == 0)
        self.assertEqual(first_key_row_pin.world_position, (-2.0, 0.0, 2.0))
        
        first_key_column_pin = next(pin for pin in column_pins if pin.switch_position.row == 0 and pin.switch_position.col == 0)
        self.assertEqual(first_key_column_pin.world_position, (2.0, 0.0, 2.0))
    
    def test_distance_based_routing(self):
        """Test distance-based routing algorithm."""
        # Create test pins in a row configuration
        pins = [
            SwitchPin(
                switch_position=KeyPosition(row=0, col=0, x=0, y=0),
                pin_name="row",
                world_position=(0, 0, 2),
                connection_type="matrix"
            ),
            SwitchPin(
                switch_position=KeyPosition(row=0, col=1, x=18.5, y=0),
                pin_name="row", 
                world_position=(18.5, 0, 2),
                connection_type="matrix"
            ),
            SwitchPin(
                switch_position=KeyPosition(row=0, col=2, x=37, y=0),
                pin_name="row",
                world_position=(37, 0, 2),
                connection_type="matrix"
            )
        ]
        
        routes = self.planner._plan_distance_based_routes(pins, "row")
        
        # Should create at least one route
        self.assertGreater(len(routes), 0)
        
        # Check that all pins are connected
        connected_pins = set()
        for route in routes:
            for pin in route.connected_pins:
                connected_pins.add(id(pin))
        
        self.assertEqual(len(connected_pins), len(pins))
    
    def test_collision_detection(self):
        """Test collision detection between routes."""
        # Create two routes that intersect
        route1 = Route(
            name="route1",
            points=[RoutePoint(0, 0, 0), RoutePoint(10, 0, 0)],
            route_type="wire",
            connected_pins=[],
            wire_radius=0.85
        )
        
        route2 = Route(
            name="route2", 
            points=[RoutePoint(5, -5, 0), RoutePoint(5, 5, 0)],
            route_type="wire",
            connected_pins=[],
            wire_radius=0.85
        )
        
        # Test collision detection
        intersects = self.planner._routes_intersect(route1, route2)
        self.assertTrue(intersects)
        
        # Test collision resolution
        routes = [route1, route2]
        resolved_routes = self.planner._resolve_collisions(routes)
        
        # After resolution, route2 should be offset in Z
        self.assertGreater(resolved_routes[1].points[0].z, 0)
    
    def test_coverage_calculation(self):
        """Test routing coverage statistics."""
        # Create test data
        pins = [
            SwitchPin(KeyPosition(0, 0, 0, 0), "row", (0, 0, 0), "matrix"),
            SwitchPin(KeyPosition(0, 1, 18.5, 0), "row", (18.5, 0, 0), "matrix"),
            SwitchPin(KeyPosition(0, 0, 0, 0), "column", (0, 0, 0), "matrix"),
            SwitchPin(KeyPosition(1, 0, 0, 18.5), "column", (0, 18.5, 0), "matrix")
        ]
        
        routes = [
            Route("test_route", [], "wire", pins[:2]),  # Connect first 2 pins
        ]
        
        coverage = self.planner._calculate_coverage(pins, routes)
        
        self.assertEqual(coverage["total_pins"], 4)
        self.assertEqual(coverage["connected_pins"], 2)
        self.assertEqual(coverage["coverage_percentage"], 50.0)
        self.assertEqual(coverage["row_pins_connected"], 2)
        self.assertEqual(coverage["column_pins_connected"], 0)
    
    def test_complete_routing_plan(self):
        """Test complete routing plan generation."""
        # Create a 2x2 layout for comprehensive test
        keys = [
            KeyPosition(row=0, col=0, x=0, y=0, z=0),
            KeyPosition(row=0, col=1, x=18.5, y=0, z=0),
            KeyPosition(row=1, col=0, x=0, y=18.5, z=0),
            KeyPosition(row=1, col=1, x=18.5, y=18.5, z=0)
        ]
        
        layout_plan = LayoutPlan(
            keys=keys,
            matrices={"main": (37, 37)},
            total_bounds=(0, 0, 37, 37)
        )
        
        route_plan = self.planner.plan_routes(layout_plan)
        
        # Check that we got routes
        self.assertGreater(len(route_plan.routes), 0)
        
        # Check coverage statistics
        self.assertIn("total_pins", route_plan.coverage_stats)
        self.assertEqual(route_plan.coverage_stats["total_pins"], 8)
        
        # Check controller connections
        self.assertIsInstance(route_plan.controller_connections, dict)
    
    def test_pin_rotation_handling(self):
        """Test that pin positions are correctly calculated with switch rotation."""
        # Create a key with rotation
        keys = [KeyPosition(row=0, col=0, x=0, y=0, z=0, angle=90)]
        
        layout_plan = LayoutPlan(
            keys=keys,
            matrices={"main": (18.5, 18.5)},
            total_bounds=(0, 0, 18.5, 18.5)
        )
        
        pins = self.planner._extract_switch_pins(layout_plan)
        
        # With 90 degree rotation, the row pin should be rotated
        row_pin = next(pin for pin in pins if pin.pin_name == "row")
        
        # Original pin position was (-2, 0, 2)
        # After 90 degree rotation: (0, -2, 2)
        expected_x = 0.0
        expected_y = -2.0
        expected_z = 2.0
        
        self.assertAlmostEqual(row_pin.world_position[0], expected_x, places=5)
        self.assertAlmostEqual(row_pin.world_position[1], expected_y, places=5)
        self.assertAlmostEqual(row_pin.world_position[2], expected_z, places=5)


if __name__ == '__main__':
    unittest.main()