"""
Playwright検索モジュール

最新のWeb情報を動的に取得するためのPlaywright検索機能を提供します。
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not installed. Web search functionality will be limited.")


class PlaywrightSearcher:
    """Playwright検索クラス"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        初期化
        
        Args:
            headless: ヘッドレスモードで実行するか
            timeout: タイムアウト時間（ミリ秒）
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.logger = logging.getLogger(__name__)
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required for web search functionality. Install with: pip install playwright")
            
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self.close()
        
    async def start(self):
        """ブラウザを起動"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # 画像読み込み無効化で高速化
                ]
            )
            
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 720},
                java_script_enabled=True
            )
            
            self.logger.info("Playwright browser started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Playwright browser: {e}")
            raise
            
    async def close(self):
        """ブラウザを閉じる"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
                
            self.logger.info("Playwright browser closed")
            
        except Exception as e:
            self.logger.error(f"Error closing Playwright browser: {e}")
            
    async def search_ai_model_info(self, ai_service: str) -> Dict[str, Any]:
        """
        AI サービスの最新モデル情報を検索
        
        Args:
            ai_service: AIサービス名（chatgpt, claude, gemini, etc.）
            
        Returns:
            最新モデル情報の辞書
        """
        search_configs = {
            "chatgpt": {
                "urls": [
                    "https://platform.openai.com/docs/models",
                    "https://chat.openai.com"
                ],
                "search_terms": ["GPT-4", "GPT-4o", "GPT-4.1", "models", "latest"]
            },
            "claude": {
                "urls": [
                    "https://docs.anthropic.com/en/docs/about-claude/models",
                    "https://claude.ai"
                ],
                "search_terms": ["Claude 3.5", "Sonnet", "Haiku", "models", "latest"]
            },
            "gemini": {
                "urls": [
                    "https://ai.google.dev/gemini-api/docs/models",
                    "https://gemini.google.com"
                ],
                "search_terms": ["Gemini 2.0", "Flash", "Pro", "models", "latest"]
            },
            "perplexity": {
                "urls": [
                    "https://www.perplexity.ai",
                    "https://docs.perplexity.ai"
                ],
                "search_terms": ["models", "Pro", "search modes", "latest"]
            },
            "genspark": {
                "urls": [
                    "https://genspark.ai",
                    "https://www.genspark.ai"
                ],
                "search_terms": ["models", "Sparkpage", "features", "latest"]
            }
        }
        
        config = search_configs.get(ai_service.lower())
        if not config:
            raise ValueError(f"Unsupported AI service: {ai_service}")
            
        results = {}
        
        for url in config["urls"]:
            try:
                page_info = await self._scrape_page(url, config["search_terms"])
                if page_info:
                    results[url] = page_info
                    
            except Exception as e:
                self.logger.warning(f"Failed to scrape {url}: {e}")
                continue
                
        return {
            "ai_service": ai_service,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
    async def _scrape_page(self, url: str, search_terms: List[str]) -> Dict[str, Any]:
        """
        ページをスクレイピング
        
        Args:
            url: スクレイピング対象URL
            search_terms: 検索キーワード
            
        Returns:
            スクレイピング結果
        """
        page = await self.context.new_page()
        
        try:
            # ページに移動
            await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
            await page.wait_for_timeout(2000)  # ページの読み込み待機
            
            # ページタイトルを取得
            title = await page.title()
            
            # メタ情報を取得
            meta_description = await page.get_attribute('meta[name="description"]', 'content') or ""
            
            # 検索キーワードに関連するテキストを抽出
            relevant_content = await self._extract_relevant_content(page, search_terms)
            
            # モデル情報を特定のセレクターから抽出を試行
            model_info = await self._extract_model_info(page, url)
            
            return {
                "url": url,
                "title": title,
                "meta_description": meta_description,
                "relevant_content": relevant_content,
                "model_info": model_info,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return None
            
        finally:
            await page.close()
            
    async def _extract_relevant_content(self, page: Page, search_terms: List[str]) -> List[str]:
        """関連コンテンツを抽出"""
        relevant_content = []
        
        try:
            # ページ内のテキストを取得
            page_text = await page.evaluate("() => document.body.innerText")
            
            # 検索キーワードに関連する段落を抽出
            paragraphs = page_text.split('\n')
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if len(paragraph) > 20:  # 短すぎる段落は除外
                    for term in search_terms:
                        if term.lower() in paragraph.lower():
                            relevant_content.append(paragraph)
                            break
                            
            # 重複を除去し、最大10件に制限
            relevant_content = list(dict.fromkeys(relevant_content))[:10]
            
        except Exception as e:
            self.logger.warning(f"Error extracting relevant content: {e}")
            
        return relevant_content
        
    async def _extract_model_info(self, page: Page, url: str) -> Dict[str, Any]:
        """モデル情報を抽出"""
        model_info = {}
        
        try:
            # URL別の特定セレクターでモデル情報を抽出
            if "openai.com" in url:
                model_info = await self._extract_openai_models(page)
            elif "anthropic.com" in url or "claude.ai" in url:
                model_info = await self._extract_claude_models(page)
            elif "google" in url and ("gemini" in url or "ai.google.dev" in url):
                model_info = await self._extract_gemini_models(page)
            elif "perplexity.ai" in url:
                model_info = await self._extract_perplexity_models(page)
            elif "genspark" in url:
                model_info = await self._extract_genspark_models(page)
                
        except Exception as e:
            self.logger.warning(f"Error extracting model info from {url}: {e}")
            
        return model_info
        
    async def _extract_openai_models(self, page: Page) -> Dict[str, Any]:
        """OpenAI モデル情報を抽出"""
        models = {}
        
        try:
            # モデル一覧のテーブルやリストを探す
            model_elements = await page.query_selector_all('h2, h3, strong, .model-name, [data-model]')
            
            for element in model_elements[:20]:  # 最大20要素まで
                text = await element.inner_text()
                if any(keyword in text.lower() for keyword in ['gpt-4', 'gpt-3.5', 'turbo', 'o1']):
                    models[text.strip()] = {"detected": True}
                    
        except Exception as e:
            self.logger.debug(f"Error extracting OpenAI models: {e}")
            
        return models
        
    async def _extract_claude_models(self, page: Page) -> Dict[str, Any]:
        """Claude モデル情報を抽出"""
        models = {}
        
        try:
            model_elements = await page.query_selector_all('h2, h3, strong, .model-name')
            
            for element in model_elements[:20]:
                text = await element.inner_text()
                if any(keyword in text.lower() for keyword in ['claude', 'sonnet', 'haiku', 'opus']):
                    models[text.strip()] = {"detected": True}
                    
        except Exception as e:
            self.logger.debug(f"Error extracting Claude models: {e}")
            
        return models
        
    async def _extract_gemini_models(self, page: Page) -> Dict[str, Any]:
        """Gemini モデル情報を抽出"""
        models = {}
        
        try:
            model_elements = await page.query_selector_all('h2, h3, strong, .model-name')
            
            for element in model_elements[:20]:
                text = await element.inner_text()
                if any(keyword in text.lower() for keyword in ['gemini', 'flash', 'pro', 'ultra']):
                    models[text.strip()] = {"detected": True}
                    
        except Exception as e:
            self.logger.debug(f"Error extracting Gemini models: {e}")
            
        return models
        
    async def _extract_perplexity_models(self, page: Page) -> Dict[str, Any]:
        """Perplexity モデル情報を抽出"""
        models = {}
        
        try:
            # Perplexity の場合はモード情報も含める
            elements = await page.query_selector_all('h2, h3, strong, .feature-name')
            
            for element in elements[:20]:
                text = await element.inner_text()
                if any(keyword in text.lower() for keyword in ['pro', 'search', 'research', 'mode']):
                    models[text.strip()] = {"detected": True}
                    
        except Exception as e:
            self.logger.debug(f"Error extracting Perplexity models: {e}")
            
        return models
        
    async def _extract_genspark_models(self, page: Page) -> Dict[str, Any]:
        """Genspark モデル情報を抽出"""
        models = {}
        
        try:
            elements = await page.query_selector_all('h2, h3, strong, .feature-name')
            
            for element in elements[:20]:
                text = await element.inner_text()
                if any(keyword in text.lower() for keyword in ['sparkpage', 'agent', 'model', 'feature']):
                    models[text.strip()] = {"detected": True}
                    
        except Exception as e:
            self.logger.debug(f"Error extracting Genspark models: {e}")
            
        return models
        
    async def batch_search_ai_services(self, ai_services: List[str]) -> Dict[str, Any]:
        """
        複数のAIサービス情報を一括検索
        
        Args:
            ai_services: AIサービス名のリスト
            
        Returns:
            各AIサービスの情報を含む辞書
        """
        results = {}
        
        for ai_service in ai_services:
            try:
                self.logger.info(f"Searching information for {ai_service}")
                service_info = await self.search_ai_model_info(ai_service)
                results[ai_service] = service_info
                
                # リクエスト間隔を空ける
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Failed to search {ai_service}: {e}")
                results[ai_service] = {"error": str(e)}
                
        return {
            "batch_search_results": results,
            "completed_at": datetime.now().isoformat()
        }
        
    def save_search_results(self, results: Dict[str, Any], file_path: str = None):
        """検索結果をJSONファイルに保存"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"ai_search_results_{timestamp}.json"
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Search results saved to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to save search results: {e}")
            return None


# 同期ラッパー関数
def search_ai_models_sync(ai_services: List[str], headless: bool = True) -> Dict[str, Any]:
    """
    同期版AI検索関数
    
    Args:
        ai_services: 検索するAIサービスのリスト
        headless: ヘッドレスモードで実行するか
        
    Returns:
        検索結果
    """
    async def _async_search():
        async with PlaywrightSearcher(headless=headless) as searcher:
            return await searcher.batch_search_ai_services(ai_services)
            
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        return loop.run_until_complete(_async_search())
    finally:
        if loop.is_running():
            loop.close()


if __name__ == "__main__":
    # テスト実行
    async def main():
        ai_services = ["chatgpt", "claude", "gemini"]
        
        async with PlaywrightSearcher(headless=True) as searcher:
            results = await searcher.batch_search_ai_services(ai_services)
            
            # 結果を保存
            file_path = searcher.save_search_results(results)
            print(f"Search completed. Results saved to: {file_path}")
            
            # 結果の一部を表示
            for service, info in results["batch_search_results"].items():
                print(f"\n=== {service} ===")
                if "error" in info:
                    print(f"Error: {info['error']}")
                else:
                    print(f"Results found: {len(info.get('results', {}))}")
                    
    # 実行
    asyncio.run(main())