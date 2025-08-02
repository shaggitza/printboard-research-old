# Printboard Research - Custom Keyboard Designer

A modern web application for designing and generating 3D printable custom keyboards.

## Features

🎨 **Web-Based Designer**
- Intuitive web interface for keyboard configuration
- Real-time 2D layout preview
- Multiple layout presets (5x5, 4x12, 3x6, 5x12)
- Responsive design works on desktop and mobile

🔧 **3D Model Generation**
- Generates OpenSCAD (.scad) files for 3D modeling
- Automatic STL conversion (when OpenSCAD is available)
- Supports various switch types and controllers
- Configurable key layouts and spacing

👁️ **3D Visualization**
- Built-in STL file viewer with Three.js
- Interactive 3D model inspection
- Orbit controls for easy navigation
- Real-time model loading

📁 **File Management**
- Download generated SCAD/STL files
- File listing with size and date information
- Bulk file operations

🧪 **Testing & Quality**
- Comprehensive test suite with 81% coverage
- Unit and integration tests
- Automated testing with pytest

## Quick Start

### Prerequisites

```bash
# Python 3.8+ required
pip install -r requirements.txt
```

### Installation

```bash
# Clone the repository
git clone https://github.com/shaggitza/printboard-research-old.git
cd printboard-research-old

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at `http://localhost:5000`

### Docker Installation (Recommended)

For the easiest setup with automatic OpenSCAD support:

```bash
# Clone the repository
git clone https://github.com/shaggitza/printboard-research-old.git
cd printboard-research-old

# Run with Docker Compose
docker-compose up -d
```

The application will be available at `http://localhost:5000` with full STL generation capabilities.

**Docker benefits:**
- Includes OpenSCAD for automatic STL generation
- No manual dependency installation
- Consistent environment across different systems
- Production-ready setup

### Manual Installation

If you prefer to run without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Optional: Install OpenSCAD

For automatic STL generation, install OpenSCAD:

```bash
# Ubuntu/Debian
sudo apt-get install openscad

# macOS
brew install openscad

# Windows
# Download from https://openscad.org/downloads.html
```

## Usage

### Web Interface

1. **Design Tab**: Configure your keyboard
   - Set keyboard name, dimensions (rows/columns)
   - Choose from preset layouts or create custom
   - Select switch types and controllers

2. **Preview Tab**: See 2D layout
   - Real-time visualization of key positions
   - Interactive preview updates as you change settings

3. **Generate Tab**: Create 3D models
   - Generate SCAD files for OpenSCAD
   - Automatic STL conversion (if OpenSCAD available)
   - Progress tracking and status updates

4. **Files Tab**: Manage generated files
   - Download SCAD/STL files
   - View STL files in 3D browser viewer
   - File management and organization

### API Endpoints

- `GET /` - Main web interface
- `POST /api/keyboard/preview` - Generate 2D layout preview
- `POST /api/keyboard/generate` - Generate 3D models
- `GET /api/keyboard/files` - List generated files
- `GET /api/keyboard/download/<filename>` - Download file
- `GET /api/keyboard/presets` - Get layout presets

### Programmatic Usage

```python
from libs import printboard as kb
from libs.switches import gamdias_lp as switch
from libs.controllers import tinys2 as controller

# Define keyboard layout
layout = {
    "name": "my_keyboard",
    "controller_placement": ("left", "top"),
    "matrixes": {
        "main": {
            "offset": (0, 0),
            "keys": [["switch"] * 5] * 5,  # 5x5 grid
        }
    },
    "switch": switch,
    "empty_switch": kb.empty_sw(switch),
    "controller": controller
}

# Generate 3D models
parts = kb.create_keyboard(layout)
for part in parts:
    scad_render_to_file(part['shape'], f"{layout['name']}_{part['name']}.scad")
```

## Architecture

### Backend (Flask)
- **app.py**: Main Flask application with REST API
- **libs/printboard.py**: Core keyboard generation logic
- **libs/switches/**: Switch type definitions and properties
- **libs/controllers/**: Microcontroller definitions and pin layouts

### Frontend (Vanilla JS)
- **templates/index.html**: Main web interface
- **static/js/stl-viewer.js**: 3D STL file viewer using Three.js
- Responsive CSS with modern design

### Testing
- **tests/test_web.py**: Web API integration tests
- **tests/test_printboard.py**: Core functionality unit tests
- **pytest.ini**: Test configuration with coverage reporting

## Switch Types

Currently supported:
- **Gamdias Low Profile**: Complete implementation with pins and housing
- Cherry MX: Planned
- Kailh Choc: Planned

## Controllers

Currently supported:
- **TinyS2**: Complete pin mapping and footprint
- RP2040: Planned  
- Pro Micro: Planned

## Development

### Running Tests

```bash
# Run all tests with coverage
python -m pytest tests/ --cov=libs --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_web.py -v

# Run with coverage report
python -m pytest tests/ --cov-report=term-missing
```

### Docker Development

**Build and run locally:**
```bash
# Build the Docker image
docker build -t printboard-app .

# Run with docker-compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Health check:**
```bash
# Check if the application is healthy and OpenSCAD is available
curl http://localhost:5000/health
```

**Production deployment:**
```bash
# Run in production mode
docker-compose -f docker-compose.yml up -d

# Scale if needed
docker-compose up --scale printboard-app=2 -d
```

### Project Structure

```
printboard-research-old/
├── app.py                  # Flask web application
├── generate.py            # Original CLI script
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Web interface
├── static/
│   └── js/
│       └── stl-viewer.js  # 3D viewer component
├── libs/
│   ├── printboard.py      # Core keyboard generation
│   ├── switches/          # Switch type definitions
│   └── controllers/       # Controller definitions
├── tests/                 # Test suite
├── output/               # Generated files
└── README.md
```

### Adding New Features

1. **New Switch Type**: Add module in `libs/switches/`
2. **New Controller**: Add module in `libs/controllers/`
3. **Web Features**: Extend `app.py` and `templates/index.html`
4. **Tests**: Add corresponding tests in `tests/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Technical Details

### 3D Modeling Pipeline
1. **Layout Planning**: Calculate key positions, angles, and spacing
2. **Matrix Generation**: Create switch matrix with proper connections
3. **Trace Routing**: Generate connection paths between switches
4. **3D Modeling**: Use SolidPython to create OpenSCAD geometry
5. **Export**: Generate SCAD files, optionally convert to STL

### File Formats
- **SCAD**: OpenSCAD source files for editing and customization
- **STL**: Binary 3D mesh files ready for 3D printing
- **JSON**: Configuration and layout data

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**STL files not generating**
- Install OpenSCAD for automatic STL conversion
- SCAD files are always generated and can be manually converted

**3D viewer not working**
- Ensure browser supports WebGL
- Check browser console for JavaScript errors
- Verify STL files are properly formatted

**Tests failing**
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests to see specific errors
python -m pytest tests/ -v
```

### Performance Tips

- Use smaller keyboard layouts for faster generation
- Clear output directory periodically to save space
- For large keyboards, generate in sections

## Future Roadmap

- [ ] Additional switch types (Cherry MX, Kailh Choc)
- [ ] More controller options (RP2040, Pro Micro)
- [ ] Advanced layout features (staggering, rotation)
- [ ] PCB generation capabilities
- [ ] Case design tools
- [ ] Community layout sharing
- [ ] Mobile app version