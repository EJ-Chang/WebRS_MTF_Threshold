#!/usr/bin/env python3
import os
import re
import subprocess
import sys

def quick_scan_and_install():
    """快速掃描並安裝套件"""

    # 常見套件映射
    package_map = {
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'sklearn': 'scikit-learn',
        'yaml': 'PyYAML',
        'dotenv': 'python-dotenv',
        'bs4': 'beautifulsoup4',
        'jwt': 'PyJWT',
        'psycopg2': 'psycopg2-binary',
    }

    # 內建模組
    builtin = {
        'os', 'sys', 'json', 'datetime', 'time', 'random', 'math', 
        'collections', 'itertools', 'functools', 're', 'string', 'io', 
        'pathlib', 'urllib', 'subprocess', 'csv', 'sqlite3', 'pickle'
    }

    print("🔍 快速掃描 Python 檔案...")

    # 找出所有 Python 檔案
    py_files = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))

    print(f"📁 找到 {len(py_files)} 個 Python 檔案")

    # 提取 import
    imports = set()
    for file in py_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 簡單的正則表達式提取 import
            import_patterns = [
                r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    imports.add(match.split('.')[0])

        except Exception as e:
            print(f"⚠️  跳過 {file}: {e}")

    # 過濾套件
    packages = set()
    for imp in imports:
        if imp not in builtin:
            pkg = package_map.get(imp, imp)
            packages.add(pkg)

    if not packages:
        print("✅ 沒有發現第三方套件")
        return

    print(f"\n📦 發現套件: {', '.join(sorted(packages))}")

    # 檢查已安裝
    need_install = []
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✅ {pkg} - 已安裝")
        except ImportError:
            need_install.append(pkg)
            print(f"❌ {pkg} - 需要安裝")

    if not need_install:
        print("\n🎉 所有套件都已安裝!")
        return

    # 安裝套件
    print(f"\n📥 安裝 {len(need_install)} 個套件...")

    install_cmd = [sys.executable, '-m', 'pip', 'install'] + need_install

    try:
        result = subprocess.run(install_cmd, check=True)
        print("\n🎉 安裝完成!")

        # 生成 requirements.txt
        with open('requirements.txt', 'w') as f:
            for pkg in sorted(packages):
                f.write(f"{pkg}\n")
        print("📝 已生成 requirements.txt")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 安裝失敗: {e}")

if __name__ == "__main__":
    quick_scan_and_install()
