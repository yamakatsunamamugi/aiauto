"""
AIハンドラー基底クラス

全AIサービス共通のインターフェースと基本機能を提供
手動ログイン前提でセッション確認とエラーハンドリングを実装
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.logger import logger, log_operation
from src.utils.config_manager import config_manager


class SessionExpiredError(Exception):
    """セッション切れエラー"""
    pass


class AIServiceError(Exception):
    """AIサービス固有のエラー"""
    pass


class BaseAIHandler(ABC):
    """AIハンドラー抽象基底クラス"""
    
    # 各サブクラスで定義する必要がある定数
    SERVICE_NAME = "base"
    SERVICE_URL = ""
    
    def __init__(self, page: Page, config: Optional[Dict[str, Any]] = None):
        """
        ハンドラーの初期化
        
        Args:
            page: Playwrightページインスタンス
            config: サービス固有の設定
        """
        self.page = page
        self.config = config or {}
        self.service_name = self.SERVICE_NAME
        self.service_url = self.SERVICE_URL
        
        # タイムアウト設定
        self.default_timeout = self.config.get('timeout', 30000)
        self.wait_timeout = self.config.get('wait_timeout', 60000)
        
        logger.info(f"{self.service_name}ハンドラーを初期化しました")

    @abstractmethod
    async def login_check(self) -> bool:
        """
        ログイン状態確認（各サービスで実装）
        
        Returns:
            bool: ログイン済みかどうか
        """
        pass

    @abstractmethod
    async def get_input_selector(self) -> str:
        """
        入力欄のセレクターを取得（各サービスで実装）
        
        Returns:
            str: 入力欄のCSSセレクター
        """
        pass

    @abstractmethod
    async def get_submit_selector(self) -> str:
        """
        送信ボタンのセレクターを取得（各サービスで実装）
        
        Returns:
            str: 送信ボタンのCSSセレクター
        """
        pass

    @abstractmethod
    async def get_response_selector(self) -> str:
        """
        応答エリアのセレクターを取得（各サービスで実装）
        
        Returns:
            str: 応答エリアのCSSセレクター
        """
        pass

    @abstractmethod
    async def wait_for_response_complete(self) -> bool:
        """
        応答完了まで待機（各サービスで実装）
        
        Returns:
            bool: 応答完了したかどうか
        """
        pass

    async def navigate_to_service(self) -> bool:
        """
        サービスサイトにナビゲート
        
        Returns:
            bool: ナビゲーション成功の可否
        """
        try:
            self._log_operation(f"{self.service_name}にナビゲート開始")
            
            await self.page.goto(self.service_url, wait_until="networkidle")
            await asyncio.sleep(2)  # 追加の安定化待機
            
            self._log_operation(f"{self.service_name}にナビゲート完了")
            return True
            
        except Exception as e:
            logger.error(f"{self.service_name}へのナビゲートに失敗: {e}")
            return False

    async def ensure_logged_in(self) -> bool:
        """
        ログイン状態確認とユーザー誘導
        
        Returns:
            bool: ログイン状態
        """
        try:
            if await self.login_check():
                logger.info(f"{self.service_name}: ログイン状態を確認しました")
                return True
            else:
                logger.error(f"{self.service_name}: ログインしていません")
                logger.info(f"手動で{self.service_name}にログインしてから再実行してください")
                raise SessionExpiredError(f"{self.service_name}にログインが必要です")
                
        except Exception as e:
            logger.error(f"{self.service_name}のログイン状態確認でエラー: {e}")
            return False

    async def input_text(self, text: str) -> bool:
        """
        テキストを入力
        
        Args:
            text: 入力するテキスト
            
        Returns:
            bool: 入力成功の可否
        """
        try:
            self._log_operation(f"テキスト入力開始: {len(text)}文字")
            
            # 入力欄を取得
            input_selector = await self.get_input_selector()
            await self.page.wait_for_selector(input_selector, timeout=self.default_timeout)
            
            # 既存のテキストをクリア
            await self.page.fill(input_selector, "")
            await asyncio.sleep(0.5)
            
            # 人間らしい速度でテキスト入力
            await self.page.type(input_selector, text, delay=50)
            await asyncio.sleep(1)
            
            self._log_operation("テキスト入力完了")
            return True
            
        except PlaywrightTimeoutError:
            logger.error(f"{self.service_name}: 入力欄が見つかりません（タイムアウト）")
            return False
        except Exception as e:
            logger.error(f"{self.service_name}: テキスト入力でエラー: {e}")
            return False

    async def submit_request(self) -> bool:
        """
        リクエストを送信
        
        Returns:
            bool: 送信成功の可否
        """
        try:
            self._log_operation("リクエスト送信開始")
            
            # 送信ボタンを取得
            submit_selector = await self.get_submit_selector()
            await self.page.wait_for_selector(submit_selector, timeout=self.default_timeout)
            
            # ボタンがクリック可能になるまで待機
            await self.page.wait_for_selector(f"{submit_selector}:not([disabled])", timeout=self.default_timeout)
            
            # 送信ボタンをクリック
            await self.page.click(submit_selector)
            await asyncio.sleep(2)  # 送信処理の安定化待機
            
            self._log_operation("リクエスト送信完了")
            return True
            
        except PlaywrightTimeoutError:
            logger.error(f"{self.service_name}: 送信ボタンが見つかりません（タイムアウト）")
            return False
        except Exception as e:
            logger.error(f"{self.service_name}: リクエスト送信でエラー: {e}")
            return False

    async def extract_response(self) -> Optional[str]:
        """
        応答テキストを抽出
        
        Returns:
            Optional[str]: 応答テキスト（取得失敗時はNone）
        """
        try:
            self._log_operation("応答テキスト抽出開始")
            
            # 応答エリアを取得
            response_selector = await self.get_response_selector()
            await self.page.wait_for_selector(response_selector, timeout=self.default_timeout)
            
            # 最新の応答を取得
            response_elements = await self.page.query_selector_all(response_selector)
            if not response_elements:
                logger.warning(f"{self.service_name}: 応答要素が見つかりません")
                return None
                
            # 最後の応答要素のテキストを取得
            latest_response = response_elements[-1]
            response_text = await latest_response.text_content()
            
            if response_text:
                response_text = response_text.strip()
                self._log_operation(f"応答テキスト抽出完了: {len(response_text)}文字")
                return response_text
            else:
                logger.warning(f"{self.service_name}: 応答テキストが空です")
                return None
                
        except PlaywrightTimeoutError:
            logger.error(f"{self.service_name}: 応答エリアが見つかりません（タイムアウト）")
            return None
        except Exception as e:
            logger.error(f"{self.service_name}: 応答テキスト抽出でエラー: {e}")
            return None

    async def process_request(self, input_text: str) -> Optional[str]:
        """
        一連の処理を実行（メインメソッド）
        
        Args:
            input_text: 入力するテキスト
            
        Returns:
            Optional[str]: AI応答テキスト（エラー時はNone）
        """
        try:
            self._log_operation(f"{self.service_name}でのリクエスト処理開始")
            
            # 1. ログイン状態確認
            if not await self.ensure_logged_in():
                return None
            
            # 2. サービスサイトにナビゲート
            if not await self.navigate_to_service():
                return None
            
            # 3. テキスト入力
            if not await self.input_text(input_text):
                return None
            
            # 4. リクエスト送信
            if not await self.submit_request():
                return None
            
            # 5. 応答完了まで待機
            if not await self.wait_for_response_complete():
                logger.error(f"{self.service_name}: 応答完了の待機に失敗")
                return None
            
            # 6. 応答テキスト抽出
            response_text = await self.extract_response()
            
            if response_text:
                self._log_operation(f"{self.service_name}でのリクエスト処理完了")
                return response_text
            else:
                logger.error(f"{self.service_name}: 応答テキストの取得に失敗")
                return None
                
        except SessionExpiredError:
            logger.error(f"{self.service_name}: セッション切れのため処理を中断")
            raise
        except Exception as e:
            logger.error(f"{self.service_name}: リクエスト処理でエラー: {e}")
            return None

    def _log_operation(self, operation: str):
        """
        操作ログの出力
        
        Args:
            operation: 操作内容
        """
        logger.info(f"[{self.service_name}] {operation}")

    async def _handle_error(self, error: Exception, context: str = ""):
        """
        エラーハンドリング
        
        Args:
            error: 発生したエラー
            context: エラーが発生したコンテキスト
        """
        error_msg = f"{self.service_name}: {context} - {str(error)}"
        logger.error(error_msg)
        
        # スクリーンショットを撮影（デバッグ用）
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"logs/error_{self.service_name}_{timestamp}.png"
            await self.page.screenshot(path=screenshot_path)
            logger.info(f"エラー時のスクリーンショットを保存: {screenshot_path}")
        except Exception as screenshot_error:
            logger.warning(f"スクリーンショット撮影に失敗: {screenshot_error}")

    async def get_available_models(self) -> list[str]:
        """
        利用可能なモデル一覧を取得（サブクラスでオーバーライド可能）
        
        Returns:
            list[str]: モデル名のリスト
        """
        return ["default"]

    async def set_model(self, model_name: str) -> bool:
        """
        使用モデルを設定（サブクラスでオーバーライド可能）
        
        Args:
            model_name: 設定するモデル名
            
        Returns:
            bool: 設定成功の可否
        """
        logger.info(f"{self.service_name}: モデル設定はサポートされていません")
        return True