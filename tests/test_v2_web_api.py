"""
Tests for V2 Web API endpoints

Tests the new V2 API endpoints alongside existing V1 endpoints.
"""

import pytest
import json
import os
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


class TestV2WebAPI:
    """Test V2 web API endpoints."""
    
    def test_v2_preview_api(self, client):
        """Test V2 preview endpoint."""
        config = {
            'name': 'v2_test',
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
        assert len(data['layout']) == 3  # 3 rows
        assert len(data['layout'][0]) == 3  # 3 cols in first row
    
    def test_v2_preview_with_advanced_params(self, client):
        """Test V2 preview with advanced parameters."""
        config = {
            'name': 'v2_advanced',
            'rows': 2,
            'cols': 4,
            'rowsStagger': [0, 5],
            'columnsStagger': [0, 2, 4, 6],
            'rotationAngle': 15,
            'matrixOffsetX': 10,
            'matrixOffsetY': 20
        }
        
        response = client.post('/api/v2/keyboard/preview',
                             data=json.dumps(config),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['api_version'] == '2.0'
        assert 'layout' in data
        
        # Check that staggering is applied
        first_row = data['layout'][0]
        second_row = data['layout'][1]
        
        # Row staggering should affect x positions
        assert first_row[0]['x'] != second_row[0]['x']
    
    def test_v2_generation_api(self, client):
        """Test V2 generation endpoint."""
        config = {
            'name': 'v2_generation',
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
        assert 'scad_files' in data
        assert 'metadata' in data
        assert len(data['scad_files']) > 0
        
        # Check metadata
        metadata = data['metadata']
        assert metadata['switch_type'] == 'gamdias_lp'
        assert metadata['controller_type'] == 'tinys2'
        assert metadata['total_keys'] == 4
    
    def test_v2_list_switches(self, client):
        """Test V2 switches listing endpoint."""
        response = client.get('/api/v2/components/switches')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['api_version'] == '2.0'
        assert 'switches' in data
        assert 'gamdias_lp' in data['switches']
    
    def test_v2_list_controllers(self, client):
        """Test V2 controllers listing endpoint."""
        response = client.get('/api/v2/components/controllers')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['api_version'] == '2.0'
        assert 'controllers' in data
        assert 'tinys2' in data['controllers']
    
    def test_v2_simple_keyboard_api(self, client):
        """Test V2 simple keyboard creation endpoint."""
        config = {
            'name': 'simple_v2',
            'rows': 4,
            'cols': 4,
            'switch_type': 'gamdias_lp',
            'controller_type': 'tinys2'
        }
        
        response = client.post('/api/v2/keyboard/simple',
                             data=json.dumps(config),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['api_version'] == '2.0'
        assert 'config' in data
        assert 'metadata' in data
        
        # Check returned config
        returned_config = data['config']
        assert returned_config['name'] == 'simple_v2'
        assert returned_config['switch_type'] == 'gamdias_lp'
        assert returned_config['controller_type'] == 'tinys2'
        assert 'main' in returned_config['matrices']
        assert returned_config['matrices']['main']['rows'] == 4
        assert returned_config['matrices']['main']['cols'] == 4
    
    def test_v2_api_error_handling(self, client):
        """Test V2 API error handling."""
        # Invalid configuration
        config = {
            'name': '',  # Empty name should cause error
            'rows': 0,   # Invalid rows
            'cols': 5
        }
        
        response = client.post('/api/v2/keyboard/preview',
                             data=json.dumps(config),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['api_version'] == '2.0'
        assert 'error' in data
    
    def test_v2_and_v1_compatibility(self, client):
        """Test that V2 API doesn't break V1 API."""
        # Test V1 API still works
        config = {
            'name': 'v1_test',
            'rows': 3,
            'cols': 3
        }
        
        v1_response = client.post('/api/keyboard/preview',
                                data=json.dumps(config),
                                content_type='application/json')
        
        assert v1_response.status_code == 200
        v1_data = json.loads(v1_response.data)
        assert v1_data['success'] is True
        assert 'api_version' not in v1_data  # V1 doesn't have version
        
        # Test V2 API works
        v2_response = client.post('/api/v2/keyboard/preview',
                                data=json.dumps(config),
                                content_type='application/json')
        
        assert v2_response.status_code == 200
        v2_data = json.loads(v2_response.data)
        assert v2_data['success'] is True
        assert v2_data['api_version'] == '2.0'
        
        # Both should generate similar layouts for same input
        assert len(v1_data['layout']) == len(v2_data['layout'])
    
    def test_v2_preview_vs_v1_preview(self, client):
        """Test that V2 preview produces equivalent results to V1."""
        config = {
            'name': 'comparison_test',
            'rows': 3,
            'cols': 4,
            'rowsStagger': [0, 3, 6],
            'columnsStagger': [0, 1, 2, 3],
            'rotationAngle': 0,  # No rotation for easier comparison
            'matrixOffsetX': 0,
            'matrixOffsetY': 0
        }
        
        # Get V1 response
        v1_response = client.post('/api/keyboard/preview',
                                data=json.dumps(config),
                                content_type='application/json')
        v1_data = json.loads(v1_response.data)
        
        # Get V2 response
        v2_response = client.post('/api/v2/keyboard/preview',
                                data=json.dumps(config),
                                content_type='application/json')
        v2_data = json.loads(v2_response.data)
        
        assert v1_response.status_code == 200
        assert v2_response.status_code == 200
        
        # Both should have same number of rows/cols
        assert len(v1_data['layout']) == len(v2_data['layout'])
        assert len(v1_data['layout'][0]) == len(v2_data['layout'][0])
        
        # Key positions should be approximately the same
        for row_idx in range(len(v1_data['layout'])):
            for col_idx in range(len(v1_data['layout'][row_idx])):
                v1_key = v1_data['layout'][row_idx][col_idx]
                v2_key = v2_data['layout'][row_idx][col_idx]
                
                # Positions should be close (allowing for small floating point differences)
                assert abs(v1_key['x'] - v2_key['x']) < 0.1
                assert abs(v1_key['y'] - v2_key['y']) < 0.1
                assert v1_key['width'] == v2_key['width']
                assert v1_key['height'] == v2_key['height']


class TestV2APIIntegration:
    """Integration tests for V2 API."""
    
    def test_full_v2_workflow(self, client):
        """Test complete workflow using V2 API."""
        # 1. List available components
        switches_response = client.get('/api/v2/components/switches')
        controllers_response = client.get('/api/v2/components/controllers')
        
        assert switches_response.status_code == 200
        assert controllers_response.status_code == 200
        
        switches_data = json.loads(switches_response.data)
        controllers_data = json.loads(controllers_response.data)
        
        available_switches = switches_data['switches']
        available_controllers = controllers_data['controllers']
        
        assert len(available_switches) > 0
        assert len(available_controllers) > 0
        
        # 2. Create simple keyboard
        simple_config = {
            'name': 'workflow_test',
            'rows': 3,
            'cols': 3,
            'switch_type': available_switches[0],
            'controller_type': available_controllers[0]
        }
        
        simple_response = client.post('/api/v2/keyboard/simple',
                                    data=json.dumps(simple_config),
                                    content_type='application/json')
        
        assert simple_response.status_code == 200
        simple_data = json.loads(simple_response.data)
        assert simple_data['success'] is True
        
        # 3. Generate preview
        preview_config = {
            'name': 'workflow_preview',
            'rows': 3,
            'cols': 3,
            'switchType': available_switches[0],
            'controllerType': available_controllers[0]
        }
        
        preview_response = client.post('/api/v2/keyboard/preview',
                                     data=json.dumps(preview_config),
                                     content_type='application/json')
        
        assert preview_response.status_code == 200
        preview_data = json.loads(preview_response.data)
        assert preview_data['success'] is True
        assert len(preview_data['layout']) == 3
        
        # 4. Generate 3D model
        generate_response = client.post('/api/v2/keyboard/generate',
                                      data=json.dumps(preview_config),
                                      content_type='application/json')
        
        assert generate_response.status_code == 200
        generate_data = json.loads(generate_response.data)
        assert generate_data['success'] is True
        assert len(generate_data['scad_files']) > 0
        assert 'metadata' in generate_data
    
    def test_v2_api_backwards_compatibility_integration(self, client):
        """Test that V2 and V1 APIs can be used interchangeably."""
        config = {
            'name': 'compatibility_test',
            'rows': 4,
            'cols': 5,
            'rowsStagger': [0, 2, 4, 6],
            'rotationAngle': 10
        }
        
        # Generate with V1
        v1_gen_response = client.post('/api/keyboard/generate',
                                    data=json.dumps(config),
                                    content_type='application/json')
        
        # Generate with V2
        v2_gen_response = client.post('/api/v2/keyboard/generate',
                                    data=json.dumps(config),
                                    content_type='application/json')
        
        assert v1_gen_response.status_code == 200
        assert v2_gen_response.status_code == 200
        
        v1_data = json.loads(v1_gen_response.data)
        v2_data = json.loads(v2_gen_response.data)
        
        # Both should succeed
        assert v1_data['success'] is True
        assert v2_data['success'] is True
        
        # Both should generate files
        assert len(v1_data['scad_files']) > 0
        assert len(v2_data['scad_files']) > 0
        
        # V2 should have additional metadata
        assert 'metadata' in v2_data
        assert 'api_version' in v2_data
        assert v2_data['api_version'] == '2.0'