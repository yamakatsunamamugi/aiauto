"""
ChatGPTハンドラー

ChatGPT (https://chat.openai.com) の自動操作を実装
手動ログイン前提でセッション状態を確認し、安全な自動化を提供
"""

import asyncio
from typing import Optional, List
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.logger import logger
from .base_handler import BaseAIHandler, SessionExpiredError


class ChatGPTHandler(BaseAIHandler):
    """ChatGPT自動操作ハンドラー"""
    
    SERVICE_NAME = "ChatGPT"
    SERVICE_URL = "https://chat.openai.com"
    
    def __init__(self, page: Page, config: Optional[dict] = None):
        """
        ChatGPTハンドラーの初期化
        
        Args:
            page: Playwrightページインスタンス
            config: ChatGPT固有の設定
        """
        super().__init__(page, config)
        
        # ChatGPT固有の設定
        self.model = config.get('model', 'gpt-4') if config else 'gpt-4'
        self.use_web_browsing = config.get('use_web_browsing', False) if config else False
        
        logger.info(f"ChatGPTハンドラーを初期化しました (モデル: {self.model})")

    async def login_check(self) -> bool:
        """
        ChatGPTのログイン状態確認
        
        Returns:
            bool: ログイン済みかどうか
        """
        try:
            # まずChatGPTサイトにアクセス
            current_url = self.page.url
            if "chat.openai.com" not in current_url:
                await self.page.goto(self.SERVICE_URL, wait_until="networkidle")
                await asyncio.sleep(3)
            
            # ログイン状態の確認方法（複数パターン）
            login_indicators = [
                # チャット入力欄の存在確認
                "[data-testid='prompt-textarea']",
                "textarea[placeholder*='Message']",
                "textarea[placeholder*='メッセージ']",
                # 新しいチャットボタン
                "button[aria-label*='New chat']",
                "[data-testid='new-chat-button']"
            ]
            
            for indicator in login_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=5000)
                    if element:
                        logger.info("ChatGPT: ログイン状態を確認しました")
                        return True
                except PlaywrightTimeoutError:
                    continue
            
            # ログイン画面の検出
            login_elements = [
                "button[data-testid='login-button']",
                "text=Log in",
                "text=ログイン",
                ".auth0-lock-widget",
                "[data-provider='auth0']"
            ]
            
            for login_element in login_elements:
                try:
                    element = await self.page.wait_for_selector(login_element, timeout=2000)
                    if element:
                        logger.warning("ChatGPT: ログイン画面が表示されています")
                        return False
                except PlaywrightTimeoutError:
                    continue
            
            logger.warning("ChatGPT: ログイン状態を確認できませんでした")
            return False
            
        except Exception as e:
            logger.error(f"ChatGPT: ログイン状態確認でエラー: {e}")
            return False

    async def get_input_selector(self) -> str:
        """
        入力欄のセレクターを取得
        
        Returns:
            str: 入力欄のCSSセレクター
        """
        # 複数のセレクターパターンを試行
        selectors = [
            "[data-testid='prompt-textarea']",
            "textarea[placeholder*='Message']",
            "textarea[placeholder*='メッセージ']",
            "#prompt-textarea",
            ".ProseMirror"
        ]
        
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    logger.debug(f"ChatGPT: 入力欄を発見: {selector}")
                    return selector
            except PlaywrightTimeoutError:
                continue
        
        # デフォルトセレクター
        return "[data-testid='prompt-textarea']"

    async def get_submit_selector(self) -> str:
        """
        送信ボタンのセレクターを取得
        
        Returns:
            str: 送信ボタンのCSSセレクター
        """
        # 複数のセレクターパターンを試行
        selectors = [
            "[data-testid='send-button']",
            "button[aria-label*='Send']",
            "button[aria-label*='送信']",
            "button:has-text('Send')",
            "svg[data-testid='send-button']",
            "[data-testid='fruitjuice-send-button']"
        ]
        
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    logger.debug(f"ChatGPT: 送信ボタンを発見: {selector}")
                    return selector
            except PlaywrightTimeoutError:
                continue
        
        # デフォルトセレクター
        return "[data-testid='send-button']"

    async def get_response_selector(self) -> str:
        """
        応答エリアのセレクターを取得
        
        Returns:
            str: 応答エリアのCSSセレクター
        """
        return "[data-message-author-role='assistant']"

    async def wait_for_response_complete(self) -> bool:
        """
        ChatGPTの応答完了まで待機
        
        Returns:
            bool: 応答完了したかどうか
        """
        try:
            self._log_operation("応答完了待機開始")
            
            # 送信ボタンが無効化される（送信中）ことを確認
            submit_selector = await self.get_submit_selector()
            
            # 送信ボタンが無効化されるまで少し待機
            await asyncio.sleep(2)
            
            # 送信ボタンが再び有効になるまで待機（応答完了の指標）
            max_wait_time = self.wait_timeout // 1000  # ミリ秒から秒に変換
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    # 送信ボタンが有効になっているかチェック
                    button = await self.page.wait_for_selector(
                        f"{submit_selector}:not([disabled])", 
                        timeout=5000
                    )
                    
                    if button:
                        # 追加の安定化待機
                        await asyncio.sleep(3)
                        
                        # 応答エリアに新しいメッセージがあるかチェック
                        response_selector = await self.get_response_selector()
                        response_elements = await self.page.query_selector_all(response_selector)
                        
                        if response_elements:
                            # 最新の応答がストリーミング完了しているかチェック
                            latest_response = response_elements[-1]
                            
                            # ストリーミング中のインジケーターがないかチェック
                            streaming_indicators = [
                                ".result-streaming",
                                ".cursor-blink",
                                "[data-testid='streaming-indicator']"
                            ]
                            
                            is_streaming = False
                            for indicator in streaming_indicators:
                                streaming_element = await latest_response.query_selector(indicator)
                                if streaming_element:
                                    is_streaming = True
                                    break
                            
                            if not is_streaming:
                                self._log_operation("応答完了を確認しました")
                                return True
                        
                        # 応答がまだない場合は続行
                        await asyncio.sleep(2)
                    
                except PlaywrightTimeoutError:
                    # タイムアウトの場合は続行
                    pass
                
                # 最大待機時間チェック
                elapsed_time = asyncio.get_event_loop().time() - start_time
                if elapsed_time > max_wait_time:
                    logger.warning(f"ChatGPT: 応答完了の待機がタイムアウトしました ({max_wait_time}秒)")
                    return False
                
                await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"ChatGPT: 応答完了待機でエラー: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """
        利用可能なモデル一覧を取得
        
        Returns:
            List[str]: モデル名のリスト
        """
        try:
            # モデル選択ボタンを探す
            model_selectors = [
                "[data-testid='model-switcher-button']",
                "button[aria-label*='model']",
                ".model-selector",
                "button:has-text('GPT')"
            ]
            
            for selector in model_selectors:
                try:
                    model_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if model_button:
                        await model_button.click()
                        await asyncio.sleep(1)
                        
                        # モデル一覧を取得
                        model_options = await self.page.query_selector_all(".model-option, [role='option']")
                        models = []
                        
                        for option in model_options:
                            text = await option.text_content()
                            if text and "gpt" in text.lower():
                                models.append(text.strip())
                        
                        # モデル選択を閉じる
                        await self.page.keyboard.press("Escape")
                        
                        if models:
                            logger.info(f"ChatGPT: 利用可能なモデル: {models}")
                            return models
                        
                except PlaywrightTimeoutError:
                    continue
            
            # デフォルトモデル
            return ["GPT-4", "GPT-3.5"]
            
        except Exception as e:
            logger.error(f"ChatGPT: モデル一覧取得でエラー: {e}")
            return ["GPT-4", "GPT-3.5"]

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
            
            # モデル選択ボタンを探す
            model_selectors = [
                "[data-testid='model-switcher-button']",
                "button[aria-label*='model']",
                ".model-selector",
                "button:has-text('GPT')"
            ]
            
            for selector in model_selectors:
                try:
                    model_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if model_button:
                        await model_button.click()
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
                            self.model = model_name
                            return True
                        
                except PlaywrightTimeoutError:
                    continue
            
            logger.warning(f"ChatGPT: モデル '{model_name}' が見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"ChatGPT: モデル設定でエラー: {e}")
            return False

    async def clear_conversation(self) -> bool:
        """
        会話をクリア（新しいチャット開始）
        
        Returns:
            bool: クリア成功の可否
        """
        try:
            self._log_operation("新しいチャット開始")
            
            # 新しいチャットボタンを探す
            new_chat_selectors = [
                "[data-testid='new-chat-button']",
                "button[aria-label*='New chat']",
                "button:has-text('New chat')",
                "a[href='/']",
                ".new-chat-button"
            ]
            
            for selector in new_chat_selectors:
                try:
                    new_chat_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if new_chat_button:
                        await new_chat_button.click()
                        await asyncio.sleep(2)
                        
                        self._log_operation("新しいチャット開始完了")
                        return True
                        
                except PlaywrightTimeoutError:
                    continue
            
            logger.warning("ChatGPT: 新しいチャットボタンが見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"ChatGPT: 会話クリアでエラー: {e}")
            return False