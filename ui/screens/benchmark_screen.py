"""
Benchmark screen for WebRS MTF Threshold experiment.
Shows ADO performance testing.
"""
import streamlit as st
from ui.components.response_buttons import create_action_button
from utils.logger import get_logger

logger = get_logger(__name__)

def display_benchmark_screen() -> None:
    """Display ADO performance benchmark screen"""
    try:
        st.header("⚡ ADO 效能基準測試")
        st.markdown("---")
        
        st.info("""
        此頁面用於測試 Adaptive Design Optimization (ADO) 引擎的效能。
        測試將模擬實際實驗條件，測量 ADO 運算所需的時間。
        """)
        
        # Import and run the benchmark from the original app
        if create_action_button("開始效能測試", key="start_benchmark"):
            _run_ado_benchmark()
        
        # Navigation
        st.markdown("---")
        if create_action_button("返回主頁", key="return_from_benchmark"):
            # Navigate back to welcome
            st.session_state.session_manager.set_experiment_stage('welcome')
            st.rerun()
            
    except Exception as e:
        logger.error(f"Error in benchmark screen: {e}")
        st.error(f"Error in benchmark screen: {e}")

def _run_ado_benchmark():
    """Run ADO performance benchmark"""
    try:
        # Import the benchmark function from original app
        from app import ado_benchmark_screen
        
        st.markdown("### 🔬 執行基準測試...")
        
        # Run the original benchmark function
        ado_benchmark_screen()
        
    except ImportError as e:
        logger.error(f"Cannot import benchmark function: {e}")
        st.error("無法載入基準測試功能，請確認 experiments/ado_utils.py 存在")
    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        st.error(f"執行基準測試時發生錯誤: {e}")