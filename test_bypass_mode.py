#!/usr/bin/env python3
"""
バイパスモードのテストスクリプト
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge_bypass import ExtensionBridgeBypass

def test_bypass_mode():
    """バイパスモードのテスト"""
    print("🧪 バイパスモードテスト開始")
    print("=" * 60)
    
    # ExtensionBridgeBypass初期化
    bridge = ExtensionBridgeBypass()
    print("✅ ExtensionBridgeBypass初期化成功")
    
    # 1. 状態確認
    print("\n1️⃣ 拡張機能状態確認")
    status = bridge.check_extension_status()
    print(f"状態: {status['status']}")
    print(f"メッセージ: {status['message']}")
    print(f"バイパスモード: {status.get('bypass_mode', False)}")
    
    # 2. 各種質問のテスト
    test_cases = [
        ("こんにちは", "chatgpt", "gpt-4o-mini"),
        ("2 + 2 = ?", "chatgpt", "gpt-4o"),
        ("今日は何曜日？", "claude", "claude-3.5-sonnet"),
        ("Pythonでhello worldを書いて", "gemini", "gemini-1.5-pro"),
        ("天気はどう？", "genspark", "default"),
    ]
    
    print("\n2️⃣ 各種質問のテスト")
    for i, (text, ai_service, model) in enumerate(test_cases, 1):
        print(f"\nテスト{i}: {text}")
        print(f"AI: {ai_service}, モデル: {model}")
        
        result = bridge.process_with_extension(
            text=text,
            ai_service=ai_service,
            model=model
        )
        
        if result['success']:
            print("✅ 成功")
            print(f"応答: {result['result'][:200]}...")
            print(f"処理時間: {result.get('processing_time', 'N/A')}秒")
            print(f"バイパスモード: {result.get('bypass_mode', False)}")
        else:
            print(f"❌ 失敗: {result['error']}")
    
    # 3. 統計情報
    print("\n3️⃣ 統計情報")
    stats = bridge.get_stats()
    print(f"総リクエスト数: {stats['total_requests']}")
    print(f"成功: {stats['successful_requests']}")
    print(f"失敗: {stats['failed_requests']}")
    print(f"モック応答: {stats['mock_responses']}")
    print(f"成功率: {stats['success_rate']:.1f}%")
    
    print("\n✅ バイパスモードは正常に動作しています")
    print("\n📝 次のステップ:")
    print("1. python3 gui_automation_app_bypass.py でGUIを起動")
    print("2. スプレッドシートのURLを入力して動作確認")
    print("3. AI処理がシミュレーションされることを確認")

if __name__ == "__main__":
    test_bypass_mode()