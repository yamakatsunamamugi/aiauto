"""
Gensparkハンドラー

Genspark (https://www.genspark.ai) の自動操作を実装
手動ログイン前提でセッション状態を確認し、安全な自動化を提供
"""

import asyncio
from typing import Optional, List
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.logger import logger
from .base_handler import BaseAIHandler, SessionExpiredError


class GensparkHandler(BaseAIHandler):
    """Genspark自動操作ハンドラー"""

    SERVICE_NAME = "Genspark"
    SERVICE_URL = "https://www.genspark.ai"

    def __init__(self, page: Page, config: Optional[dict] = None):
        """
        Gensparkハンドラーの初期化
        
        Args:
            page: Playwrightページインスタンス
            config: Genspark固有の設定
        """
        super().__init__(page, config)
        logger.info(f"{self.SERVICE_NAME}ハンドラーを初期化しました")

    async def login_check(self) -> bool:
        """
        Gensparkのログイン状態確認
        
        Returns:
            bool: ログイン済みかどうか
        """
        try:
            # Gensparkサイトにアクセス
            current_url = self.page.url
            if "genspark.ai" not in current_url:
                await self.page.goto(self.SERVICE_URL, wait_until="networkidle")
                await asyncio.sleep(3)

            # ログイン状態確認（複数パターン）
            login_indicators = [
                # 検索・質問入力欄の存在確認
                "input[placeholder*='Ask']",
                "input[placeholder*='Search']",
                "input[placeholder*='質問']",
                "input[placeholder*='検索']",
                "[data-testid='search-input']",
                "[data-testid='query-input']",
                # Genspark特有のセレクター
                ".search-box input",
                ".query-input",
                "textarea[placeholder*='question']"
            ]

            for indicator in login_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=5000)
                    if element:
                        logger.info(f"{self.SERVICE_NAME}: ログイン状態を確認しました")
                        return True
                except PlaywrightTimeoutError:
                    continue

            # ログイン画面の検出
            login_elements = [
                "button:has-text('Sign in')",
                "button:has-text('Log in')",
                "button:has-text('ログイン')",
                "text=Sign up",
                "text=Create account",
                "[data-testid='login-button']",
                ".login-button",
                ".auth-button"
            ]

            for login_element in login_elements:
                try:
                    element = await self.page.wait_for_selector(login_element, timeout=2000)
                    if element:
                        logger.warning(f"{self.SERVICE_NAME}: ログイン画面が表示されています")
                        return False
                except PlaywrightTimeoutError:
                    continue

            return False

        except Exception as e:
            logger.error(f"{self.SERVICE_NAME}: ログイン状態確認でエラー: {e}")
            return False

    async def get_input_selector(self) -> str:
        """
        入力欄のセレクターを取得
        
        Returns:
            str: 入力欄のCSSセレクター
        """
        selectors = [
            "input[placeholder*='Ask']",
            "input[placeholder*='Search']",
            "input[placeholder*='質問']",
            "input[placeholder*='検索']",
            "[data-testid='search-input']",
            "[data-testid='query-input']",
            ".search-box input",
            ".query-input",
            "textarea[placeholder*='question']",
            "input[type='search']"
        ]

        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    logger.debug(f"{self.SERVICE_NAME}: 入力欄を発見: {selector}")
                    return selector
            except PlaywrightTimeoutError:
                continue

        return "input[placeholder*='Ask']"

    async def get_submit_selector(self) -> str:
        """
        送信ボタンのセレクターを取得
        
        Returns:
            str: 送信ボタンのCSSセレクター
        """
        selectors = [
            "[data-testid='search-button']",
            "[data-testid='submit-button']",
            "button[aria-label*='Search']",
            "button[aria-label*='Send']",
            "button[aria-label*='Submit']",
            "button:has-text('Search')",
            "button:has-text('Ask')",
            ".search-button",
            ".submit-button",
            "button[type='submit']",
            "button svg"
        ]

        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    logger.debug(f"{self.SERVICE_NAME}: 送信ボタンを発見: {selector}")
                    return selector
            except PlaywrightTimeoutError:
                continue

        return "[data-testid='search-button']"

    async def get_response_selector(self) -> str:
        """
        応答エリアのセレクターを取得
        
        Returns:
            str: 応答エリアのCSSセレクター
        """
        return ".response-content, .search-results, .ai-response, .result-content, [data-testid='response']"

    async def wait_for_response_complete(self) -> bool:
        """
        Gensparkの応答完了まで待機
        
        Returns:
            bool: 応答完了したかどうか
        """
        try:
            self._log_operation("応答完了待機開始")

            max_wait_time = self.wait_timeout // 1000
            start_time = asyncio.get_event_loop().time()

            while True:
                # ローディングインジケーターをチェック
                loading_indicators = [
                    ".loading",
                    ".spinner",
                    ".searching",
                    ".generating",
                    "[data-testid='loading']",
                    ".progress-indicator"
                ]

                is_loading = False
                for indicator in loading_indicators:
                    try:
                        element = await self.page.wait_for_selector(indicator, timeout=1000)
                        if element:
                            is_loading = True
                            break
                    except PlaywrightTimeoutError:
                        continue

                # ローディングが終了している場合
                if not is_loading:
                    # 応答エリアに結果があるかチェック
                    response_selector = await self.get_response_selector()
                    response_elements = await self.page.query_selector_all(response_selector)
                    
                    if response_elements:
                        # 応答内容に実際のテキストがあるかチェック
                        for element in response_elements:
                            text_content = await element.text_content()
                            if text_content and len(text_content.strip()) > 10:
                                await asyncio.sleep(2)  # 安定化待機
                                self._log_operation("応答完了を確認しました")
                                return True
                    
                    # 送信ボタンが再度有効になっているかチェック
                    submit_selector = await self.get_submit_selector()
                    try:
                        button = await self.page.wait_for_selector(
                            f"{submit_selector}:not([disabled])", 
                            timeout=2000
                        )
                        if button and response_elements:
                            await asyncio.sleep(1)
                            self._log_operation("応答完了を確認しました")
                            return True
                    except PlaywrightTimeoutError:
                        pass

                # タイムアウトチェック
                elapsed_time = asyncio.get_event_loop().time() - start_time
                if elapsed_time > max_wait_time:
                    logger.warning(f"{self.SERVICE_NAME}: 応答完了の待機がタイムアウトしました")
                    return False

                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"{self.SERVICE_NAME}: 応答完了待機でエラー: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """
        利用可能なモデル一覧を取得
        
        Returns:
            List[str]: モデル名のリスト
        """
        try:
            # Gensparkはサーチエンジンなので、通常モデル選択はない
            # 設定やオプションがある場合のセレクター
            model_selectors = [
                "[data-testid='model-selector']",
                ".model-selector",
                ".settings-button",
                "button:has-text('Settings')",
                "select[name*='model']"
            ]

            for selector in model_selectors:
                try:
                    model_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if model_element:
                        await model_element.click()
                        await asyncio.sleep(1)

                        # モデル一覧を取得
                        model_options = await self.page.query_selector_all("[role='option'], .model-option")
                        models = []

                        for option in model_options:
                            text = await option.text_content()
                            if text:
                                models.append(text.strip())

                        # 設定を閉じる
                        await self.page.keyboard.press("Escape")

                        if models:
                            logger.info(f"{self.SERVICE_NAME}: 利用可能なオプション: {models}")
                            return models

                except PlaywrightTimeoutError:
                    continue

            # デフォルト（Gensparkは基本的にモデル選択なし）
            return ["Default Search"]

        except Exception as e:
            logger.error(f"{self.SERVICE_NAME}: モデル一覧取得でエラー: {e}")
            return ["Default Search"]

    async def set_model(self, model_name: str) -> bool:
        """
        使用モデルを設定
        
        Args:
            model_name: 設定するモデル名
            
        Returns:
            bool: 設定成功の可否
        """
        try:
            self._log_operation(f"設定変更開始: {model_name}")

            # Gensparkはサーチエンジンなので、通常モデル設定はない
            # 設定やオプションがある場合の処理
            settings_selectors = [
                "[data-testid='model-selector']",
                ".model-selector",
                ".settings-button",
                "button:has-text('Settings')"
            ]

            for selector in settings_selectors:
                try:
                    settings_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if settings_element:
                        await settings_element.click()
                        await asyncio.sleep(1)

                        # 指定オプションを選択
                        option = await self.page.wait_for_selector(
                            f"[role='option']:has-text('{model_name}'), .option:has-text('{model_name}')",
                            timeout=5000
                        )

                        if option:
                            await option.click()
                            await asyncio.sleep(1)

                            self._log_operation(f"設定変更完了: {model_name}")
                            return True

                except PlaywrightTimeoutError:
                    continue

            # Gensparkでは通常モデル設定がないため、成功として扱う
            logger.info(f"{self.SERVICE_NAME}: モデル設定はサポートされていません")
            return True

        except Exception as e:
            logger.error(f"{self.SERVICE_NAME}: 設定変更でエラー: {e}")
            return False