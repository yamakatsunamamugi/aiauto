"""
統合されたAIモデル取得機能
ブラウザセッション、API、手動入力の3つの方法でモデル情報を取得可能
"""

import json
import os
import asyncio
from typing import Dict, List, Optional, Literal
from datetime import datetime
import logging
import platform
from playwright.async_api import async_playwright, Page
import aiohttp

logger = logging.getLogger(__name__)

class UnifiedModelFetcher:
    """統合されたモデル取得クラス"""
    
    def __init__(self):
        self.chrome_user_data_dir = self._get_chrome_user_data_dir()
        self.config_dir = "config"
        os.makedirs(self.config_dir, exist_ok=True)
        
        # AIサービスの設定
        self.ai_services = {
            "chatgpt": {
                "url": "https://chat.openai.com",
                "model_selector": 'button[aria-haspopup="menu"]:has-text("GPT")',
                "model_list_selector": '[role="menuitem"]',
                "wait_selector": 'main',
                "api_endpoint": "https://api.openai.com/v1/models",
                "default_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
            },
            "claude": {
                "url": "https://claude.ai/new",
                "model_selector": 'button[aria-label*="model"]',
                "model_list_selector": '[role="option"]',
                "wait_selector": 'main',
                "api_endpoint": None,  # Claude APIは直接モデルリスト取得不可
                "default_models": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
            },
            "gemini": {
                "url": "https://gemini.google.com/app",
                "model_selector": 'button[aria-label*="Model"]',
                "model_list_selector": '[role="menuitem"]',
                "wait_selector": 'main',
                "api_endpoint": None,  # Gemini APIは別途設定必要
                "default_models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
            },
            "genspark": {
                "url": "https://www.genspark.ai",
                "model_selector": None,
                "model_list_selector": None,
                "wait_selector": 'body',
                "api_endpoint": None,
                "default_models": ["default", "research", "advanced"]
            },
            "google_ai_studio": {
                "url": "https://aistudio.google.com/app/prompts/new_chat",
                "model_selector": 'button[aria-label*="Model"]',
                "model_list_selector": '[role="option"]',
                "wait_selector": 'main',
                "api_endpoint": None,
                "default_models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "palm-2"]
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
    
    async def fetch_models(
        self, 
        method: Literal["browser", "api", "manual", "cached"] = "browser",
        service: Optional[str] = None,
        api_keys: Optional[Dict[str, str]] = None,
        manual_models: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Dict]:
        """
        指定された方法でモデルを取得
        
        Args:
            method: 取得方法 ("browser", "api", "manual", "cached")
            service: 特定のサービスのみ取得する場合に指定
            api_keys: API取得時のAPIキー辞書
            manual_models: 手動入力時のモデルリスト辞書
            
        Returns:
            サービス名をキーとした結果辞書
        """
        logger.info(f"🔍 モデル取得開始 (method={method}, service={service})")
        
        if method == "browser":
            return await self._fetch_models_browser_session(service)
        elif method == "api":
            return await self._fetch_models_api(service, api_keys or {})
        elif method == "manual":
            return self._save_manual_models(manual_models or {})
        elif method == "cached":
            return self._get_cached_models(service)
        else:
            raise ValueError(f"不明な取得方法: {method}")
    
    async def _fetch_models_browser_session(self, service: Optional[str] = None) -> Dict[str, Dict]:
        """ブラウザセッション方式でモデルを取得"""
        results = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.chrome_user_data_dir,
                headless=False,
                channel="chrome",
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )
            
            try:
                services_to_fetch = [service] if service else self.ai_services.keys()
                
                for service_name in services_to_fetch:
                    if service_name not in self.ai_services:
                        logger.warning(f"❌ 不明なサービス: {service_name}")
                        continue
                        
                    try:
                        logger.info(f"🔍 {service_name}のモデル情報を取得中...")
                        service_config = self.ai_services[service_name]
                        models = await self._fetch_single_service(browser, service_name, service_config)
                        
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
                            "models": self.ai_services[service_name]["default_models"],
                            "method": "fallback"
                        }
                        
            finally:
                await browser.close()
        
        # 結果を保存
        self._save_results(results, "browser_session")
        return results
    
    async def _fetch_single_service(self, browser, service_name: str, config: Dict) -> List[str]:
        """個別のAIサービスからモデルを取得"""
        page = await browser.new_page()
        models = []
        
        try:
            await page.goto(config["url"], wait_until="networkidle", timeout=30000)
            await page.wait_for_selector(config["wait_selector"], timeout=10000)
            await page.wait_for_timeout(2000)
            
            # サービス別の取得処理
            if service_name == "chatgpt":
                models = await self._fetch_chatgpt_models(page, config)
            elif service_name == "claude":
                models = await self._fetch_claude_models(page, config)
            elif service_name == "gemini":
                models = await self._fetch_gemini_models(page, config)
            elif service_name == "genspark":
                models = config["default_models"]  # 固定値
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
            model_button = await page.wait_for_selector(config["model_selector"], timeout=5000)
            await model_button.click()
            await page.wait_for_timeout(1000)
            
            model_elements = await page.query_selector_all(config["model_list_selector"])
            for element in model_elements:
                text = await element.text_content()
                if text and "GPT" in text:
                    model_name = text.strip().split('\n')[0]
                    if model_name and not any(x in model_name.lower() for x in ["upgrade", "plus", "team"]):
                        models.append(model_name)
            
            await page.keyboard.press("Escape")
            
        except Exception as e:
            logger.warning(f"ChatGPTモデル取得中のエラー: {e}")
            models = config["default_models"]
            
        return models
    
    async def _fetch_claude_models(self, page: Page, config: Dict) -> List[str]:
        """Claudeのモデルリストを取得"""
        models = []
        
        try:
            model_elements = await page.query_selector_all('button[class*="model"]')
            if model_elements:
                for element in model_elements:
                    text = await element.text_content()
                    if text and "Claude" in text:
                        model_name = text.strip()
                        if model_name not in models:
                            models.append(model_name)
            
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
            models = config["default_models"]
            
        return models
    
    async def _fetch_gemini_models(self, page: Page, config: Dict) -> List[str]:
        """Geminiのモデルリストを取得"""
        models = []
        
        try:
            model_button = await page.query_selector('button[aria-label*="Gemini"]')
            if model_button:
                await model_button.click()
                await page.wait_for_timeout(1000)
                
                options = await page.query_selector_all('[role="menuitem"]')
                for option in options:
                    text = await option.text_content()
                    if text and "Gemini" in text:
                        model_name = text.strip().split('\n')[0]
                        if model_name not in models:
                            models.append(model_name)
                
                await page.keyboard.press("Escape")
            
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
            models = config["default_models"]
            
        return models
    
    async def _fetch_google_ai_studio_models(self, page: Page, config: Dict) -> List[str]:
        """Google AI Studioのモデルリストを取得"""
        models = []
        
        try:
            model_selector = await page.query_selector('[aria-label*="Select model"]')
            if model_selector:
                await model_selector.click()
                await page.wait_for_timeout(1000)
                
                options = await page.query_selector_all('[role="option"]')
                for option in options:
                    text = await option.text_content()
                    if text and ("Gemini" in text or "PaLM" in text):
                        models.append(text.strip())
                
                await page.keyboard.press("Escape")
                
        except Exception as e:
            logger.warning(f"Google AI Studioモデル取得中のエラー: {e}")
            models = config["default_models"]
            
        return models
    
    async def _fetch_models_api(self, service: Optional[str], api_keys: Dict[str, str]) -> Dict[str, Dict]:
        """API経由でモデルを取得"""
        results = {}
        services_to_fetch = [service] if service else self.ai_services.keys()
        
        for service_name in services_to_fetch:
            if service_name not in self.ai_services:
                continue
                
            config = self.ai_services[service_name]
            api_key = api_keys.get(service_name)
            
            if service_name == "chatgpt" and api_key and config["api_endpoint"]:
                try:
                    async with aiohttp.ClientSession() as session:
                        headers = {"Authorization": f"Bearer {api_key}"}
                        async with session.get(config["api_endpoint"], headers=headers) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                models = [
                                    m["id"] for m in data.get("data", []) 
                                    if "gpt" in m["id"].lower()
                                ]
                                results[service_name] = {
                                    "models": sorted(models, reverse=True),
                                    "last_updated": datetime.now().isoformat(),
                                    "method": "api"
                                }
                                logger.info(f"✅ {service_name}: API経由で{len(models)}個のモデルを取得")
                            else:
                                logger.error(f"❌ {service_name}: API応答エラー ({resp.status})")
                                results[service_name] = {
                                    "error": f"API応答エラー: {resp.status}",
                                    "models": config["default_models"],
                                    "method": "fallback"
                                }
                except Exception as e:
                    logger.error(f"❌ {service_name}: APIエラー - {e}")
                    results[service_name] = {
                        "error": str(e),
                        "models": config["default_models"],
                        "method": "fallback"
                    }
            else:
                # APIキーがないかAPIエンドポイントがない場合
                logger.warning(f"⚠️ {service_name}: APIキーまたはエンドポイントが設定されていません")
                results[service_name] = {
                    "error": "APIキーまたはエンドポイントが未設定",
                    "models": config["default_models"],
                    "method": "fallback"
                }
        
        self._save_results(results, "api")
        return results
    
    def _save_manual_models(self, manual_models: Dict[str, List[str]]) -> Dict[str, Dict]:
        """手動入力されたモデルを保存"""
        results = {}
        
        for service_name, models in manual_models.items():
            if service_name in self.ai_services:
                results[service_name] = {
                    "models": models,
                    "last_updated": datetime.now().isoformat(),
                    "method": "manual"
                }
                logger.info(f"✅ {service_name}: 手動で{len(models)}個のモデルを設定")
            else:
                logger.warning(f"⚠️ {service_name}: 不明なサービス")
        
        self._save_results(results, "manual")
        return results
    
    def _get_cached_models(self, service: Optional[str] = None) -> Dict[str, Dict]:
        """キャッシュされたモデル情報を取得"""
        results = {}
        
        # 全ての保存ファイルを確認
        cache_files = [
            ("browser_session", "ai_models_browser_session.json"),
            ("api", "ai_models_api.json"),
            ("manual", "ai_models_manual.json"),
            ("latest", "ai_models_latest.json")  # 既存のAIModelUpdaterのファイル
        ]
        
        for method, filename in cache_files:
            filepath = os.path.join(self.config_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # データ構造に応じて処理
                    if "results" in data:
                        cache_results = data["results"]
                    elif "ai_services" in data:
                        # 既存のai_models_latest.jsonの形式
                        cache_results = {}
                        for svc, info in data["ai_services"].items():
                            cache_results[svc] = {
                                "models": info.get("models", []),
                                "last_updated": data.get("last_updated"),
                                "method": method
                            }
                    else:
                        cache_results = data
                    
                    # 結果をマージ
                    if service:
                        if service in cache_results:
                            results[service] = cache_results[service]
                            break
                    else:
                        for svc, info in cache_results.items():
                            if svc not in results or self._is_newer(info, results[svc]):
                                results[svc] = info
                                
                except Exception as e:
                    logger.warning(f"⚠️ キャッシュファイル読み込みエラー ({filename}): {e}")
        
        if not results:
            logger.warning("⚠️ キャッシュが見つかりません。デフォルト値を使用します。")
            services_to_return = [service] if service else self.ai_services.keys()
            for svc in services_to_return:
                if svc in self.ai_services:
                    results[svc] = {
                        "models": self.ai_services[svc]["default_models"],
                        "method": "default",
                        "last_updated": datetime.now().isoformat()
                    }
        
        return results
    
    def _is_newer(self, info1: Dict, info2: Dict) -> bool:
        """info1がinfo2より新しいかチェック"""
        try:
            time1 = datetime.fromisoformat(info1.get("last_updated", ""))
            time2 = datetime.fromisoformat(info2.get("last_updated", ""))
            return time1 > time2
        except:
            return False
    
    def _save_results(self, results: Dict, method: str):
        """結果をファイルに保存"""
        filename = f"ai_models_{method}.json"
        filepath = os.path.join(self.config_dir, filename)
        
        try:
            output_data = {
                "method": method,
                "last_updated": datetime.now().isoformat(),
                "results": results
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ 結果を{filepath}に保存しました")
            
        except Exception as e:
            logger.error(f"❌ 結果の保存エラー: {e}")
    
    def get_chrome_profile_paths(self) -> Dict[str, str]:
        """各OSのChromeプロファイルパスを返す"""
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


# 同期的なラッパー関数（GUI用）
def fetch_models_sync(
    method: Literal["browser", "api", "manual", "cached"] = "browser",
    **kwargs
) -> Dict[str, Dict]:
    """同期的にモデル情報を取得"""
    fetcher = UnifiedModelFetcher()
    return asyncio.run(fetcher.fetch_models(method, **kwargs))


# 既存の関数との互換性のため
def fetch_models_browser_session() -> Dict[str, Dict]:
    """ブラウザセッション方式で取得（既存コードとの互換性）"""
    return fetch_models_sync("browser")


if __name__ == "__main__":
    # テスト実行
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 統合モデル取得ツール")
    print("\n取得方法を選択してください:")
    print("1. ブラウザセッション（Chrome使用）")
    print("2. API（OpenAI APIキーが必要）")
    print("3. キャッシュから取得")
    
    choice = input("\n選択 (1-3): ").strip()
    
    if choice == "1":
        print("\n📌 注意: Chromeにログイン済みである必要があります")
        results = fetch_models_sync("browser")
    elif choice == "2":
        api_key = input("OpenAI APIキーを入力: ").strip()
        results = fetch_models_sync("api", api_keys={"chatgpt": api_key})
    elif choice == "3":
        results = fetch_models_sync("cached")
    else:
        print("無効な選択です")
        sys.exit(1)
    
    print("\n📊 取得結果:")
    for service, data in results.items():
        if "error" in data:
            print(f"❌ {service}: エラー - {data['error']}")
        else:
            print(f"✅ {service}: {data['models']} (method: {data.get('method', 'unknown')})")