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