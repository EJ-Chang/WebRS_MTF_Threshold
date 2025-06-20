#!/usr/bin/env python3
"""
Dependency Check Script for Replit Environment
檢查 Replit 環境中的所有關鍵依賴模組
"""

import sys
import importlib
import subprocess

# 關鍵依賴列表
CRITICAL_DEPENDENCIES = [
    'streamlit',
    'numpy', 
    'plotly',
    'pandas',
    'opencv-python-headless',  # cv2
    'scipy',
    'pillow',  # PIL
    'matplotlib',
    'sqlalchemy',
    'psycopg2',
    'scikit-learn'  # sklearn
]

# 導入名稱映射 (套件名 -> 導入名)
IMPORT_MAPPING = {
    'opencv-python-headless': 'cv2',
    'pillow': 'PIL',
    'scikit-learn': 'sklearn',
    'psycopg2': 'psycopg2'
}

def check_python_version():
    """檢查 Python 版本"""
    print(f"🐍 Python 版本: {sys.version}")
    print(f"📍 Python 路徑: {sys.executable}")
    print("-" * 50)

def check_module_import(package_name):
    """檢查模組是否可以導入"""
    import_name = IMPORT_MAPPING.get(package_name, package_name.replace('-', '_'))
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'Unknown')
        print(f"✅ {package_name} ({import_name}) - 版本: {version}")
        return True
    except ImportError as e:
        print(f"❌ {package_name} ({import_name}) - 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {package_name} ({import_name}) - 其他錯誤: {e}")
        return False

def check_pip_installed():
    """檢查 pip 已安裝的套件"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            installed_packages = result.stdout.lower()
            print("\n📦 已安裝套件檢查:")
            for package in CRITICAL_DEPENDENCIES:
                package_lower = package.lower().replace('-', '_')
                if package_lower in installed_packages or package.lower() in installed_packages:
                    print(f"✅ {package} 已安裝")
                else:
                    print(f"❌ {package} 未安裝")
        else:
            print(f"⚠️  無法檢查已安裝套件: {result.stderr}")
    except Exception as e:
        print(f"⚠️  檢查已安裝套件時出錯: {e}")

def generate_install_commands():
    """生成安裝命令"""
    print("\n🔧 安裝命令 (在 Replit Shell 中執行):")
    print("# 方法 1: 使用 uv (推薦)")
    print("uv sync")
    print("\n# 方法 2: 使用 pip")
    print("pip install -r requirements.txt")
    print("\n# 方法 3: 個別安裝")
    for package in CRITICAL_DEPENDENCIES:
        print(f"pip install {package}")

def main():
    """主函數"""
    print("🔍 Replit 環境依賴檢查")
    print("=" * 50)
    
    # 檢查 Python 版本
    check_python_version()
    
    # 檢查模組導入
    print("📋 模組導入測試:")
    failed_imports = []
    
    for package in CRITICAL_DEPENDENCIES:
        if not check_module_import(package):
            failed_imports.append(package)
    
    print("-" * 50)
    
    # 檢查 pip 已安裝套件
    check_pip_installed()
    
    # 總結
    print("\n📊 總結:")
    if failed_imports:
        print(f"❌ 失敗的模組: {len(failed_imports)}")
        print(f"   {', '.join(failed_imports)}")
        generate_install_commands()
    else:
        print("✅ 所有關鍵依賴都可以正常導入！")
    
    print("\n💡 如果有模組缺失，請在 Replit Shell 中執行上述安裝命令")

if __name__ == "__main__":
    main()