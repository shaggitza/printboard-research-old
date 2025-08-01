"""
Tests for printboard keyboard generator

This module contains comprehensive tests for all components:
- Configuration validation
- Switch and controller libraries  
- Key position calculation
- OpenSCAD generation
- JSON export
- Error handling
"""

import pytest
import json
import tempfile
import os
from printboard import (
    KeyboardGenerator, 
    SwitchLibrary, 
    ControllerLibrary, 
    LayoutValidator,
    KeyPosition,
    SwitchSpec,
    ControllerSpec
)


class TestSwitchLibrary:
    """Test switch library functionality"""
    
    def test_get_valid_switch(self):
        """Test getting a valid switch specification"""
        switch = SwitchLibrary.get_switch("mx_style")
        assert isinstance(switch, SwitchSpec)
        assert switch.name == "mx_style"
        assert switch.body_width > 0
        assert switch.body_height > 0
        assert switch.pin_count > 0
    
    def test_get_invalid_switch(self):
        """Test getting an invalid switch raises error"""
        with pytest.raises(ValueError, match="Unknown switch type"):
            SwitchLibrary.get_switch("nonexistent_switch")
    
    def test_list_switches(self):
        """Test listing available switches"""
        switches = SwitchLibrary.list_switches()
        assert isinstance(switches, list)
        assert len(switches) > 0
        assert "mx_style" in switches
        assert "low_profile" in switches


class TestControllerLibrary:
    """Test controller library functionality"""
    
    def test_get_valid_controller(self):
        """Test getting a valid controller specification"""
        controller = ControllerLibrary.get_controller("arduino_pro_micro")
        assert isinstance(controller, ControllerSpec)
        assert controller.name == "arduino_pro_micro"
        assert controller.width > 0
        assert controller.height > 0
        assert len(controller.usable_pins) > 0
    
    def test_get_invalid_controller(self):
        """Test getting an invalid controller raises error"""
        with pytest.raises(ValueError, match="Unknown controller type"):
            ControllerLibrary.get_controller("nonexistent_controller")
    
    def test_list_controllers(self):
        """Test listing available controllers"""
        controllers = ControllerLibrary.list_controllers()
        assert isinstance(controllers, list)
        assert len(controllers) > 0
        assert "arduino_pro_micro" in controllers
        assert "tiny_s2" in controllers


class TestLayoutValidator:
    """Test layout configuration validation"""
    
    def test_valid_layout(self):
        """Test validation of a valid layout"""
        layout = {
            "name": "test",
            "keys": [["key", "key"], ["key", "key"]],
            "switch_type": "mx_style",
            "controller": "arduino_pro_micro"
        }
        errors = LayoutValidator.validate_layout(layout)
        assert len(errors) == 0
    
    def test_missing_required_fields(self):
        """Test validation catches missing required fields"""
        layout = {"name": "test"}  # Missing keys, switch_type, controller
        errors = LayoutValidator.validate_layout(layout)
        assert len(errors) == 3
        assert any("keys" in error for error in errors)
        assert any("switch_type" in error for error in errors)
        assert any("controller" in error for error in errors)
    
    def test_invalid_switch_type(self):
        """Test validation catches invalid switch type"""
        layout = {
            "name": "test",
            "keys": [["key"]],
            "switch_type": "invalid_switch",
            "controller": "arduino_pro_micro"
        }
        errors = LayoutValidator.validate_layout(layout)
        assert len(errors) == 1
        assert "Unknown switch type" in errors[0]
    
    def test_invalid_controller_type(self):
        """Test validation catches invalid controller type"""
        layout = {
            "name": "test", 
            "keys": [["key"]],
            "switch_type": "mx_style",
            "controller": "invalid_controller"
        }
        errors = LayoutValidator.validate_layout(layout)
        assert len(errors) == 1
        assert "Unknown controller type" in errors[0]
    
    def test_invalid_keys_structure(self):
        """Test validation catches invalid keys structure"""
        # Test non-list keys
        layout = {
            "name": "test",
            "keys": "invalid",
            "switch_type": "mx_style", 
            "controller": "arduino_pro_micro"
        }
        errors = LayoutValidator.validate_layout(layout)
        assert len(errors) == 1
        assert "non-empty list" in errors[0]
        
        # Test inconsistent row lengths
        layout["keys"] = [["key", "key"], ["key"]]  # Different row lengths
        errors = LayoutValidator.validate_layout(layout)
        assert len(errors) == 1
        assert "same number of keys" in errors[0]


class TestKeyboardGenerator:
    """Test keyboard generation functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.generator = KeyboardGenerator()
        self.valid_layout = {
            "name": "test_keyboard",
            "keys": [
                ["key", "key", "key"],
                ["key", "key", "key"]
            ],
            "switch_type": "mx_style",
            "controller": "arduino_pro_micro"
        }
    
    def test_generate_valid_layout(self):
        """Test generating a valid keyboard layout"""
        result = self.generator.generate(self.valid_layout)
        
        # Check result structure
        assert result.layout == self.valid_layout
        assert len(result.key_positions) == 6  # 2 rows × 3 keys
        assert len(result.scad_content) > 0
        assert len(result.config_content) > 0
        
        # Check key positions are reasonable
        for pos in result.key_positions:
            assert isinstance(pos, KeyPosition)
            assert isinstance(pos.x, float)
            assert isinstance(pos.y, float)
            assert pos.row >= 0
            assert pos.col >= 0
    
    def test_generate_invalid_layout(self):
        """Test generating an invalid layout raises error"""
        invalid_layout = {"name": "test"}  # Missing required fields
        
        with pytest.raises(ValueError, match="Invalid layout configuration"):
            self.generator.generate(invalid_layout)
    
    def test_key_position_calculation(self):
        """Test key position calculation"""
        keys = [["key", "key"], ["key", "key"]]  # 2x2 layout
        positions = self.generator._calculate_key_positions(keys)
        
        assert len(positions) == 4
        
        # Check that positions are centered around origin
        x_coords = [pos.x for pos in positions]
        y_coords = [pos.y for pos in positions]
        assert min(x_coords) < 0 and max(x_coords) > 0  # Spans across x=0
        assert min(y_coords) < 0 and max(y_coords) > 0  # Spans across y=0
    
    def test_scad_generation(self):
        """Test OpenSCAD content generation"""
        positions = [
            KeyPosition(0, 0, -10.0, -10.0),
            KeyPosition(0, 1, 10.0, -10.0),
            KeyPosition(1, 0, -10.0, 10.0),
            KeyPosition(1, 1, 10.0, 10.0)
        ]
        
        scad_content = self.generator._generate_scad(self.valid_layout, positions)
        
        # Check essential OpenSCAD elements
        assert "module switch_cutout()" in scad_content
        assert "module keyboard()" in scad_content
        assert "translate([" in scad_content
        assert "cube([" in scad_content
        assert "$fn = 50;" in scad_content
        
        # Check that all positions are included
        for pos in positions:
            assert f"translate([{pos.x}, {pos.y}, 0])" in scad_content
    
    def test_config_json_generation(self):
        """Test configuration JSON generation"""
        positions = [KeyPosition(0, 0, 0.0, 0.0)]
        
        config_content = self.generator._generate_config_json(self.valid_layout, positions)
        
        # Parse JSON to verify structure
        config_data = json.loads(config_content)
        
        assert "layout" in config_data
        assert "generated_positions" in config_data
        assert "switch_spec" in config_data
        assert "controller_spec" in config_data
        
        assert config_data["layout"] == self.valid_layout
        assert len(config_data["generated_positions"]) == 1
        assert config_data["switch_spec"]["name"] == "mx_style"
        assert config_data["controller_spec"]["name"] == "arduino_pro_micro"


class TestKeyboardResult:
    """Test keyboard result functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.generator = KeyboardGenerator()
        self.layout = {
            "name": "test_save",
            "keys": [["key", "key"]],
            "switch_type": "mx_style",
            "controller": "arduino_pro_micro"
        }
        self.result = self.generator.generate(self.layout)
    
    def test_save_scad_file(self):
        """Test saving OpenSCAD file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            scad_path = f.name
        
        try:
            self.result.save_scad(scad_path)
            
            # Verify file was created and has content
            assert os.path.exists(scad_path)
            with open(scad_path, 'r') as f:
                content = f.read()
            assert content == self.result.scad_content
            assert len(content) > 0
        finally:
            os.unlink(scad_path)
    
    def test_save_config_file(self):
        """Test saving configuration JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name
        
        try:
            self.result.save_config(json_path)
            
            # Verify file was created and has valid JSON
            assert os.path.exists(json_path)
            with open(json_path, 'r') as f:
                content = f.read()
            assert content == self.result.config_content
            
            # Verify it's valid JSON
            json.loads(content)
        finally:
            os.unlink(json_path)


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_generation_workflow(self):
        """Test complete keyboard generation workflow"""
        # Define multiple layout types
        layouts = [
            {
                "name": "small_test",
                "keys": [["key", "key"], ["key", "key"]],
                "switch_type": "mx_style",
                "controller": "arduino_pro_micro"
            },
            {
                "name": "single_row", 
                "keys": [["key", "key", "key", "key", "key"]],
                "switch_type": "low_profile",
                "controller": "tiny_s2"
            },
            {
                "name": "large_test",
                "keys": [
                    ["key", "key", "key", "key"],
                    ["key", "key", "key", "key"],
                    ["key", "key", "key", "key"],
                    ["key", "key", "key", "key"]
                ],
                "switch_type": "mx_style",
                "controller": "arduino_pro_micro"
            }
        ]
        
        generator = KeyboardGenerator()
        
        for layout in layouts:
            # Generate keyboard
            result = generator.generate(layout)
            
            # Verify basic structure
            assert result.layout["name"] == layout["name"]
            assert len(result.key_positions) > 0
            assert len(result.scad_content) > 100  # Reasonable content length
            assert len(result.config_content) > 100
            
            # Verify JSON is valid
            config_data = json.loads(result.config_content)
            assert config_data["layout"]["name"] == layout["name"]
            
            # Verify OpenSCAD has essential elements  
            assert "module keyboard()" in result.scad_content
            assert "translate([" in result.scad_content
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        generator = KeyboardGenerator()
        
        # Single key layout
        single_key_layout = {
            "name": "single_key",
            "keys": [["key"]],
            "switch_type": "mx_style",
            "controller": "arduino_pro_micro"
        }
        
        result = generator.generate(single_key_layout)
        assert len(result.key_positions) == 1
        assert result.key_positions[0].x == 0.0  # Should be centered
        assert result.key_positions[0].y == 0.0
        
        # Large layout
        large_layout = {
            "name": "large_layout",
            "keys": [["key"] * 10 for _ in range(8)],  # 8x10 layout
            "switch_type": "low_profile",
            "controller": "tiny_s2"
        }
        
        result = generator.generate(large_layout)
        assert len(result.key_positions) == 80
        
        # Check that positions span appropriate range
        x_coords = [pos.x for pos in result.key_positions]
        y_coords = [pos.y for pos in result.key_positions]
        x_range = max(x_coords) - min(x_coords)
        y_range = max(y_coords) - min(y_coords)
        
        # Should span multiple key spacings
        assert x_range > generator.key_spacing * 5
        assert y_range > generator.key_spacing * 3


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])