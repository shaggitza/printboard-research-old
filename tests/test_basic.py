"""
Basic tests for printboard core functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that basic modules can be imported"""
    try:
        from libs.switches import gamdias_lp
        from libs.controllers import tinys2
        # Basic import test passes
        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

def test_switch_config():
    """Test switch configuration structure"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'switches'))
    try:
        import gamdias_lp as switch
        
        # Check that essential configuration exists
        assert hasattr(switch, 'conf'), "Switch config missing"
        assert hasattr(switch, 'pins'), "Switch pins missing"
        
        # Check essential config values
        config = switch.conf
        assert 'switch_sizes_x' in config, "Missing switch_sizes_x"
        assert 'switch_sizes_y' in config, "Missing switch_sizes_y"
        assert config['switch_sizes_x'] > 0, "Invalid switch_sizes_x"
        assert config['switch_sizes_y'] > 0, "Invalid switch_sizes_y"
        
        # Check pins structure
        pins = switch.pins
        assert isinstance(pins, list), "Pins should be a list"
        assert len(pins) > 0, "Should have at least one pin"
        
        for pin in pins:
            assert 'name' in pin, "Pin missing name"
            assert 'dist_to_center' in pin, "Pin missing distance to center"
            assert 'connection' in pin, "Pin missing connection type"
        
        return True
    except Exception as e:
        print(f"Switch config test failed: {e}")
        return False

def test_controller_config():
    """Test controller configuration structure"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'controllers'))
    try:
        import tinys2 as controller
        
        # Check essential attributes
        assert hasattr(controller, 'pin_rows'), "Controller missing pin_rows"
        assert hasattr(controller, 'usable_pins'), "Controller missing usable_pins"
        
        # Check pin_rows structure
        pin_rows = controller.pin_rows
        assert isinstance(pin_rows, dict), "pin_rows should be a dict"
        assert 'left' in pin_rows, "Missing left pin row"
        assert 'right' in pin_rows, "Missing right pin row"
        
        # Check usable_pins
        usable_pins = controller.usable_pins
        assert isinstance(usable_pins, list), "usable_pins should be a list"
        assert len(usable_pins) > 0, "Should have usable pins"
        
        return True
    except Exception as e:
        print(f"Controller config test failed: {e}")
        return False

def run_tests():
    """Run all tests and return results"""
    tests = [
        ("Import Test", test_imports),
        ("Switch Config Test", test_switch_config),  
        ("Controller Config Test", test_controller_config)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
            print(f"✓ {test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"✗ {test_name}: FAIL - {e}")
    
    return results

if __name__ == "__main__":
    print("Running basic printboard tests...")
    results = run_tests()
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    print(f"\nTest Results: {passed}/{total} passed")
    if passed < total:
        sys.exit(1)