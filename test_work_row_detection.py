#!/usr/bin/env python3
"""
作業指示行検出テスト
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.sheets.sheets_client import SheetsClient

def test_work_row_detection():
    """作業指示行検出をテスト"""
    
    print("🔍 作業指示行検出テスト開始")
    print("=" * 60)
    
    try:
        # クライアント初期化
        client = SheetsClient()
        if not client.authenticate():
            print("❌ 認証失敗")
            return False
        
        sheet_id = '1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg'
        sheet_name = '1.原稿本文作成'
        
        # シートデータ読み取り
        range_name = f"{sheet_name}!A1:Z15"
        print(f"📊 範囲を読み取り中: {range_name}")
        
        sheet_data = client.read_range(sheet_id, range_name)
        
        if not sheet_data:
            print("❌ データが取得できませんでした")
            return False
        
        print(f"✅ データ取得成功: {len(sheet_data)}行")
        
        # 作業指示行を検索（修正版）
        print("\n🔍 作業指示行の検索（修正版）:")
        work_row = None
        
        for i in range(3, min(10, len(sheet_data))):  # 4-10行目を検索（0ベースなので3から）
            if len(sheet_data[i]) > 0:
                a_value = str(sheet_data[i][0]).strip()
                print(f"  行{i+1}: A列='{a_value}'")
                
                if '作業指示行' in a_value:
                    work_row = i
                    print(f"      ✅ 作業指示行発見！行番号: {i+1}")
                    break
        
        if work_row is not None:
            print(f"\n📍 作業指示行: {work_row + 1}行目")
            work_row_data = sheet_data[work_row]
            print(f"   内容: {work_row_data}")
            
            # コピー列を検索
            print("\n🔍 'コピー'列の検索:")
            copy_columns = []
            
            for j, cell in enumerate(work_row_data):
                if str(cell).strip() == 'コピー':
                    # 列位置情報を計算
                    process_col = j - 2  # 処理列
                    error_col = j - 1    # エラー列
                    paste_col = j + 1    # 貼り付け列
                    
                    if process_col >= 0:  # 境界チェック
                        column_info = {
                            'copy_col': j,
                            'copy_letter': chr(65 + j),
                            'process_col': process_col,
                            'process_letter': chr(65 + process_col),
                            'error_col': error_col,
                            'error_letter': chr(65 + error_col),
                            'paste_col': paste_col,
                            'paste_letter': chr(65 + paste_col)
                        }
                        copy_columns.append(column_info)
                        print(f"  ✅ 'コピー'発見: 行{work_row+1}, 列{chr(65+j)} ({j+1}列目)")
                        print(f"      処理列: {chr(65 + process_col)}, エラー列: {chr(65 + error_col)}, 貼り付け列: {chr(65 + paste_col)}")
            
            if copy_columns:
                print(f"\n🎉 検出完了: {len(copy_columns)}個のコピー列")
                for i, col_info in enumerate(copy_columns):
                    print(f"  列{i+1}: {col_info['copy_letter']}列 (処理:{col_info['process_letter']}, エラー:{col_info['error_letter']}, 貼付:{col_info['paste_letter']})")
                return True
            else:
                print("\n❌ コピー列が見つかりませんでした")
                return False
        else:
            print("\n❌ 作業指示行が見つかりませんでした")
            return False
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_work_row_detection()
    
    if success:
        print("\n✅ 作業指示行検出テスト成功")
        print("🚀 修正版GUIアプリで正常に動作するはずです")
    else:
        print("\n❌ 作業指示行検出テスト失敗")