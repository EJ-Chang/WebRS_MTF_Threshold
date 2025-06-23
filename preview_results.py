#!/usr/bin/env python3
"""
預覽結果頁面腳本 - 使用實際實驗數據展示 psychometric function
"""
import streamlit as st
import pandas as pd
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.analysis_tools import plot_psychometric_function

# Configure Streamlit page
st.set_page_config(
    page_title="MTF 實驗結果預覽",
    page_icon="📊",
    layout="wide"
)

def load_trial_data():
    """載入實驗數據"""
    try:
        # Load the CSV data
        csv_path = "experiment_data/trials.csv"
        df = pd.read_csv(csv_path)
        
        # Convert to the format expected by the analysis function
        trial_results = []
        for _, row in df.iterrows():
            trial_data = {
                'trial_number': row['trial_number'],
                'mtf_value': row['mtf_value'],
                'response': row['response'],
                'reaction_time': row['reaction_time'],
                'timestamp': row['timestamp'],
                'participant_id': row['participant_id']
            }
            trial_results.append(trial_data)
        
        return trial_results, df
        
    except Exception as e:
        st.error(f"無法載入數據: {e}")
        return [], pd.DataFrame()

def display_summary_statistics(df):
    """顯示實驗統計摘要"""
    if df.empty:
        return
    
    st.subheader("📈 實驗統計")
    
    total_trials = len(df)
    clear_responses = (df['response'] == 'clear').sum()
    clear_rate = clear_responses / total_trials if total_trials > 0 else 0
    avg_reaction_time = df['reaction_time'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總試驗數", total_trials)
    
    with col2:
        st.metric("「清楚」回應", clear_responses)
    
    with col3:
        st.metric("清楚率", f"{clear_rate:.1%}")
    
    with col4:
        st.metric("平均反應時間", f"{avg_reaction_time:.2f}秒")

def main():
    """主函數"""
    st.title("🔬 MTF 實驗結果預覽")
    st.markdown("使用實際實驗數據預覧 psychometric function")
    
    # 載入數據
    trial_results, df = load_trial_data()
    
    if not trial_results:
        st.warning("沒有找到實驗數據")
        st.info("請確保 experiment_data/trials.csv 檔案存在")
        return
    
    # 顯示數據概覽
    st.success(f"成功載入 {len(trial_results)} 筆實驗數據")
    
    # 顯示統計摘要
    display_summary_statistics(df)
    
    st.markdown("---")
    
    # 顯示 psychometric function（這是主要的測試部分）
    st.header("📊 Psychometric Function 預覽")
    
    try:
        # 調用實際的 analysis_tools 函數
        plot_psychometric_function(trial_results)
        
        st.success("✅ Psychometric function 成功顯示！")
        
    except Exception as e:
        st.error(f"❌ Psychometric function 顯示錯誤: {e}")
        st.exception(e)
    
    # 顯示原始數據預覽
    with st.expander("🔍 原始數據預覽"):
        st.dataframe(df, use_container_width=True)
    
    # 顯示數據格式資訊
    with st.expander("📋 數據格式資訊"):
        st.write("**資料欄位:**")
        for col in df.columns:
            st.write(f"- {col}: {df[col].dtype}")
        
        st.write("**MTF 值範圍:**", f"{df['mtf_value'].min()} - {df['mtf_value'].max()}")
        st.write("**回應分佈:**")
        response_counts = df['response'].value_counts()
        for response, count in response_counts.items():
            st.write(f"  - {response}: {count} 次")

if __name__ == "__main__":
    main()