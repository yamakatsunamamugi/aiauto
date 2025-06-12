#!/usr/bin/env python3
"""
GUI自動化処理のデバッグテスト
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_gui_functionality():
    """GUI機能のテスト"""
    
    print("🔍 GUI自動化機能テスト開始")
    print("=" * 60)
    
    # 必要なモジュールのインポート確認
    try:
        from src.sheets.sheets_client import SheetsClient
        print("✅ SheetsClient インポート成功")
    except ImportError as e:
        print(f"❌ SheetsClient インポート失敗: {e}")
    
    try:
        from src.automation.extension_bridge import ExtensionBridge
        print("✅ ExtensionBridge インポート成功")
    except ImportError as e:
        print(f"❌ ExtensionBridge インポート失敗: {e}")
    
    # Tkinterインポート確認
    try:
        import tkinter as tk
        from tkinter import ttk
        print("✅ Tkinter インポート成功")
    except ImportError as e:
        print(f"❌ Tkinter インポート失敗: {e}")
    
    # テストデータ
    test_url = "https://docs.google.com/spreadsheets/d/1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg/edit?gid=1633283608#gid=1633283608"
    
    # SheetsClient動作確認
    print("\n📊 SheetsClient動作確認:")
    try:
        client = SheetsClient()
        if client.authenticate():
            print("✅ 認証成功")
            
            # ID抽出テスト
            sheet_id = test_url.split('/spreadsheets/d/')[1].split('/')[0]
            sheet_id = sheet_id.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            print(f"✅ ID抽出成功: {sheet_id}")
            
            # スプレッドシート情報取得
            info = client.get_spreadsheet_info(sheet_id)
            if info:
                print(f"✅ スプレッドシート情報取得成功: {info['title']}")
            else:
                print("❌ スプレッドシート情報取得失敗")
        else:
            print("❌ 認証失敗")
    except Exception as e:
        print(f"❌ SheetsClient エラー: {e}")
    
    # ExtensionBridge動作確認
    print("\n🤖 ExtensionBridge動作確認:")
    try:
        bridge = ExtensionBridge()
        status = bridge.check_extension_status()
        print(f"✅ ステータス確認成功: {status['status']} - {status['message']}")
        
        # モック応答テスト
        result = bridge.process_with_extension(
            text="テスト",
            ai_service="chatgpt",
            model="gpt-4o"
        )
        if result['success']:
            print(f"✅ モック応答成功: {result['result'][:50]}...")
        else:
            print(f"❌ 処理失敗: {result['error']}")
    except Exception as e:
        print(f"❌ ExtensionBridge エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gui_functionality()