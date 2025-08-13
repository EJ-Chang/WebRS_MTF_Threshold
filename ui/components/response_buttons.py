"""
Response button components for WebRS MTF Threshold experiment.
"""
import streamlit as st
from typing import Optional, Tuple, Callable
from utils.logger import get_logger

logger = get_logger(__name__)

def apply_ui_scaling():
    """Apply 1.5x scaling to UI elements"""
    st.markdown("""
    <style>
    /* True 1.5x scaling for buttons */
    .stButton > button {
        height: auto;
        padding: 1.125rem 2.25rem !important;  /* 1.5x of 0.75rem 1.5rem */
        font-size: 1.5rem !important;  /* True 1.5x scaling */
        font-weight: 600 !important;
        border-radius: 0.75rem !important;  /* 1.5x of 0.5rem */
        min-height: 4.5rem !important;  /* 1.5x of 3rem */
    }
    
    /* Scale button text and icons */
    .stButton > button p {
        font-size: 1.5rem !important;  /* True 1.5x scaling */
        margin: 0 !important;
    }
    
    /* Scale primary buttons */
    .stButton > button[kind="primary"] {
        height: auto;
        padding: 1.125rem 2.25rem !important;  /* 1.5x scaling */
        font-size: 1.5rem !important;  /* True 1.5x scaling */
        min-height: 4.5rem !important;  /* 1.5x of 3rem */
    }
    
    /* Scale secondary buttons */
    .stButton > button[kind="secondary"] {
        height: auto;
        padding: 1.125rem 2.25rem !important;  /* 1.5x scaling */
        font-size: 1.5rem !important;  /* True 1.5x scaling */
        min-height: 4.5rem !important;  /* 1.5x of 3rem */
    }
    
    /* Scale text input labels */
    .stTextInput label {
        font-size: 1.5rem !important;  /* True 1.5x scaling */
        font-weight: 600 !important;
    }
    
    /* Scale text input fields */
    .stTextInput input {
        font-size: 1.5rem !important;  /* True 1.5x scaling */
        padding: 1.125rem !important;  /* 1.5x of 0.75rem */
    }
    
    /* Scale headers and text - True 1.5x scaling */
    h1 {
        font-size: 3.375rem !important;  /* 1.5x of 2.25rem (36px → 54px) */
    }
    
    h2 {
        font-size: 2.8125rem !important;  /* 1.5x of 1.875rem (30px → 45px) */
    }
    
    h3 {
        font-size: 2.25rem !important;  /* 1.5x of 1.5rem (24px → 36px) */
    }
    
    /* Scale general text - True 1.5x scaling */
    .stMarkdown p {
        font-size: 1.5rem !important;  /* 1.5x of 1rem (16px → 24px) */
        line-height: 1.65 !important;  /* Adjusted for larger text */
    }
    
    /* Scale all markdown text elements */
    .stMarkdown {
        font-size: 1.5rem !important;  /* True 1.5x scaling */
    }
    
    /* Scale metrics */
    .metric-container {
        font-size: 1.5rem !important;  /* True 1.5x scaling */
    }
    
    /* Scale checkbox text */
    .stCheckbox label {
        font-size: 1.5rem !important;  /* True 1.5x scaling */
    }
    
    /* Scale expander text */
    .streamlit-expanderHeader {
        font-size: 1.5rem !important;  /* True 1.5x scaling */
    }
    
    /* Scale sidebar text */
    .css-1d391kg {
        font-size: 1.5rem !important;
    }
    
    /* Scale info/warning/error boxes */
    .stAlert {
        font-size: 1.5rem !important;
    }
    
    /* Scale success messages */
    .stSuccess {
        font-size: 1.5rem !important;
    }
    
    /* Scale file uploader text */
    .stFileUploader label {
        font-size: 1.5rem !important;
    }
    
    /* Scale column text */
    .stColumns {
        font-size: 1.5rem !important;
    }
    
    /* Scale caption text */
    .stImage figcaption {
        font-size: 1.35rem !important;  /* Slightly smaller than main text but still scaled */
    }
    
    /* === 修正遺漏的介面文字元素 1.5x 放大 === */
    
    /* 修正 st.write 內的列表項目 */
    .stMarkdown ul li {
        font-size: 1.5rem !important;  /* 列表項目 1.5x */
        line-height: 1.65 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stMarkdown ol li {
        font-size: 1.5rem !important;  /* 編號列表項目 1.5x */
        line-height: 1.65 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* 修正粗體文字 */
    .stMarkdown strong {
        font-size: 1.5rem !important;  /* 粗體文字 1.5x */
    }
    
    .stMarkdown b {
        font-size: 1.5rem !important;  /* 粗體文字 1.5x */
    }
    
    /* 修正 help 提示文字 */
    .stTextInput .help-tooltip {
        font-size: 1.35rem !important;  /* Help 文字略小但仍放大 */
    }
    
    .stCheckbox .help-tooltip {
        font-size: 1.35rem !important;
    }
    
    .stSelectbox .help-tooltip {
        font-size: 1.35rem !important;
    }
    
    /* 修正訊息框內容 */
    .stInfo {
        font-size: 1.5rem !important;
    }
    
    .stInfo .markdown-text-container {
        font-size: 1.5rem !important;
    }
    
    .stWarning {
        font-size: 1.5rem !important;
    }
    
    .stWarning .markdown-text-container {
        font-size: 1.5rem !important;
    }
    
    .stError {
        font-size: 1.5rem !important;
    }
    
    .stError .markdown-text-container {
        font-size: 1.5rem !important;
    }
    
    .stSuccess {
        font-size: 1.5rem !important;
    }
    
    .stSuccess .markdown-text-container {
        font-size: 1.5rem !important;
    }
    
    /* 修正三欄佈局中的文字 */
    .stColumns .stMarkdown {
        font-size: 1.5rem !important;
    }
    
    .stColumns .stMarkdown p {
        font-size: 1.5rem !important;
        line-height: 1.65 !important;
    }
    
    .stColumns .stMarkdown li {
        font-size: 1.5rem !important;
        line-height: 1.65 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stColumns .stMarkdown strong {
        font-size: 1.5rem !important;
    }
    
    /* 通用 Streamlit 內部元件修正 */
    [data-testid="stMarkdownContainer"] {
        font-size: 1.5rem !important;
    }
    
    [data-testid="stMarkdownContainer"] p {
        font-size: 1.5rem !important;
        line-height: 1.65 !important;
    }
    
    [data-testid="stMarkdownContainer"] li {
        font-size: 1.5rem !important;
        line-height: 1.65 !important;
    }
    
    [data-testid="stMarkdownContainer"] strong {
        font-size: 1.5rem !important;
    }
    
    /* 修正更多可能遺漏的元件 */
    .stTextArea label {
        font-size: 1.5rem !important;
    }
    
    .stNumberInput label {
        font-size: 1.5rem !important;
    }
    
    .stDateInput label {
        font-size: 1.5rem !important;
    }
    
    .stTimeInput label {
        font-size: 1.5rem !important;
    }
    
    /* 修正 DataFrame 顯示 */
    .stDataFrame {
        font-size: 1.35rem !important;  /* 表格文字略小但仍放大 */
    }
    
    /* 修正 JSON 顯示 */
    .stJson {
        font-size: 1.35rem !important;
    }
    
    /* 修正代碼塊顯示 */
    .stCodeBlock {
        font-size: 1.35rem !important;
    }
    
    /* 修正度量指標顯示 */
    .stMetric .metric-label {
        font-size: 1.35rem !important;
    }
    
    .stMetric .metric-value {
        font-size: 2.25rem !important;  /* 度量值更大 */
    }
    
    /* 確保所有容器內的文字都被放大 */
    .main .block-container {
        font-size: 1.5rem !important;
    }
    
    .main .block-container p {
        font-size: 1.5rem !important;
        line-height: 1.65 !important;
    }
    
    .main .block-container li {
        font-size: 1.5rem !important;
        line-height: 1.65 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def create_response_buttons(
    left_label: str = "不清楚",
    right_label: str = "清楚", 
    key_suffix: str = "",
    disabled: bool = False
) -> Tuple[bool, bool]:
    """
    Create standard response buttons for MTF experiment
    
    Args:
        left_label: Label for left button
        right_label: Label for right button  
        key_suffix: Suffix for button keys to ensure uniqueness
        disabled: Whether buttons should be disabled
        
    Returns:
        Tuple of (left_pressed, right_pressed)
    """
    try:
        # Apply UI scaling for buttons
        apply_ui_scaling()
        
        # Create two columns for side-by-side buttons
        col1, col2 = st.columns(2)
        
        with col1:
            left_pressed = st.button(
                f"👈 {left_label}",
                key=f"left_response_{key_suffix}",
                disabled=disabled,
                use_container_width=True,
                type="secondary"
            )
        
        with col2:
            right_pressed = st.button(
                f"👉 {right_label}",
                key=f"right_response_{key_suffix}",
                disabled=disabled,
                use_container_width=True,
                type="primary"
            )
        
        return left_pressed, right_pressed
        
    except Exception as e:
        logger.error(f"Error creating response buttons: {e}")
        return False, False

def create_navigation_buttons(
    show_back: bool = True,
    show_next: bool = True,
    back_label: str = "返回",
    next_label: str = "下一步",
    next_disabled: bool = False,
    key_suffix: str = ""
) -> Tuple[bool, bool]:
    """
    Create navigation buttons (back/next)
    
    Args:
        show_back: Whether to show back button
        show_next: Whether to show next button
        back_label: Label for back button
        next_label: Label for next button
        next_disabled: Whether next button is disabled
        key_suffix: Suffix for button keys
        
    Returns:
        Tuple of (back_pressed, next_pressed)
    """
    try:
        # Apply UI scaling for buttons
        apply_ui_scaling()
        
        cols = st.columns([1, 1] if show_back and show_next else [1])
        
        back_pressed = False
        next_pressed = False
        
        if show_back and show_next:
            with cols[0]:
                back_pressed = st.button(
                    f"⬅️ {back_label}",
                    key=f"back_nav_{key_suffix}",
                    use_container_width=True
                )
            with cols[1]:
                next_pressed = st.button(
                    f"➡️ {next_label}",
                    key=f"next_nav_{key_suffix}",
                    disabled=next_disabled,
                    use_container_width=True,
                    type="primary"
                )
        elif show_next:
            with cols[0]:
                next_pressed = st.button(
                    f"➡️ {next_label}",
                    key=f"next_nav_{key_suffix}",
                    disabled=next_disabled,
                    use_container_width=True,
                    type="primary"
                )
        elif show_back:
            with cols[0]:
                back_pressed = st.button(
                    f"⬅️ {back_label}",
                    key=f"back_nav_{key_suffix}",
                    use_container_width=True
                )
        
        return back_pressed, next_pressed
        
    except Exception as e:
        logger.error(f"Error creating navigation buttons: {e}")
        return False, False

def create_action_button(
    label: str,
    button_type: str = "primary",
    disabled: bool = False,
    key: Optional[str] = None,
    on_click: Optional[Callable] = None,
    full_width: bool = True
) -> bool:
    """
    Create a single action button
    
    Args:
        label: Button label
        button_type: Button type ('primary', 'secondary')
        disabled: Whether button is disabled
        key: Unique key for button
        on_click: Callback function
        full_width: Whether to use full container width
        
    Returns:
        Whether button was pressed
    """
    try:
        # Apply UI scaling for buttons
        apply_ui_scaling()
        
        return st.button(
            label,
            key=key,
            disabled=disabled,
            type=button_type,
            on_click=on_click,
            use_container_width=full_width
        )
    except Exception as e:
        logger.error(f"Error creating action button: {e}")
        return False

def create_start_button(
    experiment_name: str = "實驗",
    key_suffix: str = "",
    disabled: bool = False
) -> bool:
    """
    Create experiment start button
    
    Args:
        experiment_name: Name of the experiment
        key_suffix: Suffix for button key
        disabled: Whether button is disabled
        
    Returns:
        Whether button was pressed
    """
    try:
        # Apply UI scaling for buttons
        apply_ui_scaling()
        
        return st.button(
            f"🚀 開始{experiment_name}",
            key=f"start_experiment_{key_suffix}",
            disabled=disabled,
            type="primary",
            use_container_width=True
        )
    except Exception as e:
        logger.error(f"Error creating start button: {e}")
        return False

def create_reset_button(
    label: str = "重新開始",
    key_suffix: str = "",
    confirmation: bool = True
) -> bool:
    """
    Create reset button with optional confirmation
    
    Args:
        label: Button label
        key_suffix: Suffix for button key
        confirmation: Whether to show confirmation dialog
        
    Returns:
        Whether reset was confirmed
    """
    try:
        # Use session state to track confirmation phase
        confirm_key = f"reset_confirm_{key_suffix}"
        
        # Check if we're in confirmation phase
        if st.session_state.get(confirm_key, False):
            st.warning("⚠️ 確定要重新開始嗎？這將清除所有當前進度。")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("取消", key=f"cancel_reset_{key_suffix}"):
                    st.session_state[confirm_key] = False
                    st.rerun()
            with col2:
                if st.button(
                    "確認重新開始", 
                    key=f"confirm_reset_{key_suffix}",
                    type="primary"
                ):
                    st.session_state[confirm_key] = False
                    return True
            return False
        else:
            # Show initial reset button
            if st.button(
                f"🔄 {label}",
                key=f"reset_{key_suffix}",
                type="secondary"
            ):
                if confirmation:
                    st.session_state[confirm_key] = True
                    st.rerun()
                else:
                    return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error creating reset button: {e}")
        return False

def create_keyboard_shortcuts_info() -> None:
    """Display keyboard shortcuts information"""
    try:
        with st.expander("⌨️ 鍵盤快捷鍵"):
            st.markdown("""
            - **←** (左箭頭): 選擇「不清楚」
            - **→** (右箭頭): 選擇「清楚」  
            - **Space**: 繼續下一試驗
            - **R**: 重新開始實驗
            - **Q**: 退出實驗
            """)
    except Exception as e:
        logger.error(f"Error showing keyboard shortcuts: {e}")

def create_practice_mode_toggle(
    current_state: bool = False,
    key_suffix: str = ""
) -> bool:
    """
    Create practice mode toggle
    
    Args:
        current_state: Current practice mode state
        key_suffix: Suffix for widget key
        
    Returns:
        New practice mode state
    """
    try:
        return st.checkbox(
            "🎯 練習模式",
            value=current_state,
            key=f"practice_mode_{key_suffix}",
            help="在練習模式中，您可以熟悉實驗流程，結果不會被記錄"
        )
    except Exception as e:
        logger.error(f"Error creating practice mode toggle: {e}")
        return current_state