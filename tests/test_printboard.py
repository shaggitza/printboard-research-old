import pytest
import numpy as np
from libs import printboard as kb
from libs.switches import gamdias_lp as switch
from libs.controllers import tinys2 as controller

def test_create_keyboard_basic():
    """Test basic keyboard creation functionality."""
    layout = {
        "name": "test",
        "controller_placement": ("left", "top"),
        "matrixes": {
            "main": {
                "offset": (0, 0),
                "keys": [["switch"] * 3] * 2,  # 2x3 matrix
            }
        },
        "switch": switch,
        "empty_switch": kb.empty_sw(switch),
        "controller": controller
    }
    
    # Add variable key sizes
    for i in range(0, 3):
        layout[f"{i}u"] = kb.empty_sw(switch, x=18.5*i if i > 0 else 18.5)
    
    parts = kb.create_keyboard(layout)
    
    assert len(parts) > 0
    assert parts[0]['name'] == 'matrix'
    assert parts[0]['shape'] is not None

def test_plan_matrix():
    """Test matrix planning functionality."""
    config = {
        "matrixes": {
            "main": {
                "offset": (0, 0),
                "keys": [["switch"] * 2] * 2,
            }
        },
        "switch": switch,
    }
    
    matrix_data = kb.plan_matrix(config, matrix_name='main')
    
    assert 'switches' in matrix_data
    assert len(matrix_data['switches']) == 4  # 2x2 = 4 switches
    assert 'sizes' in matrix_data

def test_empty_switch_creation():
    """Test empty switch creation with different parameters."""
    empty_sw = kb.empty_sw(switch)
    assert empty_sw.conf is not None
    
    empty_sw_custom = kb.empty_sw(switch, x=37, y=37)
    assert empty_sw_custom.conf['switch_sizes_x'] == 37
    assert empty_sw_custom.conf['switch_sizes_y'] == 37

def test_switch_properties():
    """Test switch module properties."""
    assert hasattr(switch, 'conf')
    assert hasattr(switch, 'pins')
    assert hasattr(switch, 'switch_body')
    
    # Check configuration values
    assert switch.conf['switch_sizes_x'] == 18.5
    assert switch.conf['switch_sizes_y'] == 18.5

def test_controller_properties():
    """Test controller module properties."""
    assert hasattr(controller, 'pin_rows')
    assert hasattr(controller, 'usable_pins')
    assert hasattr(controller, 'controller_footprint')
    
    # Check pin configuration
    assert 'left' in controller.pin_rows
    assert 'right' in controller.pin_rows
    assert len(controller.usable_pins) > 0

def test_extract_points():
    """Test point extraction from matrices."""
    # Create a simple test matrix
    test_matrix = {
        'switches': [
            {
                'switch': switch,
                'column': 0,
                'row': 0,
                'x': 0,
                'y': 0,
                'c_angle': 0,
                'r_angle': 0
            }
        ]
    }
    
    matrixes = {'main': test_matrix}
    points = kb.extract_points(matrixes)
    
    assert 'matrix' in points
    assert len(points['matrix']) > 0

def test_rotate_point():
    """Test point rotation functionality."""
    point = (1, 0, 0)
    angle = np.pi / 2  # 90 degrees
    
    rotated = kb.rotate_point(point, angle)
    
    # After 90-degree rotation, (1,0,0) should become approximately (0,1,0)
    assert abs(rotated[0]) < 1e-10  # Should be close to 0
    assert abs(rotated[1] - 1) < 1e-10  # Should be close to 1
    assert abs(rotated[2]) < 1e-10  # z unchanged