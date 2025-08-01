#!/usr/bin/env python3
"""
Demo script for Printboard Research

Generates several example keyboard layouts and saves them to the output directory.
"""

import os
from printboard import KeyboardGenerator


def main():
    """Generate example keyboard layouts"""
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    generator = KeyboardGenerator()
    
    # Example layouts
    layouts = [
        {
            "name": "test_3x3",
            "keys": [
                ["key", "key", "key"],
                ["key", "key", "key"],
                ["key", "key", "key"]
            ],
            "switch_type": "mx_style",
            "controller": "arduino_pro_micro"
        },
        {
            "name": "mini_5x2",
            "keys": [
                ["key", "key", "key", "key", "key"],
                ["key", "key", "key", "key", "key"]
            ],
            "switch_type": "low_profile",
            "controller": "tiny_s2"
        },
        {
            "name": "compact_4x4",
            "keys": [
                ["key", "key", "key", "key"],
                ["key", "key", "key", "key"],
                ["key", "key", "key", "key"],
                ["key", "key", "key", "key"]
            ],
            "switch_type": "mx_style",
            "controller": "arduino_pro_micro"
        }
    ]
    
    print("🔧 Printboard Research - Demo Generation")
    print("=" * 50)
    
    for layout in layouts:
        print(f"\n📋 Generating '{layout['name']}'...")
        
        try:
            # Generate keyboard
            result = generator.generate(layout)
            
            # Save files
            scad_path = f"output/{layout['name']}.scad"
            config_path = f"output/{layout['name']}_config.json"
            
            result.save_scad(scad_path)
            result.save_config(config_path)
            
            print(f"   ✓ Generated {len(result.key_positions)} key positions")
            print(f"   ✓ Saved OpenSCAD file: {scad_path}")
            print(f"   ✓ Saved config file: {config_path}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎉 Demo complete! Check the 'output' directory for generated files.")
    print(f"📁 You can open the .scad files in OpenSCAD for 3D viewing and printing.")


if __name__ == "__main__":
    main()