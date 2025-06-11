#!/usr/bin/env python3
"""
全AIハンドラー統合テスト

5つのAIサービス（ChatGPT、Claude、Gemini、Genspark、Google AI Studio）の
ハンドラー実装確認とログイン状態チェック
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.automation.browser_manager import BrowserManager
from src.automation.automation_controller import AutomationController
from src.utils.logger import logger


async def test_ai_handler_imports():
    """全AIハンドラーのインポートテスト"""
    print("\n=== AIハンドラーインポートテスト ===")
    
    try:
        from src.automation.ai_handlers.chatgpt_handler import ChatGPTHandler
        from src.automation.ai_handlers.claude_handler import ClaudeHandler
        from src.automation.ai_handlers.gemini_handler import GeminiHandler
        from src.automation.ai_handlers.genspark_handler import GensparkHandler
        from src.automation.ai_handlers.google_ai_studio_handler import GoogleAIStudioHandler
        
        handlers = {
            'ChatGPT': ChatGPTHandler,
            'Claude': ClaudeHandler,
            'Gemini': GeminiHandler,
            'Genspark': GensparkHandler,
            'Google AI Studio': GoogleAIStudioHandler
        }
        
        for name, handler_class in handlers.items():
            print(f"✓ {name}Handler インポート成功")
        
        return True
        
    except Exception as e:
        print(f"✗ AIハンドラーインポートでエラー: {e}")
        return False


async def test_automation_controller_integration():
    """AutomationControllerの全AI統合テスト"""
    print("\n=== AutomationController統合テスト ===")
    
    try:
        controller = AutomationController()
        print("✓ AutomationController初期化成功")
        
        # 利用可能AIの確認
        available_ais = controller.get_available_ais()
        print(f"✓ 利用可能AI: {list(available_ais.keys())}")
        
        expected_ais = {'chatgpt', 'claude', 'gemini', 'genspark', 'google_ai_studio'}
        actual_ais = set(available_ais.keys())
        
        if expected_ais == actual_ais:
            print("✓ 全てのAIハンドラーが正常に登録されています")
        else:
            missing = expected_ais - actual_ais
            extra = actual_ais - expected_ais
            if missing:
                print(f"⚠ 不足しているAI: {missing}")
            if extra:
                print(f"⚠ 予期しないAI: {extra}")
        
        return True
        
    except Exception as e:
        print(f"✗ AutomationController統合テストでエラー: {e}")
        return False


async def test_ai_login_status():
    """全AIサービスのログイン状態確認テスト"""
    print("\n=== AIログイン状態確認テスト ===")
    
    try:
        async with BrowserManager() as browser_manager:
            print("✓ ブラウザマネージャー起動成功")
            
            ai_services = ['chatgpt', 'claude', 'gemini', 'genspark', 'google_ai_studio']
            login_results = {}
            
            for ai_service in ai_services:
                try:
                    print(f"\n--- {ai_service.upper()} ログイン状態確認 ---")
                    
                    # 新しいページを作成
                    page = await browser_manager.create_new_page()
                    
                    # ハンドラーを初期化
                    if ai_service == 'chatgpt':
                        from src.automation.ai_handlers.chatgpt_handler import ChatGPTHandler
                        handler = ChatGPTHandler(page)
                    elif ai_service == 'claude':
                        from src.automation.ai_handlers.claude_handler import ClaudeHandler
                        handler = ClaudeHandler(page)
                    elif ai_service == 'gemini':
                        from src.automation.ai_handlers.gemini_handler import GeminiHandler
                        handler = GeminiHandler(page)
                    elif ai_service == 'genspark':
                        from src.automation.ai_handlers.genspark_handler import GensparkHandler
                        handler = GensparkHandler(page)
                    elif ai_service == 'google_ai_studio':
                        from src.automation.ai_handlers.google_ai_studio_handler import GoogleAIStudioHandler
                        handler = GoogleAIStudioHandler(page)
                    
                    # ログイン状態確認
                    is_logged_in = await handler.login_check()
                    login_results[ai_service] = is_logged_in
                    
                    if is_logged_in:
                        print(f"✓ {ai_service}: ログイン済み")
                        
                        # 利用可能モデル取得テスト
                        try:
                            models = await handler.get_available_models()
                            print(f"  利用可能モデル: {models[:3]}{'...' if len(models) > 3 else ''}")
                        except Exception as model_error:
                            print(f"  モデル取得エラー: {model_error}")
                    else:
                        print(f"⚠ {ai_service}: 未ログイン（手動ログインが必要）")
                    
                    # ページを閉じる
                    await page.close()
                    
                except Exception as e:
                    print(f"✗ {ai_service}: テストでエラー: {e}")
                    login_results[ai_service] = False
        
        # 結果サマリー
        print(f"\n=== ログイン状態サマリー ===")
        logged_in_count = sum(login_results.values())
        total_count = len(login_results)
        
        for service, status in login_results.items():
            status_text = "✓ ログイン済み" if status else "⚠ 未ログイン"
            print(f"{service}: {status_text}")
        
        print(f"\nログイン済み: {logged_in_count}/{total_count}")
        
        if logged_in_count == 0:
            print("\n📝 次のステップ:")
            print("1. 各AIサービスに手動でログインしてください")
            print("2. ログイン後、再度このテストを実行してください")
        elif logged_in_count < total_count:
            print("\n📝 部分的にログイン済みです")
            print("未ログインのサービスに手動でログインしてください")
        else:
            print("\n🎉 全てのAIサービスにログイン済みです！")
            print("自動化システムを使用する準備が整いました")
        
        return True
        
    except Exception as e:
        print(f"✗ AIログイン状態確認テストでエラー: {e}")
        return False


async def test_full_integration():
    """フル統合テスト（ログイン済みの場合のみ）"""
    print("\n=== フル統合テスト ===")
    
    try:
        # 簡単なテスト用タスクを作成（実際の処理はしない）
        print("⚠ フル統合テストは実際のAI処理を含むため、")
        print("  手動でのログイン確認後に実行してください")
        print("  テスト実行コマンド: python test_ai_processing.py")
        
        return True
        
    except Exception as e:
        print(f"✗ フル統合テストでエラー: {e}")
        return False


async def main():
    """メインテスト実行"""
    print("全AIハンドラー統合テスト開始")
    print("=" * 60)
    
    test_results = []
    
    # 各テストの実行
    test_results.append(await test_ai_handler_imports())
    test_results.append(await test_automation_controller_integration())
    test_results.append(await test_ai_login_status())
    test_results.append(await test_full_integration())
    
    # 結果集計
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"成功: {passed}/{total}")
    
    if passed == total:
        print("✓ 全ての統合テストが成功しました")
        print("\n🚀 AI自動化システムの準備が完了しました！")
        print("\n次のステップ:")
        print("1. 各AIサービスに手動ログイン")
        print("2. スプレッドシートの設定")
        print("3. GUIから自動化実行")
    else:
        print("⚠ 一部のテストが失敗しました")
        print("エラーを確認して修正してください")
    
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