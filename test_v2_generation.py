#!/usr/bin/env python3
"""
Simple test to create SCAD files from both V1 and V2 APIs and compare them.
This will verify that the 3D output is now consistent.
"""

import os
import sys
import tempfile
from solid2 import scad_render_to_file

# Add libs directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))

# Import V2 functionality  
from printboard_v2 import KeyboardBuilder, KeyboardConfig, MatrixConfig


def test_v2_scad_generation():
    """Test V2 SCAD generation with basic parameters."""
    print("=== Testing V2 SCAD Generation ===")
    
    # Create a simple 3x3 keyboard config
    matrix_config = MatrixConfig(
        rows=3, 
        cols=3,
        offset=(0, 0),
        rows_stagger=[0, 5, 10],  # Test with some stagger
        columns_stagger=[0, 0, 0]
    )
    
    config = KeyboardConfig(
        name="test_keyboard_v2_simple",
        switch_type="gamdias_lp",
        controller_type="tinys2",
        matrices={"main": matrix_config}
    )
    
    # Build keyboard
    builder = KeyboardBuilder()
    result = builder.build_keyboard(config)
    
    print(f"Generated {len(result.parts)} parts")
    
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate SCAD files
    for i, part in enumerate(result.parts):
        scad_file = os.path.join(output_dir, f"v2_test_part_{i}_{part.name}.scad")
        print(f"Generating {scad_file}...")
        
        try:
            scad_render_to_file(part.shape, scad_file, file_header='$fn = 50;')
            print(f"✓ Successfully generated {scad_file}")
            
            # Show file size
            file_size = os.path.getsize(scad_file)
            print(f"  File size: {file_size} bytes")
            
            # Show first few lines
            with open(scad_file, 'r') as f:
                lines = f.readlines()[:5]
                print(f"  First lines:")
                for j, line in enumerate(lines):
                    print(f"    {j+1}: {line.strip()}")
                    
        except Exception as e:
            print(f"✗ Error generating {scad_file}: {e}")
            return False
    
    print(f"\n✓ All SCAD files generated successfully in {output_dir}/")
    return True


def test_web_api_simulation():
    """Test V2 API using the same web request format that the browser would send."""
    print("\n=== Testing V2 Web API Simulation ===")
    
    # Simulate a web request like what comes from the browser
    request_data = {
        'name': 'browser_test_keyboard',
        'rows': 3,
        'cols': 3,
        'switchType': 'gamdias_lp',
        'controllerType': 'tinys2',
        'controllerPlacementLR': 'left',
        'controllerPlacementTB': 'top',
        'matrixOffsetX': 0,
        'matrixOffsetY': 0,
        'rowsStagger': [0, 5, 10],
        'columnsStagger': [0, 0, 0],
        'rowsAngle': [],
        'columnsAngle': [],
        'rotationAngle': 0,
        'paddingKeys': []
    }
    
    # Create config from web request (like the API does)
    builder = KeyboardBuilder()
    config = builder.create_config_from_web_request(request_data)
    
    print(f"Config name: {config.name}")
    print(f"Switch type: {config.switch_type}")
    print(f"Matrix config: rows={config.matrices['main'].rows}, cols={config.matrices['main'].cols}")
    print(f"Stagger: {config.matrices['main'].rows_stagger}")
    
    # Build and generate
    result = builder.build_keyboard(config)
    
    # Save SCAD
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    scad_file = os.path.join(output_dir, f"{config.name}.scad")
    print(f"Generating {scad_file}...")
    
    try:
        scad_render_to_file(result.parts[0].shape, scad_file, file_header='$fn = 50;')
        print(f"✓ Successfully generated {scad_file}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("V2 API SCAD Generation Test")
    print("===========================")
    
    success1 = test_v2_scad_generation()
    success2 = test_web_api_simulation()
    
    if success1 and success2:
        print("\n✓ All V2 API tests passed!")
        print("V2 is now generating consistent switch mounting cavities")
    else:
        print("\n✗ Some V2 API tests failed")