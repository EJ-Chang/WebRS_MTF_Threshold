#!/usr/bin/env python3
"""Test script to check which dependencies are working"""

import sys
print(f"Python: {sys.version}")

# Test imports one by one
modules_to_test = [
    'numpy',
    'pandas', 
    'streamlit',
    'matplotlib',
    'cv2',
    'PIL',
    'plotly',
    'scipy',
    'sqlalchemy'
]

working_modules = []
failed_modules = []

for module in modules_to_test:
    try:
        __import__(module)
        working_modules.append(module)
        print(f"✓ {module}")
    except Exception as e:
        failed_modules.append((module, str(e)))
        print(f"✗ {module}: {str(e)[:100]}")

print(f"\nWorking: {len(working_modules)}/{len(modules_to_test)}")
if failed_modules:
    print("Failed modules:")
    for module, error in failed_modules:
        print(f"  {module}: {error[:50]}...")