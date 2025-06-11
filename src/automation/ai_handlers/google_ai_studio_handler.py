"""
Google AI Studioハンドラー

Google AI Studio (https://aistudio.google.com) の自動操作を実装
手動ログイン前提でセッション状態を確認し、安全な自動化を提供
"""

import asyncio
from typing import Optional, List
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.logger import logger
from .base_handler import BaseAIHandler, SessionExpiredError


class GoogleAIStudioHandler(BaseAIHandler):
    """Google AI Studio自動操作ハンドラー"""

    SERVICE_NAME = "Google AI Studio"
    SERVICE_URL = "https://aistudio.google.com"

    def __init__(self, page: Page, config: Optional[dict] = None):
        """
        Google AI Studioハンドラーの初期化
        
        Args:
            page: Playwrightページインスタンス
            config: Google AI Studio固有の設定
        """
        super().__init__(page, config)
        logger.info(f"{self.SERVICE_NAME}ハンドラーを初期化しました")

    async def login_check(self) -> bool:
        """
        Google AI Studioのログイン状態確認
        
        Returns:
            bool: ログイン済みかどうか
        """
        try:
            # Google AI Studioサイトにアクセス
            current_url = self.page.url
            if "aistudio.google.com" not in current_url:
                await self.page.goto(self.SERVICE_URL, wait_until="networkidle")
                await asyncio.sleep(3)

            # ログイン状態確認（複数パターン）
            login_indicators = [
                # プロンプト入力欄の存在確認
                "textarea[placeholder*='Enter a prompt']",
                "textarea[placeholder*='プロンプト']",
                "[data-testid='prompt-input']",
                ".prompt-textarea",
                ".input-area textarea",
                # Google AI Studio特有のセレクター
                ".chat-input",
                "[role='textbox']",
                ".studio-input"
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
                "button:has-text('Get started')",
                "button:has-text('ログイン')",
                "text=Sign in with Google",
                "text=Continue with Google",
                "[data-testid='sign-in-button']",
                ".sign-in-button"
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
            "textarea[placeholder*='Enter a prompt']",
            "textarea[placeholder*='プロンプト']",
            "[data-testid='prompt-input']",
            ".prompt-textarea",
            ".input-area textarea",
            ".chat-input",
            "[role='textbox']",
            ".studio-input",
            "textarea"
        ]

        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    logger.debug(f"{self.SERVICE_NAME}: 入力欄を発見: {selector}")
                    return selector
            except PlaywrightTimeoutError:
                continue

        return "textarea[placeholder*='Enter a prompt']"

    async def get_submit_selector(self) -> str:
        """
        送信ボタンのセレクターを取得
        
        Returns:
            str: 送信ボタンのCSSセレクター
        """
        selectors = [
            "[data-testid='run-button']",
            "[data-testid='send-button']",
            "button[aria-label*='Run']",
            "button[aria-label*='Send']",
            "button[aria-label*='Submit']",
            "button:has-text('Run')",
            "button:has-text('Send')",
            ".run-button",
            ".send-button",
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

        return "[data-testid='run-button']"

    async def get_response_selector(self) -> str:
        """
        応答エリアのセレクターを取得
        
        Returns:
            str: 応答エリアのCSSセレクター
        """
        return ".response-content, .output-area, .model-response, .result-content, [data-testid='response']"

    async def wait_for_response_complete(self) -> bool:
        """
        Google AI Studioの応答完了まで待機
        
        Returns:
            bool: 応答完了したかどうか
        """
        try:
            self._log_operation("応答完了待機開始")

            max_wait_time = self.wait_timeout // 1000
            start_time = asyncio.get_event_loop().time()

            while True:
                # 実行中インジケーターをチェック
                running_indicators = [
                    ".running",
                    ".executing",
                    ".loading",
                    ".generating",
                    "[data-testid='loading']",
                    ".progress-bar",
                    ".spinner"
                ]

                is_running = False
                for indicator in running_indicators:
                    try:
                        element = await self.page.wait_for_selector(indicator, timeout=1000)
                        if element:
                            is_running = True
                            break
                    except PlaywrightTimeoutError:
                        continue

                # 実行が終了している場合
                if not is_running:
                    # 実行ボタンが再度有効になっているかチェック
                    submit_selector = await self.get_submit_selector()
                    try:
                        button = await self.page.wait_for_selector(
                            f"{submit_selector}:not([disabled])", 
                            timeout=3000
                        )
                        
                        if button:
                            # 応答エリアに結果があるかチェック
                            response_selector = await self.get_response_selector()
                            response_elements = await self.page.query_selector_all(response_selector)
                            
                            if response_elements:
                                # 応答内容に実際のテキストがあるかチェック
                                for element in response_elements:
                                    text_content = await element.text_content()
                                    if text_content and len(text_content.strip()) > 5:
                                        await asyncio.sleep(2)  # 安定化待機
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
            # モデル選択要素を探す
            model_selectors = [
                "[data-testid='model-selector']",
                ".model-selector",
                ".model-dropdown",
                "button:has-text('Gemini')",
                "select[name*='model']",
                ".model-picker"
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
                            if text and ("gemini" in text.lower() or "model" in text.lower()):
                                models.append(text.strip())

                        # モデル選択を閉じる
                        await self.page.keyboard.press("Escape")

                        if models:
                            logger.info(f"{self.SERVICE_NAME}: 利用可能なモデル: {models}")
                            return models

                except PlaywrightTimeoutError:
                    continue

            # デフォルトモデル
            return ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini 1.0 Pro"]

        except Exception as e:
            logger.error(f"{self.SERVICE_NAME}: モデル一覧取得でエラー: {e}")
            return ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini 1.0 Pro"]

    async def set_model(self, model_name: str) -> bool:
        """
        使用モデルを設定
        
        Args:
            model_name: 設定するモデル名
            
        Returns:
            bool: 設定成功の可否
        """
        try:
            self._log_operation(f"モデル設定開始: {model_name}")

            # モデル選択要素を探す
            model_selectors = [
                "[data-testid='model-selector']",
                ".model-selector",
                ".model-dropdown",
                "button:has-text('Gemini')",
                "select[name*='model']",
                ".model-picker"
            ]

            for selector in model_selectors:
                try:
                    model_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if model_element:
                        await model_element.click()
                        await asyncio.sleep(1)

                        # 指定モデルを選択
                        model_option = await self.page.wait_for_selector(
                            f"[role='option']:has-text('{model_name}'), .model-option:has-text('{model_name}')",
                            timeout=5000
                        )

                        if model_option:
                            await model_option.click()
                            await asyncio.sleep(1)

                            self._log_operation(f"モデル設定完了: {model_name}")
                            return True

                except PlaywrightTimeoutError:
                    continue

            logger.warning(f"{self.SERVICE_NAME}: モデル '{model_name}' が見つかりません")
            return False

        except Exception as e:
            logger.error(f"{self.SERVICE_NAME}: モデル設定でエラー: {e}")
            return False

    async def set_parameters(self, temperature: float = None, max_tokens: int = None) -> bool:
        """
        モデルパラメータを設定（Google AI Studio特有の機能）
        
        Args:
            temperature: 温度パラメータ
            max_tokens: 最大トークン数
            
        Returns:
            bool: 設定成功の可否
        """
        try:
            self._log_operation("パラメータ設定開始")

            # 設定パネルを開く
            settings_selectors = [
                "[data-testid='settings-button']",
                ".settings-button",
                "button:has-text('Settings')",
                ".parameter-panel-toggle"
            ]

            for selector in settings_selectors:
                try:
                    settings_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if settings_button:
                        await settings_button.click()
                        await asyncio.sleep(1)
                        break
                except PlaywrightTimeoutError:
                    continue

            # Temperature設定
            if temperature is not None:
                temp_selectors = [
                    "input[name='temperature']",
                    "[data-testid='temperature-input']",
                    ".temperature-slider"
                ]
                
                for selector in temp_selectors:
                    try:
                        temp_input = await self.page.wait_for_selector(selector, timeout=2000)
                        if temp_input:
                            await temp_input.fill(str(temperature))
                            break
                    except PlaywrightTimeoutError:
                        continue

            # Max tokens設定
            if max_tokens is not None:
                token_selectors = [
                    "input[name='max_tokens']",
                    "[data-testid='max-tokens-input']",
                    ".max-tokens-input"
                ]
                
                for selector in token_selectors:
                    try:
                        token_input = await self.page.wait_for_selector(selector, timeout=2000)
                        if token_input:
                            await token_input.fill(str(max_tokens))
                            break
                    except PlaywrightTimeoutError:
                        continue

            self._log_operation("パラメータ設定完了")
            return True

        except Exception as e:
            logger.error(f"{self.SERVICE_NAME}: パラメータ設定でエラー: {e}")
            return False