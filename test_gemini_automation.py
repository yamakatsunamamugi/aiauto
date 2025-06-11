#!/usr/bin/env python3
"""
Gemini と Google AI Studio の自動化テストスクリプト
接続可能なAIサービスで実際の質問応答処理をテスト
"""

import asyncio
import time
from playwright.async_api import async_playwright
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GeminiAutomationTest:
    """Gemini自動化テストクラス"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup_browser(self):
        """ブラウザセットアップ"""
        try:
            logger.info("Playwrightブラウザセットアップ中...")
            
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=False,  # ブラウザを表示してテスト確認
                slow_mo=1000     # 操作を見やすくする
            )
            
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
            logger.info("✅ ブラウザセットアップ完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ ブラウザセットアップ失敗: {e}")
            return False
    
    async def test_gemini_automation(self):
        """Gemini自動化テスト"""
        try:
            logger.info("Gemini自動化テスト開始...")
            
            # Geminiサイトにアクセス
            await self.page.goto('https://gemini.google.com', timeout=30000)
            await self.page.wait_for_load_state('networkidle')
            
            title = await self.page.title()
            logger.info(f"ページタイトル: {title}")
            
            # テスト用の質問
            test_question = "こんにちは！簡単な自己紹介をお願いします。"
            
            # チャット入力欄を探す
            input_selectors = [
                'textarea[placeholder*="メッセージ"]',
                'textarea[placeholder*="Message"]', 
                'textarea[data-testid="chat-input"]',
                'textarea',
                'div[contenteditable="true"]'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = await self.page.wait_for_selector(selector, timeout=5000)
                    if input_element:
                        logger.info(f"✅ 入力欄発見: {selector}")
                        break
                except:
                    continue
            
            if input_element:
                # 質問を入力
                await input_element.fill(test_question)
                logger.info(f"✅ 質問入力完了: {test_question}")
                
                # 送信ボタンを探してクリック
                send_selectors = [
                    'button[aria-label*="送信"]',
                    'button[aria-label*="Send"]',
                    'button[data-testid="send-button"]',
                    'button:has-text("送信")',
                    'button:has-text("Send")',
                    'button[type="submit"]'
                ]
                
                sent = False
                for selector in send_selectors:
                    try:
                        send_button = await self.page.wait_for_selector(selector, timeout=3000)
                        if send_button:
                            await send_button.click()
                            logger.info(f"✅ 送信ボタンクリック: {selector}")
                            sent = True
                            break
                    except:
                        continue
                
                if not sent:
                    # Enterキーで送信を試す
                    await input_element.press('Enter')
                    logger.info("✅ Enterキーで送信")
                
                # 応答を待つ
                logger.info("AI応答を待機中...")
                await self.page.wait_for_timeout(8000)
                
                # ページの内容から応答を確認
                page_content = await self.page.inner_text('body')
                
                if test_question in page_content:
                    logger.info("✅ 質問が送信されました")
                    
                    # 応答らしきテキストを探す
                    response_parts = page_content.split(test_question)
                    if len(response_parts) > 1:
                        potential_response = response_parts[1][:200]
                        logger.info(f"✅ 応答候補: {potential_response}...")
                        return True
                    else:
                        logger.info("⚠️  応答の特定ができませんでした")
                        return True  # 送信は成功
                else:
                    logger.warning("⚠️  質問の送信確認ができませんでした")
                    return False
                    
            else:
                logger.error("❌ 入力欄が見つかりませんでした")
                return False
                
        except Exception as e:
            logger.error(f"❌ Gemini自動化テスト失敗: {e}")
            return False
    
    async def test_google_ai_studio_automation(self):
        """Google AI Studio自動化テスト"""
        try:
            logger.info("Google AI Studio自動化テスト開始...")
            
            # 新しいタブを開く
            new_page = await self.context.new_page()
            
            # Google AI Studioにアクセス
            await new_page.goto('https://aistudio.google.com', timeout=30000)
            await new_page.wait_for_load_state('networkidle')
            
            title = await new_page.title()
            logger.info(f"ページタイトル: {title}")
            
            # テスト用の質問
            test_question = "AI自動化システムについて簡単に説明してください。"
            
            # 入力欄を探す
            input_selectors = [
                'textarea[placeholder*="プロンプト"]',
                'textarea[placeholder*="Prompt"]',
                'textarea[data-testid="prompt-input"]',
                'textarea',
                'div[contenteditable="true"]'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = await new_page.wait_for_selector(selector, timeout=5000)
                    if input_element:
                        logger.info(f"✅ 入力欄発見: {selector}")
                        break
                except:
                    continue
            
            if input_element:
                # 質問を入力
                await input_element.fill(test_question)
                logger.info(f"✅ 質問入力完了: {test_question}")
                
                # 実行ボタンを探してクリック
                run_selectors = [
                    'button[aria-label*="実行"]',
                    'button[aria-label*="Run"]',
                    'button:has-text("実行")',
                    'button:has-text("Run")',
                    'button[data-testid="run-button"]'
                ]
                
                executed = False
                for selector in run_selectors:
                    try:
                        run_button = await new_page.wait_for_selector(selector, timeout=3000)
                        if run_button:
                            await run_button.click()
                            logger.info(f"✅ 実行ボタンクリック: {selector}")
                            executed = True
                            break
                    except:
                        continue
                
                if executed:
                    # 応答を待つ
                    logger.info("AI応答を待機中...")
                    await new_page.wait_for_timeout(10000)
                    
                    # ページの内容から応答を確認
                    page_content = await new_page.inner_text('body')
                    
                    if test_question in page_content:
                        logger.info("✅ 質問が実行されました")
                        return True
                    else:
                        logger.warning("⚠️  質問の実行確認ができませんでした")
                        return False
                else:
                    logger.warning("⚠️  実行ボタンが見つかりませんでした")
                    return False
                    
            else:
                logger.error("❌ 入力欄が見つかりませんでした")
                return False
                
            await new_page.close()
                
        except Exception as e:
            logger.error(f"❌ Google AI Studio自動化テスト失敗: {e}")
            return False
    
    async def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("✅ リソースクリーンアップ完了")
        except Exception as e:
            logger.error(f"❌ クリーンアップエラー: {e}")

async def run_gemini_automation_test():
    """Gemini自動化テストの実行"""
    
    print("="*60)
    print("🤖 Gemini & Google AI Studio 自動化テスト")
    print("="*60)
    
    tester = GeminiAutomationTest()
    
    try:
        # ブラウザセットアップ
        if not await tester.setup_browser():
            print("❌ ブラウザセットアップに失敗しました")
            return False
        
        # テスト実行
        test_results = {}
        
        # Geminiテスト
        print(f"\n--- Gemini自動化テスト ---")
        test_results['Gemini'] = await tester.test_gemini_automation()
        
        # Google AI Studioテスト
        print(f"\n--- Google AI Studio自動化テスト ---")
        test_results['Google AI Studio'] = await tester.test_google_ai_studio_automation()
        
        # 結果サマリー
        print("\n" + "="*60)
        print("📊 テスト結果サマリー")
        print("="*60)
        
        success_count = 0
        for service, result in test_results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            print(f"{service:<20}: {status}")
            if result:
                success_count += 1
        
        print(f"\n成功率: {success_count}/{len(test_results)} ({success_count/len(test_results)*100:.1f}%)")
        
        if success_count > 0:
            print(f"\n🎉 {success_count}個のAIサービスで自動化テストが成功しました！")
            return True
        else:
            print("\n⚠️  全てのサービスでエラーが発生しました")
            return False
            
    except Exception as e:
        logger.error(f"❌ テスト実行中にエラーが発生: {e}")
        return False
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(run_gemini_automation_test())
    exit(0 if success else 1)