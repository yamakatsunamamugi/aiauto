#!/usr/bin/env python3
"""
統合モデル取得機能のテストスクリプト
"""

import asyncio
import logging
from src.gui.unified_model_fetcher import UnifiedModelFetcher, fetch_models_sync

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_cached_models():
    """キャッシュからモデル情報を取得"""
    print("\n=== キャッシュからモデル情報を取得 ===")
    results = fetch_models_sync("cached")
    
    for service, info in results.items():
        if "error" in info:
            print(f"❌ {service}: {info['error']}")
        else:
            models = info.get("models", [])
            method = info.get("method", "unknown")
            print(f"✅ {service} ({method}): {models}")

def test_api_models():
    """API経由でモデル情報を取得（APIキーが必要）"""
    print("\n=== API経由でモデル情報を取得 ===")
    print("注意: OpenAI APIキーが必要です")
    
    # デモ用（実際のAPIキーは環境変数から取得すべき）
    api_keys = {
        "chatgpt": "sk-..."  # 実際のAPIキーを設定
    }
    
    if api_keys["chatgpt"] == "sk-...":
        print("⚠️ APIキーが設定されていません。スキップします。")
        return
    
    results = fetch_models_sync("api", api_keys=api_keys)
    
    for service, info in results.items():
        if "error" in info:
            print(f"❌ {service}: {info['error']}")
        else:
            models = info.get("models", [])
            print(f"✅ {service}: {models}")

def test_manual_models():
    """手動入力されたモデルを保存"""
    print("\n=== 手動入力モデルの保存 ===")
    
    manual_models = {
        "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo-2024-11-20"],
        "claude": ["claude-3.5-sonnet-20241022", "claude-3-opus"],
        "gemini": ["gemini-1.5-pro-latest", "gemini-1.5-flash"]
    }
    
    results = fetch_models_sync("manual", manual_models=manual_models)
    
    for service, info in results.items():
        models = info.get("models", [])
        print(f"✅ {service}: {models}")

def main():
    """メインテスト関数"""
    print("🚀 統合モデル取得機能のテスト開始")
    
    # 1. キャッシュからの取得をテスト
    test_cached_models()
    
    # 2. 手動入力のテスト
    test_manual_models()
    
    # 3. API経由のテスト（APIキーがある場合）
    test_api_models()
    
    # 4. ブラウザセッション方式の説明
    print("\n=== ブラウザセッション方式について ===")
    print("ブラウザセッション方式は実際のChromeを開くため、")
    print("GUIアプリから実行することをお勧めします。")
    print("実行例: results = fetch_models_sync('browser')")
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    main()