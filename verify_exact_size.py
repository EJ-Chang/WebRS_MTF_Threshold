#!/usr/bin/env python3
"""
驗證圖片在網頁上的確切尺寸，確保沒有被縮小
"""

import numpy as np
import cv2
import os
import sys
from io import BytesIO
from PIL import Image
import base64

# 添加模組路徑
sys.path.append('.')
sys.path.append('./experiments')

try:
    from experiments.mtf_utils import apply_mtf_to_image, load_and_prepare_image
    MTF_UTILS_AVAILABLE = True
    print("✅ MTF utilities loaded successfully")
except ImportError as e:
    print(f"⚠️ MTF utilities not available: {e}")
    MTF_UTILS_AVAILABLE = False

def simulate_exact_web_processing():
    """模擬新的網頁處理邏輯，確保沒有縮放"""
    print("🔍 驗證新的圖片顯示邏輯")
    print("=" * 50)
    
    # 1. 載入原始圖片
    img_path = "stimuli_preparation/stimuli_img.png"
    if not os.path.exists(img_path):
        print(f"❌ 圖片不存在: {img_path}")
        return
    
    original_img = cv2.imread(img_path)
    original_h, original_w = original_img.shape[:2]
    print(f"📷 原始圖片: {original_w}×{original_h}")
    
    # 2. 右半邊裁切
    mid_point = original_w // 2
    right_half = original_img[:, mid_point:]
    crop_h, crop_w = right_half.shape[:2]
    print(f"✂️ 裁切後: {crop_w}×{crop_h}")
    
    # 3. 模擬MTF處理
    if MTF_UTILS_AVAILABLE:
        try:
            mtf_img = apply_mtf_to_image(right_half, 50.0)
            mtf_h, mtf_w = mtf_img.shape[:2]
            print(f"🎛️ MTF處理: {mtf_w}×{mtf_h}")
        except Exception as e:
            print(f"❌ MTF處理失敗: {e}")
            return
    else:
        # Fallback
        sigma = (100 - 50.0) / 20.0
        mtf_img = cv2.GaussianBlur(right_half, (0, 0), sigmaX=sigma, sigmaY=sigma)
        mtf_h, mtf_w = mtf_img.shape[:2]
        print(f"🎛️ MTF處理 (fallback): {mtf_w}×{mtf_h}")
    
    # 4. 新的網頁處理邏輯 - 不進行任何像素級變更
    processed_img = mtf_img  # 直接使用，不裁切
    final_h, final_w = processed_img.shape[:2]
    print(f"🌐 網頁處理: {final_w}×{final_h} (保持原始)")
    
    # 5. 生成HTML代碼（模擬新邏輯）
    img_pil = Image.fromarray(cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB))
    buffer = BytesIO()
    img_pil.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # 新的CSS設定
    html_css = f"""
    <img style="width: {final_w}px; height: {final_h}px; object-fit: none;">
    """
    
    print("\n📐 尺寸驗證:")
    print(f"  期望顯示尺寸: {final_w}×{final_h} pixels")
    print(f"  CSS設定: width={final_w}px, height={final_h}px")
    print(f"  object-fit: none (防止縮放)")
    
    # 6. 檢查是否有尺寸損失
    if (final_w, final_h) == (crop_w, crop_h):
        print("✅ 確認：圖片尺寸在所有階段都保持一致")
        print(f"✅ 網頁顯示尺寸應該是: {final_w}×{final_h}")
    else:
        print("❌ 警告：檢測到尺寸變化")
    
    # 7. 生成測試文件
    test_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MTF圖片尺寸測試</title>
</head>
<body>
    <h1>MTF圖片尺寸測試</h1>
    <p>期望尺寸: {final_w}×{final_h}</p>
    
    <div style="text-align: center; margin: 0; padding: 0; width: 100%; display: flex; flex-direction: column; align-items: center; overflow: auto;">
        <img id="test_img" src="data:image/png;base64,{img_str}" 
             style="width: {final_w}px; height: {final_h}px; object-fit: none; border: 2px solid red;"
             onload="reportSize()">
    </div>
    
    <script>
        function reportSize() {{
            var img = document.getElementById('test_img');
            console.log('實際顯示尺寸:', img.clientWidth + 'x' + img.clientHeight);
            console.log('自然尺寸:', img.naturalWidth + 'x' + img.naturalHeight);
            
            // 顯示在頁面上
            var info = document.createElement('div');
            info.innerHTML = '<h2>實際測量結果:</h2>' +
                           '<p>clientWidth × clientHeight: ' + img.clientWidth + '×' + img.clientHeight + '</p>' +
                           '<p>naturalWidth × naturalHeight: ' + img.naturalWidth + '×' + img.naturalHeight + '</p>' +
                           '<p>期望尺寸: {final_w}×{final_h}</p>';
            document.body.appendChild(info);
            
            if (img.clientWidth === {final_w} && img.clientHeight === {final_h}) {{
                info.innerHTML += '<p style="color: green;">✅ 尺寸正確！</p>';
            }} else {{
                info.innerHTML += '<p style="color: red;">❌ 尺寸不符！被縮放了！</p>';
            }}
        }}
    </script>
</body>
</html>
"""
    
    with open('mtf_size_test.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print(f"\n📝 已生成測試文件: mtf_size_test.html")
    print(f"   請在瀏覽器中打開此文件檢查實際顯示尺寸")
    
    return {
        'expected_width': final_w,
        'expected_height': final_h,
        'html_generated': True
    }

def check_streamlit_container_impact():
    """檢查Streamlit容器對圖片尺寸的影響"""
    print("\n🔍 Streamlit容器影響分析:")
    print("=" * 30)
    
    print("可能的縮放原因:")
    print("1. Streamlit st.columns() 容器寬度限制")
    print("2. st.markdown() HTML渲染的CSS繼承")
    print("3. 瀏覽器視窗大小限制")
    print("4. CSS max-width/max-height 設定")
    
    print("\n解決方案:")
    print("✅ 已改用固定 width/height px 設定")
    print("✅ 已設定 object-fit: none")
    print("✅ 已設定容器 overflow: auto")
    print("📋 建議測試不同瀏覽器視窗大小")

if __name__ == "__main__":
    result = simulate_exact_web_processing()
    check_streamlit_container_impact()
    
    if result:
        print(f"\n🎯 最終確認:")
        print(f"   網頁應顯示尺寸: {result['expected_width']}×{result['expected_height']}")
        print(f"   如果仍顯示 864×952，表示還有其他因素在縮放")
        print(f"   請檢查瀏覽器開發者工具查看具體CSS問題")