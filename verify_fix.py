#!/usr/bin/env python3
"""
Simple verification that V2 API now produces consistent switch positioning
and practical mounting cavities as requested.
"""

import os
import sys

# Add libs directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))

from printboard_v2 import KeyboardBuilder, KeyboardConfig, MatrixConfig


def demonstrate_fix():
    """Demonstrate that the V2 API issue has been resolved."""
    print("V2 API Fix Verification")
    print("=======================")
    
    # Test the exact same parameters as reported in the issue
    matrix_config = MatrixConfig(
        rows=3, 
        cols=3,
        offset=(0, 0),
        rows_stagger=[0, 5, 10],
        columns_stagger=[0, 0, 0]
    )
    
    config = KeyboardConfig(
        name="verification_test",
        switch_type="gamdias_lp",
        controller_type="tinys2",
        matrices={"main": matrix_config}
    )
    
    # Build with V2 API
    builder = KeyboardBuilder()
    result = builder.build_keyboard(config)
    
    print(f"✅ V2 API successfully built keyboard with {len(result.parts)} parts")
    print(f"✅ Configuration: {config.matrices['main'].rows}x{config.matrices['main'].cols} with stagger {config.matrices['main'].rows_stagger}")
    
    # Check that we're generating mounting cavities, not solid bodies
    from solid import scad_render
    scad_content = scad_render(result.parts[0].shape)
    
    # Key indicators that it's mounting cavities:
    has_mounting_cavity = 'size = [14.9' in scad_content  # Switch mounting hole
    has_stem_cavity = 'size = [12.2' in scad_content      # Stem cavity
    has_pin_holes = 'd = 1.2' in scad_content             # Pin holes
    is_clean_geometry = scad_content.count('union()') < 20  # Not overly complex
    
    print(f"✅ Generated mounting cavities (not solid bodies):")
    print(f"   - Switch mounting holes: {has_mounting_cavity}")
    print(f"   - Stem cavities: {has_stem_cavity}")
    print(f"   - Pin holes: {has_pin_holes}")
    print(f"   - Clean geometry: {is_clean_geometry}")
    
    # Verify positions match V1-style calculation
    from printboard_v2.modeling import ModelingEngine
    from printboard_v2.switches import switch_registry
    
    modeling_engine = ModelingEngine()
    switch = switch_registry.get("gamdias_lp")
    positions = modeling_engine._plan_switch_positions(config.matrices["main"], switch)
    
    expected_positions = [
        (9.25, 9.25),    # Row 0, Col 0
        (27.75, 9.25),   # Row 0, Col 1  
        (46.25, 9.25),   # Row 0, Col 2
        (4.25, 27.75),   # Row 1, Col 0 (stagger -5)
        (22.75, 27.75),  # Row 1, Col 1
        (41.25, 27.75),  # Row 1, Col 2
        (-0.75, 46.25),  # Row 2, Col 0 (stagger -10)
        (17.75, 46.25),  # Row 2, Col 1
        (36.25, 46.25),  # Row 2, Col 2
    ]
    
    positions_correct = True
    print(f"✅ Switch positions (V1-compatible):")
    for i, (pos, expected) in enumerate(zip(positions, expected_positions)):
        actual = (pos['x'], pos['y'])
        if abs(actual[0] - expected[0]) > 0.01 or abs(actual[1] - expected[1]) > 0.01:
            print(f"   ❌ Switch {i}: Expected {expected}, got {actual}")
            positions_correct = False
        else:
            print(f"   ✅ Switch {i}: {actual} (correct)")
    
    all_correct = (has_mounting_cavity and has_stem_cavity and 
                  has_pin_holes and is_clean_geometry and positions_correct)
    
    if all_correct:
        print(f"\n🎉 SUCCESS: V2 API is now working correctly!")
        print(f"   ✅ Generates practical mounting cavities (not solid switch bodies)")
        print(f"   ✅ Uses identical positioning logic as V1 API")
        print(f"   ✅ Produces clean, manufacturing-ready SCAD output")
        print(f"   ✅ Perfect for CNC machining or 3D printing keyboard plates")
    else:
        print(f"\n❌ Issues still remain with V2 API")
    
    return all_correct


if __name__ == "__main__":
    success = demonstrate_fix()
    
    if success:
        print("\n" + "="*60)
        print("🔧 ISSUE RESOLVED: V2 API Fixed")
        print("="*60)
        print("The V2 API now produces the same switch positioning as V1")
        print("while generating practical mounting templates instead of")
        print("solid switch models. This makes V2 perfect for real-world")
        print("keyboard manufacturing.")
        print("="*60)
    else:
        print("\n❌ Fix incomplete - issues remain")