#!/usr/bin/env python3
"""
Google Sheets連携モジュールの統合テスト

実際のGoogle Sheetsを使用して、認証からデータ処理まで
一連の機能をテストするスクリプト
"""

import sys
import os
import logging
import json
from pathlib import Path
from datetime import datetime

# パッケージのパスを追加
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.sheets import (
        create_complete_handler,
        SheetConfig,
        TaskStatus,
        AIService,
        validate_environment,
        extract_spreadsheet_id_from_url,
        AuthenticationError,
        SheetsAPIError,
        DataProcessingError
    )
except ImportError as e:
    print(f"❌ パッケージのインポートに失敗しました: {e}")
    print("requirements.txtに記載されたパッケージがインストールされているか確認してください")
    sys.exit(1)


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/integration_test.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)


def test_environment():
    """環境設定のテスト"""
    print("🔍 環境設定をテスト中...")
    
    is_valid, errors = validate_environment()
    
    if is_valid:
        print("✅ 環境設定は正常です")
        return True
    else:
        print("❌ 環境設定にエラーがあります:")
        for error in errors:
            print(f"  - {error}")
        return False


def test_authentication():
    """認証機能のテスト"""
    print("🔐 認証機能をテスト中...")
    
    try:
        sheets_client, data_handler = create_complete_handler()
        print("✅ 認証が成功しました")
        
        # サービスアカウント情報を表示
        auth_manager = sheets_client.auth_manager
        print(f"  サービスアカウント: {auth_manager.get_service_account_email()}")
        
        return sheets_client, data_handler
        
    except AuthenticationError as e:
        print(f"❌ 認証に失敗しました: {e}")
        return None, None
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return None, None


def test_spreadsheet_access(sheets_client, test_spreadsheet_id):
    """スプレッドシートアクセステスト"""
    print(f"📊 スプレッドシートアクセスをテスト中... ID: {test_spreadsheet_id}")
    
    try:
        # アクセス権限確認
        if not sheets_client.auth_manager.validate_spreadsheet_access(test_spreadsheet_id):
            print("❌ スプレッドシートへのアクセス権限がありません")
            print(f"   サービスアカウント {sheets_client.auth_manager.get_service_account_email()} を")
            print("   スプレッドシートの編集者として追加してください")
            return False
        
        # シート名一覧を取得
        sheet_names = sheets_client.get_sheet_names(test_spreadsheet_id)
        print(f"✅ スプレッドシートアクセス成功")
        print(f"  シート一覧: {sheet_names}")
        
        return sheet_names
        
    except SheetsAPIError as e:
        print(f"❌ スプレッドシートアクセスエラー: {e}")
        return None
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return None


def test_data_structure_validation(data_handler, config):
    """データ構造検証のテスト"""
    print("🔍 データ構造検証をテスト中...")
    
    try:
        is_valid, errors = data_handler.validate_sheet_configuration(config)
        
        if is_valid:
            print("✅ データ構造検証成功")
            return True
        else:
            print("❌ データ構造検証エラー:")
            for error in errors:
                print(f"  - {error}")
            return False
            
    except DataProcessingError as e:
        print(f"❌ データ構造検証エラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False


def test_task_generation(data_handler, config):
    """タスク生成のテスト"""
    print("📋 タスク生成をテスト中...")
    
    try:
        # 未処理タスクを取得
        pending_tasks = data_handler.get_pending_tasks(config)
        
        print(f"✅ タスク生成成功: {len(pending_tasks)}個のタスクを検出")
        
        if pending_tasks:
            print("  最初の3タスク:")
            for i, task in enumerate(pending_tasks[:3]):
                print(f"    タスク{i+1}: 行{task.row_number}, "
                      f"列{task.column_positions.copy_column}, "
                      f"AI={task.ai_service.value}")
                print(f"      テキスト: '{task.copy_text[:100]}...'")
        
        return pending_tasks
        
    except DataProcessingError as e:
        print(f"❌ タスク生成エラー: {e}")
        return None
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return None


def test_sheet_writing(sheets_client, config, test_message="テスト実行"):
    """シート書き込みのテスト"""
    print("✏️  シート書き込みをテスト中...")
    
    try:
        # テストメッセージを適当なセルに書き込み
        test_row = 1
        test_col = 26  # Z列
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_value = f"{test_message} - {timestamp}"
        
        sheets_client.write_cell(
            config.spreadsheet_id, 
            config.sheet_name, 
            test_row, 
            test_col, 
            test_value
        )
        
        print(f"✅ シート書き込み成功: Z{test_row}セルに '{test_value}' を書き込み")
        return True
        
    except SheetsAPIError as e:
        print(f"❌ シート書き込みエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False


def display_summary(test_results):
    """テスト結果のサマリー表示"""
    print("\n" + "="*60)
    print("📋 テスト結果サマリー")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 結果: {passed_tests}/{total_tests} テスト合格")
    
    if passed_tests == total_tests:
        print("🎉 すべてのテストが合格しました！")
        print("   Google Sheets連携モジュールは正常に動作しています。")
    else:
        print("⚠️  一部のテストが失敗しました。")
        print("   エラー内容を確認して問題を修正してください。")
    
    return passed_tests == total_tests


def main():
    """メイン関数"""
    print("🚀 Google Sheets連携モジュール 統合テスト開始")
    print("="*60)
    
    # ログ設定
    logger = setup_logging()
    logger.info("統合テスト開始")
    
    # テスト結果を記録
    test_results = {}
    
    # テスト設定
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python test_sheets_integration.py <spreadsheet_url> <sheet_name>")
        print("\n例:")
        print("  python test_sheets_integration.py 'https://docs.google.com/spreadsheets/d/1abc.../edit' 'Sheet1'")
        sys.exit(1)
    
    spreadsheet_url = sys.argv[1]
    sheet_name = sys.argv[2]
    
    try:
        spreadsheet_id = extract_spreadsheet_id_from_url(spreadsheet_url)
    except ValueError as e:
        print(f"❌ 無効なスプレッドシートURL: {e}")
        sys.exit(1)
    
    print(f"📋 テスト対象:")
    print(f"  スプレッドシートID: {spreadsheet_id}")
    print(f"  シート名: {sheet_name}")
    print()
    
    # 1. 環境設定テスト
    test_results["環境設定"] = test_environment()
    if not test_results["環境設定"]:
        print("❌ 環境設定エラーのため、テストを中止します")
        sys.exit(1)
    
    print()
    
    # 2. 認証テスト
    sheets_client, data_handler = test_authentication()
    test_results["認証"] = sheets_client is not None and data_handler is not None
    
    if not test_results["認証"]:
        print("❌ 認証エラーのため、テストを中止します")
        print("\n🔧 認証設定手順:")
        print("1. Google Cloud Console でプロジェクトを作成")
        print("2. Google Sheets API を有効化")
        print("3. サービスアカウントを作成")
        print("4. 認証JSONファイルを config/credentials.json に保存")
        print("5. スプレッドシートにサービスアカウントを編集者として追加")
        sys.exit(1)
    
    print()
    
    # 3. スプレッドシートアクセステスト
    sheet_names = test_spreadsheet_access(sheets_client, spreadsheet_id)
    test_results["スプレッドシートアクセス"] = sheet_names is not None
    
    if not test_results["スプレッドシートアクセス"]:
        print("❌ スプレッドシートアクセスエラーのため、以降のテストをスキップします")
        display_summary(test_results)
        sys.exit(1)
    
    # シート名確認
    if sheet_name not in sheet_names:
        print(f"❌ 指定されたシート '{sheet_name}' が見つかりません")
        print(f"   利用可能なシート: {sheet_names}")
        test_results["スプレッドシートアクセス"] = False
        display_summary(test_results)
        sys.exit(1)
    
    print()
    
    # 設定作成
    config = SheetConfig(
        spreadsheet_url=spreadsheet_url,
        sheet_name=sheet_name,
        spreadsheet_id=spreadsheet_id
    )
    
    # 4. データ構造検証テスト
    test_results["データ構造検証"] = test_data_structure_validation(data_handler, config)
    print()
    
    # 5. タスク生成テスト
    pending_tasks = test_task_generation(data_handler, config)
    test_results["タスク生成"] = pending_tasks is not None
    print()
    
    # 6. シート書き込みテスト
    test_results["シート書き込み"] = test_sheet_writing(sheets_client, config)
    print()
    
    # 結果サマリー表示
    all_passed = display_summary(test_results)
    
    if all_passed:
        logger.info("統合テスト完了: すべて合格")
        print("\n🎯 次のステップ:")
        print("1. 他担当者（GUI、Automation）との統合")
        print("2. 実際のAI処理フローのテスト")
        print("3. エラーハンドリングの確認")
    else:
        logger.error("統合テスト完了: 一部失敗")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)