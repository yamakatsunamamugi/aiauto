#!/usr/bin/env python3
"""
スプレッドシート自動化GUIアプリケーション（バイパスモード版）
Chrome拡張機能をバイパスして動作確認可能
"""

import sys
from pathlib import Path

# gui_automation_app_fixed.pyの内容をインポート
sys.path.insert(0, str(Path(__file__).parent))

# 既存のGUIアプリケーションをインポート
from gui_automation_app_fixed import *

# ExtensionBridgeをバイパス版に置き換え
import src.automation.extension_bridge
import src.automation.extension_bridge_bypass

# モジュールを置き換え
src.automation.extension_bridge.ExtensionBridge = src.automation.extension_bridge_bypass.ExtensionBridgeBypass

def main():
    """メイン実行関数（バイパスモード）"""
    print("🎯 スプレッドシート自動化GUIアプリ【バイパスモード】")
    print("=" * 60)
    print("⚠️  Chrome拡張機能をバイパスして動作します")
    print("📋 主要機能:")
    print("  ✅ スプレッドシート読み込み・書き込み（実動作）")
    print("  ⚠️  AI応答（シミュレーション）")
    print("  ✅ 処理フロー確認")
    print("  ✅ エラーハンドリング確認")
    print()
    print("💡 本番環境では通常版を使用してください")
    print("=" * 60)
    print()
    
    root = tk.Tk()
    app = SpreadsheetAutomationGUI(root)
    
    # バイパスモードの説明を追加
    bypass_message = """
🔄 バイパスモード動作中

現在、Chrome拡張機能をバイパスして動作しています。
- スプレッドシートの読み書きは実際に動作します
- AI応答はシミュレーションされます
- 処理フローの確認に使用してください

本番環境での使用には：
1. Chrome拡張機能を正しくインストール
2. 各AIサービスにログイン
3. 通常版アプリケーションを使用
    """
    
    app.log(bypass_message)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n⏹️ アプリケーション終了")

if __name__ == "__main__":
    main()