#!/usr/bin/env python3
"""
Test script to compare V1 and V2 API output with identical parameters.
This will help identify why V2 produces different results than V1.
"""

import os
import sys
import json
import tempfile
from solid import scad_render_to_file

# Add libs directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))

# Import V1 functionality
import printboard as kb
from switches.gamdias_lp import conf as gamdias_conf, switch_body as gamdias_switch_body, pins as gamdias_pins

# Import V2 functionality  
from printboard_v2 import KeyboardBuilder, KeyboardConfig, MatrixConfig


def create_v1_config(rows=3, cols=3):
    """Create V1 configuration for testing."""
    # Create switch object similar to how V1 does it
    switch = kb.fake_sw()
    switch.conf = gamdias_conf.copy()
    switch.switch_body = gamdias_switch_body
    switch.pins = gamdias_pins
    
    # Create basic matrix layout 
    x = "switch"
    matrix_keys = [[x] * cols for _ in range(rows)]
    
    matrix_config = {
        "offset": (0, 0),
        "keys": matrix_keys,
        "rows_stagger": [0, 5, 10],  # Test with some stagger
        "columns_stagger": [0, 0, 0]
    }
    
    layout = {
        "name": "test_keyboard_v1",
        "controller_placement": ("left", "top"),
        "matrixes": {
            "main": matrix_config
        },
        "switch": switch,
        "empty_switch": kb.empty_sw(switch),
    }
    
    return layout


def create_v2_config(rows=3, cols=3):
    """Create V2 configuration for testing."""
    matrix_config = MatrixConfig(
        rows=rows, 
        cols=cols,
        offset=(0, 0),
        rows_stagger=[0, 5, 10],  # Same stagger as V1
        columns_stagger=[0, 0, 0]
    )
    
    config = KeyboardConfig(
        name="test_keyboard_v2",
        switch_type="gamdias_lp",
        controller_type="tinys2",
        matrices={"main": matrix_config}
    )
    
    return config


def test_switch_positions():
    """Compare switch positions between V1 and V2."""
    print("=== Testing Switch Positions ===")
    
    # Test V1
    print("\n--- V1 Switch Positions ---")
    v1_config = create_v1_config()
    v1_matrix_data = kb.plan_matrix(v1_config, matrix_name='main')
    
    print(f"V1 Matrix sizes: {v1_matrix_data['sizes']}")
    for i, switch_data in enumerate(v1_matrix_data['switches']):
        print(f"V1 Switch {i}: row={switch_data['row']}, col={switch_data['column']}, "
              f"x={switch_data['x']:.2f}, y={switch_data['y']:.2f}, "
              f"c_angle={switch_data['c_angle']}, r_angle={switch_data['r_angle']}")
    
    # Test V2
    print("\n--- V2 Switch Positions ---")
    v2_config = create_v2_config()
    builder = KeyboardBuilder()
    v2_result = builder.build_keyboard(v2_config)
    
    # Get V2 switch positions from modeling engine
    from printboard_v2.modeling import ModelingEngine
    from printboard_v2.switches import switch_registry
    
    modeling_engine = ModelingEngine()
    switch = switch_registry.get("gamdias_lp")
    matrix_config = v2_config.matrices["main"]
    v2_positions = modeling_engine._plan_switch_positions(matrix_config, switch)
    
    print(f"V2 Switch count: {len(v2_positions)}")
    for i, pos in enumerate(v2_positions):
        print(f"V2 Switch {i}: row={pos['row']}, col={pos['col']}, "
              f"x={pos['x']:.2f}, y={pos['y']:.2f}, rotation={pos['rotation']}")
    
    # Compare positions
    print("\n--- Position Comparison ---")
    if len(v1_matrix_data['switches']) != len(v2_positions):
        print(f"ERROR: Different number of switches! V1={len(v1_matrix_data['switches'])}, V2={len(v2_positions)}")
        return False
    
    differences_found = False
    for i in range(len(v1_matrix_data['switches'])):
        v1_sw = v1_matrix_data['switches'][i]
        v2_sw = v2_positions[i]
        
        x_diff = abs(v1_sw['x'] - v2_sw['x'])
        y_diff = abs(v1_sw['y'] - v2_sw['y'])
        
        if x_diff > 0.01 or y_diff > 0.01:  # Allow small floating point differences
            print(f"DIFFERENCE at switch {i}: V1=({v1_sw['x']:.2f}, {v1_sw['y']:.2f}) vs V2=({v2_sw['x']:.2f}, {v2_sw['y']:.2f})")
            differences_found = True
    
    if not differences_found:
        print("✓ All switch positions match!")
        return True
    else:
        print("✗ Position differences found!")
        return False


def test_scad_output():
    """Compare SCAD output between V1 and V2."""
    print("\n=== Testing SCAD Output ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate V1 SCAD
        print("Generating V1 SCAD...")
        v1_config = create_v1_config()
        v1_keyboard = kb.create_keyboard(v1_config)
        v1_scad_file = os.path.join(temp_dir, "v1_test.scad")
        scad_render_to_file(v1_keyboard, v1_scad_file, file_header='$fn = 50;')
        
        # Generate V2 SCAD
        print("Generating V2 SCAD...")
        v2_config = create_v2_config()
        builder = KeyboardBuilder()
        v2_result = builder.build_keyboard(v2_config)
        v2_scad_file = os.path.join(temp_dir, "v2_test.scad")
        scad_render_to_file(v2_result.parts[0].shape, v2_scad_file, file_header='$fn = 50;')
        
        # Read and compare files
        with open(v1_scad_file, 'r') as f:
            v1_content = f.read()
        with open(v2_scad_file, 'r') as f:
            v2_content = f.read()
        
        print(f"V1 SCAD length: {len(v1_content)} characters")
        print(f"V2 SCAD length: {len(v2_content)} characters")
        
        # Save files for inspection
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, "comparison_v1.scad"), 'w') as f:
            f.write(v1_content)
        with open(os.path.join(output_dir, "comparison_v2.scad"), 'w') as f:
            f.write(v2_content)
        
        print(f"SCAD files saved to {output_dir}/ for inspection")
        
        # Show first few lines of each
        print("\n--- V1 SCAD (first 10 lines) ---")
        for i, line in enumerate(v1_content.split('\n')[:10]):
            print(f"{i+1:2d}: {line}")
        
        print("\n--- V2 SCAD (first 10 lines) ---")
        for i, line in enumerate(v2_content.split('\n')[:10]):
            print(f"{i+1:2d}: {line}")


if __name__ == "__main__":
    print("API Comparison Test")
    print("===================")
    
    # Test switch positions first
    positions_match = test_switch_positions()
    
    # Test SCAD output
    test_scad_output()
    
    if positions_match:
        print("\n✓ Switch positions match between V1 and V2")
    else:
        print("\n✗ Switch positions differ between V1 and V2 - need to fix V2 positioning logic")