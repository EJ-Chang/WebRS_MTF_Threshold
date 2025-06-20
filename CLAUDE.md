# CLAUDE.md - WebRS_MTF_Threshold 開發環境配置

## 關於此專案

這是一個心理物理學研究專案，專門用於 **MTF (調制傳遞函數) 清晰度測試實驗**，使用 **ADO (適應性設計優化)** 技術進行智能實驗設計。

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
1. **app.py**: 主要 Streamlit 網頁應用程式 (2,088 行 - 需要重構)
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

## 🚨 重要提醒：代碼重構計劃

**⚠️ 注意**: 此專案存在一個詳細的重構計劃，請參閱 `REFACTOR_PLAN.md`

### 重構背景
- **問題**: `app.py` 檔案過於龐大 (2,088 行)，影響可維護性
- **狀態**: 功能完整且穩定，但建議進行結構化重構
- **優先級**: 中等 (建議但非緊急)

### 重構要點
1. **階段式重構**: 分 5 個階段，總計需要 5-6 天
2. **核心改進**: 拆分 UI 組件、集中 session state 管理、改善日誌系統
3. **風險控制**: 保持功能完整性，向後兼容，漸進式改進

### 何時考慮重構
- 當需要添加新功能時
- 當維護變得困難時
- 當有充足的開發時間時
- 當需要團隊協作時

**📖 完整重構指南**: 請詳閱 `REFACTOR_PLAN.md` 以了解詳細的實施步驟和最佳實踐。

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

**最後更新**: 2025-06-20  
**負責人**: 研究開發團隊  
**專案版本**: 穩定版 (功能完整，建議重構)