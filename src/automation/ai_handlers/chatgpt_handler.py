"""
ChatGPTハンドラー

ChatGPT (https://chat.openai.com) の自動操作を実装
手動ログイン前提でセッション状態を確認し、安全な自動化を提供
"""

import asyncio
import time
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
        ChatGPTのログイン状態確認（Cloudflare対策強化版）
        
        Returns:
            bool: ログイン済みかどうか
        """
        try:
            # まずChatGPTサイトにアクセス
            current_url = self.page.url
            if "chat.openai.com" not in current_url:
                logger.info("ChatGPTサイトにアクセス中...")
                await self.page.goto(self.SERVICE_URL, wait_until="networkidle")
                
                # Cloudflare待機
                await self._wait_for_cloudflare()
                
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

    async def process_text(self, text: str, model: Optional[str] = None, timeout: int = 60) -> str:
        """
        ChatGPTでテキストを処理
        
        Args:
            text: 処理するテキスト
            model: 使用するモデル（省略可）
            timeout: タイムアウト時間（秒）
            
        Returns:
            str: ChatGPTの応答テキスト
        """
        try:
            self._log_operation(f"ChatGPTでテキスト処理開始: {text[:50]}...")
            
            # ログイン状態確認
            if not await self.login_check():
                raise SessionExpiredError("ChatGPTにログインしていません")
            
            # 新しいチャットを開始（オプション）
            await self._start_new_chat()
            
            # モデル設定（指定された場合）
            if model:
                await self.set_model(model)
            
            # テキストを入力
            await self._input_text(text)
            
            # 送信
            await self._submit_message()
            
            # 応答完了を待機
            await self._wait_for_response_complete()
            
            # 最新の応答を取得
            response_text = await self._get_latest_response()
            
            if response_text:
                self._log_operation(f"ChatGPT応答取得成功: {len(response_text)}文字")
                return response_text
            else:
                raise Exception("ChatGPTから応答を取得できませんでした")
                
        except Exception as e:
            self._log_operation(f"ChatGPT処理エラー: {e}")
            raise

    async def _start_new_chat(self) -> bool:
        """新しいチャットを開始"""
        try:
            new_chat_selectors = [
                "button[aria-label*='New chat']",
                "[data-testid='new-chat-button']",
                "button:has-text('New chat')",
                ".new-chat-button"
            ]
            
            for selector in new_chat_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=3000)
                    if button:
                        await button.click()
                        await asyncio.sleep(1)
                        return True
                except PlaywrightTimeoutError:
                    continue
            
            # 新しいチャットボタンが見つからない場合はそのまま続行
            return True
            
        except Exception as e:
            logger.warning(f"ChatGPT: 新しいチャット開始でエラー: {e}")
            return True

    async def _input_text(self, text: str) -> bool:
        """テキストを入力欄に入力"""
        try:
            input_selector = await self.get_input_selector()
            input_element = await self.page.wait_for_selector(input_selector, timeout=10000)
            
            if input_element:
                # 入力欄をクリアして新しいテキストを入力
                await input_element.click()
                await self.page.keyboard.press("Control+a")  # 全選択
                await input_element.fill(text)
                await asyncio.sleep(0.5)
                return True
            else:
                raise Exception("入力欄が見つかりません")
                
        except Exception as e:
            logger.error(f"ChatGPT: テキスト入力でエラー: {e}")
            raise

    async def _submit_message(self) -> bool:
        """メッセージを送信"""
        try:
            submit_selectors = [
                "[data-testid='send-button']",
                "button[aria-label*='Send']",
                "button[type='submit']",
                ".send-button"
            ]
            
            for selector in submit_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=3000)
                    if button:
                        await button.click()
                        await asyncio.sleep(1)
                        return True
                except PlaywrightTimeoutError:
                    continue
            
            # ボタンが見つからない場合はEnterキーで送信
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"ChatGPT: メッセージ送信でエラー: {e}")
            raise

    async def _get_latest_response(self) -> str:
        """最新の応答を取得"""
        try:
            response_selectors = [
                "[data-message-author-role='assistant']:last-of-type",
                ".markdown:last-of-type",
                ".message.assistant:last-of-type",
                ".response-message:last-of-type"
            ]
            
            for selector in response_selectors:
                try:
                    response_element = await self.page.wait_for_selector(selector, timeout=5000)
                    if response_element:
                        response_text = await response_element.inner_text()
                        if response_text and response_text.strip():
                            return response_text.strip()
                except PlaywrightTimeoutError:
                    continue
            
            # 代替方法：ページから最後のアシスタントメッセージを探す
            messages = await self.page.query_selector_all("[role='presentation']")
            if messages:
                last_message = messages[-1]
                text = await last_message.inner_text()
                if text and text.strip():
                    return text.strip()
            
            raise Exception("応答テキストを取得できませんでした")
            
        except Exception as e:
            logger.error(f"ChatGPT: 応答取得でエラー: {e}")
            raise

    async def _wait_for_cloudflare(self):
        """Cloudflareチェック待機"""
        try:
            # Cloudflareページの検出
            cf_selectors = [
                '.cf-browser-verification',
                '#cf-wrapper',
                '.ray-id',
                'title:has-text("Just a moment")',
                '.cf-error-title'
            ]
            
            for selector in cf_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info("⏳ Cloudflareチェックを検出。待機中...")
                        
                        # ユーザーに手動対応を促す
                        logger.warning("🔐 Cloudflareチェックが検出されました。")
                        logger.warning("   ブラウザで手動でチェックを完了してください。")
                        logger.warning("   完了すると自動的に処理が継続されます。")
                        
                        # チェック完了まで待機（最大60秒）
                        try:
                            await self.page.wait_for_function(
                                "!document.querySelector('.cf-browser-verification') && !document.querySelector('#cf-wrapper')",
                                timeout=60000
                            )
                            logger.info("✅ Cloudflareチェック完了")
                            await asyncio.sleep(2)  # 安定化待ち
                        except PlaywrightTimeoutError:
                            logger.warning("⚠️ Cloudflareチェック待機タイムアウト。継続します...")
                        
                        break
                except PlaywrightTimeoutError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Cloudflareチェック: {e}")

    async def wait_for_manual_intervention(self, message: str, max_wait: int = 300):
        """手動介入待機（ログイン、Cloudflare等）"""
        logger.warning(f"🔐 手動介入が必要です: {message}")
        logger.warning("   ブラウザで操作を完了してから、任意のキーを押してください...")
        
        start_time = time.time()
        
        # シンプルな待機（実際のプロダクションではより高度な検出が必要）
        while time.time() - start_time < max_wait:
            try:
                # ページの変化を検出
                await asyncio.sleep(5)
                
                # ChatGPTのチャット画面に到達したかチェック
                chat_indicators = [
                    "[data-testid='prompt-textarea']",
                    "textarea[placeholder*='Message']",
                    ".new-chat-button"
                ]
                
                for indicator in chat_indicators:
                    try:
                        element = await self.page.wait_for_selector(indicator, timeout=2000)
                        if element:
                            logger.info("✅ ChatGPT操作画面に到達しました")
                            return True
                    except:
                        continue
                        
            except Exception as e:
                logger.debug(f"手動介入待機エラー: {e}")
                await asyncio.sleep(5)
        
        logger.warning(f"⚠️ 手動介入待機タイムアウト（{max_wait}秒）")
        return False

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