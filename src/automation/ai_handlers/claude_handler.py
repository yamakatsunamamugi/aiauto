"""
Claudeハンドラー

Claude (https://claude.ai) の自動操作を実装
手動ログイン前提でセッション状態を確認し、安全な自動化を提供
"""

import asyncio
from typing import Optional, List
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.logger import logger
from .base_handler import BaseAIHandler, SessionExpiredError


class ClaudeHandler(BaseAIHandler):
    """Claude自動操作ハンドラー"""

    SERVICE_NAME = "Claude"
    SERVICE_URL = "https://claude.ai"

    def __init__(self, page: Page, config: Optional[dict] = None):
        """
        Claudeハンドラーの初期化
        
        Args:
            page: Playwrightページインスタンス
            config: Claude固有の設定
        """
        super().__init__(page, config)
        logger.info(f"{self.SERVICE_NAME}ハンドラーを初期化しました")

    async def login_check(self) -> bool:
        """
        Claudeのログイン状態確認
        
        Returns:
            bool: ログイン済みかどうか
        """
        try:
            # Claudeサイトにアクセス
            current_url = self.page.url
            if "claude.ai" not in current_url:
                await self.page.goto(self.SERVICE_URL, wait_until="networkidle")
                await asyncio.sleep(3)

            # ログイン状態確認（複数パターン）
            login_indicators = [
                # チャット入力欄の存在確認（一般的なパターン）
                "textarea[placeholder*='message']",
                "textarea[placeholder*='Message']",
                "textarea[placeholder*='メッセージ']",
                # Claude特有のセレクター
                "[data-testid='chat-input']",
                ".ProseMirror",
                "div[contenteditable='true']",
                # 新しい会話ボタン
                "button:has-text('New Chat')",
                "button:has-text('新しい会話')"
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
                "button:has-text('ログイン')",
                "text=Sign in with Google",
                "text=Continue with Google",
                "[data-testid='login-button']",
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
            "textarea[placeholder*='message']",
            "textarea[placeholder*='Message']",
            "[data-testid='chat-input']",
            ".ProseMirror",
            "div[contenteditable='true']",
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

        return "textarea[placeholder*='message']"

    async def get_submit_selector(self) -> str:
        """
        送信ボタンのセレクターを取得
        
        Returns:
            str: 送信ボタンのCSSセレクター
        """
        selectors = [
            "[data-testid='send-button']",
            "button[aria-label*='Send']",
            "button[aria-label*='送信']",
            "button:has-text('Send')",
            "button svg",
            "button[type='submit']",
            ".send-button"
        ]

        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    logger.debug(f"{self.SERVICE_NAME}: 送信ボタンを発見: {selector}")
                    return selector
            except PlaywrightTimeoutError:
                continue

        return "[data-testid='send-button']"

    async def get_response_selector(self) -> str:
        """
        応答エリアのセレクターを取得
        
        Returns:
            str: 応答エリアのCSSセレクター
        """
        return "[data-is-streaming='false'] .font-claude-message, .message-content, .claude-message"

    async def wait_for_response_complete(self) -> bool:
        """
        Claudeの応答完了まで待機
        
        Returns:
            bool: 応答完了したかどうか
        """
        try:
            self._log_operation("応答完了待機開始")

            max_wait_time = self.wait_timeout // 1000
            start_time = asyncio.get_event_loop().time()

            while True:
                # ストリーミング状態をチェック
                streaming_indicators = [
                    "[data-is-streaming='true']",
                    ".streaming",
                    ".typing",
                    ".generating"
                ]

                is_streaming = False
                for indicator in streaming_indicators:
                    try:
                        element = await self.page.wait_for_selector(indicator, timeout=1000)
                        if element:
                            is_streaming = True
                            break
                    except PlaywrightTimeoutError:
                        continue

                # ストリーミングが終了している場合
                if not is_streaming:
                    # 送信ボタンが再度有効になっているかチェック
                    submit_selector = await self.get_submit_selector()
                    try:
                        button = await self.page.wait_for_selector(
                            f"{submit_selector}:not([disabled])", 
                            timeout=3000
                        )
                        if button:
                            # 応答エリアに新しいメッセージがあるかチェック
                            response_selector = await self.get_response_selector()
                            response_elements = await self.page.query_selector_all(response_selector)
                            
                            if response_elements:
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
                "button:has-text('Claude')",
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
                            if text and "claude" in text.lower():
                                models.append(text.strip())

                        # モデル選択を閉じる
                        await self.page.keyboard.press("Escape")

                        if models:
                            logger.info(f"{self.SERVICE_NAME}: 利用可能なモデル: {models}")
                            return models

                except PlaywrightTimeoutError:
                    continue

            # デフォルトモデル
            return ["Claude-3.5-Sonnet", "Claude-3-Opus", "Claude-3-Haiku"]

        except Exception as e:
            logger.error(f"{self.SERVICE_NAME}: モデル一覧取得でエラー: {e}")
            return ["Claude-3.5-Sonnet", "Claude-3-Opus", "Claude-3-Haiku"]

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
                "button:has-text('Claude')",
                "select[name*='model']"
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