#!/usr/bin/env python3
"""
ChatGPTブラウザ自動化テスト
実際のChatGPTサイトでテストします（手動ログイン前提）
"""

import asyncio
import sys
sys.path.append('/Users/roudousha/Dropbox/5.AI-auto')

from playwright.async_api import async_playwright
from src.automation.ai_handlers.chatgpt_handler import ChatGPTHandler
from src.utils.logger import logger

async def test_chatgpt_browser():
    """ChatGPTブラウザ自動化テスト"""
    print("🤖 ChatGPTブラウザ自動化テスト開始")
    print("=" * 40)
    
    async with async_playwright() as p:
        # ブラウザ起動（既存のChromeプロファイルを使用）
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="/Users/roudousha/Library/Application Support/Google/Chrome/Default",
            headless=False,  # GUIで動作確認
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-default-apps"
            ]
        )
        
        # 新しいページを作成
        page = await browser.new_page()
        
        try:
            # ChatGPTハンドラー初期化
            print("🔧 ChatGPTハンドラー初期化中...")
            chatgpt = ChatGPTHandler(page)
            
            # ChatGPTサイトに移動
            print("🌐 ChatGPTサイトにアクセス中...")
            await page.goto("https://chat.openai.com")
            await asyncio.sleep(5)  # 手動ログイン時間
            
            print("👤 手動でChatGPTにログインしてください...")
            print("ログイン完了後、Enterキーを押してください")
            input("準備完了後、Enterを押してください: ")
            
            # ログイン状態確認
            print("\n🔍 ログイン状態確認中...")
            is_logged_in = await chatgpt.login_check()
            print(f"ログイン状態: {'✅ ログイン済み' if is_logged_in else '❌ ログインが必要'}")
            
            if not is_logged_in:
                print("❌ ログインしてから再度実行してください")
                return
            
            # 利用可能なモデル取得
            print("\n📋 利用可能なモデル取得中...")
            models = await chatgpt.get_available_models()
            print(f"利用可能なモデル: {models}")
            
            # テスト質問
            test_questions = [
                "Hello, how are you?",
                "日本の首都は？",
                "2+2の答えを教えてください"
            ]
            
            print(f"\n💬 {len(test_questions)}個のテスト質問を実行します...")
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n--- テスト {i}/{len(test_questions)} ---")
                print(f"質問: {question}")
                
                try:
                    # AI処理実行
                    response = await chatgpt.process_request(question)
                    
                    if response:
                        print(f"✅ 回答取得成功:")
                        print(f"   {response[:100]}{'...' if len(response) > 100 else ''}")
                    else:
                        print("❌ 回答取得失敗")
                        
                    # 次の質問前に少し待機
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    print(f"❌ エラー: {e}")
            
            print("\n🎉 ChatGPTブラウザ自動化テスト完了！")
            
        except Exception as e:
            print(f"❌ 全体エラー: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            print("\n終了するにはEnterキーを押してください...")
            input()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_chatgpt_browser())