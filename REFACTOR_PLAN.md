# WebRS_MTF_Threshold 重構計劃

> **創建日期**: 2025-06-20  
> **狀態**: 計劃階段  
> **優先級**: 中等 (建議但非緊急)

## 📋 執行摘要

此專案是一個功能完整的心理物理學研究平台，用於 MTF 清晰度測試。雖然功能正常運行，但 `app.py` 檔案過於龐大 (2,088 行)，影響可維護性。建議進行結構化重構以提升代碼品質。

## 🔍 現狀分析

### 代碼統計
| 檔案 | 行數 | 函數數 | 主要問題 |
|------|------|--------|----------|
| app.py | 2,088 | 24 | 過於龐大，職責混合 |
| mtf_experiment.py | 685 | - | 結構良好 |
| database.py | 305 | - | 結構清晰 |
| csv_data_manager.py | 330 | - | 功能完整 |

### 關鍵指標
- **Session State 使用**: 222 次 (過於頻繁，缺乏集中管理)
- **Print 語句**: 170 個 (應改為 logging)
- **異常處理**: 62 個 try-catch 塊 (覆蓋完整)
- **代碼重複**: 中等程度

## ⚠️ 識別的問題

### 1. 主要問題 (高優先級)
- **app.py 過於龐大**: 2,088 行違反單一責任原則
- **UI 與業務邏輯混合**: 顯示邏輯和實驗邏輯耦合
- **Session State 管理混亂**: 狀態散布各處，難以追蹤

### 2. 次要問題 (中優先級)
- **調試代碼過多**: 170 個 print 語句
- **重複代碼模式**: UI 組件邏輯重複
- **缺乏類型提示**: 部分函數缺少型別註解

### 3. 輕微問題 (低優先級)
- **文件結構可優化**: 部分配置檔案可整理
- **測試覆蓋率**: 缺乏單元測試

## 🎯 重構目標

### 主要目標
1. **提升可維護性**: 將大型檔案拆分為模組化組件
2. **改善代碼組織**: 按功能分離 UI、業務邏輯、數據管理
3. **集中狀態管理**: 創建統一的 session state 管理系統
4. **提升可讀性**: 改善代碼結構和文檔

### 次要目標
1. **標準化日誌**: 替換 print 為 logging 系統
2. **減少重複**: 提取共用組件和函數
3. **增強錯誤處理**: 改善異常處理策略
4. **添加測試**: 為核心功能添加單元測試

## 📁 建議的新檔案結構

```
WebRS_MTF_Threshold/
├── app.py                          # 簡化的主應用入口 (~200 行)
├── config/
│   ├── __init__.py
│   ├── settings.py                 # 應用配置
│   └── logging_config.py           # 日誌配置
├── core/
│   ├── __init__.py
│   ├── session_manager.py          # Session State 管理
│   ├── experiment_controller.py    # 實驗流程控制
│   └── data_exporter.py           # 數據匯出功能
├── ui/
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── image_display.py       # 圖片顯示組件
│   │   ├── response_buttons.py    # 反應按鈕組件
│   │   └── progress_indicators.py # 進度指示器
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── welcome_screen.py      # 歡迎頁面
│   │   ├── instructions_screen.py # 說明頁面
│   │   ├── trial_screen.py        # 試驗頁面
│   │   ├── results_screen.py      # 結果頁面
│   │   └── benchmark_screen.py    # 基準測試頁面
│   └── sidebar.py                 # 側邊欄管理
├── utils/
│   ├── __init__.py
│   ├── logger.py                  # 日誌工具
│   ├── validators.py              # 數據驗證
│   └── helpers.py                 # 通用輔助函數
└── tests/                         # 單元測試 (新增)
    ├── __init__.py
    ├── test_session_manager.py
    ├── test_experiment_controller.py
    └── test_data_export.py
```

## 🚀 分階段重構計劃

### 階段 1: 核心重構 (2-3 天)
**目標**: 拆分 app.py，建立基本架構

#### 步驟 1.1: 建立基礎結構 (0.5 天)
- [ ] 創建目錄結構 (`core/`, `ui/`, `config/`, `utils/`)
- [ ] 設置 `__init__.py` 檔案
- [ ] 建立基本配置檔案

#### 步驟 1.2: 提取 Session State 管理 (1 天)
- [ ] 創建 `core/session_manager.py`
- [ ] 實作 `SessionStateManager` 類
- [ ] 定義狀態模型和類型提示
- [ ] 重構現有 session state 存取

```python
# core/session_manager.py 範例結構
class SessionStateManager:
    def __init__(self):
        self.initialize_default_states()
    
    def get_experiment_stage(self) -> str:
        return st.session_state.get('experiment_stage', 'welcome')
    
    def set_experiment_stage(self, stage: str):
        st.session_state.experiment_stage = stage
    
    # ... 其他狀態管理方法
```

#### 步驟 1.3: 拆分 UI 組件 (1 天)
- [ ] 提取 `welcome_screen()` → `ui/screens/welcome_screen.py`
- [ ] 提取 `instructions_screen()` → `ui/screens/instructions_screen.py`
- [ ] 提取 `mtf_trial_screen()` → `ui/screens/trial_screen.py`
- [ ] 提取 `mtf_results_screen()` → `ui/screens/results_screen.py`
- [ ] 提取 `ado_benchmark_screen()` → `ui/screens/benchmark_screen.py`

#### 步驟 1.4: 重構主應用 (0.5 天)
- [ ] 簡化 `app.py` 為路由器角色
- [ ] 實作模組化導入
- [ ] 測試基本功能

### 階段 2: 業務邏輯重構 (1-2 天)

#### 步驟 2.1: 提取實驗控制邏輯 (1 天)
- [ ] 創建 `core/experiment_controller.py`
- [ ] 提取實驗流程控制邏輯
- [ ] 實作 `ExperimentController` 類

```python
# core/experiment_controller.py 範例結構
class ExperimentController:
    def __init__(self, session_manager: SessionStateManager):
        self.session = session_manager
    
    def start_experiment(self, participant_id: str, config: dict):
        # 實驗啟動邏輯
        
    def process_trial_response(self, response: bool):
        # 處理試驗反應
        
    def check_completion(self) -> bool:
        # 檢查實驗完成狀態
```

#### 步驟 2.2: 重構數據處理 (1 天)
- [ ] 創建 `core/data_exporter.py`
- [ ] 整合現有數據保存邏輯
- [ ] 標準化數據格式

### 階段 3: UI 組件優化 (1 天)

#### 步驟 3.1: 提取可重用組件 (0.5 天)
- [ ] 創建 `ui/components/image_display.py`
- [ ] 創建 `ui/components/response_buttons.py`
- [ ] 創建 `ui/components/progress_indicators.py`

#### 步驟 3.2: 側邊欄管理 (0.5 天)
- [ ] 創建 `ui/sidebar.py`
- [ ] 整合數據存儲資訊顯示
- [ ] 統一側邊欄邏輯

### 階段 4: 日誌和工具 (1 天)

#### 步驟 4.1: 日誌系統 (0.5 天)
- [ ] 創建 `config/logging_config.py`
- [ ] 創建 `utils/logger.py`
- [ ] 替換 print 語句為 logging

```python
# utils/logger.py 範例
import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    # 配置日誌格式和處理器
    return logger
```

#### 步驟 4.2: 工具函數 (0.5 天)
- [ ] 創建 `utils/validators.py` (數據驗證)
- [ ] 創建 `utils/helpers.py` (通用函數)
- [ ] 重構重複代碼

### 階段 5: 測試和文檔 (1 天)

#### 步驟 5.1: 單元測試 (0.5 天)
- [ ] 設置 pytest 環境
- [ ] 為核心組件編寫測試
- [ ] 創建測試配置

#### 步驟 5.2: 文檔更新 (0.5 天)
- [ ] 更新 README.md
- [ ] 創建 API 文檔
- [ ] 更新 CLAUDE.md

## 🛠️ 實施指南

### 重構原則
1. **保持功能完整**: 確保每個階段後應用仍可正常運行
2. **向後兼容**: 保持現有 API 接口
3. **漸進式改進**: 分小步驟進行，便於回滾
4. **測試驅動**: 每個改動都要測試

### 風險管控
1. **備份策略**: 重構前創建完整備份
2. **分支管理**: 使用 Git 分支進行重構
3. **功能測試**: 每個階段完成後進行完整測試
4. **回滾計劃**: 準備快速回滾策略

### 品質檢查清單

#### 代碼品質
- [ ] 函數長度 < 50 行
- [ ] 檔案長度 < 500 行
- [ ] 循環複雜度 < 10
- [ ] 適當的類型提示
- [ ] 清晰的函數文檔

#### 架構品質
- [ ] 明確的責任分離
- [ ] 低耦合高內聚
- [ ] 可測試的設計
- [ ] 清晰的依賴關係

## 📊 成功指標

### 量化指標
- **檔案大小**: 主檔案 < 500 行
- **函數複雜度**: 平均函數 < 30 行
- **代碼重複**: < 5%
- **測試覆蓋率**: > 70%

### 質化指標
- **可維護性**: 新功能開發時間減少 30%
- **可讀性**: 代碼審查時間減少 50%
- **穩定性**: 保持現有功能 100% 正常運行
- **擴展性**: 支援未來功能需求

## 🔄 後續維護

### 代碼規範
1. **命名規範**: 使用清晰的變數和函數名稱
2. **文檔規範**: 所有公開函數都要有文檔
3. **提交規範**: 使用語義化提交訊息
4. **審查規範**: 所有變更都要代碼審查

### 持續改進
1. **定期檢查**: 每季度檢查代碼品質
2. **效能監控**: 監控應用效能指標
3. **用戶回饋**: 收集使用者體驗回饋
4. **技術更新**: 跟進技術棧更新

## 📝 注意事項

### 重要提醒
1. **不要急於重構**: 功能正常時重構風險較高
2. **保持小步快跑**: 每次改動要小而快
3. **重視測試**: 確保重構不破壞現有功能
4. **文檔同步**: 代碼變更時同步更新文檔

### 決策記錄
- **為什麼重構**: 改善可維護性，為未來擴展做準備
- **為什麼現在**: 代碼品質到達臨界點，影響開發效率
- **為什麼這個方案**: 平衡改進效果與實施風險

---

**最後更新**: 2025-06-20  
**下次審查**: 建議在開始重構前再次評估  
**責任人**: 開發團隊  
**批准狀態**: 待批准