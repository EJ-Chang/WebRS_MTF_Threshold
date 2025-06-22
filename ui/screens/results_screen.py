"""
Results screen for WebRS MTF Threshold experiment.
"""
import streamlit as st
import pandas as pd
from ui.components.progress_indicators import show_completion_celebration
from ui.components.response_buttons import create_action_button, create_reset_button
from utils.helpers import format_percentage, format_time_duration
from utils.logger import get_logger

logger = get_logger(__name__)

def display_results_screen(session_manager) -> None:
    """
    Display experiment results
    
    Args:
        session_manager: SessionStateManager instance
    """
    try:
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
        
        # Display psychometric function if possible
        _display_psychometric_function(trial_results)
        
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
    
    # Calculate statistics from trial results
    total_trials = len(trial_results)
    clear_responses = sum(1 for r in trial_results if r.get('response') == 'clear')
    clear_rate = clear_responses / total_trials if total_trials > 0 else 0
    
    reaction_times = [r.get('reaction_time', 0) for r in trial_results if r.get('reaction_time')]
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
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(trial_results)
    
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

def _display_psychometric_function(trial_results):
    """Display psychometric function if possible"""
    try:
        import plotly.graph_objects as go
        import numpy as np
        
        st.subheader("📈 心理測量函數")
        
        # Extract MTF values and responses
        mtf_values = []
        responses = []
        
        for result in trial_results:
            mtf_val = result.get('mtf_value')
            response = result.get('response')
            
            if mtf_val is not None and response is not None:
                mtf_values.append(mtf_val)
                responses.append(1 if response == 'clear' else 0)
        
        if len(mtf_values) < 5:
            st.info("數據點不足，無法繪製心理測量函數（需要至少 5 個數據點）")
            return
        
        # Create binned data for plotting
        unique_mtf = sorted(set(mtf_values))
        if len(unique_mtf) < 3:
            st.info("MTF 值變化範圍太小，無法繪製有意義的心理測量函數")
            return
        
        # Calculate proportion correct for each MTF value
        mtf_bins = []
        proportions = []
        counts = []
        
        for mtf in unique_mtf:
            indices = [i for i, x in enumerate(mtf_values) if x == mtf]
            if indices:
                responses_for_mtf = [responses[i] for i in indices]
                proportion = sum(responses_for_mtf) / len(responses_for_mtf)
                mtf_bins.append(mtf)
                proportions.append(proportion)
                counts.append(len(responses_for_mtf))
        
        # Create plot
        fig = go.Figure()
        
        # Add data points
        fig.add_trace(go.Scatter(
            x=mtf_bins,
            y=proportions,
            mode='markers+lines',
            marker=dict(size=8, color='blue'),
            line=dict(color='blue', width=2),
            name='觀察數據',
            text=[f"n={count}" for count in counts],
            hovertemplate='MTF: %{x:.1f}<br>清楚率: %{y:.1%}<br>%{text}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title="心理測量函數",
            xaxis_title="MTF 值",
            yaxis_title="「清楚」回應比例",
            yaxis=dict(range=[0, 1], tickformat='.0%'),
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show interpretation
        with st.expander("📖 結果解釋"):
            st.markdown("""
            **心理測量函數說明：**
            - X 軸：MTF 值（調制傳遞函數值，越高表示圖像越清晰）
            - Y 軸：回應「清楚」的比例
            - 理想情況下，MTF 值越高，回應「清楚」的比例應該越高
            - 函數的陡峭程度反映了您對清晰度變化的敏感性
            """)
        
    except ImportError:
        st.info("無法繪製心理測量函數：缺少 plotly 庫")
    except Exception as e:
        logger.warning(f"Error creating psychometric function: {e}")
        st.warning("繪製心理測量函數時發生錯誤")

def _display_download_options(trial_results, participant_id):
    """Display download options for results"""
    st.subheader("💾 下載結果")
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(trial_results)
        
        if not df.empty:
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
        else:
            st.warning("沒有數據可供下載")
            
    except Exception as e:
        logger.error(f"Error creating download options: {e}")
        st.error("創建下載選項時發生錯誤")

def _show_navigation_options(session_manager):
    """Show navigation options"""
    st.markdown("---")
    st.subheader("🔄 下一步")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if create_action_button(
            "重新開始實驗",
            button_type="secondary",
            key="restart_experiment"
        ):
            if create_reset_button("確認重新開始", key_suffix="results"):
                session_manager.reset_experiment()
                st.rerun()
    
    with col2:
        if create_action_button(
            "返回主頁",
            button_type="primary",
            key="return_home"
        ):
            session_manager.set_experiment_stage('welcome')
            st.rerun()
    
    with col3:
        if create_action_button(
            "效能測試",
            button_type="secondary",
            key="performance_test"
        ):
            session_manager.set_experiment_stage('benchmark')
            st.rerun()