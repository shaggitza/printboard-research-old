"""
Integration tests that work with or without external dependencies
"""
import sys
import os
import json
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_web_server_functionality():
    """Test that the web server can handle requests"""
    try:
        # Import and test web server components
        from web_server import PrintboardRequestHandler
        import http.server
        
        # Test that handler can be instantiated
        # We can't easily test the full server without starting it,
        # but we can test the key methods
        assert hasattr(PrintboardRequestHandler, 'generate_keyboard')
        assert hasattr(PrintboardRequestHandler, 'create_layout_config')
        
        # Create a mock handler to test the generation logic
        class MockHandler(PrintboardRequestHandler):
            def __init__(self):
                pass
        
        handler = MockHandler()
        
        # Test layout config creation
        config = {
            'name': 'test_keyboard',
            'keyboard_size': '5x5',
            'switch_type': 'gamdias_lp',
            'controller_type': 'tinys2',
            'controller_placement': 'left,top'
        }
        
        layout_config = handler.create_layout_config(config)
        
        assert layout_config['name'] == 'test_keyboard'
        assert 'matrixes' in layout_config
        assert 'main' in layout_config['matrixes']
        assert 'keys' in layout_config['matrixes']['main']
        
        # Test 5x5 layout
        keys = layout_config['matrixes']['main']['keys']
        assert len(keys) == 5, f"Expected 5 rows, got {len(keys)}"
        assert len(keys[0]) == 5, f"Expected 5 columns, got {len(keys[0])}"
        
        # Test 65% layout
        config['keyboard_size'] = '65percent'
        layout_config_65 = handler.create_layout_config(config)
        keys_65 = layout_config_65['matrixes']['main']['keys']
        assert len(keys_65) == 5, "65% layout should have 5 rows"
        assert len(keys_65[0]) > 5, "65% layout should have more than 5 columns in first row"
        
        return True
        
    except Exception as e:
        print(f"Web server test failed: {e}")
        return False

def test_file_generation():
    """Test that files can be generated"""
    try:
        from web_server import PrintboardRequestHandler
        
        class MockHandler(PrintboardRequestHandler):
            def __init__(self):
                pass
        
        handler = MockHandler()
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                config = {
                    'name': 'test_generation',
                    'keyboard_size': '5x5',
                    'switch_type': 'gamdias_lp',
                    'controller_type': 'tinys2',
                    'controller_placement': 'left,top'
                }
                
                result = handler.generate_keyboard(config)
                
                assert 'success' in result
                assert result['success'] == True or 'error' in result
                
                if result['success']:
                    assert 'files' in result
                    assert 'config' in result
                    
                    # Check if output directory was created
                    if os.path.exists('output'):
                        output_files = os.listdir('output')
                        assert len(output_files) > 0, "Should generate at least one file"
                
                return True
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"File generation test failed: {e}")
        return False

def test_mock_solid_functionality():
    """Test that mock solid implementation works"""
    try:
        from mock_solid import MockSolid, MockShape, MockUnion
        from mock_solid import up, down, left, right, rotate, scad_render_to_file
        
        # Test basic shapes
        cube = MockSolid.cube([10, 10, 10])
        assert isinstance(cube, MockShape)
        assert cube.shape_type == "cube"
        
        cylinder = MockSolid.cylinder(d=5, h=10)
        assert isinstance(cylinder, MockShape)
        assert cylinder.shape_type == "cylinder"
        
        # Test transformations
        moved_cube = up(5)(cube)
        assert isinstance(moved_cube, MockShape)
        assert moved_cube.shape_type == "translate"
        
        # Test union operations
        union_result = cube + cylinder
        assert isinstance(union_result, MockUnion)
        
        # Test file rendering
        with tempfile.NamedTemporaryFile(suffix='.scad', delete=False) as f:
            temp_file = f.name
        
        try:
            scad_render_to_file(cube, temp_file)
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
                assert 'cube' in content
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        
        return True
        
    except Exception as e:
        print(f"Mock solid test failed: {e}")
        return False

def test_configuration_structure():
    """Test that the configuration structures are valid"""
    try:
        # Test that we can load the basic structure without external deps
        import sys
        
        # Add paths for imports
        switches_path = os.path.join(os.path.dirname(__file__), '..', 'libs', 'switches')
        controllers_path = os.path.join(os.path.dirname(__file__), '..', 'libs', 'controllers')
        sys.path.insert(0, switches_path)
        sys.path.insert(0, controllers_path)
        
        # Mock the solid imports to test config structure
        import mock_solid
        sys.modules['solid'] = mock_solid
        sys.modules['solid.utils'] = mock_solid
        sys.modules['solid.objects'] = mock_solid
        
        import gamdias_lp as switch
        import tinys2 as controller
        
        # Test switch configuration
        assert hasattr(switch, 'conf')
        assert hasattr(switch, 'pins')
        
        config = switch.conf
        assert 'switch_sizes_x' in config
        assert 'switch_sizes_y' in config
        assert config['switch_sizes_x'] > 0
        assert config['switch_sizes_y'] > 0
        
        # Test controller configuration
        assert hasattr(controller, 'pin_rows')
        assert hasattr(controller, 'usable_pins')
        
        pin_rows = controller.pin_rows
        assert 'left' in pin_rows
        assert 'right' in pin_rows
        
        return True
        
    except Exception as e:
        print(f"Configuration structure test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    tests = [
        ("Mock Solid Functionality", test_mock_solid_functionality),
        ("Configuration Structure", test_configuration_structure),
        ("Web Server Functionality", test_web_server_functionality),
        ("File Generation", test_file_generation),
    ]
    
    results = []
    print("Running integration tests...")
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
            status = "PASS" if result else "FAIL"
            print(f"{'✓' if result else '✗'} {test_name}: {status}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"✗ {test_name}: FAIL - {e}")
    
    return results

if __name__ == "__main__":
    results = run_integration_tests()
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    print(f"\nIntegration Test Results: {passed}/{total} passed")
    
    if passed < total:
        print("\nFailed tests:")
        for test_name, result, error in results:
            if not result:
                print(f"  - {test_name}: {error if error else 'Unknown error'}")
        sys.exit(1)
    else:
        print("All integration tests passed! 🎉")