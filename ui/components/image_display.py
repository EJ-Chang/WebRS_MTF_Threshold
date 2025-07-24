"""
Image display components for WebRS MTF Threshold experiment.
"""
import streamlit as st
import numpy as np
import cv2
import time
import base64
from PIL import Image
from io import BytesIO
from typing import Optional, Dict, Any, Tuple, List
from utils.logger import get_logger

logger = get_logger(__name__)



def crop_image_center(image_array: np.ndarray) -> Optional[np.ndarray]:
    """
    Crop image to maintain original cropped dimensions without resizing
    
    Args:
        image_array: Input image array
        
    Returns:
        Original image array (no cropping or resizing applied)
    """
    if image_array is None:
        return None
    
    # Return original image without any modifications
    # Cropping logic is handled in mtf_experiment.py load_and_prepare_image function
    return image_array

def display_mtf_stimulus_image(image_data: Any, caption: str = "") -> Optional[Dict[str, Any]]:
    """
    Display MTF stimulus image with fixed container size and automatic scaling
    
    Args:
        image_data: Image data (various formats supported)
        caption: Optional caption for the image
        
    Returns:
        Dict with container dimensions for button positioning
    """
    if image_data is None:
        st.error("❌ Stimulus image not available")
        return None

    try:
        # Process image data format
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                # Extract base64 data
                base64_data = image_data.split(',')[1]
                img_bytes = base64.b64decode(base64_data)
                img = Image.open(BytesIO(img_bytes))
                image_array = np.array(img)
            else:
                st.error("❌ Invalid image data format")
                return None
        elif isinstance(image_data, np.ndarray):
            image_array = image_data
        else:
            try:
                image_array = np.array(image_data)
            except Exception as e:
                st.error(f"❌ Failed to convert to numpy array: {e}")
                return None

        if not isinstance(image_array, np.ndarray):
            st.error("❌ Invalid image array")
            return None

        # Use original image without forcing pixel-perfect cropping
        processed_img = crop_image_center(image_array)
        if processed_img is None:
            processed_img = image_array

        # Convert to PIL for display
        img_pil = Image.fromarray(processed_img)

        # Convert to base64 for HTML display
        buffer = BytesIO()
        img_pil.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        # Add unique ID for CSS targeting
        img_id = f"mtf_img_{int(time.time() * 1000)}"
        original_h, original_w = processed_img.shape[:2]

        # Fixed container dimensions (910x1080)
        container_width = 910
        container_height = 1080

        # Simple container and image styles for automatic scaling
        container_style = (
            f"text-align: center; "
            f"margin: 20px auto; "
            f"width: {container_width}px; "
            f"height: {container_height}px; "
            f"display: flex; "
            f"flex-direction: column; "
            f"align-items: center; "
            f"justify-content: center; "
            f"position: relative; "
            f"border: 1px solid #ddd; "  # Optional: visual container boundary
        )

        # Simple image style with automatic scaling
        image_style = (
            f"max-width: 100%; "
            f"max-height: calc(100% - 40px); "  # Reserve space for caption
            f"width: auto; "
            f"height: auto; "
            f"object-fit: contain; "
            f"object-position: center; "
            f"display: block; "
            f"-webkit-user-select: none; "
            f"-moz-user-select: none; "
            f"-ms-user-select: none; "
            f"user-select: none; "
        )
        
        # Simplified CSS without pixel-perfect constraints
        global_css = f"""
        <style>
        #{img_id} {{
            max-width: 100%;
            max-height: calc(100% - 40px);
            width: auto;
            height: auto;
            object-fit: contain;
            object-position: center;
            display: block;
        }}
        /* Ensure parent container respects fixed size */
        .stMarkdown > div > div:has(#{img_id}) {{
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            width: 100%;
        }}
        </style>
        """
        
        html_content = f"""
        {global_css}
        <div style="{container_style}">
            <img id="{img_id}" src="data:image/png;base64,{img_str}" 
                 style="{image_style}"
                 draggable="false">
            <p style="margin: 10px 0; color: #666; font-size: 14px; text-align: center; position: absolute; bottom: 5px; width: 100%;">{caption}</p>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)

        # Log image display for debugging
        logger.debug(f"🖼️ 顯示圖像: 原始尺寸 {original_w}x{original_h} 像素 | 容器尺寸: {container_width}x{container_height} 像素")

        # Return container dimensions for button positioning
        return {
            'display_height': container_height,
            'center_position': container_height / 2,
            'original_width': original_w,
            'original_height': original_h,
            'container_width': container_width,
            'container_height': container_height,
            'responsive_sizing': True
        }
        
    except Exception as e:
        logger.error(f"Error displaying MTF stimulus image: {e}")
        st.error(f"❌ Error displaying image: {e}")
        return None

def display_fullscreen_image(image_data: Any, caption: str = "") -> Optional[Dict[str, Any]]:
    """
    Legacy function - redirect to MTF stimulus display
    
    Args:
        image_data: Image data
        caption: Optional caption
        
    Returns:
        Image display information
    """
    return display_mtf_stimulus_image(image_data, caption)


def display_calibration_status() -> None:
    """
    顯示顯示器校準狀態信息
    
    在實驗開始前或調試時使用，讓研究者了解校準狀態
    """
    try:
        from utils.display_calibration import get_display_calibration
        
        calibration = get_display_calibration()
        status = calibration.get_calibration_status()
        
        # 根據狀態選擇顯示方式
        if status['status'] == 'success':
            st.success(f"✅ {status['message']}")
        elif status['status'] == 'warning':
            st.warning(f"⚠️ {status['message']}")
        else:
            st.error(f"❌ {status['message']}")
        
        # 詳細信息
        with st.expander("🔍 詳細校準信息"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("檢測方法", status['method'])
                st.metric("信賴度", f"{status['confidence']:.1%}")
                st.metric("螢幕解析度", status.get('resolution', 'unknown'))
                
            with col2:
                st.metric("DPI", status.get('dpi', 'unknown'))
                if status.get('pixel_size_mm'):
                    st.metric("像素大小", f"{status['pixel_size_mm']:.6f} mm")
                else:
                    st.metric("像素大小", "未知")
                    
        # 校準建議
        if status['confidence'] < 0.5:
            st.info("💡 **建議**: 使用手動校準來提高精確度")
            
    except Exception as e:
        st.error(f"❌ 無法顯示校準狀態: {e}")
        logger.error(f"Error displaying calibration status: {e}")


def display_manual_calibration_interface() -> bool:
    """
    顯示手動校準界面
    
    Returns:
        True if calibration was completed successfully
    """
    try:
        from utils.display_calibration import get_display_calibration
        
        calibration = get_display_calibration()
        return calibration.create_manual_calibration_interface()
        
    except Exception as e:
        st.error(f"❌ 無法載入手動校準界面: {e}")
        logger.error(f"Error loading manual calibration interface: {e}")
        return False


def validate_pixel_perfect_display(test_image_size: Tuple[int, int] = (100, 100)) -> Dict[str, Any]:
    """
    驗證像素完美顯示的準確性
    
    Args:
        test_image_size: 測試圖像大小 (width, height)
        
    Returns:
        Validation results dictionary
    """
    try:
        from utils.display_calibration import get_display_calibration
        import numpy as np
        from PIL import Image
        
        # 創建測試圖案
        test_width, test_height = test_image_size
        test_image = np.zeros((test_height, test_width, 3), dtype=np.uint8)
        
        # 創建棋盤格圖案
        for i in range(0, test_height, 10):
            for j in range(0, test_width, 10):
                if (i//10 + j//10) % 2 == 0:
                    test_image[i:i+10, j:j+10] = [255, 255, 255]
                else:
                    test_image[i:i+10, j:j+10] = [0, 0, 0]
        
        # 顯示測試圖案
        st.subheader("🎯 像素完美顯示驗證")
        st.markdown(f"""
        下面的測試圖案應該顯示為 **{test_width} × {test_height}** 像素的精確大小。
        每個方格應該是 10×10 像素。
        """)
        
        display_result = display_mtf_stimulus_image(
            test_image, 
            caption=f"測試圖案: {test_width}×{test_height} 像素"
        )
        
        # 獲取校準信息
        calibration = get_display_calibration()
        status = calibration.get_calibration_status()
        
        validation_results = {
            'test_image_size': test_image_size,
            'calibration_status': status,
            'display_result': display_result,
            'validation_passed': status['confidence'] > 0.5,
            'recommendations': []
        }
        
        # 生成建議
        if status['confidence'] < 0.3:
            validation_results['recommendations'].append("強烈建議進行手動校準")
        elif status['confidence'] < 0.7:
            validation_results['recommendations'].append("建議確認測試圖案的實際尺寸")
        else:
            validation_results['recommendations'].append("校準狀態良好，可以開始實驗")
            
        return validation_results
        
    except Exception as e:
        st.error(f"❌ 像素完美顯示驗證失敗: {e}")
        logger.error(f"Error validating pixel-perfect display: {e}")
        return {'error': str(e)}


def display_mtf_processing_comparison(base_image: np.ndarray, mtf_values: List[float]) -> None:
    """
    顯示MTF處理的校準前後比較
    
    Args:
        base_image: 基礎圖像
        mtf_values: 要比較的MTF值列表
    """
    try:
        from experiments.mtf_utils import apply_mtf_to_image, get_current_pixel_size_info
        
        st.subheader("🔬 MTF處理校準效果比較")
        
        # 獲取像素大小信息
        pixel_info = get_current_pixel_size_info()
        
        st.info(f"""
        **當前像素大小**: {pixel_info['pixel_size_mm']:.6f} mm  
        **DPI**: {pixel_info['dpi_x']:.1f} × {pixel_info['dpi_y']:.1f}  
        **校準狀態**: {'✅ 已校準' if pixel_info['is_calibrated'] else '❌ 未校準'}  
        **檢測方法**: {pixel_info['detection_method']}
        """)
        
        # 比較不同MTF值的處理結果
        cols = st.columns(len(mtf_values))
        
        for i, mtf_value in enumerate(mtf_values):
            with cols[i]:
                # 使用校準的像素大小處理
                processed_image = apply_mtf_to_image(base_image, mtf_value)
                
                st.markdown(f"**MTF {mtf_value}%**")
                display_mtf_stimulus_image(
                    processed_image, 
                    caption=f"MTF {mtf_value}%"
                )
                
        # 顯示處理參數
        with st.expander("🔧 處理參數詳情"):
            st.json(pixel_info)
            
    except Exception as e:
        st.error(f"❌ MTF處理比較失敗: {e}")
        logger.error(f"Error in MTF processing comparison: {e}")


def create_pixel_perfect_test() -> None:
    """
    創建pixel-perfect測試，比較網頁和系統顯示
    """
    st.header("🎯 Pixel-Perfect 顯示驗證")
    st.markdown("""
    **對於心理物理學實驗的重要性**:
    - MTF濾波器需要精確的像素控制
    - 任何平滑或抗鋸齒都會影響實驗結果
    - 網頁的 `image-rendering: pixelated` 比系統預覽更適合科學實驗
    """)
    
    # 創建測試圖案
    import numpy as np
    
    # 創建高對比度棋盤格測試圖案
    size = st.slider("測試圖案大小", 50, 200, 100)
    square_size = st.slider("方格大小", 2, 20, 10)
    
    test_image = np.zeros((size, size, 3), dtype=np.uint8)
    
    # 創建精確的黑白棋盤格
    for i in range(0, size, square_size):
        for j in range(0, size, square_size):
            if (i//square_size + j//square_size) % 2 == 0:
                test_image[i:i+square_size, j:j+square_size] = [255, 255, 255]  # 白色
            else:
                test_image[i:i+square_size, j:j+square_size] = [0, 0, 0]  # 黑色
    
    # 添加1像素寬的線條測試
    if st.checkbox("添加1像素線條測試"):
        # 垂直線
        test_image[:, size//2:size//2+1] = [255, 0, 0]  # 紅色
        # 水平線  
        test_image[size//2:size//2+1, :] = [0, 255, 0]  # 綠色
    
    st.subheader("網頁 Pixel-Perfect 顯示")
    st.markdown("**使用 `image-rendering: pixelated` 的銳利渲染**")
    
    display_result = display_mtf_stimulus_image(
        test_image,
        caption=f"網頁渲染: {size}×{size} 像素，方格 {square_size}×{square_size}"
    )
    
    st.subheader("📋 觀察指南")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **網頁顯示特徵** (正確的pixel-perfect):
        - 方格邊界銳利，無模糊
        - 黑白對比明確
        - 1像素線條銳利可見
        - 無抗鋸齒平滑
        """)
    
    with col2:
        st.markdown("""
        **Mac Preview 特徵** (系統平滑):
        - 方格邊界可能稍微模糊
        - 有subpixel渲染
        - 1像素線條可能有平滑效果
        - 整體看起來"更舒適"但不夠銳利
        """)
    
    st.info("""
    **💡 結論**: 對於MTF清晰度實驗，網頁的pixel-perfect渲染更準確！
    Mac Preview的"平滑"效果實際上會干擾對視覺銳利度的精確測量。
    """)
    
    # 顯示技術細節
    with st.expander("🔬 技術細節說明"):
        st.markdown("""
        ### Retina 顯示器真相
        
        **物理vs邏輯像素**:
        - Retina: 2880×1800 物理像素 = 1440×900 邏輯像素
        - devicePixelRatio = 2
        - 1個邏輯像素 = 4個物理像素
        
        **渲染差異**:
        1. **Mac Preview**: 使用 Core Graphics，預設平滑和抗鋸齒
        2. **網頁 pixelated**: 強制關閉平滑，保持銳利邊界
        3. **MTF實驗需求**: 需要銳利邊界來準確測量調制傳遞函數
        
        **為什麼網頁更準確**:
        - `image-rendering: pixelated` 確保每個邏輯像素對應精確的物理像素塊
        - 無subpixel渲染干擾
        - 無自動平滑處理
        - 更接近CRT顯示器的銳利像素特性
        """)


def create_calibration_dashboard() -> None:
    """
    創建完整的校準儀表板
    
    包含狀態顯示、手動校準、驗證測試等功能
    """
    st.header("🎯 顯示器校準系統")
    
    # 選項卡
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 校準狀態", 
        "🔧 手動校準", 
        "✅ 驗證測試", 
        "🎯 Pixel-Perfect測試",
        "🔬 MTF比較"
    ])
    
    with tab1:
        st.subheader("當前校準狀態")
        display_calibration_status()
        
        if st.button("🔄 重新檢測顯示器"):
            try:
                from utils.display_calibration import get_display_calibration
                calibration = get_display_calibration()
                calibration.get_display_info(force_refresh=True)
                st.success("✅ 重新檢測完成")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 重新檢測失敗: {e}")
    
    with tab2:
        st.subheader("手動校準")
        display_manual_calibration_interface()
    
    with tab3:
        st.subheader("像素完美顯示驗證")
        test_sizes = [(50, 50), (100, 100), (200, 200)]
        selected_size = st.selectbox(
            "選擇測試圖案大小", 
            test_sizes, 
            format_func=lambda x: f"{x[0]}×{x[1]} 像素"
        )
        
        if st.button("開始驗證測試"):
            validate_pixel_perfect_display(selected_size)
    
    with tab4:
        create_pixel_perfect_test()
    
    with tab5:
        st.subheader("MTF處理效果比較") 
        
        # 選擇測試圖像
        test_image_options = {
            "內建棋盤格": "checkerboard",
            "上傳圖像": "upload"
        }
        
        image_source = st.radio("選擇測試圖像", list(test_image_options.keys()))
        
        if image_source == "內建棋盤格":
            # 創建棋盤格測試圖像
            size = st.slider("圖像大小", 100, 500, 200)
            test_image = np.zeros((size, size, 3), dtype=np.uint8)
            
            # 創建棋盤格
            square_size = max(5, size // 20)
            for i in range(0, size, square_size):
                for j in range(0, size, square_size):
                    if (i//square_size + j//square_size) % 2 == 0:
                        test_image[i:i+square_size, j:j+square_size] = [255, 255, 255]
                        
        elif image_source == "上傳圖像":
            uploaded_file = st.file_uploader("上傳圖像", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                from PIL import Image
                pil_image = Image.open(uploaded_file)
                test_image = np.array(pil_image.convert('RGB'))
            else:
                st.warning("請上傳圖像文件")
                return
        
        # MTF值選擇
        mtf_values = st.multiselect(
            "選擇MTF值進行比較", 
            [10, 25, 50, 75, 90], 
            default=[25, 50, 75]
        )
        
        if st.button("開始MTF比較") and mtf_values:
            display_mtf_processing_comparison(test_image, mtf_values)