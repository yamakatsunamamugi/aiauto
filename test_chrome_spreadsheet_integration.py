#!/usr/bin/env python3
"""
Chrome拡張機能 + スプレッドシート統合テスト
GUI不要の統合テストスクリプト
"""

import sys
import time
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge import ExtensionBridge
from src.sheets.sheets_client import SheetsClient

def test_chrome_spreadsheet_integration():
    """Chrome拡張機能とスプレッドシート統合テスト"""
    
    print("🚀 Chrome拡張機能 + スプレッドシート統合テスト開始")
    print("=" * 60)
    
    # 1. ExtensionBridge初期化
    print("\n🔧 ExtensionBridge初期化中...")
    bridge = ExtensionBridge()
    print("✅ ExtensionBridge初期化完了")
    
    # 2. Chrome拡張機能状態確認
    print("\n🔌 Chrome拡張機能状態確認...")
    status = bridge.check_extension_status()
    print(f"📍 状態: {status['status']}")
    print(f"📝 詳細: {status['message']}")
    
    if status['status'] == 'missing':
        print("\n❌ Chrome拡張機能がインストールされていません")
        print("📋 インストール手順:")
        print("1. chrome://extensions/ を開く")
        print("2. 開発者モードをON")
        print("3. '読み込み'で以下フォルダを選択:")
        print(f"   {project_root}/chrome-extension")
        return False
    
    # 3. スプレッドシートAPI初期化
    print("\n📊 SheetsClient初期化中...")
    try:
        sheets_api = SheetsClient()
        print("✅ SheetsClient初期化完了")
    except Exception as e:
        print(f"❌ SheetsClient初期化失敗: {e}")
        print("💡 認証ファイルを確認してください")
        return False
    
    # 4. デモデータでテスト実行
    print("\n🔄 デモデータでテストを実行します...")
    return test_with_demo_data(bridge)
    
    # 5. 実際のスプレッドシートでテスト
    try:
        print(f"\n🎯 スプレッドシート接続テスト: {spreadsheet_url}")
        
        # URLからスプレッドシートIDを抽出
        if '/spreadsheets/d/' in spreadsheet_url:
            sheet_id = spreadsheet_url.split('/spreadsheets/d/')[1].split('/')[0]
        else:
            print("❌ 無効なスプレッドシートURLです")
            return False
        
        # シート情報取得
        spreadsheet_info = sheets_api.get_spreadsheet_info(sheet_id)
        if not spreadsheet_info:
            print("❌ スプレッドシート情報取得失敗")
            return False
        
        sheet_names = [sheet['properties']['title'] for sheet in spreadsheet_info['sheets']]
        print(f"📋 利用可能なシート: {sheet_names}")
        
        if not sheet_names:
            print("❌ シートが見つかりません")
            return False
        
        # 最初のシートでテスト
        sheet_name = sheet_names[0]
        print(f"🎯 テスト対象シート: {sheet_name}")
        
        # 統合テスト実行
        return run_integration_test(bridge, sheets_api, sheet_id, sheet_name)
        
    except Exception as e:
        print(f"❌ スプレッドシート統合テスト失敗: {e}")
        return False

def test_with_demo_data(bridge):
    """デモデータでのテスト"""
    
    print("\n🧪 デモデータでのAI処理テスト")
    print("-" * 40)
    
    # デモテストプロンプト
    test_prompts = [
        "こんにちは！簡単に挨拶してください。",
        "1+1の答えを教えてください。",
        "今日は良い天気ですか？短く答えてください。"
    ]
    
    results = []
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 テスト {i}/{len(test_prompts)}: {prompt}")
        
        try:
            # Chrome拡張機能でAI処理
            start_time = time.time()
            result = bridge.process_with_extension(
                text=prompt,
                ai_service="chatgpt",
                model=None
            )
            processing_time = time.time() - start_time
            
            if result['success']:
                print(f"✅ 処理成功 ({processing_time:.2f}秒)")
                print(f"🤖 応答: {result['result'][:100]}{'...' if len(result['result']) > 100 else ''}")
                results.append({
                    'prompt': prompt,
                    'response': result['result'],
                    'processing_time': processing_time,
                    'success': True
                })
            else:
                print(f"❌ 処理失敗: {result['error']}")
                results.append({
                    'prompt': prompt,
                    'error': result['error'],
                    'success': False
                })
                
        except Exception as e:
            print(f"❌ エラー発生: {e}")
            results.append({
                'prompt': prompt,
                'error': str(e),
                'success': False
            })
    
    # 結果サマリー
    print(f"\n📊 テスト結果サマリー:")
    successful = sum(1 for r in results if r['success'])
    print(f"  成功: {successful}/{len(results)}")
    print(f"  成功率: {successful/len(results)*100:.1f}%")
    
    if successful > 0:
        avg_time = sum(r.get('processing_time', 0) for r in results if r['success']) / successful
        print(f"  平均処理時間: {avg_time:.2f}秒")
    
    return successful > 0

def run_integration_test(bridge, sheets_api, sheet_id, sheet_name):
    """実際の統合テスト実行"""
    
    print(f"\n🎯 統合テスト実行: {sheet_name}")
    print("-" * 40)
    
    try:
        # シートデータ読み取り
        print("📖 シートデータ読み取り中...")
        data = sheets_api.read_range(sheet_id, f"{sheet_name}!A1:Z100")
        
        if not data:
            print("❌ シートデータが空です")
            return False
        
        print(f"📋 読み取り完了: {len(data)}行")
        
        # 5行目の作業指示行を検索
        work_row = None
        for i, row in enumerate(data):
            if len(row) > 0 and '作業' in str(row[0]):
                work_row = i
                break
        
        if work_row is None:
            print("❌ 作業指示行（A列に'作業'）が見つかりません")
            return False
        
        print(f"✅ 作業指示行発見: {work_row + 1}行目")
        print(f"📝 ヘッダー: {data[work_row]}")
        
        # コピー列を検索
        copy_columns = []
        for j, cell in enumerate(data[work_row]):
            if str(cell).strip() == 'コピー':
                copy_columns.append(j)
        
        if not copy_columns:
            print("❌ 'コピー'列が見つかりません")
            return False
        
        print(f"✅ コピー列発見: {[chr(65 + col) for col in copy_columns]}列")
        
        # 最初のコピー列でテスト処理
        test_copy_col = copy_columns[0]
        process_col = test_copy_col - 2  # 処理列
        paste_col = test_copy_col + 1    # 貼り付け列
        
        if process_col < 0:
            print("❌ 処理列の位置が不正です")
            return False
        
        print(f"🎯 テスト列設定:")
        print(f"  コピー列: {chr(65 + test_copy_col)}")
        print(f"  処理列: {chr(65 + process_col)}")
        print(f"  貼り付け列: {chr(65 + paste_col)}")
        
        # 処理対象行を検索（A列が1から開始）
        target_rows = []
        for i in range(work_row + 1, len(data)):
            if len(data[i]) > 0 and str(data[i][0]).strip() == '1':
                target_rows.append(i)
                break  # 最初の1行のみテスト
        
        if not target_rows:
            print("❌ 処理対象行（A列が1）が見つかりません")
            return False
        
        # テスト処理実行
        for row_idx in target_rows:
            print(f"\n📝 行 {row_idx + 1} を処理中...")
            
            # コピー列のテキスト取得
            if len(data[row_idx]) <= test_copy_col:
                print("❌ コピー列にデータがありません")
                continue
            
            copy_text = str(data[row_idx][test_copy_col]).strip()
            if not copy_text:
                print("❌ コピーテキストが空です")
                continue
            
            print(f"📄 コピーテキスト: {copy_text[:50]}{'...' if len(copy_text) > 50 else ''}")
            
            # Chrome拡張機能でAI処理
            try:
                result = bridge.process_with_extension(
                    text=copy_text,
                    ai_service="chatgpt",
                    model=None
                )
                
                if result['success']:
                    print("✅ AI処理成功")
                    response_text = result['result']
                    
                    # スプレッドシートに結果を書き戻し
                    cell_range = f"{sheet_name}!{chr(65 + paste_col)}{row_idx + 1}"
                    sheets_api.write_range(sheet_id, cell_range, [[response_text]])
                    
                    # 処理列に完了マーク
                    process_range = f"{sheet_name}!{chr(65 + process_col)}{row_idx + 1}"
                    sheets_api.write_range(sheet_id, process_range, [["処理済み"]])
                    
                    print(f"✅ スプレッドシートに書き込み完了")
                    print(f"📝 応答: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
                    
                    return True
                    
                else:
                    print(f"❌ AI処理失敗: {result['error']}")
                    return False
                    
            except Exception as e:
                print(f"❌ 統合処理エラー: {e}")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ 統合テスト失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("🎮 Chrome拡張機能 + スプレッドシート統合テスト")
    print("このスクリプトでChrome拡張機能とスプレッドシートの統合動作を確認できます")
    
    try:
        success = test_chrome_spreadsheet_integration()
        if success:
            print("\n🎉 統合テスト完了！システムは正常に動作しています。")
        else:
            print("\n⚠️ 統合テストで問題が発生しました。設定を確認してください。")
    except KeyboardInterrupt:
        print("\n\n⏹️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")

if __name__ == "__main__":
    main()