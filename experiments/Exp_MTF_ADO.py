"""
Exp_MTF_ADO.py

基於自製 ADO 的適應性心理物理實驗，用於 MTF 閾值估計

實驗設計：
- 單區間 Y/N 判斷任務，使用自製 ADO 引擎
- 參與者觀看圖片並判斷是否「清楚」
- MTF 值根據 ADO 演算法動態選擇
- 即時貝葉斯參數估計，具備早期停止機制
- 記錄反應、反應時間和參數估計到 CSV

Author: EJ
Last reviewed: 2025-06
"""

import os
import sys
import numpy as np
from psychopy import visual, core, event, gui
from datetime import datetime
import csv

def get_project_root():
    """獲取專案根目錄的絕對路徑。
    
    Returns:
        str: 專案根目錄的絕對路徑
    """
    # 獲取腳本所在目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 往上一層到專案根目錄
    return os.path.dirname(script_dir)

# 確保可以 import 專案模組
project_root = get_project_root()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from mtf_utils import apply_mtf_to_image, load_and_prepare_image, normalize_for_psychopy
    from ado_utils import ADOEngine
except ImportError as e:
    print(f"匯入錯誤：{e}")
    print("請確認 mtf_utils.py 和 ado_utils.py 在同一目錄中")
    sys.exit(1)

# 建立隨機數生成器
rng = np.random.default_rng(seed=int(datetime.now().timestamp()))


def create_window():
    """建立並設定實驗視窗"""
    win = visual.Window(
        size=[1920, 1080],
        fullscr=False,
        screen=0,
        winType='pyglet',
        allowGUI=True,
        allowStencil=False,
        monitor='testMonitor',
        color=[0.5, 0.5, 0.5],
        colorSpace='rgb',
        units='pix',
        useFBO=True,
        waitBlanking=True,
        useRetina=True,
        multiSample=False
    )

    win.winHandle.activate()
    win.winHandle.set_visible(True)
    win.winHandle.set_vsync(True)
    return win


def create_stimuli(win):
    """建立實驗中使用的刺激物件"""
    default_font = 'Arial'
    
    fixation = visual.TextStim(
        win, text='+', height=50, color='white', font=default_font
    )
    
    trial_number = visual.TextStim(
        win, text='', height=40, color='white', pos=(0, 50), font=default_font
    )
    
    instruction = visual.TextStim(
        win,
        text='您將看到一張圖片\n請判斷是否清楚\nY = 是，N = 否\n\n這是適應性實驗\n按空白鍵開始',
        height=30, color='white', font=default_font
    )
    
    prompt = visual.TextStim(
        win,
        text='這張圖片清楚嗎？\nY = 是，N = 否',
        height=30, color='white', font=default_font
    )
    
    rest_text = visual.TextStim(
        win,
        text='休息時間\n按空白鍵繼續',
        height=30, color='white', font=default_font
    )
    
    end_text = visual.TextStim(
        win,
        text='實驗結束\n按任意鍵離開',
        height=30, color='white', font=default_font
    )
    
    parameter_display = visual.TextStim(
        win,
        text='', height=25, color='yellow', pos=(0, -400), font=default_font
    )
    
    return fixation, trial_number, instruction, prompt, rest_text, end_text, parameter_display


def create_image_stimulus(win, img_array):
    """從圖片陣列建立 PsychoPy ImageStim 物件"""
    # 正規化到 0-1 範圍
    img_normalized = img_array.astype(float) / 255.0
    # numpy 運算的圖片對 PsychoPy 需要上下翻轉
    img_flipped = np.flipud(img_normalized)
    
    return visual.ImageStim(
        win,
        image=img_flipped,
        size=[960, 1080],
        units='pix',
        interpolate=False
    )


def run_ado_mtf_experiment():
    """執行主要的 ADO MTF 實驗程序"""
    
    # 實驗資訊對話框
    exp_info = {
        'subject': '001',
        'session': '001',
        'base_image': 'stimuli_img.png',
        'max_trials': 50,
        'min_trials': 15,
        'convergence_threshold': 0.15
    }
    dlg = gui.DlgFromDict(exp_info, title='MTF ADO 實驗')
    if not dlg.OK:
        core.quit()

    # 建立視窗和刺激
    win = create_window()
    fixation, trial_number, instruction, prompt, rest_text, end_text, parameter_display = create_stimuli(win)

    # 載入基礎圖片
    try:
        # 設定基礎圖片路徑
        base_image_path = os.path.join(project_root, 'stimuli_preparation', exp_info['base_image'])
        if not os.path.exists(base_image_path):
            raise FileNotFoundError(f"找不到基礎圖片：{base_image_path}")
        
        base_img = load_and_prepare_image(base_image_path, use_right_half=True)
        print(f"成功載入基礎圖片：{base_image_path}")
        print(f"圖片尺寸：{base_img.shape}")
        
    except Exception as e:
        print(f"載入圖片失敗：{e}")
        win.close()
        core.quit()
        return

    # 初始化 ADO 引擎
    try:
        ado_engine = ADOEngine(
            design_space=np.arange(10, 90, 1),  # 設計空間：10%, 11%, 12%, ..., 89% (精細 1% 間隔)
            threshold_range=(5, 95),  # 擴大範圍
            slope_range=(0.05, 5.0),  # 擴大範圍 
            threshold_points=31,  # 減少網格點數
            slope_points=21  # 減少網格點數
        )
        print("ADO 引擎初始化成功")
        
    except Exception as e:
        print(f"ADO 引擎初始化失敗：{e}")
        win.close()
        core.quit()
        return

    # 建立資料檔案
    data_dir = os.path.join(project_root, 'data')
    os.makedirs(data_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(data_dir, f"MTF_ADO_{exp_info['subject']}_{timestamp}.csv")
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([
            'trial', 'mtf_value', 'response', 'response_time',
            'threshold_mean', 'threshold_sd', 'slope_mean', 'slope_sd',
            'converged'
        ])

    # 顯示指導語
    instruction.draw()
    win.flip(clearBuffer=True)
    event.clearEvents()
    event.waitKeys(keyList=['space'])

    # 主要實驗迴圈
    trial_count = 0
    converged = False
    
    for trial_count in range(1, exp_info['max_trials'] + 1):
            
            # 每 20 個試驗休息一次
            if trial_count > 1 and (trial_count - 1) % 20 == 0:
                rest_text.draw()
                win.flip(clearBuffer=True)
                event.clearEvents()
                event.waitKeys(keyList=['space'])

            # 從 ADO 引擎取得最佳設計
            try:
                optimal_mtf = ado_engine.get_optimal_design()
                print(f"試驗 {trial_count}: 選擇 MTF {optimal_mtf:.1f}%")
                
            except Exception as e:
                print(f"ADO 引擎錯誤：{e}")
                # 後備方案：隨機選擇
                optimal_mtf = float(rng.choice(np.arange(10, 90, 10)))
                print(f"使用後備 MTF：{optimal_mtf}")

            # 產生對應的 MTF 圖片
            try:
                img_mtf = apply_mtf_to_image(base_img, optimal_mtf)
                img_stimulus = create_image_stimulus(win, img_mtf)
                
            except Exception as e:
                print(f"圖片處理錯誤：{e}")
                continue

            # 顯示試驗編號
            trial_number.setText(f'試驗：{trial_count} (MTF: {optimal_mtf:.1f}%)')
            trial_number.draw()
            win.flip(clearBuffer=True)
            core.wait(1)

            # 顯示注視點
            fixation.draw()
            win.flip(clearBuffer=True)
            core.wait(0.5)

            # 顯示圖片刺激
            img_stimulus.draw()
            win.flip(clearBuffer=True)
            core.wait(1)

            # 顯示選擇提示
            prompt.draw()
            
            # 顯示目前的參數估計（如果有的話）
            if trial_count > 1:
                try:
                    estimates = ado_engine.get_parameter_estimates()
                    param_text = (f"Estimated threshold: {estimates['threshold_mean']:.1f}±{estimates['threshold_sd']:.2f}\n"
                                f"Posterior SD: {estimates['threshold_sd']:.3f} (target < {exp_info['convergence_threshold']:.3f})")
                    parameter_display.setText(param_text)
                    parameter_display.draw()
                except Exception as e:
                    print(f"參數顯示錯誤：{e}")
                    
            win.flip(clearBuffer=True)

            # 等待反應
            event.clearEvents()
            start_time = core.getTime()
            response_key = None
            
            while True:
                keys = event.getKeys(keyList=['y', 'n', 'left', 'right', 'escape'])
                if keys:
                    response_time = core.getTime() - start_time
                    if 'escape' in keys:
                        print("使用者按下 ESC 鍵，結束實驗")
                        win.close()
                        core.quit()
                        return
                    
                    response_key = keys[0]
                    break
                
                # 檢查視窗關閉事件
                if hasattr(win, 'closed') and win.closed:
                    core.quit()
                    return
                    
                core.wait(0.001)

            # 轉換反應：y/left=1（清楚），n/right=0（不清楚）
            response_value = 1 if response_key in ['y', 'left'] else 0

            # 更新 ADO 引擎
            try:
                ado_engine.update_posterior(optimal_mtf, response_value)
                
                # 取得目前的參數估計
                estimates = ado_engine.get_parameter_estimates()
                summary = ado_engine.get_trial_summary()
                
                # Debug info: print parameter estimates and posterior SD
                print(f"Trial {trial_count}: MTF={optimal_mtf:.1f}, Response={response_value}")
                print(f"  Threshold: {estimates['threshold_mean']:.1f} ± {estimates['threshold_sd']:.3f}")
                print(f"  Slope: {estimates['slope_mean']:.2f} ± {estimates['slope_sd']:.3f}")
                print(f"  → Posterior SD (threshold): {estimates['threshold_sd']:.3f} (convergence target: < {exp_info['convergence_threshold']:.3f})")
                
            except Exception as e:
                print(f"ADO 更新錯誤：{e}")
                estimates = {
                    'threshold_mean': np.nan,
                    'threshold_sd': np.nan,
                    'slope_mean': np.nan,
                    'slope_sd': np.nan
                }
                summary = {'converged': False}

            # 簡化收斂檢查：只檢查 threshold_sd，但必須滿足最少試驗數
            if trial_count >= exp_info['min_trials']:
                converged = estimates['threshold_sd'] < exp_info['convergence_threshold']
                print(f"  Convergence check: threshold_sd={estimates['threshold_sd']:.3f} < {exp_info['convergence_threshold']:.3f}? -> {converged}")
            else:
                converged = False
                print(f"  Trial {trial_count} < {exp_info['min_trials']} (min_trials), no convergence check yet")

            # 記錄資料
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow([
                    trial_count, optimal_mtf, response_value, f'{response_time:.3f}',
                    f'{estimates["threshold_mean"]:.2f}', f'{estimates["threshold_sd"]:.3f}',
                    f'{estimates["slope_mean"]:.2f}', f'{estimates["slope_sd"]:.3f}',
                    converged
                ])

            # 檢查停止條件：收斂且達到最少試驗數，或達到最多試驗數
            if converged and trial_count >= exp_info['min_trials']:
                print(f"在第 {trial_count} 個試驗後收斂（達到收斂標準且滿足最少試驗數）")
                break
            elif trial_count >= exp_info['max_trials']:
                print(f"達到最大試驗數 {exp_info['max_trials']}，實驗結束")
                break

            core.wait(0.5)

    # 實驗結束 - 顯示最終結果
    try:
            final_estimates = ado_engine.get_parameter_estimates()
            final_text = (f"實驗完成！\n\n最終估計：\n"
                         f"閾值：{final_estimates['threshold_mean']:.1f}% MTF\n"
                         f"斜率：{final_estimates['slope_mean']:.2f}\n\n"
                         f"總試驗數：{trial_count}\n"
                         f"收斂狀態：{'是' if converged else '否'}\n\n"
                         f"按任意鍵離開")
    except:
        final_text = f"實驗完成！\n\n總試驗數：{trial_count}\n\n按任意鍵離開"
    
    end_text.setText(final_text)
    end_text.draw()
    win.flip(clearBuffer=True)
    event.clearEvents()
    event.waitKeys()

    print(f"\nADO 實驗完成，資料已儲存至：{filename}")
    print(f"總試驗數：{trial_count}")
    if converged:
        print("實驗成功收斂")
    else:
        print("實驗結束時未收斂")

    win.close()
    core.quit()


if __name__ == "__main__":
    run_ado_mtf_experiment()