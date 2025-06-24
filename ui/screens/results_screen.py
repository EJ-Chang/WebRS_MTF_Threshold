"""
Results screen for WebRS MTF Threshold experiment.
"""
import streamlit as st
import pandas as pd
from ui.components.progress_indicators import show_completion_celebration
from ui.components.response_buttons import create_action_button
from utils.helpers import format_percentage, format_time_duration
from utils.logger import get_logger
from utils.analysis_tools import plot_psychometric_function

logger = get_logger(__name__)

def display_results_screen(session_manager) -> None:
    """
    Display experiment results
    
    Args:
        session_manager: SessionStateManager instance
    """
    try:
        # Ensure all data is saved before showing results
        _ensure_final_data_save(session_manager)
        
        # Show completion celebration
        show_completion_celebration()
        
        st.header("📊 實驗結果")
        
        # Get experiment summary
        summary = st.session_state.get('experiment_summary', {})
        trial_results = session_manager.get_trial_results()
        
        if not trial_results:
            st.warning("沒有找到實驗數據")
            _show_navigation_options(session_manager)
            return
        
        # Display summary statistics
        _display_summary_statistics(summary, trial_results)
        
        # Display detailed results
        _display_detailed_results(trial_results)
        
        # Display psychometric function using the proper analysis function (only experiment trials)
        experiment_trials = [t for t in trial_results if not t.get('is_practice', False)]
        plot_psychometric_function(experiment_trials)
        
        # Download options
        _display_download_options(trial_results, session_manager.get_participant_id())
        
        # Navigation options
        _show_navigation_options(session_manager)
        
    except Exception as e:
        logger.error(f"Error in results screen: {e}")
        st.error(f"Error displaying results: {e}")

def _display_summary_statistics(summary, trial_results):
    """Display summary statistics"""
    st.subheader("📈 實驗統計")
    
    # 只計算正式實驗資料（排除練習試驗）
    experiment_trials = [t for t in trial_results if not t.get('is_practice', False)]
    
    # Calculate statistics from experiment trials only
    total_trials = len(experiment_trials)
    clear_responses = sum(1 for r in experiment_trials if r.get('response') == 'clear')
    clear_rate = clear_responses / total_trials if total_trials > 0 else 0
    
    reaction_times = [r.get('reaction_time', 0) for r in experiment_trials if r.get('reaction_time')]
    avg_reaction_time = sum(reaction_times) / len(reaction_times) if reaction_times else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總試驗數", total_trials)
    
    with col2:
        st.metric("「清楚」回應", clear_responses)
    
    with col3:
        st.metric("清楚率", format_percentage(clear_rate))
    
    with col4:
        st.metric("平均反應時間", format_time_duration(avg_reaction_time))

def _display_detailed_results(trial_results):
    """Display detailed trial results"""
    st.subheader("📋 詳細結果")
    
    # 只顯示正式實驗資料（排除練習試驗）
    experiment_trials = [t for t in trial_results if not t.get('is_practice', False)]
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(experiment_trials)
    
    if not df.empty:
        # Select relevant columns for display
        display_columns = [
            'trial_number', 'mtf_value', 'response', 'reaction_time', 'timestamp'
        ]
        
        # Only include columns that exist
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            display_df = df[available_columns].copy()
            
            # Format columns for better display
            if 'reaction_time' in display_df.columns:
                display_df['reaction_time'] = display_df['reaction_time'].apply(
                    lambda x: f"{x:.3f}s" if x else "N/A"
                )
            
            if 'mtf_value' in display_df.columns:
                display_df['mtf_value'] = display_df['mtf_value'].apply(
                    lambda x: f"{x:.1f}" if x else "N/A"
                )
            
            if 'response' in display_df.columns:
                display_df['response'] = display_df['response'].apply(
                    lambda x: "清楚" if x == "clear" else "不清楚" if x == "not_clear" else x
                )
            
            # Rename columns for Chinese display
            column_names = {
                'trial_number': '試驗編號',
                'mtf_value': 'MTF 值',
                'response': '回應',
                'reaction_time': '反應時間',
                'timestamp': '時間戳記'
            }
            
            display_df = display_df.rename(columns=column_names)
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("無法顯示詳細結果：缺少必要的數據欄位")


def _display_download_options(trial_results, participant_id):
    """Display download options for results"""
    st.subheader("💾 下載結果")
    
    try:
        # 只包含正式實驗資料（排除練習試驗）
        experiment_trials = [t for t in trial_results if not t.get('is_practice', False)]
        
        if experiment_trials:
            # Convert to DataFrame
            df = pd.DataFrame(experiment_trials)
            
            # CSV download
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 下載 CSV 格式",
                data=csv_data,
                file_name=f"{participant_id}_mtf_results.csv",
                mime="text/csv"
            )
            
            # JSON download
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 下載 JSON 格式",
                data=json_data,
                file_name=f"{participant_id}_mtf_results.json",
                mime="application/json"
            )
            
            st.info(f"📊 僅包含正式實驗資料：{len(experiment_trials)} 筆試驗")
        else:
            st.warning("沒有正式實驗數據可供下載")
            
    except Exception as e:
        logger.error(f"Error creating download options: {e}")
        st.error("創建下載選項時發生錯誤")

def _ensure_final_data_save(session_manager):
    """Ensure all data is saved before showing results"""
    try:
        # Get experiment controller from session state
        if 'experiment_controller' in st.session_state:
            experiment_controller = st.session_state.experiment_controller
            
            # Show data saving status
            with st.container():
                save_status = st.empty()
                save_status.info("🔄 正在確認實驗數據儲存...")
                
                # Ensure all data is saved
                all_saved = experiment_controller.ensure_all_data_saved()
                
                # Finalize experiment in database
                db_finalized = experiment_controller.finalize_experiment_in_database()
                
                # Update status
                if all_saved and db_finalized:
                    save_status.success("✅ 所有實驗數據已成功儲存到 CSV 和資料庫")
                elif all_saved:
                    save_status.warning("✅ 實驗數據已儲存到 CSV，但資料庫更新失敗")
                else:
                    save_status.error("❌ 部分實驗數據可能未正確儲存")
                
                # Show detailed storage information
                _display_storage_summary(session_manager, experiment_controller)
                
    except Exception as e:
        logger.error(f"Error in final data save: {e}")
        st.error(f"確認資料儲存時發生錯誤：{e}")

def _display_storage_summary(session_manager, experiment_controller):
    """Display storage summary information"""
    try:
        trial_results = session_manager.get_trial_results()
        saved_trials = session_manager.get_saved_trials()
        experiment_id = session_manager.get_experiment_id()
        participant_id = session_manager.get_participant_id()
        
        # Filter non-practice trials
        non_practice_trials = [t for t in trial_results if not t.get('is_practice', False)]
        
        # Display storage info
        with st.expander("📋 資料儲存詳情", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("總試驗數", len(trial_results))
                st.metric("正式試驗數", len(non_practice_trials))
                st.metric("已儲存試驗數", saved_trials)
            
            with col2:
                st.metric("參與者ID", participant_id or "未設定")
                st.metric("實驗ID", experiment_id or "未建立")
                
                # Check database manager status
                db_manager = session_manager.get_db_manager()
                db_status = "✅ 已連接" if db_manager and session_manager.is_db_manager_initialized() else "❌ 未連接"
                st.metric("資料庫狀態", db_status)
            
            # Show any discrepancies
            if len(non_practice_trials) != saved_trials:
                st.warning(f"⚠️ 發現資料不一致：{len(non_practice_trials)} 個正式試驗，但只有 {saved_trials} 個已儲存")
            
            if not experiment_id:
                st.warning("⚠️ 未找到資料庫實驗記錄ID，資料可能只儲存在 CSV 檔案中")
        
    except Exception as e:
        logger.error(f"Error displaying storage summary: {e}")
        st.error("顯示儲存摘要時發生錯誤")

def _show_navigation_options(session_manager):
    """Show navigation options"""
    st.markdown("---")
    st.subheader("🔄 下一步")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 重新開始實驗功能已移除，將在後續重新實現
        st.empty()
    
    with col2:
        if create_action_button(
            "返回主頁",
            button_type="primary",
            key="return_home"
        ):
            # Simulate complete page reload for clean restart
            from core.session_manager import SessionStateManager
            success = SessionStateManager.simulate_page_reload()
            if success:
                st.rerun()
            else:
                st.error("重新載入失敗，請手動重新整理頁面 (F5)")
    
    with col3:
        if create_action_button(
            "效能測試",
            button_type="secondary",
            key="performance_test"
        ):
            session_manager.set_experiment_stage('benchmark')
            st.rerun()