#!/usr/bin/env python3
"""
Replit Environment Test Suite
Tests all critical functionality for Replit hosting
"""

import os
import sys
import time

def test_environment_setup():
    """Test basic environment setup"""
    print("🌍 Testing Environment Setup...")
    
    # Check Python version
    python_version = sys.version_info
    print(f"   Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major == 3 and python_version.minor >= 11:
        print("   ✅ Python version compatible")
    else:
        print("   ⚠️ Python version may not be optimal")
    
    # Check working directory
    cwd = os.getcwd()
    print(f"   Working directory: {cwd}")
    
    # Check key files exist
    key_files = [
        'app.py', 'mtf_experiment.py', 'database.py', 
        '.replit', 'main.py', 'pyproject.toml'
    ]
    
    for file in key_files:
        if os.path.exists(file):
            print(f"   ✅ {file} found")
        else:
            print(f"   ❌ {file} missing")
    
    return True

def test_critical_imports():
    """Test critical imports for Replit"""
    print("\n📦 Testing Critical Imports...")
    
    critical_imports = [
        ('os', 'Operating system interface'),
        ('sys', 'System-specific parameters'),
        ('time', 'Time-related functions'),
        ('datetime', 'Date and time handling'),
        ('json', 'JSON encoder/decoder'),
        ('base64', 'Base64 encoding'),
        ('io', 'Input/output operations')
    ]
    
    for module, description in critical_imports:
        try:
            __import__(module)
            print(f"   ✅ {module} - {description}")
        except ImportError:
            print(f"   ❌ {module} - {description}")
            return False
    
    return True

def test_scientific_imports():
    """Test scientific computing imports"""
    print("\n🔬 Testing Scientific Computing Imports...")
    
    scientific_packages = [
        ('numpy', 'Numerical computing'),
        ('pandas', 'Data manipulation'),
        ('scipy', 'Scientific computing'),
        ('matplotlib', 'Plotting library'),
        ('plotly', 'Interactive plots'),
        ('PIL', 'Image processing'),
        ('cv2', 'OpenCV computer vision'),
        ('sqlalchemy', 'Database ORM'),
        ('streamlit', 'Web application framework')
    ]
    
    available_packages = []
    missing_packages = []
    
    for package, description in scientific_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} - {description}")
            available_packages.append(package)
        except ImportError:
            print(f"   ❌ {package} - {description}")
            missing_packages.append(package)
    
    print(f"\n   📊 Summary: {len(available_packages)}/{len(scientific_packages)} packages available")
    
    if missing_packages:
        print(f"   ⚠️ Missing: {', '.join(missing_packages)}")
        print("   💡 Install with: pip install " + ' '.join(missing_packages))
    
    return len(missing_packages) == 0

def test_database_setup():
    """Test database configuration"""
    print("\n🗄️ Testing Database Setup...")
    
    try:
        from database import DatabaseManager
        
        # Test database initialization
        db = DatabaseManager()
        print("   ✅ DatabaseManager initialized")
        
        # Check database URL
        if 'postgresql' in db.database_url.lower():
            print("   ✅ PostgreSQL database detected")
        elif 'sqlite' in db.database_url.lower():
            print("   ✅ SQLite database (fallback)")
        else:
            print(f"   ⚠️ Unknown database type: {db.database_url}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database setup failed: {e}")
        return False

def test_mtf_experiment():
    """Test MTF experiment functionality"""
    print("\n🧠 Testing MTF Experiment...")
    
    try:
        from mtf_experiment import MTFExperimentManager, PreciseTimer, StimulusCache
        
        # Test PreciseTimer
        timer = PreciseTimer()
        print("   ✅ PreciseTimer created")
        
        # Test StimulusCache
        cache = StimulusCache()
        print("   ✅ StimulusCache created")
        
        # Test MTFExperimentManager
        exp_manager = MTFExperimentManager(
            max_trials=5,
            min_trials=3,
            participant_id="test_replit"
        )
        print("   ✅ MTFExperimentManager created")
        
        # Test base image loading
        if exp_manager.base_image is not None:
            print(f"   ✅ Base image loaded: {exp_manager.base_image.shape}")
        else:
            print("   ⚠️ No base image, using test pattern")
        
        # Test ADO engine
        if exp_manager.ado_engine is not None:
            print("   ✅ ADO engine initialized")
        else:
            print("   ⚠️ ADO engine not available")
        
        return True
        
    except Exception as e:
        print(f"   ❌ MTF experiment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_compatibility():
    """Test Streamlit compatibility"""
    print("\n🌐 Testing Streamlit Compatibility...")
    
    try:
        import streamlit as st
        print("   ✅ Streamlit imported successfully")
        
        # Test Streamlit version
        st_version = st.__version__
        print(f"   ✅ Streamlit version: {st_version}")
        
        # Check if version is compatible
        version_parts = st_version.split('.')
        major_version = int(version_parts[0])
        minor_version = int(version_parts[1])
        
        if major_version >= 1 and minor_version >= 45:
            print("   ✅ Streamlit version compatible")
        else:
            print("   ⚠️ Streamlit version may be outdated")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Streamlit compatibility test failed: {e}")
        return False

def test_replit_specific():
    """Test Replit-specific functionality"""
    print("\n🔧 Testing Replit-Specific Features...")
    
    # Check for Replit environment variables
    replit_vars = [
        'REPL_SLUG', 'REPL_OWNER', 'REPLIT_DB_URL'
    ]
    
    replit_detected = False
    for var in replit_vars:
        if os.getenv(var):
            print(f"   ✅ {var} detected")
            replit_detected = True
        else:
            print(f"   ❌ {var} not found")
    
    if replit_detected:
        print("   ✅ Running in Replit environment")
    else:
        print("   ⚠️ Not detected as Replit environment")
    
    # Check port configuration
    if os.getenv('PORT'):
        print(f"   ✅ PORT environment variable: {os.getenv('PORT')}")
    else:
        print("   ⚠️ PORT not set, using default 5000")
    
    return True

def main():
    """Run all Replit environment tests"""
    print("🧪 Replit Environment Test Suite")
    print("=" * 60)
    
    tests = [
        test_environment_setup,
        test_critical_imports,
        test_scientific_imports,
        test_database_setup,
        test_mtf_experiment,
        test_streamlit_compatibility,
        test_replit_specific
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            time.sleep(0.5)  # Brief pause between tests
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Replit environment is ready!")
        print("🚀 You can now run: streamlit run app.py")
    elif passed >= total - 2:
        print("✅ Most tests passed. Environment should work with minor issues.")
        print("🚀 Try running: streamlit run app.py")
    else:
        print("⚠️ Several tests failed. Check the output above for issues.")
        print("💡 Try installing missing packages or check configuration.")
    
    return 0 if passed >= total - 1 else 1

if __name__ == "__main__":
    exit(main())