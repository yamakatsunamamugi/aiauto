#!/usr/bin/env python3
"""
スプレッドシート構造デバッグスクリプト
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.sheets.sheets_client import SheetsClient

def debug_sheet_structure():
    """スプレッドシート構造をデバッグ"""
    
    print("🔍 スプレッドシート構造デバッグ開始")
    print("=" * 60)
    
    try:
        # クライアント初期化
        client = SheetsClient()
        if not client.authenticate():
            print("❌ 認証失敗")
            return
        
        sheet_id = '1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg'
        
        # 最初のシートの最初の15行を読み取り
        range_name = "A1:Z15"  # シート名なしで直接読み取り
        print(f"📊 範囲を読み取り中: {range_name}")
        
        data = client.read_range(sheet_id, range_name)
        
        if not data:
            print("❌ データが取得できませんでした")
            return
        
        print(f"✅ データ取得成功: {len(data)}行")
        print("\n📋 各行の内容:")
        
        for i, row in enumerate(data):
            # 空の要素も含めて最低5列分表示
            display_row = row + [''] * (5 - len(row)) if len(row) < 5 else row[:10]
            print(f"  行{i+1:2d}: {display_row}")
            
            # A列の内容を詳しく確認
            if len(row) > 0:
                a_value = str(row[0]).strip()
                if '作業' in a_value:
                    print(f"      ⭐ 作業関連行発見: '{a_value}'")
        
        print("\n🔍 作業指示行の検索:")
        work_row = None
        
        # 1行目から15行目まで検索
        for i in range(len(data)):
            if len(data[i]) > 0:
                a_value = str(data[i][0]).strip()
                print(f"  行{i+1}: A列='{a_value}'")
                
                if '作業指示行' in a_value:
                    work_row = i
                    print(f"      ✅ 作業指示行発見！行番号: {i+1}")
                    break
                elif '作業' in a_value:
                    print(f"      🔍 '作業'を含む行: {i+1}")
        
        if work_row is not None:
            print(f"\n📍 作業指示行: {work_row + 1}行目")
            print(f"   内容: {data[work_row]}")
        else:
            print("\n❌ 作業指示行が見つかりませんでした")
            
        # より広い範囲でも検索
        print("\n🔍 'コピー'列の検索:")
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                if str(cell).strip() == 'コピー':
                    print(f"  'コピー'発見: 行{i+1}, 列{chr(65+j)} ({j+1}列目)")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sheet_structure()