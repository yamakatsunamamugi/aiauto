#!/usr/bin/env python3
"""
ブラウザセッション方式のモデルフェッチャーをテスト
"""

import sys
import os
import logging
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.browser_session_model_fetcher import BrowserSessionModelFetcher

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/browser_session_test.log')
    ]
)

logger = logging.getLogger(__name__)

def test_browser_session_fetcher():
    """ブラウザセッション方式のテスト"""
    print("=" * 80)
    print("🚀 ブラウザセッション方式 AIモデル取得テスト")
    print("=" * 80)
    print()
    print("📌 注意事項:")
    print("  1. Chromeブラウザにログイン済みである必要があります")
    print("  2. 各AIサービスにログインしていることを確認してください")
    print("  3. ブラウザウィンドウが自動的に開きます")
    print()
    
    # ユーザー確認
    response = input("続行しますか？ (y/n): ")
    if response.lower() != 'y':
        print("テストを中止しました")
        return
    
    print("\n🔍 モデル取得を開始します...\n")
    
    # フェッチャーを実行
    fetcher = BrowserSessionModelFetcher()
    results = None
    
    try:
        import asyncio
        results = asyncio.run(fetcher.fetch_all_models())
        
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")
        return
    
    # 結果を表示
    print("\n" + "=" * 80)
    print("📊 テスト結果:")
    print("=" * 80)
    
    if results:
        total_models = 0
        success_count = 0
        
        for service, data in results.items():
            print(f"\n【{service.upper()}】")
            
            if "error" in data:
                print(f"  ❌ エラー: {data['error']}")
                if "models" in data and data["models"]:
                    print(f"  ⚠️ フォールバック: {data['models']}")
            else:
                success_count += 1
                models = data.get("models", [])
                total_models += len(models)
                
                print(f"  ✅ 成功: {len(models)}個のモデルを取得")
                print(f"  📋 モデルリスト:")
                for i, model in enumerate(models, 1):
                    print(f"     {i}. {model}")
        
        # サマリー
        print("\n" + "=" * 80)
        print("📈 サマリー:")
        print("=" * 80)
        print(f"  ✅ 成功: {success_count}/5 サービス")
        print(f"  📊 合計: {total_models}個のモデル")
        print(f"  🕐 更新時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 期待される結果と比較
        print("\n" + "=" * 80)
        print("🎯 期待値との比較:")
        print("=" * 80)
        
        expected = {
            "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
            "claude": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet"],
            "gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
        }
        
        for service, expected_models in expected.items():
            if service in results and "models" in results[service]:
                actual_models = [m.lower().replace(" ", "-") for m in results[service]["models"]]
                matches = sum(1 for em in expected_models if any(em in am for am in actual_models))
                print(f"  {service}: {matches}/{len(expected_models)} 期待モデルが見つかりました")
        
        # 結果ファイル確認
        print("\n" + "=" * 80)
        print("💾 保存ファイル:")
        print("=" * 80)
        
        if os.path.exists("config/ai_models_browser_session.json"):
            print("  ✅ config/ai_models_browser_session.json が作成されました")
            with open("config/ai_models_browser_session.json", 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                print(f"  📅 保存時刻: {saved_data.get('last_updated', 'N/A')}")
                print(f"  🔧 手法: {saved_data.get('method', 'N/A')}")
                print(f"  👤 実装者: {saved_data.get('fetcher', 'N/A')}")
        else:
            print("  ❌ 結果ファイルが見つかりません")
    
    print("\n" + "=" * 80)
    print("✅ テスト完了")
    print("=" * 80)


if __name__ == "__main__":
    test_browser_session_fetcher()