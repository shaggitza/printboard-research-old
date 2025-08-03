"""
Tests for Printboard V2 API

Tests the new clean architecture and builder pattern.
"""

import pytest
from libs.printboard_v2 import (
    KeyboardBuilder, LayoutPlanner, SwitchRegistry, ControllerRegistry,
    KeyboardConfig, MatrixConfig
)
from libs.printboard_v2.builder import keyboard_builder
from libs.printboard_v2.switches import switch_registry
from libs.printboard_v2.controllers import controller_registry


class TestV2Config:
    """Test configuration classes."""
    
    def test_matrix_config_creation(self):
        """Test creating a matrix configuration."""
        config = MatrixConfig(rows=5, cols=5)
        assert config.rows == 5
        assert config.cols == 5
        assert config.offset == (0.0, 0.0)
        assert config.rotation_angle == 0.0
    
    def test_matrix_config_with_advanced_params(self):
        """Test matrix config with staggering and angles."""
        config = MatrixConfig(
            rows=3,
            cols=4,
            offset=(10.0, 20.0),
            rows_stagger=[0, 5, 10],
            columns_stagger=[0, 2, 4, 6],
            rows_angle=[0, 5, -5],
            rotation_angle=15.0
        )
        
        assert config.rows == 3
        assert config.cols == 4
        assert config.offset == (10.0, 20.0)
        assert config.rows_stagger == [0, 5, 10]
        assert config.columns_stagger == [0, 2, 4, 6]
        assert config.rows_angle == [0, 5, -5]
        assert config.rotation_angle == 15.0
    
    def test_matrix_config_validation(self):
        """Test matrix config validation."""
        # Invalid rows/cols
        with pytest.raises(ValueError):
            MatrixConfig(rows=0, cols=5)
        
        with pytest.raises(ValueError):
            MatrixConfig(rows=5, cols=-1)
        
        # Invalid stagger length
        with pytest.raises(ValueError):
            MatrixConfig(rows=3, cols=3, rows_stagger=[0, 5])  # Should have 3 elements
    
    def test_keyboard_config_creation(self):
        """Test creating a keyboard configuration."""
        matrix = MatrixConfig(rows=5, cols=5)
        config = KeyboardConfig(
            name="test_keyboard",
            matrices={"main": matrix}
        )
        
        assert config.name == "test_keyboard"
        assert config.switch_type == "gamdias_lp"
        assert config.controller_type == "tinys2"
        assert "main" in config.matrices
        assert config.matrices["main"].rows == 5
    
    def test_keyboard_config_with_matrix(self):
        """Test adding matrices to keyboard config."""
        matrix1 = MatrixConfig(rows=5, cols=5)
        matrix2 = MatrixConfig(rows=3, cols=6, offset=(50, 70))
        
        config = KeyboardConfig(name="split_keyboard", matrices={"main": matrix1})
        config_with_thumb = config.with_matrix("thumb", matrix2)
        
        assert len(config.matrices) == 1
        assert len(config_with_thumb.matrices) == 2
        assert "thumb" in config_with_thumb.matrices
        assert config_with_thumb.matrices["thumb"].offset == (50, 70)


class TestV2Registries:
    """Test switch and controller registries."""
    
    def test_switch_registry(self):
        """Test switch registry functionality."""
        assert switch_registry.is_registered("gamdias_lp")
        assert "gamdias_lp" in switch_registry.list_switches()
        
        switch = switch_registry.get("gamdias_lp")
        assert switch.name == "gamdias_lp"
        assert switch.specs.body_size == (14.5, 14.5, 8.0)
        assert len(switch.specs.pins) == 2
    
    def test_controller_registry(self):
        """Test controller registry functionality."""
        assert controller_registry.is_registered("tinys2")
        assert "tinys2" in controller_registry.list_controllers()
        
        controller = controller_registry.get("tinys2")
        assert controller.name == "tinys2"
        assert controller.specs.pin_pitch == 2.54
        assert len(controller.specs.usable_pins) > 0
    
    def test_registry_unknown_component(self):
        """Test handling of unknown components."""
        with pytest.raises(ValueError):
            switch_registry.get("unknown_switch")
        
        with pytest.raises(ValueError):
            controller_registry.get("unknown_controller")


class TestV2LayoutPlanner:
    """Test layout planning functionality."""
    
    def test_layout_planner_creation(self):
        """Test creating a layout planner."""
        switch = switch_registry.get("gamdias_lp")
        planner = LayoutPlanner(switch)
        assert planner.key_size == 18.5
    
    def test_simple_layout_planning(self):
        """Test planning a simple 3x3 layout."""
        switch = switch_registry.get("gamdias_lp")
        planner = LayoutPlanner(switch)
        
        matrix_config = MatrixConfig(rows=3, cols=3)
        config = KeyboardConfig(name="test", matrices={"main": matrix_config})
        
        layout_plan = planner.plan_layout(config)
        
        assert len(layout_plan.keys) == 9  # 3x3 = 9 keys
        assert "main" in layout_plan.matrices
        
        # Check key positions
        keys = layout_plan.get_keys_for_matrix("main")
        assert len(keys) == 9
        
        # Check first key (0,0)
        first_key = next(k for k in keys if k.row == 0 and k.col == 0)
        assert first_key.x == 0
        assert first_key.y == 0
        assert first_key.label == "R0C0"
    
    def test_layout_with_staggering(self):
        """Test layout planning with staggering."""
        switch = switch_registry.get("gamdias_lp")
        planner = LayoutPlanner(switch)
        
        matrix_config = MatrixConfig(
            rows=2, 
            cols=2,
            rows_stagger=[0, 5],
            columns_stagger=[0, 3]
        )
        config = KeyboardConfig(name="staggered", matrices={"main": matrix_config})
        
        layout_plan = planner.plan_layout(config)
        keys = layout_plan.get_keys_for_matrix("main")
        
        # Check staggering is applied
        key_r1c0 = next(k for k in keys if k.row == 1 and k.col == 0)
        key_r0c1 = next(k for k in keys if k.row == 0 and k.col == 1)
        
        assert key_r1c0.x == -5  # Row 1 staggered by 5
        assert key_r0c1.y == -3  # Column 1 staggered by 3
    
    def test_generate_preview_data(self):
        """Test generating preview data for UI."""
        switch = switch_registry.get("gamdias_lp")
        planner = LayoutPlanner(switch)
        
        matrix_config = MatrixConfig(rows=2, cols=3)
        config = KeyboardConfig(name="preview_test", matrices={"main": matrix_config})
        
        preview_data = planner.generate_preview_data(config)
        
        assert len(preview_data) == 2  # 2 rows
        assert len(preview_data[0]) == 3  # 3 columns in first row
        assert len(preview_data[1]) == 3  # 3 columns in second row
        
        # Check preview data structure
        first_key = preview_data[0][0]
        assert 'x' in first_key
        assert 'y' in first_key
        assert 'width' in first_key
        assert 'height' in first_key
        assert 'angle' in first_key
        assert 'label' in first_key


class TestV2Builder:
    """Test keyboard builder functionality."""
    
    def test_builder_creation(self):
        """Test creating a keyboard builder."""
        builder = KeyboardBuilder()
        assert builder.switch_registry is not None
        assert builder.controller_registry is not None
    
    def test_simple_keyboard_creation(self):
        """Test creating a simple keyboard."""
        result = keyboard_builder.create_simple_keyboard(
            name="test_simple",
            rows=3,
            cols=3
        )
        
        assert result.config.name == "test_simple"
        assert result.config.switch_type == "gamdias_lp"
        assert result.config.controller_type == "tinys2"
        assert len(result.layout_plan.keys) == 9
        assert len(result.parts) > 0
        assert result.metadata["total_keys"] == 9
    
    def test_build_keyboard_from_config(self):
        """Test building keyboard from configuration."""
        matrix_config = MatrixConfig(rows=4, cols=4)
        config = KeyboardConfig(
            name="config_test",
            switch_type="gamdias_lp",
            controller_type="tinys2",
            matrices={"main": matrix_config}
        )
        
        result = keyboard_builder.build_keyboard(config)
        
        assert result.config == config
        assert len(result.layout_plan.keys) == 16
        assert result.metadata["total_keys"] == 16
        assert result.metadata["switch_type"] == "gamdias_lp"
    
    def test_config_from_web_request(self):
        """Test creating config from web request data."""
        request_data = {
            'name': 'web_keyboard',
            'rows': 5,
            'cols': 6,
            'switchType': 'gamdias_lp',
            'controllerType': 'tinys2',
            'controllerPlacementLR': 'right',
            'controllerPlacementTB': 'bottom',
            'matrixOffsetX': 10,
            'matrixOffsetY': 20,
            'rowsStagger': [0, 2, 4, 6, 8],
            'rotationAngle': 15
        }
        
        config = keyboard_builder.create_config_from_web_request(request_data)
        
        assert config.name == 'web_keyboard'
        assert config.switch_type == 'gamdias_lp'
        assert config.controller_type == 'tinys2'
        assert config.controller_placement == ('right', 'bottom')
        
        main_matrix = config.matrices['main']
        assert main_matrix.rows == 5
        assert main_matrix.cols == 6
        assert main_matrix.offset == (10, 20)
        assert main_matrix.rows_stagger == [0, 2, 4, 6, 8]
        assert main_matrix.rotation_angle == 15
    
    def test_generate_preview(self):
        """Test generating preview using builder."""
        matrix_config = MatrixConfig(rows=2, cols=2)
        config = KeyboardConfig(name="preview", matrices={"main": matrix_config})
        
        preview_data = keyboard_builder.generate_preview(config)
        
        assert len(preview_data) == 2
        assert len(preview_data[0]) == 2
        assert len(preview_data[1]) == 2
    
    def test_list_components(self):
        """Test listing available components."""
        switches = keyboard_builder.list_available_switches()
        controllers = keyboard_builder.list_available_controllers()
        
        assert "gamdias_lp" in switches
        assert "tinys2" in controllers
        assert len(switches) >= 1
        assert len(controllers) >= 1


class TestV2LegacyCompatibility:
    """Test backward compatibility with V1 API."""
    
    def test_config_to_legacy_format(self):
        """Test converting V2 config to legacy format."""
        matrix_config = MatrixConfig(
            rows=3,
            cols=3,
            rows_stagger=[0, 2, 4],
            rotation_angle=10
        )
        config = KeyboardConfig(
            name="legacy_test",
            switch_type="gamdias_lp",
            controller_type="tinys2",
            matrices={"main": matrix_config}
        )
        
        legacy_format = config.to_legacy_format()
        
        assert legacy_format["name"] == "legacy_test"
        assert "matrixes" in legacy_format
        assert "main" in legacy_format["matrixes"]
        
        main_matrix = legacy_format["matrixes"]["main"]
        assert main_matrix["keys"] == [["switch"] * 3] * 3
        assert main_matrix["rows_stagger"] == [0, 2, 4]
        assert main_matrix["rotation_angle"] == 10
        
        # Check variable key sizes are included
        assert "1u" in legacy_format
        assert "1.5u" in legacy_format
        assert "2u" in legacy_format