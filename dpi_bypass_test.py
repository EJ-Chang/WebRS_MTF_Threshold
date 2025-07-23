"""
DPI 繞過測試工具
測試不同方法來達到真正的 pixel perfect 控制

Author: EJ_CHANG
Created: 2025-01-22
"""

import streamlit as st
import streamlit.components.v1 as components
import numpy as np
from PIL import Image
import base64
import io

def create_test_image(width_px: int = 200, height_px: int = 200):
    """創建測試圖像"""
    # 創建帶有像素標記的測試圖像
    img = np.ones((height_px, width_px, 3), dtype=np.uint8) * 255
    
    # 繪製像素網格
    for i in range(0, height_px, 10):
        img[i, :] = [0, 0, 0]  # 黑色橫線
    for j in range(0, width_px, 10):
        img[:, j] = [0, 0, 0]  # 黑色直線
    
    # 標記中心點
    center_y, center_x = height_px // 2, width_px // 2
    img[center_y-5:center_y+5, center_x-5:center_x+5] = [255, 0, 0]  # 紅色中心
    
    return Image.fromarray(img)

def method_1_meta_viewport():
    """方法1：Meta Viewport 控制"""
    st.subheader("🎯 方法1：Meta Viewport DPI 控制")
    
    # 嘗試插入 meta viewport 標籤
    viewport_html = """
    <script>
        // 嘗試修改或添加 viewport meta tag
        let viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, user-scalable=no, target-densitydpi=device-dpi');
        } else {
            let meta = document.createElement('meta');
            meta.name = 'viewport';
            meta.content = 'width=device-width, initial-scale=1.0, user-scalable=no, target-densitydpi=device-dpi';
            document.head.appendChild(meta);
        }
        
        // 報告當前 DPI 相關信息
        console.log('devicePixelRatio:', window.devicePixelRatio);
        console.log('screen.width:', screen.width);
        console.log('screen.height:', screen.height);
    </script>
    """
    st.markdown(viewport_html, unsafe_allow_html=True)
    
    test_img = create_test_image(200, 200)
    buffer = io.BytesIO()
    test_img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # 使用強制像素大小
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <p>200×200 像素測試圖像 (方法1)</p>
        <img src="data:image/png;base64,{img_str}" 
             style="width: 200px !important; 
                    height: 200px !important;
                    image-rendering: pixelated !important;
                    zoom: 1 !important;
                    transform: none !important;
                    object-fit: none !important;
                    -webkit-transform: none !important;
                    -moz-transform: none !important;">
    </div>
    """, unsafe_allow_html=True)

def method_2_css_scaling():
    """方法2：CSS 尺度計算"""
    st.subheader("🎯 方法2：基於 devicePixelRatio 的 CSS 縮放")
    
    # JavaScript 檢測 devicePixelRatio 並動態調整
    detection_html = """
    <div id="dpi-info-method2"></div>
    <div id="test-image-container-method2"></div>
    
    <script>
        (function() {
            const dpr = window.devicePixelRatio || 1;
            const targetDPI = 163.2;  // 你的 4K 螢幕 DPI
            const standardDPI = 96;
            
            // 計算縮放比例
            const scaleFactor = standardDPI / targetDPI;
            
            document.getElementById('dpi-info-method2').innerHTML = `
                <p>Device Pixel Ratio: ${dpr}</p>
                <p>計算縮放係數: ${scaleFactor.toFixed(4)}</p>
                <p>調整後尺寸: ${Math.round(200 * scaleFactor)}px</p>
            `;
            
            // 創建動態縮放的圖像
            const adjustedSize = Math.round(200 / dpr * (targetDPI / standardDPI));
            
            document.getElementById('test-image-container-method2').innerHTML = `
                <img src="data:image/png;base64,${window.testImageBase64}" 
                     style="width: ${adjustedSize}px !important; 
                            height: ${adjustedSize}px !important;
                            image-rendering: pixelated !important;
                            transform: none !important;
                            zoom: 1 !important;">
            `;
        })();
    </script>
    """
    
    test_img = create_test_image(200, 200)
    buffer = io.BytesIO()
    test_img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # 將圖像數據傳遞給 JavaScript
    st.markdown(f"""
    <script>
        window.testImageBase64 = '{img_str}';
    </script>
    {detection_html}
    """, unsafe_allow_html=True)

def method_3_custom_component():
    """方法3：自定義 Streamlit 組件"""
    st.subheader("🎯 方法3：自定義 HTML 組件")
    
    test_img = create_test_image(200, 200)
    buffer = io.BytesIO()
    test_img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # 使用 Streamlit components 創建完全自定義的 HTML
    custom_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, target-densitydpi=device-dpi">
        <style>
            body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
            .container {{ text-align: center; }}
            .pixel-perfect-img {{
                width: 200px !important;
                height: 200px !important;
                image-rendering: pixelated !important;
                image-rendering: -moz-crisp-edges !important;
                image-rendering: crisp-edges !important;
                transform: none !important;
                zoom: 1 !important;
                object-fit: none !important;
                border: 1px solid #ccc;
            }}
            #info {{
                margin-top: 20px;
                background: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p><strong>200×200 像素測試圖像 (自定義組件)</strong></p>
            <img src="data:image/png;base64,{img_str}" class="pixel-perfect-img">
            <div id="info">
                <p>Device Pixel Ratio: <span id="dpr"></span></p>
                <p>Screen Size: <span id="screen-size"></span></p>
                <p>Window Size: <span id="window-size"></span></p>
            </div>
        </div>
        
        <script>
            document.getElementById('dpr').textContent = window.devicePixelRatio || 1;
            document.getElementById('screen-size').textContent = screen.width + ' × ' + screen.height;
            document.getElementById('window-size').textContent = window.innerWidth + ' × ' + window.innerHeight;
        </script>
    </body>
    </html>
    """
    
    components.html(custom_html, height=400)

def method_4_canvas_approach():
    """方法4：Canvas 方法"""
    st.subheader("🎯 方法4：HTML5 Canvas 像素完美渲染")
    
    test_img = create_test_image(200, 200)
    buffer = io.BytesIO()
    test_img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    canvas_html = f"""
    <div style="text-align: center;">
        <p><strong>200×200 像素測試圖像 (Canvas 方法)</strong></p>
        <canvas id="pixelCanvas" width="200" height="200" 
                style="border: 1px solid #ccc; 
                       image-rendering: pixelated !important;
                       image-rendering: -moz-crisp-edges !important;
                       image-rendering: crisp-edges !important;"></canvas>
        <div id="canvas-info" style="margin-top: 10px; background: #f0f0f0; padding: 10px; border-radius: 5px;"></div>
    </div>
    
    <script>
        (function() {{
            const canvas = document.getElementById('pixelCanvas');
            const ctx = canvas.getContext('2d');
            
            // 禁用圖像平滑
            ctx.imageSmoothingEnabled = false;
            ctx.webkitImageSmoothingEnabled = false;
            ctx.mozImageSmoothingEnabled = false;
            ctx.msImageSmoothingEnabled = false;
            
            // 創建圖像
            const img = new Image();
            img.onload = function() {{
                // 直接繪製，無縮放
                ctx.drawImage(img, 0, 0, 200, 200);
                
                // 報告 Canvas 信息
                document.getElementById('canvas-info').innerHTML = `
                    <p>Canvas Size: ${{canvas.width}} × ${{canvas.height}}</p>
                    <p>CSS Size: ${{canvas.style.width}} × ${{canvas.style.height}}</p>
                    <p>Device Pixel Ratio: ${{window.devicePixelRatio || 1}}</p>
                `;
            }};
            img.src = 'data:image/png;base64,{img_str}';
        }})();
    </script>
    """
    
    st.markdown(canvas_html, unsafe_allow_html=True)

def main():
    st.title("🔬 DPI 繞過方法測試")
    st.markdown("測試不同方法來繞過瀏覽器的 96 DPI 假設，達到真正的 pixel perfect 控制。")
    
    st.markdown("---")
    
    # 顯示當前環境信息
    st.subheader("📊 當前環境信息")
    info_html = """
    <div id="env-info" style="background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h4>瀏覽器信息</h4>
        <p id="user-agent"></p>
        <p>Device Pixel Ratio: <span id="env-dpr"></span></p>
        <p>Screen: <span id="env-screen"></span></p>
        <p>Window: <span id="env-window"></span></p>
        <p>Viewport: <span id="env-viewport"></span></p>
    </div>
    
    <script>
        document.getElementById('user-agent').textContent = 'User Agent: ' + navigator.userAgent.substring(0, 100) + '...';
        document.getElementById('env-dpr').textContent = window.devicePixelRatio || 1;
        document.getElementById('env-screen').textContent = screen.width + ' × ' + screen.height + ' (可用: ' + screen.availWidth + ' × ' + screen.availHeight + ')';
        document.getElementById('env-window').textContent = window.innerWidth + ' × ' + window.innerHeight;
        
        const viewport = document.querySelector('meta[name="viewport"]');
        document.getElementById('env-viewport').textContent = viewport ? viewport.getAttribute('content') : '未設置';
    </script>
    """
    st.markdown(info_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 測試不同方法
    method_1_meta_viewport()
    st.markdown("---")
    method_2_css_scaling()
    st.markdown("---")
    method_3_custom_component()
    st.markdown("---")
    method_4_canvas_approach()
    
    st.markdown("---")
    st.subheader("📝 測試指南")
    st.markdown("""
    **如何測試這些方法：**
    
    1. **視覺檢查**：所有圖像都應該是 200×200 像素的清晰網格
    2. **尺子測量**：在你的 27吋 4K 螢幕上，200 像素應該約等於 31.2mm (200 × 25.4 / 163.2)
    3. **比較效果**：看哪個方法最接近實際物理尺寸
    4. **縮放測試**：縮放瀏覽器時圖像應該保持相同的物理大小
    
    **預期結果：**
    - 如果某個方法成功繞過 96 DPI 假設，它顯示的圖像應該比其他方法更小
    - 成功的方法應該讓 200px = 31.2mm (而不是 52.9mm)
    """)
    
    # 添加返回主應用的鏈接
    st.markdown("---")
    st.info("💡 測試完成後，你可以將最有效的方法整合到主實驗應用中")

if __name__ == "__main__":
    main()