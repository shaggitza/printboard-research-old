# Printboard Research

🔧 **Generate custom keyboard PCB layouts and 3D models**

A Python project for creating custom keyboard PCBs with 3D printable components. This project has been rebooted with modern web interface, test coverage, and improved architecture.

## Features

- 🖥️ **Web Interface**: Easy-to-use web interface for keyboard configuration
- 🗂️ **Multiple Layouts**: Support for various keyboard sizes (65%, custom layouts)
- 🔧 **Configurable Components**: Different switch types and controller options  
- 📐 **3D Model Generation**: Generates OpenSCAD files for 3D printing
- 🧪 **Test Coverage**: Comprehensive test suite with integration tests
- 📊 **Real-time Preview**: Live keyboard layout preview in the browser

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Note: If external dependencies fail to install, the project includes mock implementations for development.

### 2. Run the Web Server

```bash
python web_server.py
```

Then open http://localhost:8080 in your browser.

### 3. Configure Your Keyboard

- Choose keyboard size (5×5 test, 65%, or custom)
- Select switch type (currently supports Gamdias Low Profile)
- Pick controller (TinyS2 supported)
- Set controller placement
- Click "Generate Keyboard"

### 4. Download Generated Files

The web interface will generate:
- `.scad` files for 3D printing
- `.json` configuration files
- Real-time preview of your layout

## Development

### Running Tests

```bash
python run_tests.py
```

### Project Structure

```
printboard-research-old/
├── libs/                    # Core libraries
│   ├── printboard.py       # Main keyboard generation logic
│   ├── switches/           # Switch definitions
│   └── controllers/        # Controller definitions
├── tests/                  # Test suite
├── output/                 # Generated files
├── web_server.py          # Web interface server
├── mock_solid.py          # Mock implementation for development
└── requirements.txt       # Python dependencies
```

### Architecture

The project follows a modular architecture:

- **Core Library** (`libs/printboard.py`): Matrix planning, tube routing, 3D model generation
- **Component Definitions**: Switches and controllers with physical specifications
- **Web Interface**: Flask-based server with HTML/JavaScript frontend  
- **Test Suite**: Unit and integration tests with mock implementations
- **Build System**: Requirements management and dependency handling

### Adding New Components

#### New Switch Type
1. Create a new file in `libs/switches/`
2. Define `conf` dict with physical dimensions
3. Define `pins` array with electrical connections
4. Add switch body 3D model definition

#### New Controller  
1. Create a new file in `libs/controllers/`
2. Define `pin_rows` with pin layout
3. Define `usable_pins` array
4. Add controller footprint definition

## Original vs. Rebooted

### What's New
- ✅ **Web Interface**: Modern browser-based configuration
- ✅ **Test Coverage**: Comprehensive test suite
- ✅ **Mock System**: Development without external dependencies
- ✅ **Architecture Refactor**: Cleaner, more modular code
- ✅ **Bug Fixes**: Removed blocking exit() calls and other issues

### Maintained Features
- ✅ **3D Model Generation**: Still generates OpenSCAD files
- ✅ **Multiple Layouts**: Support for various keyboard configurations  
- ✅ **Switch/Controller System**: Extensible component definitions
- ✅ **Matrix Planning**: Advanced routing and layout algorithms

## Dependencies

### Required
- Python 3.7+

### Optional (for full functionality)  
- solidpython: 3D model generation
- numpy, scipy: Mathematical operations
- shapely: Geometric calculations
- flask: Web interface

The project includes mock implementations so you can develop and test even without external dependencies.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite: `python run_tests.py`
5. Submit a pull request

## License

This project is licensed under the terms in the LICENSE file.