#!/usr/bin/env python3
"""
接続テストスクリプト
各コンポーネントが正常に動作するか確認
"""

print("🔍 接続テスト開始")
print("="*50)

# 1. Google Sheets接続テスト
print("\n1️⃣ Google Sheets API テスト")
try:
    from src.sheets.sheets_client import SheetsClient
    client = SheetsClient()
    if client.authenticate():
        print("✅ Google Sheets API認証成功")
    else:
        print("❌ Google Sheets API認証失敗")
except Exception as e:
    print(f"❌ エラー: {e}")

# 2. ExtensionBridge テスト
print("\n2️⃣ ExtensionBridge テスト")
try:
    from src.automation.extension_bridge import ExtensionBridge
    bridge = ExtensionBridge()
    print("✅ ExtensionBridge初期化成功")
    
    # 拡張機能の状態確認
    status = bridge.check_extension_status()
    print(f"📊 拡張機能状態: {status}")
except Exception as e:
    print(f"❌ エラー: {e}")

# 3. AI処理テスト（モック）
print("\n3️⃣ AI処理テスト（モック）")
try:
    result = bridge.process_with_extension(
        text="テストメッセージ",
        ai_service="chatgpt",
        model="gpt-4o"
    )
    print(f"📥 結果: {result}")
    if result.get('mock', False):
        print("⚠️  モック応答が返されました（実際のAI処理は実行されていません）")
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()

print("\n"+"="*50)
print("テスト完了")