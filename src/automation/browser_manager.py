"""
ブラウザ管理モジュール

Playwrightを使用したブラウザ自動化の管理
既存のChromeプロファイルを使用して手動ログイン状態を維持
"""

import asyncio
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from src.utils.logger import logger
from src.utils.config_manager import config_manager


class BrowserManager:
    """Playwrightブラウザ管理クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        ブラウザ管理の初期化
        
        Args:
            config: ブラウザ設定辞書
        """
        self.config = config or config_manager.get('automation', {})
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        
        # ユーザーデータディレクトリの設定
        self.user_data_dir = self._get_chrome_user_data_dir()
        logger.info(f"Chrome ユーザーデータディレクトリ: {self.user_data_dir}")

    def _get_chrome_user_data_dir(self) -> str:
        """
        OS別のChromeユーザーデータディレクトリを取得
        
        Returns:
            str: Chromeユーザーデータディレクトリのパス
        """
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return str(Path.home() / "Library/Application Support/Google/Chrome")
        elif system == "Windows":
            return str(Path.home() / "AppData/Local/Google/Chrome/User Data")
        elif system == "Linux":
            return str(Path.home() / ".config/google-chrome")
        else:
            logger.warning(f"未対応のOS: {system}")
            return str(Path.home() / ".chrome")

    async def launch_browser(self) -> Browser:
        """
        ブラウザを起動
        
        Returns:
            Browser: Playwrightブラウザインスタンス
        """
        try:
            self.playwright = await async_playwright().start()
            
            # ブラウザオプションの設定
            browser_options = self._get_browser_options()
            
            # Chromiumブラウザを起動
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                **browser_options
            )
            
            logger.info("ブラウザを起動しました")
            return self.browser
            
        except Exception as e:
            logger.error(f"ブラウザ起動に失敗しました: {e}")
            raise

    def _get_browser_options(self) -> Dict[str, Any]:
        """
        ブラウザ起動オプションを取得
        
        Returns:
            Dict[str, Any]: ブラウザオプション
        """
        # Cloudflare対策を考慮したオプション
        return {
            "headless": self.config.get('headless', False),  # 手動ログインのためヘッドレスは無効
            "slow_mo": self.config.get('slow_mo', 100),  # 人間らしい操作速度
            "viewport": {"width": 1280, "height": 720},
            "locale": "ja-JP",
            "timezone_id": "Asia/Tokyo",
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        }

    async def create_new_page(self) -> Page:
        """
        新しいページを作成
        
        Returns:
            Page: Playwrightページインスタンス
        """
        if not self.browser:
            await self.launch_browser()
            
        page = await self.browser.new_page()
        
        # ページの基本設定
        await self._setup_page(page)
        
        logger.info("新しいページを作成しました")
        return page

    async def _setup_page(self, page: Page):
        """
        ページの基本設定
        
        Args:
            page: 設定するページ
        """
        # ユーザーエージェントの設定（より自然なもの）
        await page.set_extra_http_headers({
            "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8"
        })
        
        # JavaScript無効化やその他の検知を回避
        await page.add_init_script("""
            // WebDriver検知を回避
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // プラグインの偽装
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // 言語設定
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ja-JP', 'ja', 'en'],
            });
        """)

    async def take_screenshot(self, page: Page, path: str) -> bool:
        """
        スクリーンショットを撮影
        
        Args:
            page: 撮影するページ
            path: 保存先パス
            
        Returns:
            bool: 撮影成功の可否
        """
        try:
            # スクリーンショット保存ディレクトリの作成
            screenshot_dir = Path(path).parent
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            await page.screenshot(path=path, full_page=True)
            logger.info(f"スクリーンショットを保存しました: {path}")
            return True
            
        except Exception as e:
            logger.error(f"スクリーンショット撮影に失敗しました: {e}")
            return False

    async def wait_for_network_idle(self, page: Page, timeout: int = 30000):
        """
        ネットワークアイドル状態まで待機
        
        Args:
            page: 待機するページ
            timeout: タイムアウト時間（ミリ秒）
        """
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            logger.debug("ネットワークアイドル状態を確認しました")
        except Exception as e:
            logger.warning(f"ネットワークアイドル待機中にタイムアウト: {e}")

    async def random_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """
        ランダムな待機時間（人間らしい操作のため）
        
        Args:
            min_ms: 最小待機時間（ミリ秒）
            max_ms: 最大待機時間（ミリ秒）
        """
        import random
        delay = random.randint(min_ms, max_ms) / 1000.0
        await asyncio.sleep(delay)
        logger.debug(f"ランダム待機: {delay:.2f}秒")

    async def close_browser(self):
        """ブラウザを終了"""
        try:
            if self.browser:
                await self.browser.close()
                logger.info("ブラウザを終了しました")
                
            if self.playwright:
                await self.playwright.stop()
                logger.info("Playwrightを終了しました")
                
        except Exception as e:
            logger.error(f"ブラウザ終了時にエラーが発生しました: {e}")
        finally:
            self.browser = None
            self.context = None
            self.playwright = None

    async def __aenter__(self):
        """非同期コンテキストマネージャー（enter）"""
        await self.launch_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー（exit）"""
        await self.close_browser()