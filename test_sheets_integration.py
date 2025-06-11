#!/usr/bin/env python3
"""
Google Sheets統合機能テストスクリプト
認証、シート読み取り、データ解析の総合テスト
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.sheets.auth_manager import AuthManager
from src.sheets.sheets_client import SheetsClient
from src.sheets.data_handler import DataHandler
from src.utils.logger import logger


def test_authentication():
    """認証テスト"""
    print("=" * 60)
    print("🔐 Google Sheets API認証テスト")
    print("=" * 60)
    
    try:
        auth_manager = AuthManager()
        
        # 認証状態確認
        status = auth_manager.get_auth_status()
        print(f"認証ファイル存在: {status['credentials_file_exists']}")
        print(f"トークンファイル存在: {status['token_file_exists']}")
        
        # 認証実行
        print("\n認証を実行中...")
        success = auth_manager.authenticate()
        
        if success:
            print("✅ 認証成功")
            
            # 接続テスト
            print("接続テストを実行中...")
            connection_ok = auth_manager.test_connection()
            
            if connection_ok:
                print("✅ Google Sheets API接続成功")
                return True
            else:
                print("❌ Google Sheets API接続失敗")
                return False
        else:
            print("❌ 認証失敗")
            print("\n📋 認証設定手順:")
            print("1. Google Cloud Consoleでプロジェクトを作成")
            print("2. Google Sheets APIを有効化")
            print("3. 認証情報（OAuth2またはサービスアカウント）を作成")
            print("4. 認証ファイルを config/credentials.json に保存")
            return False
            
    except Exception as e:
        print(f"❌ 認証テストエラー: {e}")
        return False


def test_sheets_client():
    """SheetsClientテスト"""
    print("\n" + "=" * 60)
    print("📊 Sheets APIクライアントテスト")
    print("=" * 60)
    
    try:
        client = SheetsClient()
        
        # 認証
        print("認証中...")
        if not client.authenticate():
            print("❌ 認証に失敗しました")
            return False
        
        print("✅ Sheets APIクライアント認証成功")
        
        # URL解析テスト
        test_urls = [
            "https://docs.google.com/spreadsheets/d/1abc123def456/edit#gid=0",
            "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit",
            "invalid_url"
        ]
        
        print("\nURL解析テスト:")
        for url in test_urls:
            spreadsheet_id = client.extract_spreadsheet_id(url)
            status = "✅" if spreadsheet_id else "❌"
            print(f"{status} {url} → {spreadsheet_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ SheetsClientテストエラー: {e}")
        return False


def test_data_handler():
    """DataHandlerテスト"""
    print("\n" + "=" * 60)
    print("🔍 データハンドラーテスト")
    print("=" * 60)
    
    try:
        data_handler = DataHandler()
        
        # 認証
        print("認証中...")
        if not data_handler.authenticate():
            print("❌ データハンドラー認証に失敗しました")
            return False
        
        print("✅ データハンドラー認証成功")
        
        # 状態確認
        status = data_handler.get_data_handler_status()
        print(f"データハンドラー状態: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ データハンドラーテストエラー: {e}")
        return False


def test_sheet_parsing_demo():
    """シート解析デモテスト"""
    print("\n" + "=" * 60)
    print("📋 シート解析デモテスト")
    print("=" * 60)
    
    # 実際のスプレッドシートURLでテスト（ユーザー入力）
    test_url = input("テスト用スプレッドシートURLを入力してください（空白でスキップ）: ").strip()
    
    if not test_url:
        print("⚠️  URLが入力されていないため、シート解析テストをスキップします")
        return True
    
    try:
        data_handler = DataHandler()
        
        # 認証
        if not data_handler.authenticate():
            print("❌ 認証に失敗しました")
            return False
        
        # シート一覧取得
        print("シート一覧を取得中...")
        sheets = data_handler.get_available_sheets(test_url)
        
        if sheets:
            print(f"✅ 利用可能シート数: {len(sheets)}")
            for i, sheet in enumerate(sheets):
                print(f"  {i+1}. {sheet['title']} ({sheet['rowCount']}行 x {sheet['columnCount']}列)")
            
            # 最初のシートで解析テスト
            sheet_name = sheets[0]['title']
            print(f"\n'{sheet_name}'シートの構造解析中...")
            
            structure = data_handler.load_sheet_from_url(test_url, sheet_name)
            
            if structure:
                print("✅ シート構造解析成功")
                print(f"  - 作業ヘッダー行: {structure.work_header_row}")
                print(f"  - データ開始行: {structure.data_start_row}")
                print(f"  - コピー列数: {len(structure.copy_columns)}")
                
                # タスク行作成テスト
                print("\nタスク行作成中...")
                task_rows = data_handler.create_task_rows()
                print(f"✅ タスク行作成完了: {len(task_rows)}件")
                
                # 最初の3件を表示
                for i, task in enumerate(task_rows[:3]):
                    print(f"  タスク{i+1}: 行{task.row_number} - {task.copy_text[:50]}...")
                
                return True
            else:
                print("❌ シート構造解析に失敗しました")
                return False
        else:
            print("❌ シート一覧の取得に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ シート解析デモエラー: {e}")
        return False


def run_comprehensive_test():
    """総合テスト実行"""
    print("🚀 Google Sheets統合機能総合テスト開始")
    print("実行日時:", "2025-06-12 00:00")
    
    test_results = {}
    
    # テスト1: 認証
    test_results["認証"] = test_authentication()
    
    # テスト2: SheetsClient
    if test_results["認証"]:
        test_results["SheetsClient"] = test_sheets_client()
    else:
        test_results["SheetsClient"] = False
        print("⚠️  認証に失敗したため、SheetsClientテストをスキップ")
    
    # テスト3: DataHandler
    if test_results["認証"]:
        test_results["DataHandler"] = test_data_handler()
    else:
        test_results["DataHandler"] = False
        print("⚠️  認証に失敗したため、DataHandlerテストをスキップ")
    
    # テスト4: シート解析デモ
    if test_results["認証"]:
        test_results["シート解析"] = test_sheet_parsing_demo()
    else:
        test_results["シート解析"] = False
        print("⚠️  認証に失敗したため、シート解析テストをスキップ")
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in test_results.items():
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name:<20}: {status}")
        if result:
            success_count += 1
    
    success_rate = success_count / len(test_results) * 100
    print(f"\n成功率: {success_count}/{len(test_results)} ({success_rate:.1f}%)")
    
    if success_count == len(test_results):
        print("\n🎉 全てのテストが成功しました！")
        print("Google Sheets統合機能は正常に動作しています。")
    elif success_count > 0:
        print("\n⚠️  一部のテストが失敗しました")
        print("認証設定を確認してください。")
    else:
        print("\n❌ 全てのテストが失敗しました")
        print("Google Sheets API認証の設定が必要です。")
    
    return success_count == len(test_results)


if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 テストが中断されました")
        exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        exit(1)