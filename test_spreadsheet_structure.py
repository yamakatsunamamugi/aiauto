#!/usr/bin/env python3
"""
スプレッドシート構造確認テスト
列数修正が正しく行われたかを確認
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.sheets.sheets_client import SheetsClient
from src.sheets.sheet_parser import SheetParser
from src.utils.logger import logger

def test_spreadsheet_structure():
    """スプレッドシート構造の確認テスト"""
    
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg/edit?gid=1633283608#gid=1633283608"
    sheet_name = "1.原稿本文作成"
    
    print("=" * 60)
    print("🔍 スプレッドシート構造確認テスト")
    print("=" * 60)
    
    try:
        # SheetsClientを初期化
        print("📊 Google Sheets API接続中...")
        sheets_client = SheetsClient()
        
        # 認証実行
        print("🔐 Google Sheets API認証中...")
        auth_success = sheets_client.authenticate()
        if not auth_success:
            print("❌ Google Sheets API認証に失敗しました")
            return False
        print("✅ Google Sheets API認証成功")
        
        # スプレッドシートIDを抽出
        spreadsheet_id = sheets_client.extract_spreadsheet_id(spreadsheet_url)
        print(f"✅ スプレッドシートID: {spreadsheet_id}")
        
        # シート情報を取得
        print(f"📋 シート '{sheet_name}' の情報を取得中...")
        sheet_info = sheets_client.get_spreadsheet_info(spreadsheet_id)
        print(f"✅ スプレッドシート名: {sheet_info.get('properties', {}).get('title', 'N/A')}")
        
        # SheetParserでシート構造を解析
        print("🔍 シート構造を解析中...")
        parser = SheetParser(sheets_client)
        structure = parser.parse_sheet_structure(spreadsheet_id, sheet_name)
        
        if structure:
            print("\n" + "=" * 40)
            print("📈 シート構造解析結果")
            print("=" * 40)
            print(f"🏷️  シート名: {structure.sheet_name}")
            print(f"📏  総列数: {structure.total_columns}")
            print(f"📐  総行数: {structure.total_rows}")
            print(f"🎯  作業ヘッダー行: {structure.work_header_row}")
            print(f"🚀  データ開始行: {structure.data_start_row}")
            print(f"📋  コピー列数: {len(structure.copy_columns)}")
            
            print("\n📋 コピー列詳細:")
            for i, copy_col in enumerate(structure.copy_columns):
                print(f"   コピー列 {i+1}: {copy_col.column_letter}列 (インデックス:{copy_col.column_index})")
                print(f"      - 処理列: {copy_col.process_column + 1}")
                print(f"      - エラー列: {copy_col.error_column + 1}")
                print(f"      - 結果列: {copy_col.result_column + 1}")
                
                # 結果列が範囲内かチェック
                if copy_col.result_column >= structure.total_columns:
                    print(f"      ❌ 結果列が範囲外! (列{copy_col.result_column + 1} > 最大列数{structure.total_columns})")
                else:
                    print(f"      ✅ 結果列は範囲内")
                print()
            
            # 成功判定
            all_in_range = all(
                copy_col.result_column < structure.total_columns 
                for copy_col in structure.copy_columns
            )
            
            print("=" * 40)
            if all_in_range:
                print("🎉 ✅ 列数修正成功！すべての結果列が範囲内です")
                print("🚀 ChatGPT自動化の準備完了!")
            else:
                print("⚠️ ❌ まだ列数不足です。さらに列を追加してください")
            print("=" * 40)
            
            return all_in_range
            
        else:
            print("❌ シート構造の解析に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_spreadsheet_structure()
    if success:
        print("\n🎯 次のステップ: python gui_app.py でChatGPT自動化を実行してください！")
    else:
        print("\n🔧 スプレッドシートに列を追加してから再実行してください")