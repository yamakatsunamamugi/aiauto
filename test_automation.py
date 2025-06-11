#!/usr/bin/env python3
"""
自動化モジュール基本テスト

実装したAutomation機能の動作確認テスト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.automation.browser_manager import BrowserManager
from src.automation.automation_controller import AutomationController
from src.automation.automation_controller import TaskRow as AutoTaskRow
from src.automation.ai_handlers.chatgpt_handler import ChatGPTHandler
from src.utils.logger import logger


async def test_browser_manager():
    """BrowserManagerのテスト"""
    print("\n=== BrowserManager テスト ===")
    
    try:
        async with BrowserManager() as browser_manager:
            print("✓ ブラウザ起動成功")
            
            # 新しいページ作成
            page = await browser_manager.create_new_page()
            print("✓ ページ作成成功")
            
            # テストサイトにアクセス
            await page.goto("https://www.google.com")
            title = await page.title()
            print(f"✓ ページアクセス成功: {title}")
            
            # スクリーンショット撮影
            screenshot_success = await browser_manager.take_screenshot(page, "logs/test_screenshot.png")
            if screenshot_success:
                print("✓ スクリーンショット撮影成功")
            
        print("✓ ブラウザ終了成功")
        return True
        
    except Exception as e:
        print(f"✗ BrowserManagerテストでエラー: {e}")
        return False


async def test_chatgpt_handler():
    """ChatGPTHandlerのテスト（ログイン状態確認のみ）"""
    print("\n=== ChatGPTHandler テスト ===")
    
    try:
        async with BrowserManager() as browser_manager:
            page = await browser_manager.create_new_page()
            
            # ChatGPTハンドラー初期化
            handler = ChatGPTHandler(page)
            print("✓ ChatGPTハンドラー初期化成功")
            
            # ログイン状態確認
            is_logged_in = await handler.login_check()
            if is_logged_in:
                print("✓ ChatGPTにログイン済み")
                
                # 利用可能モデルの取得テスト
                models = await handler.get_available_models()
                print(f"✓ 利用可能モデル: {models}")
                
            else:
                print("⚠ ChatGPTにログインしていません（手動ログインが必要）")
            
        return True
        
    except Exception as e:
        print(f"✗ ChatGPTHandlerテストでエラー: {e}")
        return False


async def test_automation_controller():
    """AutomationControllerのテスト"""
    print("\n=== AutomationController テスト ===")
    
    try:
        # AutomationControllerは他のモジュールとの依存関係があるため、基本的な初期化のみテスト
        print("⚠ AutomationControllerは他のモジュール(Sheets)との統合後にフルテスト予定")
        
        async with AutomationController() as controller:
            print("✓ AutomationController初期化成功")
            
            # 利用可能AIの確認
            available_ais = controller.get_available_ais()
            print(f"✓ 利用可能AI: {list(available_ais.keys())}")
            
            # AIハンドラーセットアップ（ChatGPTのみ）
            setup_results = await controller.setup_ai_handlers(['chatgpt'])
            print(f"✓ AIハンドラーセットアップ結果: {setup_results}")
            
            # ログイン状態確認
            login_status = await controller.check_ai_login_status(['chatgpt'])
            print(f"✓ ログイン状態: {login_status}")
            
            # 実際の処理は手動ログインが必要なため、ここではセットアップのみテスト
            if login_status.get('chatgpt', False):
                print("⚠ 実際のタスク処理はスキップ（デモ実行は手動で行ってください）")
            else:
                print("⚠ ChatGPTにログインしていないため、処理テストをスキップ")
        
        return True
        
    except Exception as e:
        print(f"✗ AutomationControllerテストでエラー: {e}")
        return False


async def test_session_manager():
    """SessionManagerのテスト"""
    print("\n=== SessionManager テスト ===")
    
    try:
        from src.automation.session_manager import SessionManager
        
        session_manager = SessionManager()
        print("✓ SessionManager初期化成功")
        
        # セッション概要取得
        summary = session_manager.get_session_summary()
        print(f"✓ セッション概要: {len(summary)}件のセッション")
        
        # 期限切れセッションクリーンアップ
        cleaned = await session_manager.cleanup_expired_sessions()
        print(f"✓ 期限切れセッションクリーンアップ: {cleaned}件")
        
        return True
        
    except Exception as e:
        print(f"✗ SessionManagerテストでエラー: {e}")
        return False


async def main():
    """メインテスト実行"""
    print("自動化モジュール基本テスト開始")
    print("=" * 50)
    
    test_results = []
    
    # 各テストの実行
    test_results.append(await test_browser_manager())
    test_results.append(await test_session_manager())
    test_results.append(await test_chatgpt_handler())
    test_results.append(await test_automation_controller())
    
    # 結果集計
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"成功: {passed}/{total}")
    
    if passed == total:
        print("✓ 全てのテストが成功しました")
        print("\n次のステップ:")
        print("1. ChatGPTに手動でログインしてください")
        print("2. python test_automation.py --full でフルテストを実行")
        print("3. 他の開発者にAIハンドラー実装を依頼")
    else:
        print("⚠ 一部のテストが失敗しました")
        print("ログを確認して問題を修正してください")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nテストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        sys.exit(1)