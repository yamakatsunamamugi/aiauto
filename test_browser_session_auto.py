#!/usr/bin/env python3
"""
ブラウザセッション方式のモデルフェッチャーを自動テスト
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
    """ブラウザセッション方式の自動テスト"""
    print("=" * 80)
    print("🚀 ブラウザセッション方式 AIモデル取得テスト（自動実行）")
    print("=" * 80)
    print()
    print("📌 注意: ブラウザウィンドウが自動的に開きます")
    print()
    
    print("🔍 モデル取得を開始します...\n")
    
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
    
    # 簡易レポート生成
    if results:
        with open("browser_session_test_report.txt", 'w', encoding='utf-8') as f:
            f.write("ブラウザセッション方式 テストレポート\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"成功率: {success_count}/5 サービス\n")
            f.write(f"取得モデル数: {total_models}\n\n")
            
            f.write("詳細結果:\n")
            for service, data in results.items():
                f.write(f"\n{service}:\n")
                if "error" not in data:
                    models = data.get("models", [])
                    for model in models:
                        f.write(f"  - {model}\n")
                else:
                    f.write(f"  エラー: {data['error']}\n")
        
        print("\n📄 レポートを browser_session_test_report.txt に保存しました")


if __name__ == "__main__":
    test_browser_session_fetcher()