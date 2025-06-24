"""
Response button components for WebRS MTF Threshold experiment.
"""
import streamlit as st
from typing import Optional, Tuple, Callable
from utils.logger import get_logger

logger = get_logger(__name__)

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