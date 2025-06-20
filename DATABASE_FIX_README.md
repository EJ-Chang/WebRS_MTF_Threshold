# 資料庫修正指南 - 確保實驗資料完整儲存

## 問題描述

您發現CSV儲存了完整的實驗資料（參與者、試驗編號、MTF值、圖片、反應、反應時間），但資料庫可能沒有儲存這些關鍵資訊。

## 解決方案

### 🔧 在Replit上執行修正

1. **在Replit Console中運行遷移腳本**：
```bash
python migrate_database.py
```

2. **驗證修正結果**：
```bash
python replit_migration.py
```

3. **如果成功，您會看到**：
```
🎉 SUCCESS: All critical experimental data stored correctly!
💾 Database is ready to store:
   - Participant information
   - Trial numbers and MTF values
   - Stimulus images used
   - Participant responses
   - Reaction times
```

### 📊 修正的內容

**新增的資料庫欄位**：
- `participant_id` - 參與者ID
- `experiment_type` - 實驗類型
- `experiment_timestamp` - 實驗時間戳記
- `stimulus_image_file` - 使用的刺激圖片

**現在資料庫會儲存與CSV相同的資料**：
```
trial_number, mtf_value, response, reaction_time, timestamp, 
participant_id, experiment_type, stimulus_image_file, 
is_correct, left_stimulus, right_stimulus, stimulus_difference, 
ado_stimulus_value, is_practice, experiment_timestamp
```

### 🔍 驗證資料儲存

修正後，每次試驗會在console看到詳細的儲存資訊：

```
📊 Critical experimental data:
   participant_id: your_participant_id
   trial_number: 1
   mtf_value: 50.0
   stimulus_image_file: text_img.png
   response: clear
   reaction_time: 2.345

✅ Trial data saved to CSV
✅ Trial data saved to database (experiment_id: 123)

🔍 Database verification - saved fields: [all fields listed]
📊 Database critical fields:
   participant_id: your_participant_id
   trial_number: 1
   mtf_value: 50.0
   ...
```

### ⚠️ 如果遷移失敗

1. **檢查錯誤訊息** - 通常會顯示具體問題
2. **確認資料庫連接** - 檢查Replit的DATABASE_URL環境變數
3. **聯繫管理員** - 如果是權限問題

### 📈 使用修正後的資料庫

修正後，您可以：
- 從資料庫直接查詢特定參與者的所有試驗
- 分析MTF值和反應的關係
- 追蹤使用了哪些刺激圖片
- 分析反應時間模式

**查詢範例**：
```python
# 取得特定參與者的實驗資料
participant_data = db_manager.get_participant_experiments("participant_id")

# 取得完整實驗資料
experiment_data = db_manager.get_experiment_data(experiment_id)
```

## 確認修正成功

運行 `python replit_migration.py` 後應該看到：
- ✅ 所有關鍵實驗欄位都有資料
- 📊 資料庫與CSV內容一致
- 🎉 SUCCESS 訊息

現在您的資料庫會完整儲存所有實驗資料！