import pytest
import json
import os
import tempfile
from app import app

@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    app.config['OUTPUT_DIR'] = tempfile.mkdtemp()
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Test the main page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Printboard Research' in response.data

def test_keyboard_preview_api(client):
    """Test keyboard preview API."""
    config = {
        'name': 'test_keyboard',
        'rows': 3,
        'cols': 4
    }
    
    response = client.post('/api/keyboard/preview',
                          data=json.dumps(config),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'layout' in data
    assert len(data['layout']) == 3  # 3 rows
    assert len(data['layout'][0]) == 4  # 4 columns

def test_keyboard_generation_api(client):
    """Test keyboard 3D model generation API."""
    config = {
        'name': 'test_keyboard',
        'rows': 2,
        'cols': 2
    }
    
    response = client.post('/api/keyboard/generate',
                          data=json.dumps(config),
                          content_type='application/json')
    
    # Debug the response if it fails
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'scad_files' in data
    assert len(data['scad_files']) > 0

def test_stl_generation_status_reporting(client):
    """Test that STL generation status is properly reported."""
    config = {
        'name': 'stl_test_keyboard',
        'rows': 2, 
        'cols': 2
    }
    
    response = client.post('/api/keyboard/generate',
                          data=json.dumps(config),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Verify response structure includes STL status
    assert 'scad_files' in data
    assert 'stl_files' in data
    assert 'message' in data
    
    # Verify that message indicates STL generation status
    # Since OpenSCAD is not available in test environment, STL files should be empty
    # and message should indicate STL generation requires OpenSCAD
    assert len(data['scad_files']) > 0
    assert len(data['stl_files']) == 0  # No STL files when OpenSCAD not available
    assert 'OpenSCAD' in data['message']  # Message should mention OpenSCAD requirement
    
def test_stl_generation_success_display(client):
    """Test that successful STL generation is properly displayed in frontend logic."""
    # Simulate what the frontend logic would do with successful STL generation
    
    # Mock response with successful STL generation
    mock_result = {
        'success': True,
        'scad_files': ['test_keyboard_matrix.scad'],
        'stl_files': ['test_keyboard_matrix.stl'],
        'message': 'Generated 1 SCAD files and 1 STL files successfully'
    }
    
    # Test the frontend logic that determines STL status message
    stl_status_message = None
    if len(mock_result['stl_files']) > 0:
        stl_status_message = f"STL Files: {', '.join(mock_result['stl_files'])}"
    else:
        if 'requires OpenSCAD' in mock_result['message']:
            stl_status_message = "STL Generation: Failed - OpenSCAD not available"
        else:
            stl_status_message = "STL Generation: Skipped"
    
    # Verify the logic works correctly for success case
    assert stl_status_message == "STL Files: test_keyboard_matrix.stl"
    
    # Test the failure case logic too
    mock_failure_result = {
        'success': True,
        'scad_files': ['test_keyboard_matrix.scad'],
        'stl_files': [],
        'message': 'Generated 1 SCAD files (STL generation requires OpenSCAD)'
    }
    
    stl_status_message_failure = None
    if len(mock_failure_result['stl_files']) > 0:
        stl_status_message_failure = f"STL Files: {', '.join(mock_failure_result['stl_files'])}"
    else:
        if 'requires OpenSCAD' in mock_failure_result['message']:
            stl_status_message_failure = "STL Generation: Failed - OpenSCAD not available"
        else:
            stl_status_message_failure = "STL Generation: Skipped"
    
    # Verify the logic works correctly for failure case
    assert stl_status_message_failure == "STL Generation: Failed - OpenSCAD not available"

def test_files_list_api(client):
    """Test files listing API."""
    response = client.get('/api/keyboard/files')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'files' in data

def test_invalid_preview_config(client):
    """Test preview API with invalid configuration."""
    config = {
        'rows': 'invalid',
        'cols': 4
    }
    
    response = client.post('/api/keyboard/preview',
                          data=json.dumps(config),
                          content_type='application/json')
    
    # Should handle gracefully, might succeed with default values
    assert response.status_code in [200, 400]

def test_presets_api(client):
    """Test keyboard presets API."""
    response = client.get('/api/keyboard/presets')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'presets' in data
    assert 'basic_5x5' in data['presets']
    assert data['presets']['basic_5x5']['rows'] == 5
    assert data['presets']['basic_5x5']['cols'] == 5