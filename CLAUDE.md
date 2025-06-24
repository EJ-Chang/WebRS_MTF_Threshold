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

## 專案結構

### 核心應用程式檔案
1. **app.py**: 主要 Streamlit 網頁應用程式 (模組化架構)
2. **run_app.py**: 本地環境啟動腳本 (推薦使用)
3. **main.py**: Replit 環境啟動腳本
4. **mtf_experiment.py**: MTF 實驗管理核心，包含精確時間測量和刺激緩存

### 資料管理模組
1. **database.py**: PostgreSQL/SQLite 資料庫操作管理
2. **csv_data_manager.py**: CSV 檔案資料管理和備份
3. **data_manager.py**: 統一資料管理介面

### 實驗核心模組
1. **experiments/ado_utils.py**: 完整的 ADO 引擎實作
2. **experiments/mtf_utils.py**: MTF 圖片處理工具函數
3. **experiments/Exp_MTF_ADO.py**: ADO MTF 實驗主程式
4. **experiments/Exp_MTF_Psychometric_YN.py**: 心理測量函數實驗

### 模組化架構
- **core/**: 核心邏輯
  - `session_manager.py`: 會話狀態管理
  - `experiment_controller.py`: 實驗控制器
- **ui/**: 使用者介面組件
  - `screens/`: 各實驗畫面 (welcome, instructions, trial, results, etc.)
  - `components/`: 可重用 UI 組件 (按鈕、進度條、圖像顯示)
- **config/**: 配置檔案
  - `settings.py`: 實驗參數配置 (集中管理)
  - `logging_config.py`: 日誌配置
- **utils/**: 工具函數
  - `logger.py`: 日誌工具
  - `analysis_tools.py`: 分析工具
  - `helpers.py`: 通用助手函數

## 開發命令

### Python Streamlit 應用程式
```bash
# 本地開發 (推薦)
python run_app.py

# 或直接使用 streamlit
streamlit run app.py

# Replit 環境
python main.py
```

### 實驗配置管理
實驗參數現在集中管理在 `config/settings.py`：
```python
# 實驗配置常數
MAX_TRIALS = 45              # 最大試驗次數
MIN_TRIALS = 15              # 最小試驗次數
CONVERGENCE_THRESHOLD = 0.15 # 收斂閾值
STIMULUS_DURATION = 1.0      # 刺激持續時間 (秒)
PRACTICE_TRIAL_LIMIT = 1     # 練習試驗次數
```

## 🔧 當前狀態與最新更新

### 專案狀態 (2025-06-24)
- **當前分支**: cleanstart-repl
- **部署狀態**: 已部署並運行
- **模組化架構**: 完全重構完成，採用現代化架構設計
- **配置管理**: 實驗參數已集中化管理

### 最新架構特點
1. **集中配置管理**: 實驗參數集中在 `config/settings.py`
2. **研究者控制**: 參與者無法修改實驗設定
3. **模組化設計**: UI 組件、會話管理、實驗控制完全分離
4. **統一狀態管理**: SessionStateManager 集中管理所有實驗狀態
5. **錯誤處理**: 完善的錯誤處理和日誌系統

### 系統架構優化
- **圖像顯示優化**: 移除 DPI 縮放影響，改用固定像素大小顯示
- **響應式設計移除**: 改為固定尺寸顯示以提升一致性
- **圖像渲染增強**: 新增圖像渲染與縮放屬性，提升顯示穩定性
- **刺激預覽功能**: 支援刺激材料預覽 (`stimuli_preview_screen.py`)

### ADO 功能狀態
- **ADO 計算已暫時禁用**: 為確保實驗時間測量的準確性
- **介面相容性維持**: 相關函數返回預設值以維持系統介面的相容性
- **快速回應導向**: 實驗專注於快速回應測試，減少計算延遲
- **資料庫結構完整**: ADO 相關欄位仍保留在資料庫中，以備未來重新啟用

## 🔄 MTF Threshold 實驗流程

### 完整實驗流程說明

#### 1. Welcome Page (歡迎頁面)
- **功能**: 參與者輸入 ID，選擇刺激圖像
- **配置**: 實驗參數現已鎖定，無法由參與者修改
- **可用刺激圖像**:
  - `stimuli_img.png`: 原始刺激圖
  - `text_img.png`: 文字圖像
  - `tw_newsimg.png`: 台灣新聞
  - `us_newsimg.png`: 美國新聞
- **狀態**: `experiment_stage = 'welcome'`

#### 2. Instructions Page (指示頁面)
- **功能**: 說明實驗內容，選擇是否進行練習
- **使用者選擇**:
  - 啟用練習模式 → 進入練習階段
  - 直接開始實驗 → 跳過練習，進入正式實驗
- **狀態**: `experiment_stage = 'instructions'`

#### 3. Trial Phase (實驗階段)
**狀態**: `experiment_stage = 'trial'`

##### 3.1 練習模式 (`is_practice = True`)
- **試驗次數**: `PRACTICE_TRIAL_LIMIT` (設定為 1 次)
- **資料儲存**: 不儲存練習資料
- **目的**: 讓參與者熟悉實驗流程

##### 3.2 正式實驗 (`is_practice = False`)
- **最大試驗次數**: `MAX_TRIALS` (45 次)
- **最小試驗次數**: `MIN_TRIALS` (15 次)
- **收斂閾值**: `CONVERGENCE_THRESHOLD` (0.15)
- **刺激持續時間**: `STIMULUS_DURATION` (1.0 秒)
- **資料儲存**: 雙重備份 (CSV + 資料庫)

#### 4. Results Page (結果頁面)
- **功能**: 顯示實驗結果與統計分析
- **內容包含**:
  - 統計摘要 (總試驗數、清楚率、平均反應時間)
  - 詳細結果 (每次試驗的 MTF 值、回應、反應時間)
  - 心理測量函數圖表分析
  - 資料下載 (CSV 和 JSON 格式)
  - 導航選項 (重新開始實驗、返回主頁)

### 資料處理與儲存邏輯

#### 資料分離機制
```python
# 練習資料 (不儲存)
practice_trials = [t for t in trial_results if t.get('is_practice') == True]

# 正式實驗資料 (儲存並用於分析)
experiment_trials = [t for t in trial_results if t.get('is_practice') == False]
```

#### 儲存保護機制
- **雙重檢查**: Session state + Trial data 的 `is_practice` 標記
- **強制過濾**: 所有儲存函數都檢查練習模式
- **日誌記錄**: 詳細記錄每次儲存嘗試和結果

## 配置管理指南

### 修改實驗參數
研究者可以透過編輯 `config/settings.py` 來調整實驗參數：

```python
# 在 config/settings.py 中修改這些值
MAX_TRIALS = 45              # 根據研究需求調整
MIN_TRIALS = 15              # 根據收斂需求調整
CONVERGENCE_THRESHOLD = 0.15 # 根據精確度需求調整
STIMULUS_DURATION = 1.0      # 根據實驗設計調整
PRACTICE_TRIAL_LIMIT = 1     # 根據訓練需求調整
```

### 環境配置
系統會自動檢測運行環境：
- **Replit**: 使用 PostgreSQL，端口 5000
- **Ubuntu Server**: 端口 3838
- **本地環境**: SQLite，端口 8501

## 資料管理

### 資料儲存策略
- **主要格式**: CSV 檔案 (位於 `experiment_data/` 目錄)
- **備份**: PostgreSQL/SQLite 資料庫
- **雲端同步**: 透過 Google Drive 確保資料安全

### 資料表結構
- **participants**: 參與者基本資訊
- **experiments**: 實驗設定和元資料
- **trials**: 每次試驗的詳細資料

## 開發指南

### 程式碼品質標準
- 類型提示用於核心函數
- 完整的錯誤處理機制
- 中文註解和文件
- 模組化設計原則

### 測試與驗證
- MTF 處理演算法的數學正確性驗證
- ADO 引擎的收斂性測試 (目前暫時禁用)
- 跨平台相容性測試
- 使用者體驗測試

### 常見問題排除

#### Replit 部署問題
- 確保 `main.py` 為入口點
- 檢查環境變數設定 (DATABASE_URL, STREAMLIT_SERVER_PORT)
- 驗證相依性安裝

#### 本地開發環境
- 使用 `run_app.py` 啟動應用程式
- 確認虛擬環境正確配置
- 檢查 OpenCV 和 Streamlit 版本相容性

#### MTF 實驗相關
- 確保刺激圖片存在於 `stimuli_preparation/` 目錄
- 驗證實驗配置參數正確載入
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
- 實驗參數修改請在 `config/settings.py` 中進行

### 重要提醒
- **配置集中管理**: 所有實驗參數都在 `config/settings.py` 中
- **參與者無法修改設定**: 歡迎頁面已移除配置滑桿
- **研究者控制**: 透過編輯配置檔案來調整實驗參數
- **資料安全**: 練習資料不會被儲存，正式實驗資料有雙重備份

---

**最後更新**: 2025-06-24  
**負責人**: EJ_CHANG  
**專案版本**: 穩定版 v2.0 (模組化架構，配置集中管理)  
**Git 分支**: cleanstart-repl (當前開發分支)  
**主要更新**: 實驗配置集中化管理，參與者介面簡化