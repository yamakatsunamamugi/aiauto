#!/usr/bin/env python3
"""
基本モジュール動作確認テスト

依存関係のない基本機能のテスト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_imports():
    """インポートテスト"""
    print("\n=== インポートテスト ===")
    
    try:
        # 基本ユーティリティ
        from src.utils.logger import logger
        from src.utils.config_manager import config_manager
        print("✓ 基本ユーティリティのインポート成功")
        
        # ブラウザ管理
        from src.automation.browser_manager import BrowserManager
        print("✓ BrowserManagerのインポート成功")
        
        # リトライ管理
        from src.automation.retry_manager import RetryManager
        print("✓ RetryManagerのインポート成功")
        
        # セッション管理
        from src.automation.session_manager import SessionManager
        print("✓ SessionManagerのインポート成功")
        
        # AIハンドラー
        from src.automation.ai_handlers.base_handler import BaseAIHandler
        from src.automation.ai_handlers.chatgpt_handler import ChatGPTHandler
        print("✓ AIハンドラーのインポート成功")
        
        return True
        
    except Exception as e:
        print(f"✗ インポートテストでエラー: {e}")
        return False


async def test_config_manager():
    """設定管理テスト"""
    print("\n=== 設定管理テスト ===")
    
    try:
        from src.utils.config_manager import config_manager
        
        # 基本的な設定読み込み
        automation_config = config_manager.get('automation', {})
        print(f"✓ 自動化設定読み込み: {len(automation_config)}項目")
        
        # テスト設定の書き込み・読み込み
        test_key = "test.playwright.installed"
        config_manager.set(test_key, True)
        test_value = config_manager.get(test_key)
        
        if test_value:
            print("✓ 設定の書き込み・読み込み成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 設定管理テストでエラー: {e}")
        return False


async def test_session_manager():
    """セッション管理テスト"""
    print("\n=== セッション管理テスト ===")
    
    try:
        from src.automation.session_manager import SessionManager
        
        session_manager = SessionManager()
        print("✓ SessionManager初期化成功")
        
        # セッション概要取得
        summary = session_manager.get_session_summary()
        print(f"✓ セッション概要取得: {len(summary)}件")
        
        # セッションディレクトリ取得
        session_dir = session_manager.get_session_dir("test_service")
        print(f"✓ セッションディレクトリ作成: {session_dir}")
        
        return True
        
    except Exception as e:
        print(f"✗ セッション管理テストでエラー: {e}")
        return False


async def test_retry_manager():
    """リトライ管理テスト"""
    print("\n=== リトライ管理テスト ===")
    
    try:
        from src.automation.retry_manager import RetryManager
        
        retry_manager = RetryManager(max_retries=3, base_delay=0.1)
        print("✓ RetryManager初期化成功")
        
        # 成功するテスト関数
        async def success_func():
            return "success"
        
        result = await retry_manager.retry_with_backoff(
            success_func, "test_service"
        )
        
        if result == "success":
            print("✓ 成功ケースのリトライテスト完了")
        
        # リトライ統計取得
        stats = retry_manager.get_retry_stats()
        print(f"✓ リトライ統計取得: {len(stats)}サービス")
        
        return True
        
    except Exception as e:
        print(f"✗ リトライ管理テストでエラー: {e}")
        return False


async def main():
    """メインテスト実行"""
    print("基本モジュール動作確認テスト開始")
    print("=" * 50)
    
    test_results = []
    
    # 各テストの実行
    test_results.append(await test_imports())
    test_results.append(await test_config_manager())
    test_results.append(await test_session_manager())
    test_results.append(await test_retry_manager())
    
    # 結果集計
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"成功: {passed}/{total}")
    
    if passed == total:
        print("✓ 全ての基本テストが成功しました")
        print("\n次のステップ:")
        print("1. Playwrightブラウザをインストール: playwright install chromium")
        print("2. 他のモジュール（GUI、Sheets）との統合テスト")
        print("3. 実際のAIサービスでのテスト（手動ログイン後）")
    else:
        print("⚠ 一部のテストが失敗しました")
    
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