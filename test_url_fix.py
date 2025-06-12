#!/usr/bin/env python3
"""
URL解析修正テスト
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.sheets.sheets_client import SheetsClient

def test_url_parsing():
    """URL解析修正をテスト"""
    
    print("🔍 URL解析修正テスト開始")
    print("=" * 60)
    
    # 改行が含まれるURLのテストケース
    test_urls = [
        # 正常なURL
        "https://docs.google.com/spreadsheets/d/1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg/edit?gid=1633283608#gid=1633283608",
        # 改行が含まれるURL（問題のケース）
        "https://docs.google.com/spreadsheets/d/1C5aOSyyCBXf7HwF-BGGu-cz5jdRwN\nBaoW4G4ivIRrRg/edit?gid=1633283608#gid=1633283608",
        # スペースが含まれるURL
        "https://docs.google.com/spreadsheets/d/1C5aOSyyCBXf7HwF-BGGu-cz5jdRwN  BaoW4G4ivIRrRg/edit?gid=1633283608#gid=1633283608"
    ]
    
    for i, url in enumerate(test_urls):
        print(f"\n📋 テストケース{i+1}:")
        print(f"  元URL: {repr(url)}")
        
        # URL前処理
        cleaned_url = url.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        print(f"  処理後URL: {cleaned_url}")
        
        # ID抽出
        if '/spreadsheets/d/' in cleaned_url:
            sheet_id = cleaned_url.split('/spreadsheets/d/')[1].split('/')[0]
            sheet_id = sheet_id.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            print(f"  ✅ 抽出ID: {sheet_id}")
            
            # 正しいIDと比較
            correct_id = "1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg"
            if sheet_id == correct_id:
                print(f"  ✅ IDが正しい！")
            else:
                print(f"  ❌ IDが不正: 期待値={correct_id}")
        else:
            print(f"  ❌ スプレッドシートURLとして認識できません")
    
    # 実際のAPI呼び出しテスト
    print("\n🔍 実際のAPI呼び出しテスト:")
    try:
        client = SheetsClient()
        if client.authenticate():
            print("✅ 認証成功")
            
            # 正しいIDでテスト
            correct_id = "1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg"
            info = client.get_spreadsheet_info(correct_id)
            
            if info:
                print(f"✅ スプレッドシート情報取得成功: {info['title']}")
            else:
                print("❌ スプレッドシート情報取得失敗")
        else:
            print("❌ 認証失敗")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    test_url_parsing()