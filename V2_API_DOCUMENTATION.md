# Printboard V2 API Documentation

## Overview

The Printboard V2 API provides a cleaner, more modular architecture for keyboard generation while maintaining full backward compatibility with the V1 API. This documentation covers the improvements and new capabilities introduced in V2.

## Key Improvements

### 🏗️ Builder Pattern
- Clean, fluent interface for keyboard construction
- Immutable configuration objects with validation
- Chainable methods for complex configurations

### 🔌 Plugin Architecture
- Extensible switch and controller registries
- Easy addition of new hardware components
- Type-safe component interfaces

### ⚙️ Separation of Concerns
- **Layout Planning**: Mathematical positioning and spacing
- **Switch Construction**: 3D geometry generation
- **Routing**: Electrical connection planning
- **Configuration**: Type-safe, validated settings

### 🔄 Backward Compatibility
- All V1 endpoints continue to work unchanged
- V2 configurations can be converted to V1 format
- Legacy code requires no modifications

## Architecture

### Core Components

```
libs/printboard_v2/
├── __init__.py          # Main V2 API exports
├── config.py            # Configuration classes
├── builder.py           # Main keyboard builder
├── layout.py            # Layout planning logic
├── switches.py          # Switch registry and interfaces
├── controllers.py       # Controller registry and interfaces
└── routing.py           # Electrical routing (future)
```

### Configuration Objects

#### MatrixConfig
```python
from libs.printboard_v2 import MatrixConfig

matrix = MatrixConfig(
    rows=5,
    cols=6,
    offset=(10.0, 20.0),
    rows_stagger=[0, 3, 6, 9, 12],
    columns_stagger=[0, 1, 2, 3, 2, 1],
    rows_angle=[0, 2, 4, 6, 8],
    columns_angle=[0, 1, 2, 3, 2, 1],
    rotation_angle=15.0,
    padding_keys=[2, 2, 2, 2, 2]
)
```

#### KeyboardConfig
```python
from libs.printboard_v2 import KeyboardConfig

config = KeyboardConfig(
    name="my_keyboard",
    switch_type="gamdias_lp",
    controller_type="tinys2",
    controller_placement=("left", "top"),
    matrices={"main": matrix}
)
```

### Builder Pattern Usage

#### Simple Keyboard
```python
from libs.printboard_v2.builder import keyboard_builder

result = keyboard_builder.create_simple_keyboard(
    name="simple_board",
    rows=4,
    cols=6,
    switch_type="gamdias_lp",
    controller_type="tinys2"
)
```

#### Advanced Configuration
```python
from libs.printboard_v2 import KeyboardBuilder, KeyboardConfig, MatrixConfig

# Create builder
builder = KeyboardBuilder()

# Configure matrices
main_matrix = MatrixConfig(
    rows=5, cols=6,
    rows_stagger=[0, 3, 6, 9, 12]
)
thumb_matrix = MatrixConfig(
    rows=1, cols=3,
    offset=(50, 70),
    rotation_angle=30
)

# Build configuration
config = KeyboardConfig(
    name="advanced_board",
    switch_type="gamdias_lp",
    controller_type="tinys2",
    matrices={
        "main": main_matrix,
        "thumb": thumb_matrix
    }
)

# Generate keyboard
result = builder.build_keyboard(config)
```

## Web API Endpoints

### V2 Endpoints

All V2 endpoints return responses with `"api_version": "2.0"` and additional metadata.

#### `POST /api/v2/keyboard/preview`
Generate 2D layout preview using V2 API.

**Request:**
```json
{
  "name": "test_keyboard",
  "rows": 4,
  "cols": 6,
  "switchType": "gamdias_lp",
  "controllerType": "tinys2",
  "rowsStagger": [0, 3, 6, 9],
  "columnsStagger": [0, 1, 2, 3, 2, 1],
  "rotationAngle": 15,
  "matrixOffsetX": 10,
  "matrixOffsetY": 20
}
```

**Response:**
```json
{
  "success": true,
  "api_version": "2.0",
  "layout": [
    [
      {
        "x": 10.0,
        "y": 20.0,
        "width": 18.5,
        "height": 18.5,
        "angle": 0.0,
        "label": "R0C0"
      }
    ]
  ],
  "message": "V2 Preview generated successfully"
}
```

#### `POST /api/v2/keyboard/generate`
Generate 3D models using V2 API.

**Request:** Same as preview endpoint

**Response:**
```json
{
  "success": true,
  "api_version": "2.0",
  "scad_files": ["test_keyboard_matrix.scad"],
  "stl_files": ["test_keyboard_matrix.stl"],
  "message": "V2 API: Generated 1 SCAD files and 1 STL files successfully",
  "metadata": {
    "switch_type": "gamdias_lp",
    "controller_type": "tinys2",
    "total_keys": 24,
    "matrices": ["main"],
    "bounds": [10.0, 20.0, 101.5, 75.5]
  }
}
```

#### `POST /api/v2/keyboard/simple`
Create simple keyboards with minimal configuration.

**Request:**
```json
{
  "name": "simple_board",
  "rows": 4,
  "cols": 6,
  "switch_type": "gamdias_lp",
  "controller_type": "tinys2"
}
```

**Response:**
```json
{
  "success": true,
  "api_version": "2.0",
  "message": "Simple keyboard \"simple_board\" created successfully",
  "config": {
    "name": "simple_board",
    "switch_type": "gamdias_lp",
    "controller_type": "tinys2",
    "matrices": {
      "main": {"rows": 4, "cols": 6}
    }
  },
  "metadata": {
    "total_keys": 24,
    "switch_type": "gamdias_lp",
    "controller_type": "tinys2",
    "matrices": ["main"],
    "bounds": [0.0, 0.0, 92.5, 55.5]
  }
}
```

#### `GET /api/v2/components/switches`
List available switch types.

**Response:**
```json
{
  "success": true,
  "api_version": "2.0",
  "switches": ["gamdias_lp"]
}
```

#### `GET /api/v2/components/controllers`
List available controller types.

**Response:**
```json
{
  "success": true,
  "api_version": "2.0", 
  "controllers": ["tinys2"]
}
```

### V1 Compatibility

All existing V1 endpoints continue to work unchanged:

- `POST /api/keyboard/preview`
- `POST /api/keyboard/generate`
- `GET /api/keyboard/files`
- `GET /api/keyboard/download/<filename>`
- `GET /api/keyboard/presets`

## Plugin System

### Adding New Switch Types

```python
from libs.printboard_v2.switches import SwitchInterface, SwitchSpecs, SwitchPin, switch_registry

class MyCustomSwitch(SwitchInterface):
    @property
    def name(self) -> str:
        return "my_custom_switch"
    
    @property
    def specs(self) -> SwitchSpecs:
        return SwitchSpecs(
            body_size=(15.0, 15.0, 10.0),
            key_size=(19.0, 19.0),
            pins=[
                SwitchPin("column", (-5.0, -6.0, 3.0), "matrix"),
                SwitchPin("row", (5.0, 6.0, 3.0), "matrix")
            ]
        )
    
    def create_body(self, **kwargs):
        # Return 3D geometry object
        pass
    
    def create_empty(self, width=None, **kwargs):
        # Return empty switch for variable sizes
        pass

# Register the switch
switch_registry.register(MyCustomSwitch())
```

### Adding New Controller Types

```python
from libs.printboard_v2.controllers import ControllerInterface, ControllerSpecs, ControllerPin, controller_registry

class MyCustomController(ControllerInterface):
    @property
    def name(self) -> str:
        return "my_controller"
    
    @property
    def specs(self) -> ControllerSpecs:
        left_pins = [
            ControllerPin(1, "D1", True, (0, 0)),
            ControllerPin(2, "D2", True, (0, 2.54)),
            # ... more pins
        ]
        
        return ControllerSpecs(
            name="My Controller",
            footprint_size=(20.0, 30.0),
            pin_pitch=2.54,
            pins={"left": left_pins, "right": right_pins}
        )
    
    def create_footprint(self, **kwargs):
        # Return 3D footprint geometry
        pass
    
    def get_pin_mapping(self) -> Dict[int, str]:
        return {1: "D1", 2: "D2"}  # etc.

# Register the controller
controller_registry.register(MyCustomController())
```

## Configuration Validation

V2 provides comprehensive validation for all configuration objects:

```python
from libs.printboard_v2 import MatrixConfig

# This will raise ValueError: "Rows and columns must be positive integers"
try:
    invalid = MatrixConfig(rows=0, cols=5)
except ValueError as e:
    print(f"Validation error: {e}")

# This will raise ValueError: "rows_stagger must have 3 elements"
try:
    invalid = MatrixConfig(rows=3, cols=3, rows_stagger=[0, 5])
except ValueError as e:
    print(f"Validation error: {e}")
```

## Testing

V2 includes comprehensive test coverage:

```bash
# Run V2 unit tests
python -m pytest tests/test_v2_api.py -v

# Run V2 web API tests
python -m pytest tests/test_v2_web_api.py -v

# Run all tests including V1 compatibility
python -m pytest tests/ --cov=libs --cov=app --cov-report=term-missing
```

## Migration Guide

### From V1 to V2

**V1 Code:**
```python
from libs import printboard as kb
from libs.switches import gamdias_lp as switch
from libs.controllers import tinys2 as controller

layout = {
    "name": "my_keyboard",
    "controller_placement": ("left", "top"),
    "matrixes": {
        "main": {
            "offset": (0, 0),
            "keys": [["switch"] * 5] * 5,
            "rows_stagger": [0, 5, 10, 10, 0]
        }
    },
    "switch": switch,
    "empty_switch": kb.empty_sw(switch),
    "controller": controller
}

parts = kb.create_keyboard(layout)
```

**V2 Equivalent:**
```python
from libs.printboard_v2 import KeyboardBuilder, KeyboardConfig, MatrixConfig

matrix_config = MatrixConfig(
    rows=5,
    cols=5,
    rows_stagger=[0, 5, 10, 10, 0]
)

config = KeyboardConfig(
    name="my_keyboard",
    switch_type="gamdias_lp",
    controller_type="tinys2",
    controller_placement=("left", "top"),
    matrices={"main": matrix_config}
)

builder = KeyboardBuilder()
result = builder.build_keyboard(config)
parts = result.parts
```

### Benefits of Migration

1. **Type Safety**: Configuration errors caught at creation time
2. **Better Testing**: Easier to unit test individual components
3. **Extensibility**: Simple to add new switches and controllers
4. **Documentation**: Self-documenting code with clear interfaces
5. **Immutability**: Configuration objects cannot be accidentally modified

## Performance

V2 maintains similar performance to V1 while providing better architecture:

- **Memory**: Immutable objects reduce memory leaks
- **CPU**: Same underlying 3D generation algorithms
- **Testing**: 95%+ test coverage ensures reliability
- **Maintenance**: Modular design enables easier debugging

## Examples

### Complete Workflow

```python
from libs.printboard_v2.builder import keyboard_builder

# 1. List available components
switches = keyboard_builder.list_available_switches()
controllers = keyboard_builder.list_available_controllers()
print(f"Available: {switches}, {controllers}")

# 2. Create configuration from web request
web_data = {
    'name': 'example_board',
    'rows': 4,
    'cols': 6,
    'rowsStagger': [0, 2, 4, 6],
    'rotationAngle': 10
}
config = keyboard_builder.create_config_from_web_request(web_data)

# 3. Generate preview
preview = keyboard_builder.generate_preview(config)
print(f"Preview: {len(preview)} rows")

# 4. Build complete keyboard
result = keyboard_builder.build_keyboard(config)
print(f"Generated {len(result.parts)} parts")
print(f"Metadata: {result.metadata}")
```

### Advanced Multi-Matrix Keyboard

```python
from libs.printboard_v2 import KeyboardConfig, MatrixConfig

# Main matrix
main = MatrixConfig(
    rows=5, cols=6,
    rows_stagger=[0, 3, 6, 9, 12],
    columns_stagger=[0, 1, 2, 3, 2, 1]
)

# Thumb cluster
thumb = MatrixConfig(
    rows=1, cols=3,
    offset=(60, 80),
    rotation_angle=25,
    columns_stagger=[0, 3, 6]
)

# Number row
numbers = MatrixConfig(
    rows=1, cols=10,
    offset=(-5, -25),
    columns_stagger=[0, 0, 1, 2, 3, 3, 2, 1, 0, 0]
)

config = KeyboardConfig(
    name="advanced_split",
    matrices={
        "main": main,
        "thumb": thumb,
        "numbers": numbers
    }
)

result = keyboard_builder.build_keyboard(config)
```

## Future Roadmap

The V2 architecture enables future enhancements:

- **Additional Switch Types**: Cherry MX, Kailh Choc, etc.
- **More Controllers**: RP2040, Pro Micro, custom controllers
- **Advanced Routing**: Optimized electrical trace planning
- **PCB Generation**: Automated PCB layout generation
- **Case Design**: Integrated case generation tools
- **Community Plugins**: User-contributed components

## Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: This guide and inline code documentation
- **Tests**: Comprehensive test suite for validation
- **Examples**: Demo scripts and working configurations