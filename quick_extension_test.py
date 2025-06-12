#!/usr/bin/env python3
"""
Chrome拡張機能の簡単な動作確認スクリプト
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge import ExtensionBridge

def main():
    print("🔍 Chrome拡張機能の動作確認")
    print("=" * 60)
    
    try:
        # ExtensionBridge初期化
        bridge = ExtensionBridge()
        print("✅ ExtensionBridge初期化成功")
        
        # 拡張機能状態確認
        status = bridge.check_extension_status()
        print(f"\n📊 拡張機能ステータス:")
        print(f"  状態: {status['status']}")
        print(f"  メッセージ: {status['message']}")
        print(f"  パス: {status.get('path', 'N/A')}")
        
        if status['status'] == 'missing':
            print("\n❌ Chrome拡張機能がインストールされていません")
            print("\n📋 インストール手順:")
            print("1. Chromeブラウザを開く")
            print("2. chrome://extensions/ にアクセス")
            print("3. 右上の「デベロッパーモード」をON")
            print("4. 「パッケージ化されていない拡張機能を読み込む」をクリック")
            print(f"5. 以下のフォルダを選択:\n   {project_root}/chrome-extension")
            
        elif status['status'] == 'ready':
            print("\n✅ Chrome拡張機能は正しくインストールされています")
            print("\n🧪 簡単なテストを実行しますか？ (y/n): ", end='')
            
            if input().lower() == 'y':
                print("\n📝 テストメッセージ送信中...")
                result = bridge.process_with_extension(
                    text="テストメッセージ",
                    ai_service="chatgpt",
                    model="gpt-4o-mini"
                )
                
                if result['success']:
                    if result.get('mock', False):
                        print("⚠️ モック応答（拡張機能は動作していません）")
                    else:
                        print("✅ Chrome拡張機能は正常に動作しています")
                    print(f"応答: {result['result'][:100]}...")
                else:
                    print(f"❌ エラー: {result['error']}")
                    
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()