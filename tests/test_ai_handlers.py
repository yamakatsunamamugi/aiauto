"""
AIハンドラーの基本テスト

全AIハンドラーの基本的な機能をテストする
実際のブラウザでのテストが必要（手動ログイン前提）
"""

import asyncio
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.automation.browser_manager import BrowserManager
from src.automation.ai_handlers import (
    ChatGPTHandler,
    ClaudeHandler,
    GeminiHandler,
    GensparkHandler,
    GoogleAIStudioHandler
)
from src.utils.logger import logger


class AIHandlerTester:
    """AIハンドラーテスト実行クラス"""
    
    def __init__(self):
        self.test_prompt = "こんにちは。今日の天気はどうですか？"
        self.handlers = {
            'ChatGPT': ChatGPTHandler,
            'Claude': ClaudeHandler,
            'Gemini': GeminiHandler,
            'Genspark': GensparkHandler,
            'Google AI Studio': GoogleAIStudioHandler
        }
        
    async def test_handler_basic_functionality(self, handler_name: str, handler_class):
        """
        個別ハンドラーの基本機能テスト
        
        Args:
            handler_name: ハンドラー名
            handler_class: ハンドラークラス
        """
        print(f"\n{'='*50}")
        print(f"{handler_name} ハンドラーテスト開始")
        print(f"{'='*50}")
        
        try:
            async with BrowserManager() as browser:
                page = await browser.create_new_page()
                handler = handler_class(page)
                
                # 1. ログイン状態確認テスト
                print(f"\n[テスト1] ログイン状態確認")
                is_logged_in = await handler.login_check()
                print(f"結果: {'✓ ログイン済み' if is_logged_in else '✗ 未ログイン'}")
                
                if not is_logged_in:
                    print(f"⚠️  {handler_name}に手動でログインしてから再実行してください")
                    return False
                
                # 2. セレクター取得テスト
                print(f"\n[テスト2] セレクター取得")
                try:
                    input_selector = await handler.get_input_selector()
                    submit_selector = await handler.get_submit_selector()
                    response_selector = await handler.get_response_selector()
                    
                    print(f"入力欄セレクター: {input_selector}")
                    print(f"送信ボタンセレクター: {submit_selector}")
                    print(f"応答エリアセレクター: {response_selector}")
                    print("✓ セレクター取得成功")
                except Exception as e:
                    print(f"✗ セレクター取得エラー: {e}")
                    return False
                
                # 3. モデル一覧取得テスト
                print(f"\n[テスト3] モデル一覧取得")
                try:
                    models = await handler.get_available_models()
                    print(f"利用可能なモデル: {models}")
                    print("✓ モデル一覧取得成功")
                except Exception as e:
                    print(f"✗ モデル一覧取得エラー: {e}")
                
                # 4. 簡単なテキスト処理テスト（実際にリクエストを送信）
                print(f"\n[テスト4] テキスト処理テスト")
                print(f"テストプロンプト: {self.test_prompt}")
                
                user_input = input(f"{handler_name}でテストを実行しますか？ (y/n): ")
                if user_input.lower() == 'y':
                    try:
                        response = await handler.process_request(self.test_prompt)
                        if response:
                            print(f"✓ レスポンス取得成功")
                            print(f"応答内容（最初の100文字）: {response[:100]}...")
                        else:
                            print("✗ レスポンス取得失敗")
                            return False
                    except Exception as e:
                        print(f"✗ テキスト処理エラー: {e}")
                        return False
                else:
                    print("⚠️  テキスト処理テストをスキップしました")
                
                print(f"\n✓ {handler_name} ハンドラーテスト完了")
                return True
                
        except Exception as e:
            print(f"✗ {handler_name} ハンドラーテストでエラー: {e}")
            return False
    
    async def test_all_handlers(self):
        """全ハンドラーの基本テスト実行"""
        print("AIハンドラー基本テスト開始")
        print("注意: 各AIサービスに事前にログインしておいてください")
        
        results = {}
        
        for handler_name, handler_class in self.handlers.items():
            user_input = input(f"\n{handler_name}をテストしますか？ (y/n): ")
            if user_input.lower() == 'y':
                result = await self.test_handler_basic_functionality(handler_name, handler_class)
                results[handler_name] = result
            else:
                results[handler_name] = "スキップ"
        
        # 結果サマリー
        print(f"\n{'='*50}")
        print("テスト結果サマリー")
        print(f"{'='*50}")
        
        for handler_name, result in results.items():
            if result == "スキップ":
                print(f"{handler_name}: ⚠️  スキップ")
            elif result:
                print(f"{handler_name}: ✓ 成功")
            else:
                print(f"{handler_name}: ✗ 失敗")


async def main():
    """メイン実行関数"""
    try:
        tester = AIHandlerTester()
        await tester.test_all_handlers()
    except KeyboardInterrupt:
        print("\n\nテストが中断されました")
    except Exception as e:
        logger.error(f"テスト実行でエラー: {e}")
        print(f"エラー: {e}")


if __name__ == "__main__":
    print("AIハンドラー基本機能テスト")
    print("=" * 30)
    print("このテストを実行する前に:")
    print("1. 各AIサービス（ChatGPT、Claude、Gemini、Genspark、Google AI Studio）に手動でログインしてください")
    print("2. ブラウザがChromeまたはChromiumであることを確認してください")
    print("3. テストは実際にAIサービスにリクエストを送信します")
    print()
    
    user_input = input("テストを開始しますか？ (y/n): ")
    if user_input.lower() == 'y':
        asyncio.run(main())
    else:
        print("テストをキャンセルしました")