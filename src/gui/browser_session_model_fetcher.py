"""
ブラウザセッション方式でAIモデル情報を取得
ユーザーがログイン済みのChromeプロファイルを使用して、各AIサービスから実際のモデルリストを取得
"""

import json
import os
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page
import logging
import platform

logger = logging.getLogger(__name__)

class BrowserSessionModelFetcher:
    """ブラウザセッション方式でAIモデル情報を取得するクラス"""
    
    def __init__(self):
        self.chrome_user_data_dir = self._get_chrome_user_data_dir()
        self.ai_services = {
            "chatgpt": {
                "url": "https://chat.openai.com",
                "model_selector": 'button[aria-haspopup="menu"]:has-text("GPT")',
                "model_list_selector": '[role="menuitem"]',
                "wait_selector": 'main',
            },
            "claude": {
                "url": "https://claude.ai/new",
                "model_selector": 'button[aria-label*="model"]',
                "model_list_selector": '[role="option"]',
                "wait_selector": 'main',
            },
            "gemini": {
                "url": "https://gemini.google.com/app",
                "model_selector": 'button[aria-label*="Model"]',
                "model_list_selector": '[role="menuitem"]',
                "wait_selector": 'main',
            },
            "genspark": {
                "url": "https://www.genspark.ai",
                "model_selector": None,  # Gensparkは固定モデル
                "model_list_selector": None,
                "wait_selector": 'body',
            },
            "google_ai_studio": {
                "url": "https://aistudio.google.com/app/prompts/new_chat",
                "model_selector": 'button[aria-label*="Model"]',
                "model_list_selector': '[role="option"]',
                "wait_selector": 'main',
            }
        }
        
    def _get_chrome_user_data_dir(self) -> str:
        """Chromeのユーザーデータディレクトリを取得"""
        system = platform.system()
        home = os.path.expanduser("~")
        
        if system == "Darwin":  # macOS
            return os.path.join(home, "Library/Application Support/Google/Chrome")
        elif system == "Windows":
            return os.path.join(home, "AppData\\Local\\Google\\Chrome\\User Data")
        else:  # Linux
            return os.path.join(home, ".config/google-chrome")
    
    async def fetch_all_models(self) -> Dict[str, Dict]:
        """全AIサービスのモデル情報を取得"""
        results = {}
        
        async with async_playwright() as p:
            # ユーザーのChromeプロファイルを使用
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.chrome_user_data_dir,
                headless=False,  # ユーザーセッションを使うためヘッドレスモードはオフ
                channel="chrome",
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )
            
            try:
                for service_name, service_config in self.ai_services.items():
                    try:
                        logger.info(f"🔍 {service_name}のモデル情報を取得中...")
                        models = await self._fetch_models(browser, service_name, service_config)
                        results[service_name] = {
                            "models": models,
                            "last_updated": datetime.now().isoformat(),
                            "method": "browser_session"
                        }
                        logger.info(f"✅ {service_name}: {len(models)}個のモデルを取得")
                    except Exception as e:
                        logger.error(f"❌ {service_name}のモデル取得エラー: {e}")
                        results[service_name] = {
                            "error": str(e),
                            "models": self._get_fallback_models(service_name)
                        }
            finally:
                await browser.close()
        
        # 結果を保存
        self._save_results(results)
        return results
    
    async def _fetch_models(self, browser, service_name: str, config: Dict) -> List[str]:
        """個別のAIサービスからモデルを取得"""
        page = await browser.new_page()
        models = []
        
        try:
            # ページに移動
            await page.goto(config["url"], wait_until="networkidle", timeout=30000)
            await page.wait_for_selector(config["wait_selector"], timeout=10000)
            await page.wait_for_timeout(2000)  # ページの完全読み込みを待つ
            
            if service_name == "chatgpt":
                models = await self._fetch_chatgpt_models(page, config)
            elif service_name == "claude":
                models = await self._fetch_claude_models(page, config)
            elif service_name == "gemini":
                models = await self._fetch_gemini_models(page, config)
            elif service_name == "genspark":
                models = ["default", "research", "advanced"]  # 固定値
            elif service_name == "google_ai_studio":
                models = await self._fetch_google_ai_studio_models(page, config)
                
        except Exception as e:
            logger.error(f"{service_name}でエラー発生: {e}")
            raise
        finally:
            await page.close()
            
        return models
    
    async def _fetch_chatgpt_models(self, page: Page, config: Dict) -> List[str]:
        """ChatGPTのモデルリストを取得"""
        models = []
        
        try:
            # モデル選択ボタンをクリック
            model_button = await page.wait_for_selector(config["model_selector"], timeout=5000)
            await model_button.click()
            await page.wait_for_timeout(1000)
            
            # モデルリストを取得
            model_elements = await page.query_selector_all(config["model_list_selector"])
            for element in model_elements:
                text = await element.text_content()
                if text and "GPT" in text:
                    # モデル名をクリーンアップ
                    model_name = text.strip().split('\n')[0]
                    if model_name and not any(x in model_name.lower() for x in ["upgrade", "plus", "team"]):
                        models.append(model_name)
            
            # ポップアップを閉じる
            await page.keyboard.press("Escape")
            
        except Exception as e:
            logger.warning(f"ChatGPTモデル取得中のエラー: {e}")
            # フォールバック
            models = ["GPT-4o", "GPT-4o mini", "GPT-4", "GPT-3.5"]
            
        return models
    
    async def _fetch_claude_models(self, page: Page, config: Dict) -> List[str]:
        """Claudeのモデルリストを取得"""
        models = []
        
        try:
            # モデル選択要素を探す
            model_elements = await page.query_selector_all('button[class*="model"]')
            if model_elements:
                for element in model_elements:
                    text = await element.text_content()
                    if text and "Claude" in text:
                        model_name = text.strip()
                        if model_name not in models:
                            models.append(model_name)
            
            # 代替方法：モデル選択ドロップダウンを確認
            if not models:
                await page.wait_for_timeout(2000)
                dropdown = await page.query_selector('[aria-label*="model"]')
                if dropdown:
                    await dropdown.click()
                    await page.wait_for_timeout(1000)
                    options = await page.query_selector_all('[role="option"]')
                    for option in options:
                        text = await option.text_content()
                        if text and "Claude" in text:
                            models.append(text.strip())
                    await page.keyboard.press("Escape")
                    
        except Exception as e:
            logger.warning(f"Claudeモデル取得中のエラー: {e}")
            # フォールバック
            models = ["Claude 3.5 Sonnet", "Claude 3 Opus", "Claude 3 Sonnet", "Claude 3 Haiku"]
            
        return models
    
    async def _fetch_gemini_models(self, page: Page, config: Dict) -> List[str]:
        """Geminiのモデルリストを取得"""
        models = []
        
        try:
            # モデル選択ボタンを探す
            model_button = await page.query_selector('button[aria-label*="Gemini"]')
            if model_button:
                await model_button.click()
                await page.wait_for_timeout(1000)
                
                # モデルリストを取得
                options = await page.query_selector_all('[role="menuitem"]')
                for option in options:
                    text = await option.text_content()
                    if text and "Gemini" in text:
                        model_name = text.strip().split('\n')[0]
                        if model_name not in models:
                            models.append(model_name)
                
                await page.keyboard.press("Escape")
            
            # 代替方法：設定メニューから取得
            if not models:
                settings_button = await page.query_selector('[aria-label*="Settings"]')
                if settings_button:
                    await settings_button.click()
                    await page.wait_for_timeout(1000)
                    model_info = await page.query_selector_all('text=/Gemini.*/i')
                    for info in model_info:
                        text = await info.text_content()
                        if text and "Gemini" in text:
                            models.append(text.strip())
                    
        except Exception as e:
            logger.warning(f"Geminiモデル取得中のエラー: {e}")
            # フォールバック
            models = ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini Pro"]
            
        return models
    
    async def _fetch_google_ai_studio_models(self, page: Page, config: Dict) -> List[str]:
        """Google AI Studioのモデルリストを取得"""
        models = []
        
        try:
            # モデル選択ドロップダウンを探す
            model_selector = await page.query_selector('[aria-label*="Select model"]')
            if model_selector:
                await model_selector.click()
                await page.wait_for_timeout(1000)
                
                # オプションを取得
                options = await page.query_selector_all('[role="option"]')
                for option in options:
                    text = await option.text_content()
                    if text and ("Gemini" in text or "PaLM" in text):
                        models.append(text.strip())
                
                await page.keyboard.press("Escape")
                
        except Exception as e:
            logger.warning(f"Google AI Studioモデル取得中のエラー: {e}")
            # フォールバック（Geminiと同じ）
            models = ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini Pro", "PaLM 2"]
            
        return models
    
    def _get_fallback_models(self, service_name: str) -> List[str]:
        """フォールバック用のモデルリスト"""
        fallbacks = {
            "chatgpt": ["GPT-4o", "GPT-4o mini", "GPT-4", "GPT-3.5"],
            "claude": ["Claude 3.5 Sonnet", "Claude 3 Opus", "Claude 3 Sonnet", "Claude 3 Haiku"],
            "gemini": ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini Pro"],
            "genspark": ["default", "research", "advanced"],
            "google_ai_studio": ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini Pro", "PaLM 2"]
        }
        return fallbacks.get(service_name, [])
    
    def _save_results(self, results: Dict):
        """結果をファイルに保存"""
        output_path = "config/ai_models_browser_session.json"
        
        try:
            os.makedirs("config", exist_ok=True)
            
            output_data = {
                "method": "browser_session",
                "last_updated": datetime.now().isoformat(),
                "fetcher": "AI-A",
                "results": results
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ 結果を{output_path}に保存しました")
            
        except Exception as e:
            logger.error(f"結果の保存エラー: {e}")


def fetch_models_sync() -> Dict:
    """同期的にモデル情報を取得（GUI用）"""
    fetcher = BrowserSessionModelFetcher()
    return asyncio.run(fetcher.fetch_all_models())


if __name__ == "__main__":
    # テスト実行
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 ブラウザセッション方式でAIモデル情報を取得します...")
    print("📌 注意: Chromeにログイン済みである必要があります")
    
    results = fetch_models_sync()
    
    print("\n📊 取得結果:")
    for service, data in results.items():
        if "error" in data:
            print(f"❌ {service}: エラー - {data['error']}")
        else:
            print(f"✅ {service}: {data['models']}")