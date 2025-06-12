#!/usr/bin/env python3
"""
完全自動化実行スクリプト
GUI不要でスプレッドシート→AI→スプレッドシートの完全自動化
"""

import sys
import time
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge import ExtensionBridge
from src.sheets.sheets_client import SheetsClient

def run_full_automation():
    """完全自動化実行"""
    
    print("🚀 AI自動化システム 完全自動実行")
    print("=" * 50)
    
    # 1. 初期化
    print("\n🔧 システム初期化...")
    bridge = ExtensionBridge()
    sheets_client = SheetsClient()
    
    # 2. 設定入力
    print("\n📝 設定入力:")
    spreadsheet_url = input("スプレッドシートURL: ").strip()
    
    if not spreadsheet_url:
        print("❌ スプレッドシートURLが必要です")
        return False
    
    # URLからID抽出
    if '/spreadsheets/d/' in spreadsheet_url:
        sheet_id = spreadsheet_url.split('/spreadsheets/d/')[1].split('/')[0]
    else:
        print("❌ 無効なURL")
        return False
    
    # シート一覧取得
    spreadsheet_info = sheets_client.get_spreadsheet_info(sheet_id)
    sheet_names = [sheet['properties']['title'] for sheet in spreadsheet_info['sheets']]
    
    print(f"📋 利用可能シート: {sheet_names}")
    sheet_name = input(f"シート名 [{sheet_names[0]}]: ").strip() or sheet_names[0]
    
    # AI設定
    ai_services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
    print(f"🤖 対応AI: {ai_services}")
    ai_service = input(f"使用AI [{ai_services[0]}]: ").strip() or ai_services[0]
    
    if ai_service not in ai_services:
        ai_service = ai_services[0]
    
    # 3. スプレッドシート解析
    print(f"\n📊 スプレッドシート解析: {sheet_name}")
    data = sheets_client.read_range(sheet_id, f"{sheet_name}!A1:Z100")
    
    if not data:
        print("❌ データが見つかりません")
        return False
    
    # 作業指示行検索
    work_row = None
    for i, row in enumerate(data):
        if len(row) > 0 and '作業' in str(row[0]):
            work_row = i
            break
    
    if work_row is None:
        print("❌ 作業指示行が見つかりません")
        return False
    
    print(f"✅ 作業指示行: {work_row + 1}行目")
    
    # コピー列検索
    copy_columns = []
    for j, cell in enumerate(data[work_row]):
        if str(cell).strip() == 'コピー':
            copy_columns.append(j)
    
    if not copy_columns:
        print("❌ コピー列が見つかりません")
        return False
    
    print(f"✅ コピー列: {[chr(65 + col) for col in copy_columns]}")
    
    # 4. 自動処理実行
    print("\n🤖 AI自動処理開始...")
    
    total_processed = 0
    total_success = 0
    
    for copy_col in copy_columns:
        process_col = copy_col - 2  # 処理列
        paste_col = copy_col + 1    # 貼り付け列
        error_col = copy_col - 1    # エラー列
        
        if process_col < 0:
            continue
        
        print(f"\n📝 列 {chr(65 + copy_col)} を処理中...")
        
        # 処理対象行検索
        row_idx = work_row + 1
        while row_idx < len(data):
            # A列チェック
            if len(data[row_idx]) == 0 or not str(data[row_idx][0]).strip():
                break
            
            if not str(data[row_idx][0]).strip().isdigit():
                row_idx += 1
                continue
            
            # 処理列チェック
            if (len(data[row_idx]) > process_col and 
                str(data[row_idx][process_col]).strip() == '処理済み'):
                row_idx += 1
                continue
            
            # コピー列のテキスト取得
            if len(data[row_idx]) <= copy_col:
                row_idx += 1
                continue
            
            copy_text = str(data[row_idx][copy_col]).strip()
            if not copy_text:
                row_idx += 1
                continue
            
            print(f"  行 {row_idx + 1}: {copy_text[:30]}...")
            total_processed += 1
            
            try:
                # AI処理実行
                result = bridge.process_with_extension(
                    text=copy_text,
                    ai_service=ai_service,
                    model=None
                )
                
                if result['success']:
                    response_text = result['result']
                    
                    # 結果書き込み
                    paste_range = f"{sheet_name}!{chr(65 + paste_col)}{row_idx + 1}"
                    sheets_client.write_range(sheet_id, paste_range, [[response_text]])
                    
                    # 処理完了マーク
                    process_range = f"{sheet_name}!{chr(65 + process_col)}{row_idx + 1}"
                    sheets_client.write_range(sheet_id, process_range, [["処理済み"]])
                    
                    total_success += 1
                    print(f"    ✅ 成功")
                    
                else:
                    # エラー記録
                    error_range = f"{sheet_name}!{chr(65 + error_col)}{row_idx + 1}"
                    sheets_client.write_range(sheet_id, error_range, [[result['error']]])
                    print(f"    ❌ 失敗: {result['error']}")
                
            except Exception as e:
                # エラー記録
                error_range = f"{sheet_name}!{chr(65 + error_col)}{row_idx + 1}"
                sheets_client.write_range(sheet_id, error_range, [[str(e)]])
                print(f"    ❌ エラー: {e}")
            
            row_idx += 1
            time.sleep(2)  # レート制限対策
    
    # 5. 結果表示
    print(f"\n📊 処理完了")
    print(f"  総処理数: {total_processed}")
    print(f"  成功数: {total_success}")
    print(f"  成功率: {total_success/total_processed*100:.1f}%" if total_processed > 0 else "  成功率: 0%")
    
    return total_success > 0

if __name__ == "__main__":
    try:
        success = run_full_automation()
        print(f"\n{'🎉 自動化完了!' if success else '❌ 自動化失敗'}")
    except KeyboardInterrupt:
        print("\n⏹️ 自動化中断")
    except Exception as e:
        print(f"\n❌ エラー: {e}")