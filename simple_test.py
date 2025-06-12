#!/usr/bin/env python3
"""
シンプルなブラウザセッション方式のテスト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.browser_session_model_fetcher import fetch_models_sync

print("🚀 ブラウザセッション方式でモデル取得中...")
print("📌 ブラウザが開きます。ログイン済みであることを確認してください。")
print()

try:
    results = fetch_models_sync()
    
    print("\n📊 結果:")
    for service, data in results.items():
        if "error" not in data:
            models = data.get("models", [])
            print(f"✅ {service}: {models}")
        else:
            print(f"❌ {service}: エラー - {data['error']}")
            
except Exception as e:
    print(f"エラー: {e}")