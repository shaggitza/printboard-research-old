from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import subprocess
import tempfile
import datetime
import uuid
from libs import printboard as kb
from libs.switches import gamdias_lp as switch
from libs.controllers import tinys2 as controller
from solid import scad_render_to_file

# Import V2 API
from libs.printboard_v2 import KeyboardBuilder, KeyboardConfig, MatrixConfig
from libs.printboard_v2.builder import keyboard_builder
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

def generate_unique_keyboard_name(base_name: str = "keyboard") -> str:
    """Generate a unique keyboard name with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"{base_name}_{timestamp}_{short_uuid}"

@app.route('/')
def index():
    """Main page with keyboard designer interface."""
    from flask import make_response
    import time
    response = make_response(render_template('index.html', cache_bust=int(time.time())))
    # Add cache-busting headers to prevent browser caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/health')
def health_check():
    """Health check endpoint for Docker."""
    return jsonify({
        'status': 'healthy',
        'openscad_available': subprocess.run(['which', 'openscad'], capture_output=True).returncode == 0
    })





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



# V2 API Endpoints

@app.route('/api/v2/keyboard/preview', methods=['POST'])
def preview_keyboard_v2():
    """Generate 2D preview using V2 API."""
    try:
        request_data = request.get_json()
        
        # Create configuration using V2 API
        config = keyboard_builder.create_config_from_web_request(request_data)
        
        # Generate preview with routing data
        preview_data = keyboard_builder.generate_preview(config)
        
        return jsonify({
            'success': True,
            'layout': preview_data['layout'],
            'routing': preview_data['routing'],
            'message': 'V2 Preview generated successfully',
            'api_version': '2.0'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'api_version': '2.0'
        }), 400

@app.route('/api/v2/keyboard/generate', methods=['POST'])  
def generate_keyboard_v2():
    """Generate 3D model using V2 API."""
    try:
        request_data = request.get_json()
        
        # Create configuration using V2 API
        config = keyboard_builder.create_config_from_web_request(request_data)
        
        # Build keyboard
        result = keyboard_builder.build_keyboard(config)
        
        # Generate files (same file generation as V1 for compatibility)
        scad_files = []
        stl_files = []
        
        for part in result.parts:
            # Generate SCAD
            filename = f"{config.name}_{part.name}"
            scad_file = os.path.join(app.config['OUTPUT_DIR'], f'{filename}.scad')
            scad_render_to_file(part.shape, scad_file, file_header='$fn = 50;')
            scad_files.append(f'{filename}.scad')
            
            # Generate STL if OpenSCAD is available
            stl_file = os.path.join(app.config['OUTPUT_DIR'], f'{filename}.stl')
            try:
                # Use Xvfb for headless OpenSCAD rendering in Docker
                subprocess_result = subprocess.run([
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
        success_msg = f'V2 API: Generated {len(scad_files)} SCAD files'
        if stl_files:
            success_msg += f' and {len(stl_files)} STL files successfully'
        else:
            success_msg += ' (STL generation requires OpenSCAD)'
        
        # Create file information with action buttons
        files_with_actions = []
        for scad_file in scad_files:
            files_with_actions.append({
                'name': scad_file,
                'type': 'scad',
                'download_url': f'/api/keyboard/download/{scad_file}',
                'action_label': 'Download SCAD'
            })
        for stl_file in stl_files:
            files_with_actions.append({
                'name': stl_file,
                'type': 'stl', 
                'download_url': f'/api/keyboard/download/{stl_file}',
                'action_label': 'Open STL'
            })
        
        return jsonify({
            'success': True,
            'scad_files': scad_files,
            'stl_files': stl_files,
            'files_with_actions': files_with_actions,
            'keyboard_name': config.name,
            'message': success_msg,
            'api_version': '2.0',
            'metadata': result.metadata
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'api_version': '2.0'
        }), 400

@app.route('/api/v2/components/switches')
def list_switches_v2():
    """List available switch types in V2 API."""
    try:
        switches = keyboard_builder.list_available_switches()
        return jsonify({
            'success': True,
            'switches': switches,
            'api_version': '2.0'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'api_version': '2.0'
        }), 400

@app.route('/api/v2/components/controllers')
def list_controllers_v2():
    """List available controller types in V2 API."""
    try:
        controllers = keyboard_builder.list_available_controllers()
        return jsonify({
            'success': True,
            'controllers': controllers,
            'api_version': '2.0'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'api_version': '2.0'
        }), 400

@app.route('/api/v2/keyboard/simple', methods=['POST'])
def create_simple_keyboard_v2():
    """Create a simple keyboard with V2 API - demonstrating builder pattern."""
    try:
        request_data = request.get_json()
        
        name = request_data.get('name', 'simple_keyboard')
        rows = request_data.get('rows', 5)
        cols = request_data.get('cols', 5)
        switch_type = request_data.get('switch_type', 'gamdias_lp')
        controller_type = request_data.get('controller_type', 'tinys2')
        
        # Use the clean builder interface
        result = keyboard_builder.create_simple_keyboard(
            name=name,
            rows=rows,
            cols=cols,
            switch_type=switch_type,
            controller_type=controller_type
        )
        
        return jsonify({
            'success': True,
            'message': f'Simple keyboard "{name}" created successfully',
            'api_version': '2.0',
            'config': {
                'name': result.config.name,
                'switch_type': result.config.switch_type,
                'controller_type': result.config.controller_type,
                'matrices': {k: {'rows': v.rows, 'cols': v.cols} 
                           for k, v in result.config.matrices.items()}
            },
            'metadata': result.metadata
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'api_version': '2.0'
        }), 400

@app.route('/api/keyboard/files')
def list_files():
    """List available generated files organized by generation."""
    try:
        output_dir = app.config['OUTPUT_DIR']
        generations = {}
        
        for filename in os.listdir(output_dir):
            if filename.endswith(('.scad', '.stl')):
                file_path = os.path.join(output_dir, filename)
                
                # Extract keyboard name (everything before the last _part.ext)
                # Format: keyboard_YYYYMMDD_HHMMSS_uuid_part.ext
                name_parts = filename.rsplit('_', 1)  # Split off the part.ext
                if len(name_parts) == 2:
                    base_name = name_parts[0]  # keyboard_YYYYMMDD_HHMMSS_uuid
                    part_and_ext = name_parts[1]  # part.ext
                    
                    # Extract the keyboard generation name (without the part)
                    keyboard_base = '_'.join(base_name.split('_')[:-1])  # Remove the part name
                    if not keyboard_base:
                        keyboard_base = base_name  # Fallback if parsing fails
                else:
                    keyboard_base = filename.split('.')[0]  # Fallback for unexpected format
                
                # Create generation info if not exists
                if keyboard_base not in generations:
                    generations[keyboard_base] = {
                        'name': keyboard_base,
                        'files': [],
                        'created': os.path.getctime(file_path),
                        'total_size': 0
                    }
                
                # Add file to generation
                file_info = {
                    'name': filename,
                    'size': os.path.getsize(file_path),
                    'type': filename.split('.')[-1].upper(),
                    'created': os.path.getctime(file_path)
                }
                generations[keyboard_base]['files'].append(file_info)
                generations[keyboard_base]['total_size'] += file_info['size']
                
                # Update generation creation time to be the earliest file
                if file_info['created'] < generations[keyboard_base]['created']:
                    generations[keyboard_base]['created'] = file_info['created']
        
        # Convert to list and sort by creation time (most recent first)
        generations_list = list(generations.values())
        generations_list.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'generations': generations_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400





if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    app.run(debug=True, host='0.0.0.0', port=port)