# CLAUDE.md - WebRS_MTF_Threshold 開發環境配置

## 關於此專案

這是一個心理物理學研究專案，專門用於 **MTF (調制轉換函數) 清晰度測試實驗**，使用 **ADO (適應性設計優化)** 技術進行智能實驗設計。

## 專案概述

### 研究重點領域
- **心理物理學與實驗心理學**: MTF 閾值研究、適應性設計優化
- **人因工程**: 視覺清晰度感知、人機介面研究
- **數據科學與統計**: 貝葉斯推理、實驗設計優化
- **網頁開發**: Streamlit 研究儀表板和分析工具

### 技術堆疊
- **Python**: Streamlit, OpenCV, NumPy, SciPy, Plotly, SQLAlchemy
- **數據庫**: PostgreSQL (Replit), SQLite (本地開發)
- **版本控制**: Git repositories
- **部署平台**: Replit, 本地環境, Ubuntu 服務器

## 主要專案結構

### 核心檔案
1. **app.py**: 主要 Streamlit 網頁應用程式 (模組化架構，已完成重構)
2. **mtf_experiment.py**: MTF 實驗管理核心，包含精確時間測量和刺激緩存
3. **database.py**: PostgreSQL/SQLite 資料庫操作管理
4. **csv_data_manager.py**: CSV 檔案資料管理和備份
5. **main.py**: Replit 環境啟動腳本
6. **run_app.py**: 本地環境啟動腳本

### 實驗核心模組
1. **experiments/ado_utils.py**: 完整的 ADO 引擎實作
2. **experiments/mtf_utils.py**: MTF 圖片處理工具函數
3. **experiments/Exp_MTF_ADO.py**: ADO MTF 實驗主程式
4. **experiments/Exp_MTF_Psychometric_YN.py**: 心理測量函數實驗

## 開發命令

### Python Streamlit 應用程式
```bash
# 本地開發
python run_app.py
# 或直接使用 streamlit
streamlit run app.py

# Replit 環境
python main.py
```

### 常用開發工作流程

### MTF 實驗開發
1. 使用 Streamlit 設計實驗界面
2. 整合 ADO 引擎進行智能實驗設計
3. 實時資料儲存 (CSV + 資料庫雙備份)
4. 結果分析和視覺化

### 資料分析工作流程
1. 使用 Python 工具進行資料收集
2. 統計分析使用 SciPy 和 NumPy
3. 透過 Streamlit 儀表板進行視覺化
4. 文件記錄使用專案內建系統

## 檔案結構說明

- 所有主要專案都使用 Git 版本控制
- Python 專案使用虛擬環境隔離
- 資料儲存使用雲端同步 (Google Drive)
- 實驗資料採用 CSV + 資料庫雙重備份策略

## 相依性與套件管理

### Python 環境
- 虛擬環境位於: `psychophysics_env/`
- 主要相依性: streamlit, opencv-python, numpy, scipy, plotly, sqlalchemy
- 環境配置: 自動檢測運行平台並調整設定

### 資料庫配置
- **Replit**: 自動使用 PostgreSQL (DATABASE_URL)
- **本地開發**: 自動回退到 SQLite
- **資料表**: participants, experiments, trials

## 測試與品質保證

### 實驗驗證
- MTF 處理演算法的數學正確性驗證
- ADO 引擎的收斂性測試
- 跨平台相容性測試

### 程式碼品質
- 類型提示用於核心函數
- 完整的錯誤處理機制
- 中文註解和文件

## ✅ 重構完成狀態

**🎉 重構已完成**: 此專案已成功完成模組化重構

### 重構成果
- **架構**: 模組化設計，程式碼分離為專門的組件
- **程式碼大小**: 從 2,088 行縮減為 139 行主檔案 + 模組化組件
- **維護性**: 大幅提升，各功能分離至獨立模組
- **資料儲存**: 修復並優化了 CSV 和資料庫雙重備份機制

### 新架構特點
1. **模組化設計**: UI 組件、會話管理、實驗控制分離
2. **集中狀態管理**: 統一的 session state 管理
3. **錯誤處理**: 完善的錯誤處理和日誌系統
4. **向後兼容**: 保持所有原有功能完整性

### 專案結構
- **core/**: 核心邏輯 (會話管理、實驗控制)
- **ui/**: 使用者介面組件 (畫面、組件)
- **config/**: 配置和設定檔案
- **utils/**: 工具函數和助手

**📚 參考資料**: 重構的詳細記錄保存在 `REFACTORING_SUMMARY.md` 中。

## 🔧 當前狀態與最新更新

### 專案狀態 (2025-06-24)
- **當前分支**: cleanstart-repl
- **部署狀態**: 已部署並運行
- **模組化架構**: 完全重構完成，採用現代化架構設計

### 系統架構更新
- **圖像顯示優化**: 移除 DPI 縮放影響，改用固定像素大小顯示
- **響應式設計移除**: 改為固定尺寸顯示以提升一致性
- **圖像渲染增強**: 新增圖像渲染與縮放屬性，提升顯示穩定性
- **刺激預覽功能**: 新增 stimuli_preview_screen.py 支援刺激材料預覽

### ADO 功能狀態
- **ADO 計算已暫時禁用**: 為確保實驗時間測量的準確性，ADO 計算功能已被禁用
- **介面相容性維持**: 相關函數返回 None 或 True 以維持系統介面的相容性
- **快速回應導向**: 實驗現在專注於快速回應測試，減少計算延遲
- **資料庫結構完整**: ADO 相關欄位仍保留在資料庫中，以備未來重新啟用

### 使用者介面優化
- **指示畫面重新設計**: 採用三欄佈局顯示主要說明、回應方式及時間安排
- **測試特性強調**: 指示畫面現在強調快速回應的測試特性
- **使用者體驗提升**: 更直觀的介面佈局和說明文字
- **圖像顯示一致性**: 固定尺寸顯示確保跨設備體驗一致

## 🔄 MTF Threshold 實驗流程

### 完整實驗流程說明

#### 1. Welcome Page (歡迎頁面 - 實驗設定)
- **功能**: 參與者輸入 ID，選擇刺激圖像
- **設定參數**: 
  - `max_trials`: 最大試驗次數 (預設 50)
  - `min_trials`: 最小試驗次數 (預設 15)
  - `convergence_threshold`: 收斂閾值 (預設 0.15)
- **狀態**: `experiment_stage = 'welcome'`
- **轉換條件**: 參與者 ID 輸入完成且選擇刺激圖像

#### 2. Instruction Page (指示頁面 - 實驗說明)
- **功能**: 說明實驗內容，選擇是否進行練習
- **使用者選擇**:
  - "開始練習" → 進入練習模式
  - "直接開始實驗" → 跳過練習，直接進入正式實驗
- **狀態**: `experiment_stage = 'instructions'`

#### 3. 實驗階段 (Trial Phase)
**狀態**: `experiment_stage = 'trial'`

##### 3.1 練習模式 (`is_practice = True`)
```python
if is_practice == True:
    # 練習模式特性
    max_trials = 3  # 固定 3 次試驗
    data_storage = False  # 不儲存資料
    trial_counter = practice_trials_completed  # 使用練習計數器
    
    # 流程
    for trial in range(3):
        show_fixation_cross()  # 注視點 (預設 3 秒)
        present_mtf_stimulus()  # 顯示 MTF 處理後的圖像
        collect_response()  # 收集 "清楚" 或 "不清楚" 回應
        
    # 練習完成後
    show_practice_completion_screen()
    user_choice = ["再練習一次", "開始正式實驗"]
```

##### 3.2 正式實驗 (`is_practice = False`)
```python
if is_practice == False:
    # 正式實驗特性
    max_trials = user_defined  # 使用者設定的最大試驗次數
    data_storage = True  # 儲存所有試驗資料
    trial_counter = experiment_trial  # 使用實驗計數器
    
    # 流程
    while not experiment_complete:
        show_fixation_cross()  # 注視點
        present_mtf_stimulus()  # 顯示 MTF 刺激
        collect_response()  # 收集回應
        
        # 資料儲存 (雙重備份)
        save_to_csv()  # 主要儲存
        save_to_database()  # 次要備份
        
        # 檢查結束條件
        if experiment_trial >= max_trials:
            experiment_complete = True
    
    # 轉換到結算畫面
    experiment_stage = 'results'
```

#### 4. 結算畫面 (Results Page)
- **功能**: 顯示實驗結果與統計分析
- **狀態**: `experiment_stage = 'results'`
- **內容包含**:
  - **統計摘要**: 總試驗數、清楚回應數、清楚率、平均反應時間
  - **詳細結果**: 每次試驗的 MTF 值、回應、反應時間
  - **心理測量函數**: Psychometric function 圖表分析
  - **資料下載**: CSV 和 JSON 格式下載
  - **導航選項**: 重新開始實驗、返回主頁、效能測試

### 資料處理與儲存邏輯

#### 資料分離機制
```python
# 練習資料 (不儲存)
practice_trials = [t for t in trial_results if t.get('is_practice') == True]

# 正式實驗資料 (儲存並用於分析)
experiment_trials = [t for t in trial_results if t.get('is_practice') == False]
```

#### 儲存保護機制
- **雙重檢查**: Session state (`is_practice`) + Trial data (`is_practice`)
- **強制過濾**: 所有儲存函數都檢查練習模式
- **日誌記錄**: 詳細記錄每次儲存嘗試和結果

### 狀態管理架構
- **Session State Manager**: 集中管理所有實驗狀態
- **Experiment Controller**: 處理實驗邏輯和資料儲存
- **MTF Experiment Manager**: 管理 MTF 刺激產生和 ADO 計算

## 研究資料管理

- **實驗資料**: 自動備份到 `experiment_data/` 目錄
- **參與者隱私**: 遵循研究倫理協議
- **資料格式**: CSV 主要格式，PostgreSQL 作為次要備份
- **跨平台同步**: 透過雲端存儲確保資料一致性

## 常見問題與解決方案

### Replit 部署問題
- 確保 `main.py` 為入口點
- 檢查環境變數設定 (DATABASE_URL, STREAMLIT_SERVER_PORT)
- 驗證相依性安裝

### 本地開發環境
- 使用虛擬環境避免相依性衝突
- 確認 OpenCV 和 Streamlit 版本相容性
- SQLite 作為本地資料庫備份

### MTF 實驗相關
- 確保刺激圖片存在於 `stimuli_preparation/` 目錄
- 驗證 ADO 引擎正確初始化
- 檢查反應時間測量精確度

## Claude Code 使用提醒

### 專案特性
- 這是一個**心理物理學研究專案**，重視數據精確性和實驗可重現性
- 代碼修改時請注意**實驗邏輯的完整性**
- 遵循**學術研究代碼標準** (可重現性、文件完整性)
- 跨平台相容性很重要 (Replit、本地、服務器)

### 開發建議
- 修改實驗邏輯前先備份
- 測試新功能時使用練習模式
- 保持 CSV 和資料庫資料格式一致性
- 重視用戶體驗 (研究參與者友好的介面)

---

**最後更新**: 2025-06-24  
**負責人**: EJ_CHANG  
**專案版本**: 穩定版 (功能完整，模組化架構，圖像顯示優化完成)  
**Git 分支**: cleanstart-repl (當前開發分支)