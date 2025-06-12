#!/usr/bin/env python3
"""
Chrome拡張機能のデバッグスクリプト
"""

import sys
import os
import json
import time
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge import ExtensionBridge

def main():
    print("🔍 Chrome拡張機能デバッグ開始")
    print("=" * 60)
    
    try:
        # ExtensionBridge初期化
        bridge = ExtensionBridge()
        print("✅ ExtensionBridge初期化成功")
        
        # 1. 拡張機能の状態確認
        print("\n1️⃣ 拡張機能の状態確認")
        status = bridge.check_extension_status()
        print(f"状態: {status['status']}")
        print(f"メッセージ: {status['message']}")
        
        # 2. 通信ディレクトリの確認
        print("\n2️⃣ 通信ディレクトリの確認")
        bridge_dir = Path("/tmp/ai_automation_bridge")
        print(f"ディレクトリ存在: {bridge_dir.exists()}")
        if bridge_dir.exists():
            files = list(bridge_dir.glob("*"))
            print(f"ファイル数: {len(files)}")
            for f in files[:5]:  # 最初の5ファイルのみ表示
                print(f"  - {f.name}")
        
        # 3. Chrome拡張機能の検出
        print("\n3️⃣ Chrome拡張機能の検出")
        extension_detected = bridge._check_chrome_extension()
        print(f"拡張機能検出: {extension_detected}")
        
        # 4. テストリクエストの送信
        print("\n4️⃣ テストリクエスト送信")
        print("短いテストメッセージを送信します...")
        
        result = bridge.process_with_extension(
            text="テスト",
            ai_service="chatgpt",
            model="gpt-4o-mini"
        )
        
        print(f"\n結果:")
        print(f"成功: {result.get('success', False)}")
        if result.get('success'):
            print(f"応答: {result.get('result', 'なし')[:100]}...")
            print(f"モック使用: {result.get('mock', False)}")
        else:
            print(f"エラー: {result.get('error', '不明')}")
        
        # 5. ログファイルの確認
        print("\n5️⃣ ログファイルの確認")
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                print(f"最新ログ: {latest_log.name}")
                print("最後の10行:")
                with open(latest_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(f"  {line.rstrip()}")
        
        # 6. Chrome拡張機能の手動確認手順
        print("\n6️⃣ Chrome拡張機能の手動確認")
        print("以下を確認してください：")
        print("1. Chromeで chrome://extensions/ を開く")
        print("2. 'AI Automation Bridge' が有効になっているか確認")
        print("3. 拡張機能のアイコンをクリックしてポップアップが表示されるか確認")
        print("4. ChatGPT (https://chat.openai.com/) にログインしているか確認")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()