"""
Analysis tools for psychometric function plotting and data analysis.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import curve_fit
from scipy.stats import norm
from typing import List, Dict, Any, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

def logistic_psychometric(x, alpha, beta, gamma=0.0, lambda_=0.02):
    """
    Logistic psychometric function for 2AFC tasks
    
    Args:
        x: Stimulus values (MTF values)
        alpha: Threshold parameter (50% point)
        beta: Slope parameter (larger = shallower slope)
        gamma: Guess rate (lower asymptote)
        lambda_: Lapse rate (upper asymptote = 1 - lambda)
    
    Returns:
        Probability of 'clear' response
    """
    return gamma + (1 - gamma - lambda_) / (1 + np.exp(-(x - alpha) / beta))

def cumulative_gaussian_psychometric(x, mu, sigma, gamma=0.0, lambda_=0.02):
    """
    Cumulative Gaussian psychometric function for 2AFC tasks
    
    Args:
        x: Stimulus values (MTF values)
        mu: Mean parameter (50% point)
        sigma: Standard deviation parameter
        gamma: Guess rate (lower asymptote)
        lambda_: Lapse rate (upper asymptote = 1 - lambda)
    
    Returns:
        Probability of 'clear' response
    """
    return gamma + (1 - gamma - lambda_) * norm.cdf(x, loc=mu, scale=sigma)

def fit_psychometric_functions(x_data: np.ndarray, y_data: np.ndarray) -> Dict[str, Any]:
    """
    Fit both logistic and cumulative Gaussian psychometric functions to data
    
    Args:
        x_data: MTF values
        y_data: Proportion of 'clear' responses
    
    Returns:
        Dictionary containing fit results for both models
    """
    results = {
        'logistic': {'success': False, 'params': None, 'r_squared': None, 'fitted_curve': None},
        'gaussian': {'success': False, 'params': None, 'r_squared': None, 'fitted_curve': None}
    }
    
    if len(x_data) < 4:  # Need at least 4 points for fitting
        logger.warning("Insufficient data points for psychometric function fitting")
        return results
    
    # Generate initial parameter estimates
    x_median = np.median(x_data)
    x_range = np.ptp(x_data)  # peak-to-peak range
    initial_slope = x_range / 4  # reasonable slope estimate
    
    # Create smooth x values for fitted curves (fixed range 0-99)
    x_smooth = np.linspace(0, 99, 300)
    
    # Fit logistic function
    try:
        # Initial parameters: [alpha, beta]
        p0_logistic = [x_median, initial_slope]
        bounds_logistic = ([x_data.min() - x_range, 0.1], [x_data.max() + x_range, x_range*2])
        
        popt_logistic, _ = curve_fit(
            lambda x, alpha, beta: logistic_psychometric(x, alpha, beta, 0.0, 0.02),
            x_data, y_data,
            p0=p0_logistic,
            bounds=bounds_logistic,
            maxfev=2000
        )
        
        # Calculate R-squared
        y_pred_logistic = logistic_psychometric(x_data, *popt_logistic, 0.0, 0.02)
        ss_res = np.sum((y_data - y_pred_logistic) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared_logistic = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Generate smooth fitted curve
        y_smooth_logistic = logistic_psychometric(x_smooth, *popt_logistic, 0.0, 0.02)
        
        results['logistic'] = {
            'success': True,
            'params': {'alpha': popt_logistic[0], 'beta': popt_logistic[1]},
            'r_squared': r_squared_logistic,
            'fitted_curve': {'x': x_smooth, 'y': y_smooth_logistic}
        }
        
        logger.info(f"Logistic fit successful: alpha={popt_logistic[0]:.2f}, beta={popt_logistic[1]:.2f}, R²={r_squared_logistic:.3f}")
        
    except Exception as e:
        logger.warning(f"Logistic fit failed: {e}")
    
    # Fit cumulative Gaussian function
    try:
        # Initial parameters: [mu, sigma]
        p0_gaussian = [x_median, initial_slope]
        bounds_gaussian = ([x_data.min() - x_range, 0.1], [x_data.max() + x_range, x_range*2])
        
        popt_gaussian, _ = curve_fit(
            lambda x, mu, sigma: cumulative_gaussian_psychometric(x, mu, sigma, 0.0, 0.02),
            x_data, y_data,
            p0=p0_gaussian,
            bounds=bounds_gaussian,
            maxfev=2000
        )
        
        # Calculate R-squared
        y_pred_gaussian = cumulative_gaussian_psychometric(x_data, *popt_gaussian, 0.0, 0.02)
        ss_res = np.sum((y_data - y_pred_gaussian) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared_gaussian = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Generate smooth fitted curve
        y_smooth_gaussian = cumulative_gaussian_psychometric(x_smooth, *popt_gaussian, 0.0, 0.02)
        
        results['gaussian'] = {
            'success': True,
            'params': {'mu': popt_gaussian[0], 'sigma': popt_gaussian[1]},
            'r_squared': r_squared_gaussian,
            'fitted_curve': {'x': x_smooth, 'y': y_smooth_gaussian}
        }
        
        logger.info(f"Gaussian fit successful: mu={popt_gaussian[0]:.2f}, sigma={popt_gaussian[1]:.2f}, R²={r_squared_gaussian:.3f}")
        
    except Exception as e:
        logger.warning(f"Gaussian fit failed: {e}")
    
    return results

def plot_psychometric_function(trial_data: List[Dict[str, Any]]) -> None:
    """
    Plot psychometric function for MTF clarity data with proper curve fitting
    
    Args:
        trial_data: List of trial dictionaries containing experimental data
    """
    try:
        if not trial_data:
            st.warning("沒有試驗資料可供繪製")
            return

        df = pd.DataFrame(trial_data)
        
        # Check required columns
        required_columns = ['mtf_value', 'response']
        if not all(col in df.columns for col in required_columns):
            st.error(f"缺少必要的資料欄位: {required_columns}")
            _show_available_columns(df)
            return

        # Convert response to numeric if needed
        df['response_numeric'] = df['response'].apply(
            lambda x: 1 if x == 'clear' else 0 if x == 'not_clear' else x
        )

        # Group by MTF value and calculate proportion clear
        grouped = df.groupby('mtf_value').agg({
            'response_numeric': ['count', 'sum', 'mean'],
            'reaction_time': 'mean' if 'reaction_time' in df.columns else lambda x: np.nan
        }).round(3)

        # Flatten column names
        grouped.columns = ['n_trials', 'n_clear', 'prop_clear', 'mean_rt']
        grouped = grouped.reset_index()

        # Filter groups with sufficient data
        grouped = grouped[grouped['n_trials'] >= 1]

        if len(grouped) == 0:
            st.warning("沒有足夠的數據點繪製心理計量函數")
            return

        # Prepare data for fitting
        x_data = grouped['mtf_value'].values
        y_data = grouped['prop_clear'].values
        
        # Fit psychometric functions
        fit_results = fit_psychometric_functions(x_data, y_data)

        # Create the plot with fitted curves
        _create_psychometric_plot_with_fits(grouped, df, fit_results)
        
        # Show fitting results
        _show_fitting_results(fit_results)
        
        # Show detailed results
        _show_detailed_results(grouped, df)
        
    except Exception as e:
        logger.error(f"Error plotting psychometric function: {e}")
        st.error(f"繪製心理計量函數時發生錯誤: {e}")

def _create_psychometric_plot_with_fits(grouped: pd.DataFrame, df: pd.DataFrame, fit_results: Dict[str, Any]) -> None:
    """Create the psychometric function plot with fitted curves"""
    try:
        fig = go.Figure()

        # Add raw data points (scatter plot)
        fig.add_trace(go.Scatter(
            x=grouped['mtf_value'],
            y=grouped['prop_clear'],
            mode='markers',
            marker=dict(
                size=np.maximum(grouped['n_trials'] * 4, 10),  # Size based on number of trials
                color=grouped['mean_rt'] if 'reaction_time' in df.columns else 'black',
                colorscale='Viridis',
                showscale=True if 'reaction_time' in df.columns else False,
                colorbar=dict(title="平均反應時間 (秒)") if 'reaction_time' in df.columns else None,
                line=dict(width=1, color='white'),
                opacity=0.8
            ),
            name='原始數據',
            hovertemplate=
            'MTF 值: %{x:.1f}<br>' +
            '清楚比例: %{y:.2f}<br>' +
            '試驗次數: %{text}<br>' +
            ('平均反應時間: %{marker.color:.2f}秒<br>' if 'reaction_time' in df.columns else '') +
            '<extra></extra>',
            text=grouped['n_trials']
        ))

        # Add fitted curves
        colors = {'logistic': 'blue', 'gaussian': 'red'}
        line_styles = {'logistic': 'solid', 'gaussian': 'dash'}
        
        for model_name, result in fit_results.items():
            if result['success'] and result['fitted_curve'] is not None:
                model_label = 'Logistic 擬合' if model_name == 'logistic' else 'Gaussian 擬合'
                fig.add_trace(go.Scatter(
                    x=result['fitted_curve']['x'],
                    y=result['fitted_curve']['y'],
                    mode='lines',
                    line=dict(
                        width=3, 
                        color=colors[model_name],
                        dash=line_styles[model_name]
                    ),
                    name=f"{model_label} (R²={result['r_squared']:.3f})",
                    hovertemplate=f'{model_label}<br>MTF: %{{x:.1f}}<br>P(清楚): %{{y:.3f}}<extra></extra>'
                ))

        # Add 50% threshold line
        fig.add_hline(
            y=0.5, 
            line_dash="dot", 
            line_color="gray", 
            annotation_text="50% 閾值",
            annotation_position="top right"
        )

        # Add threshold markers for successful fits
        for model_name, result in fit_results.items():
            if result['success']:
                if model_name == 'logistic':
                    threshold = result['params']['alpha']
                    model_label = 'Logistic'
                else:
                    threshold = result['params']['mu']
                    model_label = 'Gaussian'
                
                fig.add_vline(
                    x=threshold,
                    line_dash="dot",
                    line_color=colors[model_name],
                    annotation_text=f"{model_label} 閾值: {threshold:.1f}",
                    annotation_position="top"
                )

        # Update layout
        fig.update_layout(
            title="心理計量函數 - MTF 清晰度判斷（含模型適配）",
            xaxis_title="MTF 值",
            yaxis_title="回應「清楚」的比例",
            xaxis=dict(range=[0, 99]),
            yaxis=dict(range=[-0.05, 1.05], tickformat='.0%'),
            width=800,
            height=600,
            showlegend=True,
            hovermode='closest',
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            )
        )

        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error creating plot with fits: {e}")
        st.error("繪製適配曲線時發生錯誤")

def _show_fitting_results(fit_results: Dict[str, Any]) -> None:
    """Show psychometric function fitting results"""
    try:
        st.subheader("🔬 心理計量函數適配結果")
        
        successful_fits = [name for name, result in fit_results.items() if result['success']]
        
        if not successful_fits:
            st.warning("⚠️ 模型適配失敗。可能需要更多數據點或數據範圍更廣。")
            return
        
        # Create columns for each successful fit
        cols = st.columns(len(successful_fits))
        
        for i, model_name in enumerate(successful_fits):
            result = fit_results[model_name]
            with cols[i]:
                if model_name == 'logistic':
                    st.markdown("#### 📈 Logistic 模型")
                    st.metric("閾值 (α)", f"{result['params']['alpha']:.2f}")
                    st.metric("斜率 (β)", f"{result['params']['beta']:.2f}")
                    st.metric("適配度 (R²)", f"{result['r_squared']:.3f}")
                    
                    # Interpretation
                    if result['params']['beta'] < 5:
                        slope_desc = "陡峭（敏感度高）"
                    elif result['params']['beta'] < 15:
                        slope_desc = "中等"
                    else:
                        slope_desc = "平緩（敏感度低）"
                    st.caption(f"斜率: {slope_desc}")
                    
                else:  # gaussian
                    st.markdown("#### 📊 Gaussian 模型")
                    st.metric("閾值 (μ)", f"{result['params']['mu']:.2f}")
                    st.metric("標準差 (σ)", f"{result['params']['sigma']:.2f}")
                    st.metric("適配度 (R²)", f"{result['r_squared']:.3f}")
                    
                    # Interpretation
                    if result['params']['sigma'] < 5:
                        sigma_desc = "低變異性（穩定）"
                    elif result['params']['sigma'] < 15:
                        sigma_desc = "中等變異性"
                    else:
                        sigma_desc = "高變異性（不穩定）"
                    st.caption(f"變異性: {sigma_desc}")
        
        # Model comparison if both successful
        if len(successful_fits) == 2:
            st.markdown("#### 🆚 模型比較")
            logistic_r2 = fit_results['logistic']['r_squared']
            gaussian_r2 = fit_results['gaussian']['r_squared']
            
            if logistic_r2 > gaussian_r2:
                best_model = "Logistic"
                r2_diff = logistic_r2 - gaussian_r2
            else:
                best_model = "Gaussian"
                r2_diff = gaussian_r2 - logistic_r2
            
            st.info(f"📌 **最佳模型**: {best_model} (R² 差異: +{r2_diff:.3f})")
            
    except Exception as e:
        logger.error(f"Error showing fitting results: {e}")
        st.error("顯示擬合結果時發生錯誤")

def _create_psychometric_plot(grouped: pd.DataFrame, df: pd.DataFrame) -> None:
    """Create the psychometric function plot"""
    try:
        fig = go.Figure()

        # Add main data trace
        fig.add_trace(go.Scatter(
            x=grouped['mtf_value'],
            y=grouped['prop_clear'],
            mode='markers+lines',
            marker=dict(
                size=np.maximum(grouped['n_trials'] * 3, 8),  # Minimum size of 8
                color=grouped['mean_rt'] if 'reaction_time' in df.columns else 'blue',
                colorscale='Viridis',
                showscale=True if 'reaction_time' in df.columns else False,
                colorbar=dict(title="平均反應時間 (秒)") if 'reaction_time' in df.columns else None,
                line=dict(width=1, color='white')
            ),
            line=dict(width=2, color='blue'),
            name='觀察數據',
            hovertemplate=
            'MTF 值: %{x:.1f}<br>' +
            '清楚比例: %{y:.2f}<br>' +
            '試驗次數: %{text}<br>' +
            ('平均反應時間: %{marker.color:.2f}秒<br>' if 'reaction_time' in df.columns else '') +
            '<extra></extra>',
            text=grouped['n_trials']
        ))

        # Add 50% threshold line
        fig.add_hline(
            y=0.5, 
            line_dash="dash", 
            line_color="red", 
            annotation_text="50% 閾值",
            annotation_position="top right"
        )

        # Estimate and add threshold line
        threshold_estimate = _estimate_threshold(grouped)
        if threshold_estimate is not None:
            fig.add_vline(
                x=threshold_estimate,
                line_dash="dash",
                line_color="orange",
                annotation_text=f"估計閾值: {threshold_estimate:.1f}",
                annotation_position="top"
            )

        # Update layout
        fig.update_layout(
            title="心理計量函數 - MTF 清晰度判斷",
            xaxis_title="MTF 值",
            yaxis_title="回應「清楚」的比例",
            xaxis=dict(range=[0, 99]),
            yaxis=dict(range=[0, 1], tickformat='.0%'),
            width=700,
            height=500,
            showlegend=True,
            hovermode='closest'
        )

        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error creating plot: {e}")
        st.error("繪製圖表時發生錯誤")

def _estimate_threshold(grouped: pd.DataFrame) -> Optional[float]:
    """Estimate the 50% threshold from the data"""
    try:
        if len(grouped) < 2:
            return None
        
        # Sort by MTF value
        sorted_data = grouped.sort_values('mtf_value')
        
        # Simple linear interpolation to find 50% point
        x_vals = sorted_data['mtf_value'].values
        y_vals = sorted_data['prop_clear'].values
        
        # Check if we have data points around 0.5
        if y_vals.min() <= 0.5 <= y_vals.max():
            threshold = np.interp(0.5, y_vals, x_vals)
            return threshold
        else:
            # Extrapolate if needed
            if len(x_vals) >= 2:
                # Use linear fit
                slope, intercept = np.polyfit(x_vals, y_vals, 1)
                if slope != 0:
                    threshold = (0.5 - intercept) / slope
                    return threshold
        
        return None
        
    except Exception as e:
        logger.warning(f"Could not estimate threshold: {e}")
        return None

def _show_detailed_results(grouped: pd.DataFrame, df: pd.DataFrame) -> None:
    """Show detailed results table"""
    try:
        with st.expander("📊 詳細結果數據"):
            # Format the grouped data for display
            display_df = grouped.copy()
            
            # Rename columns for Chinese display
            column_mapping = {
                'mtf_value': 'MTF 值',
                'n_trials': '試驗次數',
                'n_clear': '清楚回應數',
                'prop_clear': '清楚比例',
                'mean_rt': '平均反應時間'
            }
            
            display_df = display_df.rename(columns=column_mapping)
            
            # Format values
            if '清楚比例' in display_df.columns:
                display_df['清楚比例'] = display_df['清楚比例'].apply(lambda x: f"{x:.1%}")
            
            if '平均反應時間' in display_df.columns and not display_df['平均反應時間'].isna().all():
                display_df['平均反應時間'] = display_df['平均反應時間'].apply(
                    lambda x: f"{x:.3f}秒" if not pd.isna(x) else "N/A"
                )
            else:
                # Remove the column if all values are NaN
                display_df = display_df.drop(columns=['平均反應時間'], errors='ignore')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Summary statistics
            st.markdown("### 📈 統計摘要")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("總試驗數", len(df))
            
            with col2:
                overall_clear_rate = df['response_numeric'].mean() if 'response_numeric' in df.columns else 0
                st.metric("整體清楚率", f"{overall_clear_rate:.1%}")
            
            with col3:
                if 'reaction_time' in df.columns:
                    avg_rt = df['reaction_time'].mean()
                    st.metric("平均反應時間", f"{avg_rt:.2f}秒")
                else:
                    st.metric("反應時間", "N/A")
            
    except Exception as e:
        logger.error(f"Error showing detailed results: {e}")
        st.error("顯示詳細結果時發生錯誤")

def _show_available_columns(df: pd.DataFrame) -> None:
    """Show available columns in the dataframe"""
    with st.expander("📋 可用的資料欄位"):
        st.write("**找到的欄位:**")
        for col in df.columns:
            st.write(f"- {col}: {df[col].dtype}")
        
        st.write("**資料預覽:**")
        st.dataframe(df.head(), use_container_width=True)

def analyze_experiment_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze experimental data and return summary statistics
    
    Args:
        df: DataFrame containing experimental data
        
    Returns:
        Dictionary containing analysis results
    """
    try:
        analysis = {}
        
        # Basic statistics
        analysis['total_trials'] = len(df)
        
        if 'response' in df.columns:
            clear_responses = (df['response'] == 'clear').sum()
            analysis['clear_responses'] = clear_responses
            analysis['clear_rate'] = clear_responses / len(df) if len(df) > 0 else 0
        
        if 'reaction_time' in df.columns:
            rt_data = df['reaction_time'].dropna()
            if len(rt_data) > 0:
                analysis['mean_rt'] = rt_data.mean()
                analysis['median_rt'] = rt_data.median()
                analysis['std_rt'] = rt_data.std()
        
        if 'mtf_value' in df.columns:
            mtf_data = df['mtf_value'].dropna()
            if len(mtf_data) > 0:
                analysis['mtf_range'] = (mtf_data.min(), mtf_data.max())
                analysis['mtf_mean'] = mtf_data.mean()
        
        # Participant info
        if 'participant_id' in df.columns:
            analysis['participant_ids'] = df['participant_id'].unique().tolist()
        
        # Stimulus info
        if 'stimulus_image_file' in df.columns:
            analysis['stimulus_files'] = df['stimulus_image_file'].unique().tolist()
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing data: {e}")
        return {'error': str(e)}