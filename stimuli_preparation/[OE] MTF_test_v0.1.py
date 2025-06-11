import cv2
import numpy as np

def create_text_image(text, width=800, height=200, font_scale=2, thickness=3):
    """產生黑底白字的測試圖像"""
    img = np.zeros((height, width), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    textsize = cv2.getTextSize(text, font, font_scale, thickness)[0]
    textX = (img.shape[1] - textsize[0]) // 2
    textY = (img.shape[0] + textsize[1]) // 2
    cv2.putText(img, text, (textX, textY), font, font_scale, (255,), thickness)
    return img

def simulate_mtf_blur(image, mtf_level, lpmm=10):
    """
    mtf_level: 0.0 ~ 1.0
    lpmm: 模擬的空間頻率，單位為 lp/mm
    """
    if mtf_level >= 1.0:
        return image.copy()

    # 模擬用係數，可依照螢幕 dpi 或實驗需求調整
    scaling_factor = 400  # 可理解為 "模糊感知倍率"，你可以調整這個數字來匹配實際情況

    base_blur_size = scaling_factor / lpmm  # 頻率越高 → 模糊越少
    kernel_size = int((1 - mtf_level) * base_blur_size)
    if kernel_size < 1:
        kernel_size = 1
    if kernel_size % 2 == 0:
        kernel_size += 1

    blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    return blurred


def stack_and_show(img1, img2, label1='50% MTF', label2='10% MTF'):
    """將兩張圖並排顯示，並加上標籤"""
    img1_color = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR)
    img2_color = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR)
    cv2.putText(img1_color, label1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.putText(img2_color, label2, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    stacked = np.hstack((img1_color, img2_color))
    cv2.imshow("MTF Simulation", stacked)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# 主程式執行範例
if __name__ == "__main__":
    text_img = create_text_image("AR Glasses Clarity Test")
    img_mtf_50 = simulate_mtf_blur(text_img, mtf_level=0.8, lpmm=20)
    img_mtf_10 = simulate_mtf_blur(text_img, mtf_level=0.2, lpmm=20)
    stack_and_show(img_mtf_50, img_mtf_10)
