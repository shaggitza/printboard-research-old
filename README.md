# Printboard Research

A simple, clean library for generating custom keyboard PCB layouts and 3D models.

## What it does

1. **Define keyboard layouts** - Specify key positions, sizes, and arrangements
2. **Generate 3D models** - Create OpenSCAD files for 3D printing keyboard structures  
3. **Plan wiring routes** - Calculate optimal paths between switches and controllers
4. **Export configurations** - Save layouts as JSON for sharing and modification

## Quick Start

```python
from printboard import KeyboardGenerator

# Define a simple 3x3 layout
layout = {
    "name": "test_3x3",
    "keys": [
        ["key", "key", "key"],
        ["key", "key", "key"], 
        ["key", "key", "key"]
    ],
    "switch_type": "mx_style",
    "controller": "arduino_pro_micro"
}

# Generate the keyboard
generator = KeyboardGenerator()
result = generator.generate(layout)

# Save outputs
result.save_scad("output/keyboard.scad")
result.save_config("output/keyboard.json")
```

## Features

- **Simple Configuration**: Easy-to-understand layout definitions
- **Modular Design**: Pluggable switches and controllers  
- **Clean Output**: Well-formatted OpenSCAD and JSON files
- **Well Tested**: Comprehensive test coverage
- **Web Interface**: Optional browser-based layout editor

## Installation

```bash
# Basic usage (no 3D dependencies)
python -m pip install -r requirements.txt

# For 3D model generation
python -m pip install solidpython
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Web Interface

```bash
python server.py
# Open http://localhost:8000
```