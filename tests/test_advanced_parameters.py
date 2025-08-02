"""Test advanced keyboard generation parameters."""
import pytest
from app import app, generate_layout_data, build_keyboard_config


class TestAdvancedParameters:
    """Test the new advanced parameters functionality."""

    def test_generate_layout_data_with_staggering(self):
        """Test that staggering is applied correctly in preview."""
        config = {
            'rows': 3,
            'cols': 3,
            'rowsStagger': [0, 5, 10],
            'columnsStagger': [0, 2, 4]
        }
        
        layout = generate_layout_data(config)
        
        # Check that staggering is applied
        assert layout[0][0]['x'] == 0  # First row, first column - no stagger
        assert layout[1][0]['x'] == -5  # Second row gets -5 offset
        assert layout[2][0]['x'] == -10  # Third row gets -10 offset
        
        assert layout[0][0]['y'] == 0  # First column, first row - no stagger  
        assert layout[0][1]['y'] == -2  # Second column gets -2 offset
        assert layout[0][2]['y'] == -4  # Third column gets -4 offset

    def test_generate_layout_data_with_angles(self):
        """Test that angles are applied correctly in preview."""
        config = {
            'rows': 2,
            'cols': 2,
            'rowsAngle': [0, 5],
            'columnsAngle': [0, 10]
        }
        
        layout = generate_layout_data(config)
        
        # Check that angles are applied
        assert layout[0][0]['angle'] == 0  # No angle
        assert layout[0][1]['angle'] == 10  # Column angle only
        assert layout[1][0]['angle'] == 5  # Row angle only  
        assert layout[1][1]['angle'] == 15  # Both row and column angles

    def test_generate_layout_data_with_rotation(self):
        """Test that matrix rotation is applied correctly."""
        config = {
            'rows': 2,
            'cols': 2,
            'rotationAngle': 90
        }
        
        layout = generate_layout_data(config)
        
        # After 90-degree rotation, (0,0) should become (0,0), (18.5,0) should become (0,18.5)
        # Allow for small floating point differences
        assert abs(layout[0][0]['x'] - 0) < 0.1
        assert abs(layout[0][0]['y'] - 0) < 0.1
        assert abs(layout[0][1]['x'] - 0) < 0.1
        assert abs(layout[0][1]['y'] - 18.5) < 0.1

    def test_build_keyboard_config_with_advanced_params(self):
        """Test that advanced parameters are included in keyboard config."""
        config = {
            'name': 'test_keyboard',
            'rows': 3,
            'cols': 3,
            'controllerPlacementLR': 'right',
            'controllerPlacementTB': 'bottom',
            'matrixOffsetX': 10,
            'matrixOffsetY': 20,
            'rowsAngle': [0, 5, 10],
            'columnsAngle': [0, 0, 15],
            'rowsStagger': [0, 2, 4],
            'columnsStagger': [0, 1, 2],
            'rotationAngle': 30,
            'paddingKeys': [5, 5, 5]
        }
        
        keyboard_config = build_keyboard_config(config)
        
        # Check that basic config is correct
        assert keyboard_config['name'] == 'test_keyboard'
        assert keyboard_config['controller_placement'] == ('right', 'bottom')
        
        # Check matrix configuration
        matrix_config = keyboard_config['matrixes']['main']
        assert matrix_config['offset'] == (10, 20)
        assert matrix_config['rows_angle'] == [0, 5, 10]
        assert matrix_config['columns_angle'] == [0, 0, 15]
        assert matrix_config['rows_stagger'] == [0, 2, 4]
        assert matrix_config['columns_stagger'] == [0, 1, 2]
        assert matrix_config['rotation_angle'] == 30
        assert matrix_config['padding_keys'] == [5, 5, 5]

    def test_preview_api_with_advanced_params(self):
        """Test that the preview API works with advanced parameters."""
        with app.test_client() as client:
            config = {
                'rows': 2,
                'cols': 2,
                'rowsStagger': [0, 5],
                'columnsAngle': [0, 10]
            }
            
            response = client.post('/api/keyboard/preview', json=config)
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            assert 'layout' in data
            
            # Verify the layout has the expected structure
            layout = data['layout']
            assert len(layout) == 2  # 2 rows
            assert len(layout[0]) == 2  # 2 columns
            
            # Check that staggering and angles are applied
            assert layout[1][0]['x'] != layout[0][0]['x']  # Row stagger applied
            assert layout[0][1]['angle'] == 10  # Column angle applied

    def test_empty_params_dont_break_generation(self):
        """Test that empty/missing advanced parameters don't break generation."""
        config = {
            'rows': 2,
            'cols': 2,
            'name': 'simple_keyboard'
        }
        
        # This should not raise any errors
        layout = generate_layout_data(config)
        keyboard_config = build_keyboard_config(config)
        
        # Should generate a basic layout
        assert len(layout) == 2
        assert len(layout[0]) == 2
        assert keyboard_config['name'] == 'simple_keyboard'