#!/usr/bin/env python3
"""
Googleスプレッドシートアクセステスト
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.sheets.sheets_client import SheetsClient

def test_sheets_access():
    """スプレッドシートアクセステスト"""
    
    # テストするスプレッドシートID
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg/edit?gid=1633283608#gid=1633283608"
    
    print("🔍 Googleスプレッドシートアクセステスト開始")
    print("=" * 60)
    
    try:
        # Sheets クライアント初期化
        print("📋 SheetsClient初期化中...")
        client = SheetsClient()
        
        # 認証
        print("🔐 Google Sheets API認証中...")
        auth_success = client.authenticate()
        
        if not auth_success:
            print("❌ 認証失敗")
            print("\n📝 解決方法:")
            print("1. config/credentials.json が正しく配置されているか確認")
            print("2. Google Cloud Project でSheets APIが有効化されているか確認")
            return False
        
        print("✅ 認証成功")
        
        # スプレッドシートID抽出
        print(f"🔗 URL解析中: {spreadsheet_url}")
        spreadsheet_id = client.extract_spreadsheet_id(spreadsheet_url)
        
        if not spreadsheet_id:
            print("❌ スプレッドシートID抽出失敗")
            return False
        
        print(f"✅ スプレッドシートID: {spreadsheet_id}")
        
        # スプレッドシート情報取得
        print("📊 スプレッドシート情報取得中...")
        info = client.get_spreadsheet_info(spreadsheet_id)
        
        if not info:
            print("❌ スプレッドシート情報取得失敗")
            print("\n📝 よくある原因:")
            print("1. スプレッドシートが以下のメールアドレスに共有されていない:")
            print("   ai-automation-bot@my-ai-automation-462102.iam.gserviceaccount.com")
            print("2. 共有権限が「閲覧者」になっている（「編集者」が必要）")
            print("3. スプレッドシートが削除されているか、URLが間違っている")
            print("\n🔧 解決手順:")
            print("1. Googleスプレッドシートを開く")
            print("2. 右上の「共有」ボタンをクリック")
            print("3. 以下のメールアドレスを追加:")
            print("   ai-automation-bot@my-ai-automation-462102.iam.gserviceaccount.com")
            print("4. 権限を「編集者」に設定")
            print("5. 「送信」をクリック")
            return False
        
        print("✅ スプレッドシート情報取得成功")
        print(f"📝 タイトル: {info['title']}")
        print(f"📄 シート数: {len(info['sheets'])}")
        
        # シート一覧表示
        print("\n📋 利用可能なシート:")
        for i, sheet in enumerate(info['sheets']):
            print(f"  {i+1}. {sheet['title']} (ID: {sheet['id']})")
        
        # 最初のシートのデータを少し読み込み
        first_sheet = info['sheets'][0]
        sheet_name = first_sheet['title']
        test_range = f"{sheet_name}!A1:E10"
        
        print(f"\n🔍 テストデータ読み込み: {test_range}")
        data = client.read_range(spreadsheet_id, test_range)
        
        if data:
            print("✅ データ読み込み成功")
            print(f"📊 読み込み行数: {len(data)}")
            
            # 最初の数行を表示
            for i, row in enumerate(data[:5]):
                print(f"  行{i+1}: {row}")
                
            if len(data) > 5:
                print(f"  ... 他 {len(data) - 5} 行")
        else:
            print("⚠️ データが空、またはアクセス権限に問題があります")
        
        print("\n🎉 全てのテストが完了しました！")
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print(f"📝 詳細: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_sheets_access()
    
    if success:
        print("\n✅ スプレッドシートアクセス設定は正常です")
        print("🚀 gui_automation_app_fixed.py を実行できます")
    else:
        print("\n❌ 設定に問題があります")
        print("📝 上記の解決手順に従って設定を修正してください")