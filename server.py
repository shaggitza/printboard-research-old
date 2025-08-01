"""
Simple web server for keyboard layout generation

Provides a clean, minimal web interface for:
- Configuring keyboard layouts 
- Previewing key positions
- Generating and downloading files
- Testing different configurations
"""

import http.server
import socketserver
import json
import urllib.parse
import os
from printboard import KeyboardGenerator, SwitchLibrary, ControllerLibrary


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Printboard Research - Keyboard Generator</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5; 
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px;
        }
        .content { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .panel { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 500; }
        input, select, textarea { 
            width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;
        }
        button { 
            background: #667eea; color: white; border: none; padding: 12px 24px; 
            border-radius: 4px; cursor: pointer; font-size: 14px; margin-right: 10px;
        }
        button:hover { background: #5a6fd8; }
        .preview { min-height: 200px; border: 1px solid #ddd; border-radius: 4px; padding: 10px; }
        .key { 
            display: inline-block; background: #333; color: white; margin: 2px;
            padding: 8px; border-radius: 3px; font-size: 12px; min-width: 20px; text-align: center;
        }
        .row { margin-bottom: 5px; }
        .log { 
            background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 4px; 
            font-family: 'Courier New', monospace; font-size: 12px; max-height: 200px; overflow-y: auto;
        }
        .downloads { margin-top: 15px; }
        .downloads a { 
            display: inline-block; background: #28a745; color: white; padding: 8px 16px; 
            text-decoration: none; border-radius: 4px; margin-right: 10px; margin-bottom: 5px;
        }
        .downloads a:hover { background: #218838; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Printboard Research</h1>
            <p>Generate custom keyboard PCB layouts and 3D models</p>
        </div>
        
        <div class="content">
            <div class="panel">
                <h2>Configuration</h2>
                <form id="layoutForm">
                    <div class="form-group">
                        <label for="name">Layout Name:</label>
                        <input type="text" id="name" value="custom_keyboard" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="switch_type">Switch Type:</label>
                        <select id="switch_type">
                            <option value="mx_style">MX Style</option>
                            <option value="low_profile">Low Profile</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="controller">Controller:</label>
                        <select id="controller">
                            <option value="arduino_pro_micro">Arduino Pro Micro</option>
                            <option value="tiny_s2">TinyS2</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="layout_preset">Layout Preset:</label>
                        <select id="layout_preset">
                            <option value="3x3">3×3 Test Layout</option>
                            <option value="2x5">2×5 Mini Layout</option>
                            <option value="4x4">4×4 Square Layout</option>
                            <option value="custom">Custom (edit below)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="keys">Key Layout (JSON format):</label>
                        <textarea id="keys" rows="6">
[
  ["key", "key", "key"],
  ["key", "key", "key"],
  ["key", "key", "key"]
]</textarea>
                    </div>
                    
                    <button type="submit">Generate Keyboard</button>
                    <button type="button" onclick="updatePreview()">Preview Layout</button>
                </form>
            </div>
            
            <div class="panel">
                <h2>Preview</h2>
                <div id="preview" class="preview">
                    <div class="row">
                        <span class="key">K</span>
                        <span class="key">K</span>
                        <span class="key">K</span>
                    </div>
                    <div class="row">
                        <span class="key">K</span>
                        <span class="key">K</span>
                        <span class="key">K</span>
                    </div>
                    <div class="row">
                        <span class="key">K</span>
                        <span class="key">K</span>
                        <span class="key">K</span>
                    </div>
                </div>
                
                <div class="downloads" id="downloads" style="display: none;">
                    <h3>Output Files</h3>
                    <a href="#" id="download_scad">Download SCAD</a>
                    <a href="#" id="download_config">Download Config JSON</a>
                </div>
            </div>
        </div>
        
        <div class="panel" style="margin-top: 20px;">
            <h2>Generation Log</h2>
            <div id="log" class="log">Ready to generate keyboards...\n</div>
        </div>
    </div>

    <script>
        const presets = {
            '3x3': [['key', 'key', 'key'], ['key', 'key', 'key'], ['key', 'key', 'key']],
            '2x5': [['key', 'key', 'key', 'key', 'key'], ['key', 'key', 'key', 'key', 'key']],
            '4x4': [['key', 'key', 'key', 'key'], ['key', 'key', 'key', 'key'], ['key', 'key', 'key', 'key'], ['key', 'key', 'key', 'key']]
        };
        
        function updateKeysFromPreset() {
            const preset = document.getElementById('layout_preset').value;
            if (preset !== 'custom' && presets[preset]) {
                document.getElementById('keys').value = JSON.stringify(presets[preset], null, 2);
                updatePreview();
            }
        }
        
        function updatePreview() {
            try {
                const keys = JSON.parse(document.getElementById('keys').value);
                const preview = document.getElementById('preview');
                preview.innerHTML = '';
                
                keys.forEach(row => {
                    const rowDiv = document.createElement('div');
                    rowDiv.className = 'row';
                    row.forEach(key => {
                        if (key && key !== 'empty') {
                            const keySpan = document.createElement('span');
                            keySpan.className = 'key';
                            keySpan.textContent = 'K';
                            rowDiv.appendChild(keySpan);
                        }
                    });
                    preview.appendChild(rowDiv);
                });
            } catch (e) {
                document.getElementById('preview').innerHTML = '<div style="color: red;">Invalid JSON format</div>';
            }
        }
        
        function log(message) {
            const logElement = document.getElementById('log');
            logElement.innerHTML += new Date().toLocaleTimeString() + ': ' + message + '\\n';
            logElement.scrollTop = logElement.scrollHeight;
        }
        
        document.getElementById('layout_preset').addEventListener('change', updateKeysFromPreset);
        document.getElementById('keys').addEventListener('input', updatePreview);
        
        document.getElementById('layoutForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            log('Starting keyboard generation...');
            
            try {
                const keys = JSON.parse(document.getElementById('keys').value);
                
                const config = {
                    name: document.getElementById('name').value,
                    keys: keys,
                    switch_type: document.getElementById('switch_type').value,
                    controller: document.getElementById('controller').value
                };
                
                log(`Generating keyboard "${config.name}"...`);
                
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    log(`✓ Generation completed successfully!`);
                    log(`✓ Generated ${result.key_count} key positions`);
                    log(`✓ Files ready for download`);
                    
                    // Show download links
                    document.getElementById('downloads').style.display = 'block';
                    document.getElementById('download_scad').href = `/download/scad/${config.name}`;
                    document.getElementById('download_config').href = `/download/config/${config.name}`;
                } else {
                    const error = await response.text();
                    log(`✗ Error: ${error}`);
                }
            } catch (error) {
                log(`✗ Error: ${error.message}`);
            }
        });
        
        // Initialize
        updatePreview();
    </script>
</body>
</html>"""


class KeyboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for keyboard generation"""
    
    def __init__(self, *args, **kwargs):
        self.generator = KeyboardGenerator()
        self.generated_files = {}  # Store generated content in memory
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        
        elif self.path.startswith('/download/'):
            self.handle_download()
        
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/generate':
            self.handle_generate()
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_generate(self):
        """Handle keyboard generation request"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            config = json.loads(post_data.decode())
            
            # Generate keyboard
            result = self.generator.generate(config)
            
            # Store generated files in memory
            layout_name = config['name']
            self.generated_files[f"scad_{layout_name}"] = result.scad_content
            self.generated_files[f"config_{layout_name}"] = result.config_content
            
            # Send response
            response_data = {
                "success": True,
                "key_count": len(result.key_positions),
                "layout_name": layout_name
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(e).encode())
    
    def handle_download(self):
        """Handle file download requests"""
        try:
            # Parse download URL: /download/{type}/{name}
            parts = self.path.split('/')
            if len(parts) != 4:
                raise ValueError("Invalid download URL")
            
            file_type = parts[2]  # 'scad' or 'config'
            layout_name = parts[3]
            
            # Get file content
            file_key = f"{file_type}_{layout_name}"
            if file_key not in self.generated_files:
                raise ValueError("File not found")
            
            content = self.generated_files[file_key]
            
            # Determine content type and filename
            if file_type == 'scad':
                content_type = 'text/plain'
                filename = f"{layout_name}.scad"
            elif file_type == 'config':
                content_type = 'application/json'
                filename = f"{layout_name}_config.json"
            else:
                raise ValueError("Invalid file type")
            
            # Send file
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(content.encode())
            
        except Exception as e:
            self.send_error(404, str(e))


def run_server(port=8000):
    """Start the web server"""
    try:
        with socketserver.TCPServer(("", port), KeyboardRequestHandler) as httpd:
            print(f"🌐 Printboard Research web server running at http://localhost:{port}")
            print("📋 Open the URL in your browser to start generating keyboards")
            print("⏹️  Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Try a different port:")
            print(f"   python server.py --port {port + 1}")
        else:
            print(f"❌ Server error: {e}")


if __name__ == "__main__":
    import sys
    
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1] == '--port':
        port = int(sys.argv[2])
    
    run_server(port)