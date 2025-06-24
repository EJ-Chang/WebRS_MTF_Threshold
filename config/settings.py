"""
Environment detection and configuration settings for WebRS MTF Threshold experiment.
"""
import os
import platform

def detect_environment():
    """檢測當前運行環境並設定相應的端口"""
    
    # 檢查是否在 Replit 環境
    if os.path.exists('/home/runner') or 'REPL_ID' in os.environ:
        # Replit 環境
        os.environ['STREAMLIT_SERVER_PORT'] = '5000'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
        print("🌐 檢測到 Replit 環境，使用端口 5000")
        return 'replit'
    elif platform.system() == 'Linux' and 'ubuntu' in platform.platform().lower():
        # Ubuntu Server 環境 (非Replit)
        os.environ['STREAMLIT_SERVER_PORT'] = '3838'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
        print("🖥️ 檢測到 Ubuntu Server 環境，使用端口 3838 (共用 R Shiny port)")
        return 'ubuntu'
    else:
        # 本地環境 (Windows/macOS)
        os.environ['STREAMLIT_SERVER_PORT'] = '8501'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
        return 'local'

def get_page_config():
    """Get Streamlit page configuration"""
    return {
        "page_title": "心理物理學 2AFC 實驗",
        "page_icon": "🧠",
        "layout": "wide",
        "initial_sidebar_state": "collapsed"
    }

# Environment variables
ENVIRONMENT = detect_environment()
PAGE_CONFIG = get_page_config()

# Experiment configuration
PRACTICE_TRIAL_LIMIT = 3  # Number of practice trials before main experiment

# Main experiment configuration
MAX_TRIALS = 45  # Maximum number of trials in the main experiment
MIN_TRIALS = 15  # Minimum number of trials before convergence check
CONVERGENCE_THRESHOLD = 0.15  # Convergence criterion for threshold SD
STIMULUS_DURATION = 1.0  # Stimulus display duration in seconds