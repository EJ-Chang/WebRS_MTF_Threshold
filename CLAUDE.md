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
- **ADO 核心功能運行中**: 實驗使用完整的 ADO 引擎進行智能刺激選擇
- **Bayesian 優化**: 每次試驗後更新後驗分布，學習參與者的感知閾值
- **最佳設計選擇**: 系統根據當前參數估計選擇最佳 MTF 值
- **部分功能為提高時間精確性而禁用**:
  - 試驗間 ADO 計算被禁用，減少延遲
  - 提前收斂終止被禁用，確保執行完整試驗次數
  - ADO 參數更新仍正常運作，資料仍被記錄

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

## ADO 技術詳細說明

### ADO 引擎架構
實驗使用完整的 Bayesian 適應性設計優化系統：

#### 核心 ADO 功能 (運行中)
1. **參數估計**: Logistic psychometric function 的閾值和斜率參數
2. **Bayesian 更新**: 每次試驗後更新後驗分布
3. **互資訊計算**: 計算各候選 MTF 值的效用函數
4. **最佳設計選擇**: 選擇能最大化資訊增益的 MTF 值
5. **收斂監控**: 追蹤參數估計的不確定性

#### ADO 實作細節
```python
# 在 experiments/ado_utils.py 中的核心 ADO 類別
class ADOEngine:
    - Bayesian 後驗更新
    - 互資訊 (Mutual Information) 計算
    - 最佳化設計選擇
    - 參數估計與信賴區間
    - 收斂檢查機制
```

#### 運行狀態說明
- ✅ **刺激選擇**: ADO 引擎選擇每個試驗的最佳 MTF 值
- ✅ **學習機制**: 系統從每個回應學習，更新對參與者閾值的估計
- ✅ **參數追蹤**: 所有 ADO 估計參數都被記錄在試驗資料中
- ❌ **提前終止**: 為確保固定試驗次數，提前收斂終止被禁用
- ❌ **即時計算**: 部分試驗間 ADO 計算被禁用以提高時間精確性

#### ADO 資料記錄
每個試驗記錄以下 ADO 相關資料：
- `estimated_threshold`: 當前閾值估計
- `estimated_slope`: 當前斜率估計  
- `threshold_std`: 閾值估計的標準差
- `slope_std`: 斜率估計的標準差
- `threshold_ci_lower/upper`: 閾值 95% 信賴區間
- `slope_ci_lower/upper`: 斜率 95% 信賴區間
- `ado_entropy`: ADO 熵值 (不確定性指標)

### ADO 計算時機分析 (2025-06-25 詳細驗證)

經過代碼分析確認，ADO 計算確實在運行，但時機與原始設計不同：

#### ✅ 實際 ADO 計算時間點

**1. Trial 開始時 - 刺激選擇計算**
```python
# 位置: mtf_experiment.py line 548
# 時機: 當 get_next_trial() 被調用時
mtf_value = self.ado_engine.get_optimal_design()  # 計算最佳 MTF 值
```

**2. Trial 結束時 - 學習更新計算**
```python
# 位置: mtf_experiment.py line 623  
# 時機: 當 record_response() 被調用時
self.ado_engine.update_posterior(trial_data['mtf_value'], response_value)  # 更新學習
```

#### 📋 實際試驗流程時序

```
Trial N:
├── 用戶回應 Trial N-1
├── record_response() 調用 → ADO 學習更新 (計算發生在這裡)
│
Trial N+1:  
├── get_next_trial() 調用 → ADO 選擇下個 MTF 值 (計算發生在這裡)
├── 生成刺激圖像
├── Fixation Cross (3秒) → 什麼都不做 (原始優化設計被禁用)
├── 呈現刺激
└── 等待回應
```

#### 🤔 當前問題分析

- **ADO 計算確實運行**: 每次選擇刺激和學習都有計算
- **計算時機不理想**: 計算發生在用戶等待時，可能造成延遲
- **原始設計更優**: 在 fixation 期間預先計算可避免延遲
- **結論**: ADO 沒有被完全禁用，只是「在 fixation 期間提前計算下次刺激」的優化被禁用了

#### 💡 ADO 強度來源機制

1. 用戶回應完 Trial N 後，`record_response()` 立即更新 ADO 學習
2. 準備 Trial N+1 時，`get_next_trial()` 立即調用 ADO 計算最佳強度
3. 每個 trial 的強度都是 ADO 實時計算出來的 (需要時才計算，而非提前計算)

## 🚀 優化計劃與待辦事項

### 當前優化目標 (2025-06-25)

#### 1. 🐌 Replit 載入性能優化 (高優先級)
**問題描述**: Replit 平台上應用程式載入緩慢
**影響範圍**: 
- 用戶體驗下降
- 實驗開始延遲
- 可能影響實驗資料收集效率

**調查方向**:
- [ ] 分析應用程式啟動時間瓶頸
- [ ] 檢查模組導入順序和相依性
- [ ] 評估 Streamlit 配置優化機會
- [ ] 檢查資料庫連接初始化時間
- [ ] 分析圖像預載入機制效率

#### 2. 🖼️ 像素精確圖像處理優化 (中優先級)
**問題描述**: Pixel-to-pixel 圖像處理尚未完善
**當前解決方案**: 硬體強制 100% DPI 顯示
**技術債務**: 臨時解決方案，需要完善的像素精確控制

**優化計劃**:
- [ ] 實作真正的 pixel-to-pixel 圖像渲染
- [ ] 移除硬體 DPI 強制設定依賴
- [ ] 確保跨平台像素精確性一致
- [ ] 優化圖像縮放算法
- [ ] 驗證 MTF 處理的數學精確性

#### 3. 🔄 ADO 計算時機優化 (低優先級)
**潛在改進**: 恢復 fixation 期間預先計算機制
**目標**: 減少試驗間延遲，提升用戶體驗
**考量**: 需權衡計算精確性與響應速度

### 性能監控指標

#### 載入時間基準
- **本地環境**: < 3 秒
- **Replit 環境**: 目標 < 10 秒 (當前需優化)
- **Ubuntu Server**: < 5 秒

#### 圖像處理精確度
- **像素精確性**: 100% (當前透過硬體強制達成)
- **跨平台一致性**: 需驗證
- **MTF 計算精確度**: 數學驗證通過

### 技術債務管理

#### 高技術債務項目
1. **DPI 硬體強制設定**: 需要軟體解決方案
2. **Replit 性能瓶頸**: 需深入分析和優化
3. **圖像渲染依賴**: 需要更健壯的跨平台解決方案

#### 代碼健康度
- **模組化程度**: ✅ 優秀 (v2.0 重構完成)
- **錯誤處理**: ✅ 完善
- **文檔完整度**: ✅ 詳細
- **測試覆蓋**: ⚠️ 需要更多自動化測試

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
- ADO 引擎的收斂性測試 (核心功能運行，提前終止禁用)
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
- 驗證 ADO 引擎正確初始化和運行
- 確認實驗配置參數正確載入
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

**最後更新**: 2025-06-25  
**負責人**: EJ_CHANG  
**專案版本**: 穩定版 v2.0 (模組化架構，配置集中管理，ADO 智能實驗設計)  
**Git 分支**: cleanstart-repl (當前開發分支)  
**主要更新**: ADO 計算時機分析完成，優化計劃制定，性能瓶頸識別  
**技術狀態**: ADO 核心功能運行中，識別載入性能和像素精確處理優化需求
