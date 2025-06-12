#!/usr/bin/env python3
"""
シンプルなブラウザセッションテスト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.browser_session_fetcher import update_model_list

print("=== ブラウザセッション方式テスト ===")
print("\n注意: 通常のChromeでAIサービスにログインしている必要があります。")
print("Chromeが起動しますが、自動的に閉じられます。\n")

try:
    print("モデルリスト取得中...")
    models = update_model_list()
    
    print("\n取得結果:")
    for service, model_list in models.items():
        if model_list:
            print(f"✅ {service}: {len(model_list)}個のモデル - {model_list[:2]}...")
        else:
            print(f"❌ {service}: 取得失敗")
            
except Exception as e:
    print(f"\nエラー: {e}")
    print("\n通常のChromeでAIサービスにログインしているか確認してください。")