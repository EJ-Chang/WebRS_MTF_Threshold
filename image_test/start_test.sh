#!/bin/bash

# 圖片顯示測試快速啟動腳本

echo "🔬 啟動圖片顯示測試工具"
echo "=========================="
echo

cd "$(dirname "$0")"

echo "📁 當前目錄: $(pwd)"
echo "🖼️  測試圖片數量: $(ls images/*.png | wc -l)"
echo

echo "🚀 啟動HTTP服務器..."
echo "💡 提示: 使用 Ctrl+C 可以停止服務器"
echo

python3 simple_server.py