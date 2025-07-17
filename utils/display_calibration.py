"""
Display calibration utilities for pixel-perfect image rendering.

This module provides comprehensive display calibration capabilities for ensuring
pixel-perfect image rendering across different platforms and display configurations.
Essential for psychophysical experiments where precise stimulus presentation is critical.

Author: EJ_CHANG
Created: 2025-01-16
"""

import streamlit as st
import platform
import subprocess
import json
import os
import time
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class DisplayInfo:
    """顯示器信息數據類"""
    width_pixels: int
    height_pixels: int
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    dpi_x: Optional[float] = None
    dpi_y: Optional[float] = None
    device_pixel_ratio: Optional[float] = None
    detected_method: str = "unknown"
    confidence: float = 0.0
    
    @property
    def pixel_size_mm(self) -> Optional[float]:
        """計算平均像素大小（毫米）"""
        if self.dpi_x and self.dpi_y:
            avg_dpi = (self.dpi_x + self.dpi_y) / 2
            return 25.4 / avg_dpi  # 1 inch = 25.4 mm
        return None
    
    @property
    def is_valid(self) -> bool:
        """檢查顯示器信息是否有效"""
        return (self.width_pixels > 0 and self.height_pixels > 0 and 
                self.pixel_size_mm is not None)

class DisplayCalibration:
    """
    顯示器校準管理器
    
    提供多種DPI檢測方法並管理校準數據，確保在不同平台和顯示器上
    都能實現像素完美的圖像渲染。
    """
    
    def __init__(self):
        self.display_info: Optional[DisplayInfo] = None
        self.calibration_cache = {}
        self._js_detection_attempted = False
        
    def get_display_info(self, force_refresh: bool = False) -> Optional[DisplayInfo]:
        """
        獲取顯示器信息，使用多種檢測方法
        
        Args:
            force_refresh: 是否強制重新檢測
            
        Returns:
            DisplayInfo object or None if detection failed
        """
        if self.display_info and not force_refresh:
            return self.display_info
            
        # 嘗試多種檢測方法
        detection_methods = [
            self._detect_via_javascript,
            self._detect_via_system_api,
            self._detect_via_default_values
        ]
        
        best_info = None
        highest_confidence = 0.0
        
        for method in detection_methods:
            try:
                info = method()
                if info and info.confidence > highest_confidence:
                    best_info = info
                    highest_confidence = info.confidence
                    logger.info(f"DPI檢測成功 - 方法: {info.detected_method}, "
                              f"DPI: {info.dpi_x:.1f}x{info.dpi_y:.1f}, "
                              f"像素大小: {info.pixel_size_mm:.4f}mm")
            except Exception as e:
                logger.warning(f"DPI檢測方法失敗: {method.__name__}: {e}")
                continue
        
        if best_info:
            self.display_info = best_info
            self._cache_calibration_data(best_info)
        else:
            logger.error("所有DPI檢測方法都失敗")
            
        return self.display_info
    
    def _detect_via_javascript(self) -> Optional[DisplayInfo]:
        """
        通過JavaScript檢測顯示器DPI
        
        Returns:
            DisplayInfo with JavaScript-detected values
        """
        if self._js_detection_attempted:
            # 從session state獲取之前的結果
            return self._get_cached_js_detection()
            
        # 創建JavaScript檢測界面
        js_detection_html = self._create_js_detection_interface()
        
        # 顯示檢測界面
        st.markdown("### 🔍 正在檢測顯示器規格...")
        st.markdown(js_detection_html, unsafe_allow_html=True)
        
        # 檢查是否有檢測結果
        if 'display_detection' in st.session_state:
            detection_data = st.session_state.display_detection
            self._js_detection_attempted = True
            
            return DisplayInfo(
                width_pixels=detection_data.get('screen_width', 1920),
                height_pixels=detection_data.get('screen_height', 1080),
                dpi_x=detection_data.get('dpi_x', 96),
                dpi_y=detection_data.get('dpi_y', 96),
                device_pixel_ratio=detection_data.get('device_pixel_ratio', 1.0),
                detected_method="javascript",
                confidence=0.8
            )
        
        return None
    
    def _create_js_detection_interface(self) -> str:
        """創建JavaScript檢測界面"""
        return f"""
        <div id="dpi-detection" style="margin: 20px 0;">
            <p id="detection-status">正在檢測顯示器規格...</p>
            <div id="test-ruler" style="width: 96px; height: 96px; background: #ddd; border: 1px solid #000;"></div>
        </div>
        
        <script>
        function detectDisplayInfo() {{
            const screen_width = screen.width;
            const screen_height = screen.height; 
            const device_pixel_ratio = window.devicePixelRatio || 1;
            
            // 使用測試元素檢測實際DPI
            const testElement = document.getElementById('test-ruler');
            const testRect = testElement.getBoundingClientRect();
            const assumedDPI = 96; // CSS像素假設的DPI
            
            // 計算實際DPI
            const actual_dpi_x = (testRect.width * assumedDPI) / testRect.width * device_pixel_ratio;
            const actual_dpi_y = (testRect.height * assumedDPI) / testRect.height * device_pixel_ratio;
            
            const detection_result = {{
                screen_width: screen_width,
                screen_height: screen_height,
                device_pixel_ratio: device_pixel_ratio,
                dpi_x: actual_dpi_x,
                dpi_y: actual_dpi_y,
                timestamp: Date.now()
            }};
            
            // 儲存檢測結果到Streamlit session state
            window.parent.postMessage({{
                type: 'display_detection',
                data: detection_result
            }}, '*');
            
            document.getElementById('detection-status').innerHTML = 
                `檢測完成: ${{screen_width}}x${{screen_height}}, DPI: ${{actual_dpi_x.toFixed(1)}}x${{actual_dpi_y.toFixed(1)}}`;
        }}
        
        // 延遲執行檢測以確保元素已渲染
        setTimeout(detectDisplayInfo, 100);
        
        // 監聽消息
        window.addEventListener('message', function(event) {{
            if (event.data.type === 'display_detection') {{
                // 存儲到session state (這需要特殊處理)
                console.log('Display detection result:', event.data.data);
            }}
        }});
        </script>
        """
    
    def _get_cached_js_detection(self) -> Optional[DisplayInfo]:
        """從緩存獲取JavaScript檢測結果"""
        if 'display_detection' not in st.session_state:
            return None
            
        data = st.session_state.display_detection
        return DisplayInfo(
            width_pixels=data.get('screen_width', 1920),
            height_pixels=data.get('screen_height', 1080),
            dpi_x=data.get('dpi_x', 96),
            dpi_y=data.get('dpi_y', 96),
            device_pixel_ratio=data.get('device_pixel_ratio', 1.0),
            detected_method="javascript_cached",
            confidence=0.8
        )
    
    def _detect_via_system_api(self) -> Optional[DisplayInfo]:
        """
        通過系統API檢測顯示器DPI
        
        Returns:
            DisplayInfo with system-detected values
        """
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            return self._detect_macos_dpi()
        elif system == "windows":  # Windows
            return self._detect_windows_dpi()
        elif system == "linux":  # Linux
            return self._detect_linux_dpi()
        else:
            logger.warning(f"不支持的系統: {system}")
            return None
    
    def _detect_macos_dpi(self) -> Optional[DisplayInfo]:
        """檢測macOS顯示器DPI"""
        try:
            # 使用system_profiler獲取顯示器信息
            cmd = ["system_profiler", "SPDisplaysDataType", "-json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                displays = data.get("SPDisplaysDataType", [])
                
                if displays:
                    display = displays[0]  # 使用主顯示器
                    
                    # 提取顯示器信息
                    resolution = display.get("_spdisplays_resolution", "")
                    if "x" in resolution:
                        width_str, height_str = resolution.split("x")
                        width = int(width_str.strip())
                        height = int(height_str.strip())
                        
                        # macOS通常使用72 DPI作為基準，但現代顯示器可能更高
                        # 嘗試從其他字段獲取實際DPI
                        dpi = self._estimate_macos_dpi(display)
                        
                        return DisplayInfo(
                            width_pixels=width,
                            height_pixels=height,
                            dpi_x=dpi,
                            dpi_y=dpi,
                            detected_method="macos_system_profiler",
                            confidence=0.7
                        )
                        
        except Exception as e:
            logger.error(f"macOS DPI檢測失敗: {e}")
            
        return None
    
    def _estimate_macos_dpi(self, display_info: Dict) -> float:
        """估算macOS顯示器DPI"""
        # 檢查是否為Retina顯示器
        pixel_depth = display_info.get("_spdisplays_pixeldepth", "")
        if "Retina" in str(display_info) or "Retina" in pixel_depth:
            return 220.0  # Retina顯示器典型DPI
        else:
            return 72.0   # 標準顯示器DPI
    
    def _detect_windows_dpi(self) -> Optional[DisplayInfo]:
        """檢測Windows顯示器DPI"""
        try:
            # 使用wmic查詢顯示器信息
            cmd = ["wmic", "desktopmonitor", "get", "ScreenWidth,ScreenHeight", "/format:csv"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    # 解析CSV輸出
                    header = lines[0].split(',')
                    data = lines[1].split(',')
                    
                    if len(data) >= 3:
                        width = int(data[2]) if data[2] else 1920
                        height = int(data[1]) if data[1] else 1080
                        
                        # Windows默認DPI為96
                        dpi = 96.0
                        
                        return DisplayInfo(
                            width_pixels=width,
                            height_pixels=height,
                            dpi_x=dpi,
                            dpi_y=dpi,
                            detected_method="windows_wmic",
                            confidence=0.6
                        )
                        
        except Exception as e:
            logger.error(f"Windows DPI檢測失敗: {e}")
            
        return None
    
    def _detect_linux_dpi(self) -> Optional[DisplayInfo]:
        """檢測Linux顯示器DPI"""
        try:
            # 嘗試使用xrandr
            cmd = ["xrandr", "--query"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if " connected primary" in line or " connected " in line:
                        # 解析解析度信息
                        parts = line.split()
                        for part in parts:
                            if "x" in part and "+" in part:
                                resolution = part.split("+")[0]
                                width, height = map(int, resolution.split("x"))
                                
                                return DisplayInfo(
                                    width_pixels=width,
                                    height_pixels=height,
                                    dpi_x=96.0,  # Linux默認DPI
                                    dpi_y=96.0,
                                    detected_method="linux_xrandr",
                                    confidence=0.6
                                )
                                
        except Exception as e:
            logger.error(f"Linux DPI檢測失敗: {e}")
            
        return None
    
    def _detect_via_default_values(self) -> DisplayInfo:
        """
        使用默認值作為後備方案
        
        Returns:
            DisplayInfo with default values
        """
        logger.warning("使用默認DPI值 (96 DPI)")
        
        return DisplayInfo(
            width_pixels=1920,
            height_pixels=1080,
            dpi_x=96.0,
            dpi_y=96.0,
            detected_method="default_fallback",
            confidence=0.3
        )
    
    def calculate_mtf_pixel_size(self) -> float:
        """
        計算MTF處理使用的像素大小
        
        Returns:
            Pixel size in millimeters
        """
        display_info = self.get_display_info()
        if display_info and display_info.pixel_size_mm:
            return display_info.pixel_size_mm
        else:
            # 使用原始默認值作為後備
            logger.warning("無法檢測像素大小，使用默認值")
            return 0.005649806841172989  # 原始硬編碼值
    
    def get_pixel_perfect_css(self, width_px: int, height_px: int) -> str:
        """
        生成像素完美的CSS樣式
        
        Args:
            width_px: 圖像寬度（像素）
            height_px: 圖像高度（像素）
            
        Returns:
            CSS style string
        """
        display_info = self.get_display_info()
        
        # 計算DPI補償因子
        dpi_compensation = 1.0
        if display_info and display_info.device_pixel_ratio:
            dpi_compensation = 1.0 / display_info.device_pixel_ratio
        
        return f"""
        display: block;
        margin: 0 auto;
        width: {width_px}px !important;
        height: {height_px}px !important;
        max-width: none !important;
        max-height: none !important;
        
        /* 像素完美渲染 */
        image-rendering: pixelated;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
        image-rendering: -webkit-optimize-contrast;
        
        /* 變換控制 */
        transform: scale({dpi_compensation}) !important;
        transform-origin: center !important;
        zoom: 1 !important;
        
        /* 禁用所有平滑和變換 */
        -webkit-transform: none !important;
        -moz-transform: none !important;
        -ms-transform: none !important;
        -webkit-font-smoothing: none !important;
        -moz-osx-font-smoothing: unset !important;
        
        /* 防止用戶選擇 */
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
        
        /* 確保無邊距和填充 */
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        """
    
    def _cache_calibration_data(self, display_info: DisplayInfo):
        """緩存校準數據"""
        cache_key = f"{display_info.width_pixels}x{display_info.height_pixels}"
        self.calibration_cache[cache_key] = {
            'display_info': display_info,
            'timestamp': time.time()
        }
        
        # 也保存到session state以便持久化
        st.session_state.display_calibration_cache = self.calibration_cache
    
    def create_manual_calibration_interface(self) -> bool:
        """
        創建手動校準界面
        
        Returns:
            True if calibration was completed
        """
        st.subheader("🔧 手動顯示器校準")
        st.markdown("""
        如果自動檢測不準確，您可以手動校準您的顯示器。
        請使用尺子測量下面的測試圖案，並輸入實際測量值。
        """)
        
        # 顯示測試圖案 (已知尺寸)
        test_size_mm = 50  # 50毫米的測試正方形
        test_size_px = 189  # 在96 DPI下，50mm = 189px
        
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <p><strong>測試圖案 (應該是 {test_size_mm}mm × {test_size_mm}mm)</strong></p>
            <div style="
                width: {test_size_px}px; 
                height: {test_size_px}px; 
                background: #000; 
                border: 2px solid #666;
                margin: 10px auto;
                position: relative;
            ">
                <div style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: white;
                    font-size: 12px;
                ">50mm</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 手動輸入實際測量值
        col1, col2 = st.columns(2)
        with col1:
            measured_width = st.number_input(
                "實際測量寬度 (mm)", 
                min_value=1.0, 
                max_value=200.0, 
                value=50.0,
                step=0.1
            )
        with col2:
            measured_height = st.number_input(
                "實際測量高度 (mm)", 
                min_value=1.0, 
                max_value=200.0, 
                value=50.0,
                step=0.1
            )
        
        if st.button("應用手動校準"):
            # 計算實際DPI
            actual_dpi_x = (test_size_px * 25.4) / measured_width
            actual_dpi_y = (test_size_px * 25.4) / measured_height
            
            # 創建手動校準的DisplayInfo
            manual_info = DisplayInfo(
                width_pixels=1920,  # 假設值，實際不重要
                height_pixels=1080,
                dpi_x=actual_dpi_x,
                dpi_y=actual_dpi_y,
                detected_method="manual_calibration",
                confidence=1.0  # 手動校準具有最高可信度
            )
            
            self.display_info = manual_info
            self._cache_calibration_data(manual_info)
            
            st.success(f"✅ 手動校準完成！DPI: {actual_dpi_x:.1f} x {actual_dpi_y:.1f}")
            st.success(f"📏 像素大小: {manual_info.pixel_size_mm:.4f} mm")
            
            return True
            
        return False
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """
        獲取校準狀態信息
        
        Returns:
            Dictionary with calibration status
        """
        display_info = self.get_display_info()
        
        if not display_info:
            return {
                'status': 'failed',
                'message': '顯示器檢測失敗',
                'confidence': 0.0
            }
        
        return {
            'status': 'success' if display_info.confidence > 0.5 else 'warning',
            'method': display_info.detected_method,
            'confidence': display_info.confidence,
            'pixel_size_mm': display_info.pixel_size_mm,
            'dpi': f"{display_info.dpi_x:.1f} x {display_info.dpi_y:.1f}",
            'resolution': f"{display_info.width_pixels} x {display_info.height_pixels}",
            'message': self._get_status_message(display_info)
        }
    
    def _get_status_message(self, display_info: DisplayInfo) -> str:
        """獲取狀態消息"""
        if display_info.confidence >= 0.8:
            return "✅ 顯示器校準精確，可進行實驗"
        elif display_info.confidence >= 0.5:
            return "⚠️ 顯示器校準可能不夠精確，建議手動校準"
        else:
            return "❌ 顯示器校準失敗，強烈建議手動校準"

# 全局實例
_display_calibration_instance = None

def get_display_calibration() -> DisplayCalibration:
    """獲取全局顯示器校準實例"""
    global _display_calibration_instance
    if _display_calibration_instance is None:
        _display_calibration_instance = DisplayCalibration()
    return _display_calibration_instance

def quick_pixel_size_detection() -> float:
    """快速獲取像素大小，用於MTF處理"""
    calibration = get_display_calibration()
    return calibration.calculate_mtf_pixel_size()