"""
Pixel Perfect 測試工具
用於驗證顯示系統是否真正達到像素完美控制

Author: EJ_CHANG
Created: 2025-01-22
"""

import streamlit as st
import numpy as np
from PIL import Image
import base64
import io
from utils.display_calibration import get_display_calibration

def create_pixel_perfect_test_pattern(width_px: int = 300, height_px: int = 300):
    """創建像素完美測試圖案"""
    # 創建棋盤格模式
    pattern = np.zeros((height_px, width_px, 3), dtype=np.uint8)
    
    # 5px × 5px 的棋盤格
    block_size = 5
    for i in range(0, height_px, block_size):
        for j in range(0, width_px, block_size):
            if (i // block_size + j // block_size) % 2 == 0:
                pattern[i:i+block_size, j:j+block_size] = [255, 255, 255]  # 白色
            else:
                pattern[i:i+block_size, j:j+block_size] = [0, 0, 0]        # 黑色
    
    return Image.fromarray(pattern)

def create_ruler_test_pattern():
    """創建毫米刻度尺測試圖案"""
    # 創建 100mm × 20mm 的刻度尺 (假設96 DPI)
    width_mm = 100
    height_mm = 20
    
    # 根據校準系統計算像素尺寸
    calibration = get_display_calibration()
    display_info = calibration.get_display_info()
    
    if display_info and display_info.pixel_size_mm:
        width_px = int(width_mm / display_info.pixel_size_mm)
        height_px = int(height_mm / display_info.pixel_size_mm)
        actual_dpi = int(25.4 / display_info.pixel_size_mm)
    else:
        # 使用96 DPI作為預設
        width_px = int(width_mm * 96 / 25.4)  # 378 pixels
        height_px = int(height_mm * 96 / 25.4)  # 76 pixels
        actual_dpi = 96
    
    pattern = np.ones((height_px, width_px, 3), dtype=np.uint8) * 255  # 白色背景
    
    # 繪製毫米刻度線
    for mm in range(0, width_mm + 1):
        x_pos = int(mm * width_px / width_mm)
        if x_pos < width_px:
            if mm % 10 == 0:  # 10mm 主刻度線
                pattern[:, x_pos:x_pos+2] = [255, 0, 0]  # 紅色粗線
            elif mm % 5 == 0:  # 5mm 刻度線
                pattern[:height_px//2, x_pos] = [0, 0, 0]  # 黑色中線
            else:  # 1mm 刻度線
                pattern[:height_px//4, x_pos] = [128, 128, 128]  # 灰色短線
    
    return Image.fromarray(pattern), width_px, height_px, actual_dpi

def main():
    st.title("🎯 Pixel Perfect 驗證測試")
    st.markdown("這個工具用於測試你的顯示系統是否真正達到像素完美控制。")
    
    # 獲取顯示校準狀態
    calibration = get_display_calibration()
    status = calibration.get_calibration_status()
    
    st.subheader("📊 當前校準狀態")
    if status['status'] == 'success':
        st.success(status['message'])
    elif status['status'] == 'warning':
        st.warning(status['message'])
    else:
        st.error(status['message'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("檢測方法", status.get('method', 'unknown'))
    with col2:
        st.metric("信心度", f"{status.get('confidence', 0):.1%}")
    with col3:
        st.metric("像素大小", f"{status.get('pixel_size_mm', 0):.4f} mm")
    
    st.markdown("---")
    
    # 測試選項
    test_type = st.selectbox(
        "選擇測試類型",
        ["棋盤格模式", "毫米刻度尺", "手動校準界面"]
    )
    
    if test_type == "棋盤格模式":
        st.subheader("🏁 棋盤格測試圖案")
        st.markdown("此圖案每個方格都是精確的 5×5 像素。如果你看到模糊或縮放，表示未達到 pixel perfect。")
        
        # 創建測試圖案
        test_image = create_pixel_perfect_test_pattern()
        
        # 轉換為可顯示格式
        buffer = io.BytesIO()
        test_image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # 使用pixel perfect CSS顯示
        pixel_perfect_css = calibration.get_pixel_perfect_css(300, 300)
        
        st.markdown(
            f'<img src="data:image/png;base64,{img_str}" style="{pixel_perfect_css}" />',
            unsafe_allow_html=True
        )
        
        st.markdown("**驗證方法：**")
        st.markdown("- 每個方格應該是清晰的5×5像素正方形")
        st.markdown("- 邊界應該是銳利的，沒有模糊或抗鋸齒")
        st.markdown("- 縮放瀏覽器時圖案不應該變化")
        
    elif test_type == "毫米刻度尺":
        st.subheader("📏 毫米刻度尺測試")
        st.markdown("使用實體尺子測量下面的刻度尺，驗證物理尺寸是否正確。")
        
        ruler_image, width_px, height_px, dpi = create_ruler_test_pattern()
        
        # 轉換為可顯示格式
        buffer = io.BytesIO()
        ruler_image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # 使用pixel perfect CSS顯示
        pixel_perfect_css = calibration.get_pixel_perfect_css(width_px, height_px)
        
        st.markdown(f"**測試參數：** 100mm × 20mm (使用 DPI: {dpi})")
        st.markdown(f"**像素尺寸：** {width_px} × {height_px} pixels")
        
        st.markdown(
            f'<img src="data:image/png;base64,{img_str}" style="{pixel_perfect_css}" />',
            unsafe_allow_html=True
        )
        
        st.markdown("**驗證方法：**")
        st.markdown("1. 使用實體尺子測量上面刻度尺的總長度")
        st.markdown("2. 總長度應該是 **100.0 mm**")  
        st.markdown("3. 紅色粗線之間的間距應該是 **10.0 mm**")
        st.markdown("4. 如果測量不準確，表示需要重新校準")
        
        # 測量結果輸入
        st.markdown("---")
        st.subheader("📝 測量結果")
        measured_length = st.number_input(
            "請輸入你測量到的刻度尺總長度 (mm)",
            min_value=50.0,
            max_value=150.0,
            value=100.0,
            step=0.1
        )
        
        if measured_length != 100.0:
            error_percent = abs(measured_length - 100.0) / 100.0 * 100
            if error_percent > 5:
                st.error(f"❌ 誤差過大：{error_percent:.1f}% (測量: {measured_length}mm)")
                st.error("建議進行手動校準")
            elif error_percent > 2:
                st.warning(f"⚠️ 誤差較大：{error_percent:.1f}% (測量: {measured_length}mm)")
                st.warning("可考慮手動校準以提高精確度")
            else:
                st.success(f"✅ 誤差可接受：{error_percent:.1f}% (測量: {measured_length}mm)")
        else:
            st.success("✅ 完美！像素完美控制正常運作")
    
    elif test_type == "手動校準界面":
        st.subheader("🔧 手動校準")
        calibration.create_manual_calibration_interface()
    
    # 額外診斷資訊
    st.markdown("---")
    st.subheader("🔍 診斷資訊")
    
    with st.expander("詳細校準資訊"):
        display_info = calibration.get_display_info()
        if display_info:
            st.json({
                "解析度": f"{display_info.width_pixels} × {display_info.height_pixels}",
                "DPI": f"{display_info.dpi_x:.2f} × {display_info.dpi_y:.2f}",
                "像素大小": f"{display_info.pixel_size_mm:.6f} mm",
                "檢測方法": display_info.detected_method,
                "信心度": f"{display_info.confidence:.2%}",
                "devicePixelRatio": getattr(display_info, 'device_pixel_ratio', 'unknown')
            })
        else:
            st.error("無法獲取顯示器資訊")
    
    st.markdown("---")
    st.markdown("**使用說明：**")
    st.markdown("1. 先檢查校準狀態是否正常")
    st.markdown("2. 使用棋盤格測試檢查像素銳利度")
    st.markdown("3. 使用刻度尺測試檢查物理尺寸準確性")
    st.markdown("4. 如果測試不通過，使用手動校準")

if __name__ == "__main__":
    main()