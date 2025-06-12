"""
改善されたAIモデル取得機能
実際のWebアプリケーションから確実にモデル情報を取得
"""

import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging
from playwright.async_api import async_playwright, Browser

logger = logging.getLogger(__name__)

class ImprovedModelFetcher:
    """改善されたモデル取得クラス"""
    
    def __init__(self):
        # デフォルトのモデルリスト（フォールバック用）
        self.default_models = {
            "chatgpt": {
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "selector": "button[aria-label*='Model']",  # モデル選択ボタン
                "dropdown": "[role='menu'] [role='menuitem']",  # ドロップダウン項目
                "url": "https://chat.openai.com"
            },
            "claude": {
                "models": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "selector": "[data-testid='model-selector']",
                "dropdown": "select option, [role='listbox'] [role='option']",
                "url": "https://claude.ai/new"
            },
            "gemini": {
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
                "selector": "[aria-label*='Model']",
                "dropdown": "[role='menu'] button",
                "url": "https://gemini.google.com"
            }
        }
        
    async def get_models_with_user_profile(self, service: str, chrome_profile_path: str = None) -> Dict:
        """
        ユーザーのChromeプロファイルを使用してモデルを取得
        
        Args:
            service: AIサービス名
            chrome_profile_path: Chromeプロファイルのパス
        """
        try:
            async with async_playwright() as p:
                # ユーザーのプロファイルを使用
                browser_args = []
                if chrome_profile_path:
                    browser_args.extend([
                        f"--user-data-dir={chrome_profile_path}",
                        "--profile-directory=Default"
                    ])
                
                browser = await p.chromium.launch(
                    headless=False,  # UIを表示
                    channel="chrome",
                    args=browser_args
                )
                
                context = await browser.new_context()
                page = await context.new_page()
                
                # サービスのURLに移動
                service_info = self.default_models.get(service, {})
                await page.goto(service_info.get("url", ""))
                
                # ユーザーに確認を促す
                logger.info(f"ブラウザで{service}のページを開きました。モデル選択メニューを開いてください。")
                
                # 10秒待機（ユーザーがモデル選択メニューを開く時間）
                await page.wait_for_timeout(10000)
                
                # モデル情報を取得
                models = await self._extract_models(page, service)
                
                await browser.close()
                
                return {
                    "models": models,
                    "source": "browser",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"{service}のモデル取得エラー: {e}")
            return {
                "models": self.default_models.get(service, {}).get("models", []),
                "source": "default",
                "error": str(e)
            }
            
    async def _extract_models(self, page, service: str) -> List[str]:
        """ページからモデル情報を抽出"""
        models = []
        service_info = self.default_models.get(service, {})
        
        try:
            # モデル選択要素を探す
            dropdown_selector = service_info.get("dropdown", "")
            
            if service == "chatgpt":
                # ChatGPTの場合
                elements = await page.query_selector_all("button[class*='model']")
                for elem in elements:
                    text = await elem.text_content()
                    if text and "GPT" in text.upper():
                        models.append(text.strip())
                        
            elif service == "claude":
                # Claudeの場合
                elements = await page.query_selector_all("[data-value*='claude']")
                for elem in elements:
                    value = await elem.get_attribute("data-value")
                    if value:
                        models.append(value)
                        
            elif service == "gemini":
                # Geminiの場合
                elements = await page.query_selector_all("[aria-label*='Gemini']")
                for elem in elements:
                    text = await elem.text_content()
                    if text and "gemini" in text.lower():
                        models.append(text.strip())
                        
        except Exception as e:
            logger.error(f"モデル抽出エラー: {e}")
            
        # 重複を除去
        models = list(set(models))
        
        # モデルが見つからない場合はデフォルトを返す
        if not models:
            models = self.default_models.get(service, {}).get("models", [])
            
        return models
        
    async def get_models_from_api(self, service: str, api_key: str = None) -> Dict:
        """
        APIを使用してモデルリストを取得（可能な場合）
        """
        if service == "chatgpt" and api_key:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {api_key}"}
                    async with session.get("https://api.openai.com/v1/models", headers=headers) as resp:
                        data = await resp.json()
                        models = [m["id"] for m in data.get("data", []) if "gpt" in m["id"]]
                        return {
                            "models": sorted(models, reverse=True),
                            "source": "api",
                            "timestamp": datetime.now().isoformat()
                        }
            except Exception as e:
                logger.error(f"OpenAI API エラー: {e}")
                
        return {
            "models": self.default_models.get(service, {}).get("models", []),
            "source": "default"
        }
        
    def get_chrome_profile_paths(self) -> Dict[str, str]:
        """
        各OSのChromeプロファイルパスを返す
        """
        import platform
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return {
                "chrome": "~/Library/Application Support/Google/Chrome",
                "edge": "~/Library/Application Support/Microsoft Edge"
            }
        elif system == "Windows":
            return {
                "chrome": "%LOCALAPPDATA%\\Google\\Chrome\\User Data",
                "edge": "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data"
            }
        else:  # Linux
            return {
                "chrome": "~/.config/google-chrome",
                "chromium": "~/.config/chromium"
            }
            
    def save_manual_models(self, service: str, models: List[str]):
        """
        ユーザーが手動で入力したモデルリストを保存
        """
        config_path = "config/manual_models.json"
        
        try:
            # 既存の設定を読み込み
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except FileNotFoundError:
                config = {}
                
            # 更新
            config[service] = {
                "models": models,
                "updated": datetime.now().isoformat(),
                "source": "manual"
            }
            
            # 保存
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"{service}のモデルリストを手動で更新しました")
            
        except Exception as e:
            logger.error(f"モデルリスト保存エラー: {e}")