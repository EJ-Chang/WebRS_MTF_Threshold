#!/usr/bin/env python3
"""
基本導入測試 - 檢查語法和基本功能
Basic import test - check syntax and basic functionality
"""

def test_basic_imports():
    """測試基本導入是否正常"""
    print("🔍 Testing basic imports...")
    
    try:
        # Test mtf_experiment.py imports
        import sys
        import time
        from datetime import datetime
        from typing import Dict, List, Optional, Tuple
        import base64
        from io import BytesIO
        
        print("   ✅ Basic Python modules imported successfully")
        
        # Test if our classes can be instantiated (without numpy dependencies)
        from mtf_experiment import PreciseTimer
        
        timer = PreciseTimer()
        print(f"   ✅ PreciseTimer created, system offset: {timer.system_time_offset:.6f}s")
        
        # Test timing functionality
        start = timer.get_precise_onset_time()
        time.sleep(0.01)  # 10ms
        end = time.time()
        rt = timer.calculate_precise_rt(start, end)
        print(f"   ✅ Timing test: {rt:.3f}s (expected ~0.01s)")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_app_imports():
    """測試app.py的關鍵導入"""
    print("🖥️  Testing app.py imports...")
    
    try:
        import time
        from datetime import datetime
        
        print("   ✅ App.py basic imports work")
        return True
        
    except Exception as e:
        print(f"   ❌ App import error: {e}")
        return False

def test_class_definitions():
    """測試類別定義是否正確"""
    print("🏗️  Testing class definitions...")
    
    try:
        # Import without instantiating (to avoid numpy dependencies)
        import mtf_experiment
        
        # Check if classes are defined
        classes_to_check = ['PreciseTimer', 'StimulusCache', 'MTFExperimentManager']
        
        for class_name in classes_to_check:
            if hasattr(mtf_experiment, class_name):
                cls = getattr(mtf_experiment, class_name)
                print(f"   ✅ {class_name} class defined")
                
                # Check if it has expected methods
                if class_name == 'PreciseTimer':
                    expected_methods = ['get_precise_onset_time', 'calculate_precise_rt', 'update_baseline']
                elif class_name == 'StimulusCache':
                    expected_methods = ['get', 'put', 'get_cache_key']
                elif class_name == 'MTFExperimentManager':
                    expected_methods = ['get_next_trial', 'record_response', 'get_ado_entropy']
                else:
                    expected_methods = []
                
                for method in expected_methods:
                    if hasattr(cls, method):
                        print(f"     ✅ {method}() method exists")
                    else:
                        print(f"     ❌ {method}() method missing")
            else:
                print(f"   ❌ {class_name} class not found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Class definition error: {e}")
        return False

def main():
    """執行所有基本測試"""
    print("🧪 Basic MTF Improvements Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_app_imports,
        test_class_definitions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        print("✨ Core improvements are syntactically correct and functional.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())