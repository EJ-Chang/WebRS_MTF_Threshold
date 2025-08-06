# WebRS MTF 實驗執行流程文檔

## 🧪 專案架構概覽

WebRS_MTF_Threshold 是一個基於 Streamlit 的網頁實驗系統，用於測量 MTF (Modulation Transfer Function) 閾值，採用先進的 ADO (Adaptive Design Optimization) 演算法。

## 📋 實驗執行流程 Pseudo Code

```pseudocode
// ============================================================================
// 主要入口點：app.py
// ============================================================================

MAIN APPLICATION:
    INITIALIZE Streamlit page config
    DETECT environment (local/replit/server)
    SETUP logging system
    
    IF session_manager not initialized:
        CREATE SessionStateManager()
        CREATE ExperimentController(session_manager)
    
    ROUTE to appropriate screen based on experiment_stage:
        - 'welcome' → WelcomeScreen
        - 'instructions' → InstructionsScreen  
        - 'trial' → TrialScreen
        - 'results' → ResultsScreen
        - 'stimuli_preview' → PreviewScreen
        - 'benchmark' → BenchmarkScreen

// ============================================================================
// 實驗流程：SessionStateManager + ExperimentController
// ============================================================================

EXPERIMENT LIFECYCLE:

1. WELCOME STAGE:
    DISPLAY welcome screen
    INPUT participant_id
    SELECT experiment_mode (practice/experiment)
    SELECT stimulus_image (stimuli_img.png/text images)
    
    ON start_button_click:
        IF participant_id valid:
            SET experiment_stage = 'instructions'
            RERUN streamlit

2. INSTRUCTIONS STAGE:
    DISPLAY experiment instructions
    IF not practice_mode:
        CREATE database experiment record
    INITIALIZE MTFExperimentManager:
        LOAD base_image from stimuli_preparation/
        INITIALIZE v0.4 MTF parameters:
            CALCULATE dynamic_mtf_parameters(27", 3840x2160)
            BUILD MTF lookup table for fast processing
        INITIALIZE ADOEngine:
            SET design_space = [10%-99% MTF values]
            SET threshold_range = (5, 99)
            SET slope_range = (0.05, 5.0)
        SETUP precision timer and stimulus cache
    
    ON start_experiment_click:
        SET experiment_stage = 'trial' 
        RESET trial counters
        RERUN streamlit

3. TRIAL STAGE (核心實驗循環):

    MAIN_TRIAL_LOOP:
        WHILE not experiment_complete:
            
            // === Trial Preparation ===
            CALL mtf_experiment_manager.get_next_trial():
                IF ADO_engine available:
                    mtf_value = ado_engine.get_optimal_design()  // ADO 選擇最優 MTF 值
                ELSE:
                    mtf_value = random_choice([10,20,30...90])   // 備用隨機選擇
                
                // === MTF 刺激圖片生成 (關鍵處理) ===
                stimulus_image = generate_stimulus_image(mtf_value):
                    CHECK stimulus_cache for mtf_value
                    IF not cached:
                        // 使用修正後的 v0.4 算法
                        processed_image = experiments/mtf_utils.apply_mtf_to_image(
                            base_image, 
                            mtf_value, 
                            use_v4_algorithm=True  // 啟用查表系統和兼容性修正
                        ):
                            // 這裡會調用已修正的 MTF test v0.4 兼容邏輯
                            sigma_pixels = get_sigma_from_mtf_lookup(mtf_value)
                            sigma_pixels = sigma_pixels / pixel_size_mm  // 關鍵修正
                            APPLY cv2.GaussianBlur(sigma=sigma_pixels)
                        CACHE processed_image for future use
                    RETURN stimulus_image
            
            // === 刺激呈現與反應收集 ===
            DISPLAY animated fixation cross (1 second)
            DISPLAY stimulus_image (1 second duration)
            DISPLAY response buttons ("Clear" / "Not Clear")
            
            MEASURE response_time from stimulus_onset
            RECORD user_response (clear=1, not_clear=0)
            
            // === ADO 更新 (關鍵科學演算法) ===
            CALL mtf_experiment_manager.record_response():
                ado_engine.update_posterior(mtf_value, user_response)
                    // Bayesian 參數更新
                    UPDATE threshold posterior distribution  
                    UPDATE slope posterior distribution
                    CALCULATE new parameter estimates
                    EVALUATE convergence criteria
                
                STORE trial_result:
                    - mtf_value
                    - user_response  
                    - reaction_time
                    - threshold_mean, threshold_sd
                    - slope_mean, slope_sd
                    - converged flag
                
                SAVE to both CSV and database
            
            // === 終止條件檢查 ===
            INCREMENT trial_counter
            IF practice_mode AND trials >= PRACTICE_TRIAL_LIMIT:
                BREAK
            IF experiment_mode AND trials >= MAX_TRIALS:
                BREAK
            IF convergence_achieved AND trials >= MIN_TRIALS:
                BREAK  // 可選：目前被禁用以確保完整試驗

4. RESULTS STAGE:
    CALCULATE experiment_summary:
        - total_trials
        - accuracy_rate (clear responses %)
        - average_reaction_time
        - final_threshold_estimate ± uncertainty
        - convergence_status
    
    DISPLAY results with visualizations
    PROVIDE data export options
    
    ON restart_click:
        RESET all session states
        SET experiment_stage = 'welcome'

// ============================================================================
// 資料儲存雙重備份系統
// ============================================================================

DATA STORAGE:
    FOR each trial:
        CSV_backup: participant_id_timestamp.csv
        DATABASE_backup: 
            experiments table (session metadata)
            trials table (individual trial data)
            
    SYNC both storage systems
    HANDLE database failures gracefully

// ============================================================================
// 關鍵技術特點
// ============================================================================

TECHNICAL HIGHLIGHTS:
    1. MTF Processing: 
        - v0.4 algorithm with lookup table system (10-100x faster)
        - MTF test v0.4 compatibility (sigma calculation corrected)
        - Dynamic parameter calculation (27" 4K panel optimized)
    
    2. ADO Engine:
        - Real-time Bayesian optimization
        - Grid-search parameter space (threshold × slope)
        - Entropy-based trial selection
        - Convergence monitoring
    
    3. Performance Optimization:
        - Image caching system (LRU)
        - Pre-loading likely MTF values
        - Precision timing system
        - Background computation during fixation
    
    4. Robust Architecture:
        - Modular UI screens
        - Centralized session management  
        - Dual data storage backup
        - Environment-specific configuration
        - Error recovery mechanisms

// ============================================================================
// 執行命令
// ============================================================================

TO RUN EXPERIMENT:
    cd /path/to/WebRS_MTF_Threshold/
    ./psychophysics_env/bin/python run_app.py     // 本地開發
    // OR
    streamlit run app.py                          // 直接執行
    // OR  
    python main.py                                // Replit 環境
```

## 🎯 實驗執行流程總結

### 1. **系統啟動**
- Streamlit 網頁應用程式透過模組化路由系統
- 環境自動偵測 (local/replit/server)
- 日誌系統初始化

### 2. **實驗初始化**
- 載入基礎刺激圖片
- 建立 MTF v0.4 查表系統（10-100倍效能提升）
- 初始化 ADO 貝葉斯最佳化引擎
- 設定精確計時和刺激快取系統

### 3. **試驗循環 (核心流程)**
- **ADO 選擇**: 貝葉斯最佳化選擇下一個最有訊息量的 MTF 值
- **刺激生成**: 即時產生 MTF 模糊圖片（使用修正後的 v0.4 算法）
- **反應收集**: 測量使用者對圖片清晰度的判斷和反應時間
- **參數更新**: 貝葉斯更新閾值和斜率的後驗分佈

### 4. **資料管理**
- 雙重備份系統：CSV 檔案 + 資料庫
- 即時儲存每個試驗結果
- 容錯機制確保資料完整性

### 5. **結果呈現**
- MTF 閾值估計值與信心區間
- 實驗收斂狀態
- 詳細統計報告和視覺化

## 🔬 技術架構重點

### MTF 處理系統
- **v0.4 演算法**: 與 `[OE] MTF_test_v0.4.py` 完全相容
- **查表系統**: 預計算 MTF-sigma 對應表，大幅提升效能
- **動態參數**: 自動計算 27" 4K 面板的像素大小和 Nyquist 頻率
- **關鍵修正**: `sigma_pixels = sigma_pixels / pixel_size_mm` 確保與標準實作一致

### ADO 最佳化引擎
- **貝葉斯方法**: 即時更新參數的後驗分佈
- **格點搜尋**: 閾值 (5-99%) × 斜率 (0.05-5.0) 參數空間
- **熵導向選擇**: 選擇資訊量最大的下一個試驗點
- **收斂監控**: 自動偵測參數估計的收斂狀況

### 效能最佳化
- **LRU 快取**: 智慧圖片快取系統
- **預載機制**: 根據 ADO 預測預載可能的刺激
- **精確計時**: 校正系統延遲，提供準確的反應時間測量
- **背景計算**: 在注視點期間進行 ADO 計算

## 📁 主要檔案結構

```
WebRS_MTF_Threshold/
├── app.py                          # 主路由器 (135行，重構版)
├── mtf_experiment.py               # MTF 實驗管理核心
├── experiments/
│   ├── ado_utils.py               # ADO 貝葉斯最佳化引擎
│   └── mtf_utils.py               # MTF 處理工具 (v0.4 相容)
├── core/
│   ├── session_manager.py         # 集中式 session 狀態管理
│   └── experiment_controller.py   # 實驗流程控制
├── ui/
│   ├── screens/                   # 模組化畫面
│   └── components/                # 可重用 UI 元件
└── stimuli_preparation/
    └── [OE] MTF_test_v0.4.py      # 標準 MTF 處理參考實作
```

## 🚀 執行方式

### 本地開發
```bash
cd /path/to/WebRS_MTF_Threshold/
./psychophysics_env/bin/python run_app.py
```

### 直接執行
```bash
streamlit run app.py
```

### Replit 環境
```bash
python main.py
```

## 🎭 實驗模式

### Practice Mode (練習模式)
- 限制試驗次數 (可設定)
- 相同的 ADO 邏輯但較短的體驗
- 不儲存至主資料庫

### Experiment Mode (正式實驗)
- 完整的 ADO 最佳化流程
- 最多 45 次試驗或達收斂標準
- 完整資料記錄和分析

---

**文件建立時間**: 2025-01-25  
**MTF 算法版本**: v0.4 (兼容 MTF test v0.4)  
**ADO 引擎狀態**: 完整貝葉斯最佳化實作  
