#!/usr/bin/env python3
"""
Test runner for printboard-research project
"""
import sys
import os
import subprocess

def run_tests():
    """Run all available tests"""
    test_files = [
        'tests/test_basic.py',
        'tests/test_integration.py'
    ]
    
    print("🧪 Running Printboard Research Tests")
    print("=" * 50)
    
    all_passed = True
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📋 Running {test_file}...")
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test_file}: PASSED")
                # Print last line of output for summary
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        print(f"   {lines[-1]}")
            else:
                print(f"❌ {test_file}: FAILED")
                if result.stdout:
                    print("STDOUT:")
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:")
                    print(result.stderr)
                all_passed = False
        else:
            print(f"⚠️  {test_file}: NOT FOUND")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())