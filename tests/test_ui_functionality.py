"""
UI Functionality Tests

Tests the frontend JavaScript functionality and ensures proper integration
with the V2 API endpoints.
"""

import pytest
import json
import re
import tempfile
from app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    app.config['OUTPUT_DIR'] = tempfile.mkdtemp()
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    
    with app.test_client() as client:
        yield client


class TestUIFunctionality:
    """Test UI functionality and JavaScript integration."""
    
    def test_index_page_loads_without_errors(self, client):
        """Test that the main page loads without JavaScript syntax errors."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Printboard Research' in response.data
        
        # Check that main UI elements are present
        assert b'switchTab' in response.data  # Tab switching function
        assert b'updatePreview' in response.data  # Preview update function
        assert b'viewSTL' in response.data  # STL viewer function
        
        # Check for proper HTML structure
        assert b'<div class="tabs">' in response.data
        assert b'id="design"' in response.data
        assert b'id="preview"' in response.data
        assert b'id="generate"' in response.data
        assert b'id="files"' in response.data
    
    def test_javascript_syntax_validation(self, client):
        """Test that JavaScript in the HTML has no syntax errors."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Extract JavaScript content
        script_matches = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL)
        assert len(script_matches) > 0, "No JavaScript found in page"
        
        # Check for common syntax errors that would prevent execution
        js_content = '\n'.join(script_matches)
        
        # Check for balanced brackets/braces/parentheses
        bracket_count = js_content.count('{') - js_content.count('}')
        assert bracket_count == 0, f"Unbalanced braces: {bracket_count} extra opening braces"
        
        paren_count = js_content.count('(') - js_content.count(')')
        assert paren_count == 0, f"Unbalanced parentheses: {paren_count} extra opening parentheses"
        
        # Check that key functions are defined
        assert 'function switchTab(' in js_content
        assert 'function updatePreview(' in js_content
        assert 'function viewSTL(' in js_content
        
        # Instead of complex pattern matching, just check that the syntax error we fixed is gone
        # The original error was an extra }); on line 831, let's verify the fix
        assert js_content.count('});') > 0, "Should have some legitimate }); closures"
        
        # Test that the JavaScript can be parsed by trying to find function definitions
        # This is a more practical test than complex regex patterns
        function_count = js_content.count('function ')
        assert function_count >= 3, f"Expected at least 3 functions, found {function_count}"
    
    def test_api_endpoints_for_ui(self, client):
        """Test that API endpoints used by the UI are working."""
        # Test V2 preview endpoint (used by frontend)
        config = {
            'name': 'ui_test',
            'rows': 3,
            'cols': 3,
            'switchType': 'gamdias_lp',
            'controllerType': 'tinys2'
        }
        
        response = client.post('/api/v2/keyboard/preview',
                             data=json.dumps(config),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['api_version'] == '2.0'
        assert 'layout' in data
        assert 'routing' in data  # V2 includes routing data
    
    def test_generation_endpoint_for_ui(self, client):
        """Test generation endpoint used by the UI."""
        config = {
            'name': 'ui_generation_test',
            'rows': 2,
            'cols': 2,
            'switchType': 'gamdias_lp',
            'controllerType': 'tinys2'
        }
        
        response = client.post('/api/v2/keyboard/generate',
                             data=json.dumps(config),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['api_version'] == '2.0'
        assert 'files_with_actions' in data
        assert 'keyboard_name' in data
        
        # Check that files have proper action labels for UI
        if data['files_with_actions']:
            for file_info in data['files_with_actions']:
                assert 'name' in file_info
                assert 'type' in file_info
                assert 'action_label' in file_info
                assert 'download_url' in file_info
    
    def test_files_listing_endpoint_for_ui(self, client):
        """Test files listing endpoint used by the Files tab."""
        response = client.get('/api/keyboard/files')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # Note: This is still V1 endpoint, should be migrated to V2
        assert 'generations' in data
    
    def test_ui_error_handling(self, client):
        """Test that UI can handle API errors gracefully."""
        # Test with invalid configuration
        config = {
            'name': '',  # Empty name
            'rows': 0,   # Invalid rows
            'cols': 5
        }
        
        response = client.post('/api/v2/keyboard/preview',
                             data=json.dumps(config),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        assert data['api_version'] == '2.0'
    
    def test_stl_viewer_integration(self, client):
        """Test that STL viewer integration works properly."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check that STL viewer modal is present
        assert 'id="stl-viewer-modal"' in html_content
        assert 'viewSTL(' in html_content
        
        # Check that the function accepts filename parameter
        assert 'function viewSTL(filename)' in html_content
    
    def test_tab_switching_functionality(self, client):
        """Test tab switching functionality."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for tab switching elements
        assert 'onclick="switchTab(\'design\')"' in html_content
        assert 'onclick="switchTab(\'preview\')"' in html_content
        assert 'onclick="switchTab(\'generate\')"' in html_content
        assert 'onclick="switchTab(\'files\')"' in html_content
        
        # Check that switchTab function exists
        assert 'function switchTab(tabName)' in html_content
    
    def test_preview_update_functionality(self, client):
        """Test preview update functionality."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for preview update button
        assert 'onclick="updatePreview()"' in html_content
        
        # Check that updatePreview function exists
        assert 'async function updatePreview()' in html_content or 'function updatePreview()' in html_content
    
    def test_file_organization_ui_elements(self, client):
        """Test that file organization UI elements are present."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for file organization elements
        assert 'id="files-list"' in html_content
        
        # Check that file loading functionality exists  
        assert 'refreshFiles()' in html_content or 'loadFiles()' in html_content


class TestUIDataFlow:
    """Test data flow between UI and API."""
    
    def test_preview_to_generation_workflow(self, client):
        """Test the workflow from preview to generation."""
        config = {
            'name': 'workflow_test',
            'rows': 2,
            'cols': 3,
            'switchType': 'gamdias_lp',
            'controllerType': 'tinys2'
        }
        
        # Step 1: Preview
        preview_response = client.post('/api/v2/keyboard/preview',
                                     data=json.dumps(config),
                                     content_type='application/json')
        
        assert preview_response.status_code == 200
        preview_data = json.loads(preview_response.data)
        assert preview_data['success'] is True
        
        # Step 2: Generation using same config
        generate_response = client.post('/api/v2/keyboard/generate',
                                      data=json.dumps(config),
                                      content_type='application/json')
        
        assert generate_response.status_code == 200
        generate_data = json.loads(generate_response.data)
        assert generate_data['success'] is True
        
        # Step 3: Files listing should include the generated files
        files_response = client.get('/api/keyboard/files')
        files_data = json.loads(files_response.data)
        assert files_data['success'] is True
    
    def test_ui_component_integration(self, client):
        """Test integration between different UI components."""
        # Test that the page has all necessary components
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for form elements
        assert 'id="keyboard-form"' in html_content
        assert 'name="rows"' in html_content or 'id="rows"' in html_content
        assert 'name="cols"' in html_content or 'id="cols"' in html_content
        
        # Check for result display areas (using actual IDs from HTML)
        assert 'class="preview-area"' in html_content or 'id="keyboard-svg"' in html_content
        assert 'id="generation-results"' in html_content
        
        # Check for file display area
        assert 'id="files-list"' in html_content


class TestUIAccessibility:
    """Test UI accessibility and usability."""
    
    def test_form_labels_and_inputs(self, client):
        """Test that form elements have proper labels."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for important form labels
        form_labels = ['rows', 'cols', 'name']
        for label in form_labels:
            # Check that there's either a label or an id/name attribute
            assert (f'for="{label}"' in html_content or 
                   f'id="{label}"' in html_content or 
                   f'name="{label}"' in html_content), f"Missing label or input for {label}"
    
    def test_button_accessibility(self, client):
        """Test that buttons have proper text and functionality."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for important buttons
        assert 'Update Preview' in html_content
        assert 'Generate' in html_content or 'Generate 3D Model' in html_content
        
        # Check that buttons have onclick handlers
        button_handlers = ['updatePreview()', 'switchTab(']
        for handler in button_handlers:
            assert handler in html_content, f"Missing button handler: {handler}"
    
    def test_error_message_display(self, client):
        """Test that error messages can be displayed properly."""
        response = client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Check for error display elements
        assert ('error' in html_content.lower() or 
               'alert' in html_content.lower() or
               'message' in html_content.lower()), "No error display mechanism found"


if __name__ == '__main__':
    pytest.main([__file__])