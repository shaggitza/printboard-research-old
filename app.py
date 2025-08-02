from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import subprocess
import tempfile
from libs import printboard as kb
from libs.switches import gamdias_lp as switch
from libs.controllers import tinys2 as controller
from solid import scad_render_to_file
import io
import base64

app = Flask(__name__)
CORS(app)

# Serve static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_file(os.path.join('static', filename))

# Configuration
app.config['SECRET_KEY'] = 'dev-key-change-in-production'
app.config['OUTPUT_DIR'] = os.path.join(os.path.dirname(__file__), 'output')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Ensure directories exist
os.makedirs(app.config['OUTPUT_DIR'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Main page with keyboard designer interface."""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for Docker."""
    return jsonify({
        'status': 'healthy',
        'openscad_available': subprocess.run(['which', 'openscad'], capture_output=True).returncode == 0
    })

@app.route('/api/keyboard/preview', methods=['POST'])
def preview_keyboard():
    """Generate 2D preview of keyboard layout."""
    try:
        config = request.get_json()
        
        # Create a simplified layout for preview
        layout_data = generate_layout_data(config)
        
        return jsonify({
            'success': True,
            'layout': layout_data,
            'message': 'Preview generated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/keyboard/generate', methods=['POST'])
def generate_keyboard():
    """Generate 3D model files (SCAD and STL)."""
    try:
        config = request.get_json()
        
        # Build keyboard configuration
        layout = build_keyboard_config(config)
        
        # Generate SCAD file
        parts = kb.create_keyboard(layout)
        scad_files = []
        stl_files = []
        
        for part in parts:
            # Generate SCAD
            filename = f"{layout['name']}_{part['name']}"
            scad_file = os.path.join(app.config['OUTPUT_DIR'], f'{filename}.scad')
            scad_render_to_file(part['shape'], scad_file, file_header='$fn = 50;')
            scad_files.append(f'{filename}.scad')
            
            # Generate STL if OpenSCAD is available
            stl_file = os.path.join(app.config['OUTPUT_DIR'], f'{filename}.stl')
            try:
                # Use Xvfb for headless OpenSCAD rendering in Docker
                result = subprocess.run([
                    'xvfb-run', '-a', 'openscad', 
                    '-o', stl_file, 
                    scad_file
                ], check=True, capture_output=True, text=True, timeout=60)
                
                # Verify STL file was created and has content
                if os.path.exists(stl_file) and os.path.getsize(stl_file) > 0:
                    stl_files.append(f'{filename}.stl')
                    print(f"Successfully generated STL: {filename}.stl")
                else:
                    print(f"STL generation failed for {filename}: file not created or empty")
                    
            except subprocess.TimeoutExpired:
                print(f"STL generation timed out for {filename}")
            except subprocess.CalledProcessError as e:
                print(f"OpenSCAD error for {filename}: {e.stderr}")
            except FileNotFoundError:
                print("OpenSCAD not found - STL generation skipped")
                # Fall back to trying without xvfb
                try:
                    subprocess.run([
                        'openscad', '-o', stl_file, scad_file
                    ], check=True, capture_output=True, timeout=60)
                    if os.path.exists(stl_file) and os.path.getsize(stl_file) > 0:
                        stl_files.append(f'{filename}.stl')
                except Exception:
                    pass
        
        # Generate success message with details
        success_msg = f'Generated {len(scad_files)} SCAD files'
        if stl_files:
            success_msg += f' and {len(stl_files)} STL files successfully'
        else:
            success_msg += ' (STL generation requires OpenSCAD)'
        
        return jsonify({
            'success': True,
            'scad_files': scad_files,
            'stl_files': stl_files,
            'message': success_msg
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/keyboard/download/<filename>')
def download_file(filename):
    """Download generated files."""
    try:
        file_path = os.path.join(app.config['OUTPUT_DIR'], filename)
        if os.path.exists(file_path) and filename.endswith(('.scad', '.stl')):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/keyboard/presets')
def get_presets():
    """Get available keyboard layout presets."""
    presets = {
        'basic_5x5': {
            'name': 'Basic 5x5',
            'description': '25-key grid layout',
            'rows': 5,
            'cols': 5,
            'layout_type': 'grid'
        },
        'compact_4x12': {
            'name': 'Compact 4x12',
            'description': '48-key compact layout',
            'rows': 4,
            'cols': 12,
            'layout_type': 'grid'
        },
        'split_3x6': {
            'name': 'Split 3x6',
            'description': '36-key split layout',
            'rows': 3,
            'cols': 6,
            'layout_type': 'split'
        },
        'ortho_5x12': {
            'name': 'Ortholinear 5x12',
            'description': '60-key ortholinear layout',
            'rows': 5,
            'cols': 12,
            'layout_type': 'grid'
        }
    }
    
    return jsonify({
        'success': True,
        'presets': presets
    })

@app.route('/api/keyboard/files')
def list_files():
    """List available generated files."""
    try:
        files = []
        output_dir = app.config['OUTPUT_DIR']
        
        for filename in os.listdir(output_dir):
            if filename.endswith(('.scad', '.stl')):
                file_path = os.path.join(output_dir, filename)
                file_info = {
                    'name': filename,
                    'size': os.path.getsize(file_path),
                    'type': filename.split('.')[-1].upper(),
                    'created': os.path.getctime(file_path)
                }
                files.append(file_info)
        
        return jsonify({
            'success': True,
            'files': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def generate_layout_data(config):
    """Generate 2D layout data for preview."""
    rows = config.get('rows', 5)
    cols = config.get('cols', 5)
    switch_size = 18.5  # Standard key size
    
    layout = []
    for row in range(rows):
        row_data = []
        for col in range(cols):
            key = {
                'x': col * switch_size,
                'y': row * switch_size,
                'width': switch_size,
                'height': switch_size,
                'label': f'R{row}C{col}'
            }
            row_data.append(key)
        layout.append(row_data)
    
    return layout

def build_keyboard_config(config):
    """Build keyboard configuration from user input."""
    rows = config.get('rows', 5)
    cols = config.get('cols', 5)
    name = config.get('name', 'custom_keyboard')
    
    # Create basic matrix
    x = "switch"
    matrix_keys = [[x] * cols for _ in range(rows)]
    
    # Build keyboard layout
    layout = {
        "name": name,
        "controller_placement": ("left", "top"),
        "matrixes": {
            "main": {
                "offset": (0, 0),
                "keys": matrix_keys,
            }
        },
        "switch": switch,
        "empty_switch": kb.empty_sw(switch),
        "controller": controller
    }
    
    # Add variable key sizes
    for i in range(0, 7):
        for num in [0, 0.25, 0.5, 0.75]:
            total_i = i + num
            if int(total_i) == total_i:
                total_i = int(total_i)
            layout[f"{total_i}u"] = kb.empty_sw(switch, body=switch.switch_body, pins=switch.pins, x=18.5*total_i)
    
    return layout

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)