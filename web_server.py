#!/usr/bin/env python3
"""
Simple web server for printboard visualization and configuration
"""
import http.server
import socketserver
import json
import os
import sys
import urllib.parse
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class PrintboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.path = '/index.html'
            
        if self.path == '/index.html':
            self.send_keyboard_interface()
        elif self.path == '/api/layouts':
            self.send_layouts_api()
        elif self.path == '/api/generate':
            self.send_generate_api()
        elif self.path.startswith('/output/'):
            # Serve files from output directory
            super().do_GET()
        else:
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/generate':
            self.handle_generate_request()
        else:
            self.send_error(404, "Not Found")
    
    def send_keyboard_interface(self):
        """Send the main keyboard configuration interface"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Printboard Research - Keyboard Generator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .panel {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select, textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #5a6fd8;
        }
        .keyboard-preview {
            border: 1px solid #ddd;
            min-height: 200px;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 4px;
        }
        .key {
            display: inline-block;
            background: #333;
            color: white;
            padding: 8px 12px;
            margin: 2px;
            border-radius: 4px;
            min-width: 30px;
            text-align: center;
        }
        .output-section {
            margin-top: 20px;
        }
        .log {
            background: #1e1e1e;
            color: #0f0;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            min-height: 100px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 Printboard Research</h1>
        <p>Generate custom keyboard PCB layouts and 3D models</p>
    </div>
    
    <div class="container">
        <div class="panel">
            <h2>Configuration</h2>
            <form id="keyboardForm">
                <div class="form-group">
                    <label for="layoutName">Layout Name:</label>
                    <input type="text" id="layoutName" value="custom_keyboard" required>
                </div>
                
                <div class="form-group">
                    <label for="keyboardSize">Keyboard Size:</label>
                    <select id="keyboardSize">
                        <option value="5x5">5×5 Test Layout</option>
                        <option value="65percent">65% Layout</option>
                        <option value="custom">Custom</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="switchType">Switch Type:</label>
                    <select id="switchType">
                        <option value="gamdias_lp">Gamdias Low Profile</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="controllerType">Controller:</label>
                    <select id="controllerType">
                        <option value="tinys2">TinyS2</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="controllerPlacement">Controller Placement:</label>
                    <select id="controllerPlacement">
                        <option value="left,top">Left Top</option>
                        <option value="right,top">Right Top</option>
                        <option value="left,bottom">Left Bottom</option>
                        <option value="right,bottom">Right Bottom</option>
                    </select>
                </div>
                
                <button type="submit">Generate Keyboard</button>
            </form>
        </div>
        
        <div class="panel">
            <h2>Preview</h2>
            <div id="keyboardPreview" class="keyboard-preview">
                <p>Configure your keyboard and click Generate to see preview</p>
            </div>
            
            <div class="output-section">
                <h3>Output Files</h3>
                <div id="outputFiles">
                    <p>No files generated yet</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="panel" style="margin-top: 20px;">
        <h2>Generation Log</h2>
        <div id="log" class="log">Ready to generate keyboards...\n</div>
    </div>
    
    <script>
        function log(message) {
            const logDiv = document.getElementById('log');
            logDiv.innerHTML += new Date().toLocaleTimeString() + ': ' + message + '\\n';
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        function updatePreview(data) {
            const preview = document.getElementById('keyboardPreview');
            const config = data.config;
            let html = `<h4>${config.name}</h4>`;
            
            if (config.matrixes && config.matrixes.main && config.matrixes.main.keys) {
                html += '<div>';
                config.matrixes.main.keys.forEach((row, i) => {
                    html += '<div style="margin: 2px 0;">';
                    row.forEach((key, j) => {
                        html += `<span class="key" title="Row ${i}, Col ${j}">${key}</span>`;
                    });
                    html += '</div>';
                });
                html += '</div>';
            }
            
            preview.innerHTML = html;
        }
        
        function updateOutputFiles(data) {
            const outputDiv = document.getElementById('outputFiles');
            if (data.files && data.files.length > 0) {
                let html = '<ul>';
                data.files.forEach(file => {
                    html += `<li><a href="/output/${file}" target="_blank">${file}</a></li>`;
                });
                html += '</ul>';
                outputDiv.innerHTML = html;
            } else {
                outputDiv.innerHTML = '<p>No files generated</p>';
            }
        }
        
        document.getElementById('keyboardForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const config = {
                name: formData.get('layoutName') || 'custom_keyboard',
                keyboard_size: formData.get('keyboardSize') || '5x5',
                switch_type: formData.get('switchType') || 'gamdias_lp',
                controller_type: formData.get('controllerType') || 'tinys2',
                controller_placement: formData.get('controllerPlacement') || 'left,top'
            };
            
            log('Starting keyboard generation...');
            log('Config: ' + JSON.stringify(config));
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    log('✓ Generation completed successfully!');
                    updatePreview(result);
                    updateOutputFiles(result);
                } else {
                    log('✗ Generation failed: ' + result.error);
                }
            } catch (error) {
                log('✗ Request failed: ' + error.message);
            }
        });
        
        // Load initial data
        log('Printboard Research web interface loaded');
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def send_layouts_api(self):
        """Send available layouts via API"""
        layouts = {
            "5x5": {"name": "5×5 Test", "description": "Simple 5x5 test layout"},
            "65percent": {"name": "65%", "description": "65% compact layout"}
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(layouts).encode())
    
    def handle_generate_request(self):
        """Handle keyboard generation requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            config = json.loads(post_data.decode('utf-8'))
            
            # Generate keyboard with the provided config
            result = self.generate_keyboard(config)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_result).encode())
    
    def generate_keyboard(self, config):
        """Generate keyboard based on configuration"""
        try:
            # Import our mock version if real imports fail
            try:
                from mock_solid import MockSolid, scad_render_to_file
                print("Using mock solid implementation")
            except:
                # Return a simple mock result
                return self.generate_mock_keyboard(config)
            
            # Create a simplified keyboard configuration
            layout_config = self.create_layout_config(config)
            
            # Generate output files
            output_files = []
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Create a simple SCAD file
            scad_filename = f"{config['name']}_matrix.scad"
            scad_path = os.path.join(output_dir, scad_filename)
            
            # Mock generation
            scad_render_to_file(MockSolid.cube([100, 100, 10]), scad_path)
            output_files.append(scad_filename)
            
            # Create a JSON configuration file
            json_filename = f"{config['name']}_config.json"
            json_path = os.path.join(output_dir, json_filename)
            with open(json_path, 'w') as f:
                json.dump(layout_config, f, indent=2)
            output_files.append(json_filename)
            
            return {
                "success": True,
                "config": layout_config,
                "files": output_files,
                "message": "Keyboard generated successfully (mock implementation)"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Generation failed: {str(e)}"}
    
    def generate_mock_keyboard(self, config):
        """Generate a completely mock keyboard for demonstration"""
        layout_config = self.create_layout_config(config)
        
        return {
            "success": True,
            "config": layout_config,
            "files": [],
            "message": "Mock keyboard generated (dependencies not available)"
        }
    
    def create_layout_config(self, config):
        """Create layout configuration from user input"""
        keyboard_size = config.get('keyboard_size', '5x5')
        
        if keyboard_size == '5x5':
            keys = [['x'] * 5 for _ in range(5)]
        elif keyboard_size == '65percent':
            keys = [
                ['x'] * 13 + ['2u'] + ['x'],
                ['1.5u'] + ['x'] * 12 + ['1.5u'] + ['x'],
                ['1.75u'] + ['x'] * 11 + ['2.25u'] + ['x'],
                ['2.25u'] + ['x'] * 10 + ['1.75u'] + ['x'] * 2,
                ['1.25u'] + ['x'] * 3 + ['6.25u'] + ['x'] + ['1.25u'] + ['x'] * 3,
            ]
        else:
            keys = [['x'] * 5 for _ in range(5)]  # default
        
        controller_placement = config.get('controller_placement', 'left,top').split(',')
        
        layout_config = {
            "name": config.get('name', 'custom'),
            "controller_placement": (controller_placement[0], controller_placement[1]),
            "matrixes": {
                "main": {
                    "offset": (0, 0),
                    "keys": keys
                }
            },
            "switch_type": config.get('switch_type', 'gamdias_lp'),
            "controller_type": config.get('controller_type', 'tinys2')
        }
        
        return layout_config

def start_server(port=8080):
    """Start the web server"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", port), PrintboardRequestHandler) as httpd:
        print(f"🌐 Printboard Research server starting on http://localhost:{port}")
        print(f"📁 Serving from: {os.getcwd()}")
        print("🔧 Visit http://localhost:8080 to configure and generate keyboards")
        print("⏹️  Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Printboard Research Web Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to serve on (default: 8080)')
    args = parser.parse_args()
    
    start_server(args.port)