"""
リトライ管理モジュール

エラーハンドリング・リトライ機能の実装
指数バックオフとサーキットブレーカーパターンを使用
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.logger import logger
from src.automation.ai_handlers.base_handler import SessionExpiredError, AIServiceError


class ErrorType(Enum):
    """エラー種別"""
    NETWORK = "network"
    TIMEOUT = "timeout" 
    SESSION_EXPIRED = "session_expired"
    ELEMENT_NOT_FOUND = "element_not_found"
    AI_SERVICE = "ai_service"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """サーキットブレーカー状態"""
    CLOSED = "closed"      # 正常状態
    OPEN = "open"          # 開放状態（エラー多発）
    HALF_OPEN = "half_open"  # 半開状態（テスト中）


class RetryManager:
    """エラーハンドリング・リトライ管理クラス"""
    
    def __init__(self, 
                 max_retries: int = 5,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_multiplier: float = 2.0):
        """
        リトライ管理の初期化
        
        Args:
            max_retries: 最大リトライ回数
            base_delay: 基本遅延時間（秒）
            max_delay: 最大遅延時間（秒）
            backoff_multiplier: バックオフ倍率
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        
        # サーキットブレーカー設定
        self.circuit_states: Dict[str, CircuitState] = {}
        self.failure_counts: Dict[str, int] = {}
        self.last_failure_times: Dict[str, datetime] = {}
        self.failure_threshold = 3  # 連続失敗しきい値
        self.recovery_timeout = 300  # 回復タイムアウト（秒）
        
        logger.info("RetryManagerを初期化しました")

    async def retry_with_backoff(self, 
                                func: Callable,
                                service_name: str,
                                *args, 
                                **kwargs) -> Any:
        """
        指数バックオフによるリトライ実行
        
        Args:
            func: 実行する関数
            service_name: サービス名（サーキットブレーカー用）
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            Any: 関数の実行結果
            
        Raises:
            Exception: 最大リトライ回数到達時
        """
        # サーキットブレーカーチェック
        if not self._is_circuit_closed(service_name):
            raise AIServiceError(f"{service_name}: サーキットブレーカーが開いています")
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # 関数実行
                result = await func(*args, **kwargs)
                
                # 成功時はサーキットブレーカーをリセット
                self._record_success(service_name)
                
                if attempt > 0:
                    logger.info(f"{service_name}: リトライ{attempt}回目で成功しました")
                
                return result
                
            except Exception as e:
                last_exception = e
                error_type = self._classify_error(e)
                
                # セッション切れは即座に失敗
                if error_type == ErrorType.SESSION_EXPIRED:
                    logger.error(f"{service_name}: セッション切れのためリトライを中断")
                    raise e
                
                # 最大リトライ回数チェック
                if attempt >= self.max_retries:
                    self._record_failure(service_name)
                    logger.error(f"{service_name}: 最大リトライ回数({self.max_retries})に到達")
                    break
                
                # リトライ可能かチェック
                if not self._should_retry(error_type):
                    logger.error(f"{service_name}: リトライ不可能なエラー: {error_type.value}")
                    break
                
                # リトライログ
                await self._log_retry_attempt(service_name, attempt + 1, e)
                
                # バックオフ待機
                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)
        
        # 全リトライ失敗
        self._record_failure(service_name)
        logger.error(f"{service_name}: 全てのリトライが失敗しました")
        raise last_exception

    def _classify_error(self, error: Exception) -> ErrorType:
        """
        エラーを分類
        
        Args:
            error: 発生したエラー
            
        Returns:
            ErrorType: エラー種別
        """
        if isinstance(error, SessionExpiredError):
            return ErrorType.SESSION_EXPIRED
        elif isinstance(error, PlaywrightTimeoutError):
            return ErrorType.TIMEOUT
        elif isinstance(error, AIServiceError):
            return ErrorType.AI_SERVICE
        elif "network" in str(error).lower() or "connection" in str(error).lower():
            return ErrorType.NETWORK
        elif "not found" in str(error).lower() or "element" in str(error).lower():
            return ErrorType.ELEMENT_NOT_FOUND
        else:
            return ErrorType.UNKNOWN

    def _should_retry(self, error_type: ErrorType) -> bool:
        """
        リトライすべきかどうか判定
        
        Args:
            error_type: エラー種別
            
        Returns:
            bool: リトライするかどうか
        """
        retryable_errors = {
            ErrorType.NETWORK,
            ErrorType.TIMEOUT,
            ErrorType.ELEMENT_NOT_FOUND,
            ErrorType.UNKNOWN
        }
        return error_type in retryable_errors

    def _calculate_delay(self, attempt: int) -> float:
        """
        バックオフ遅延時間を計算
        
        Args:
            attempt: 試行回数（0から開始）
            
        Returns:
            float: 遅延時間（秒）
        """
        # 指数バックオフ + ジッター
        delay = self.base_delay * (self.backoff_multiplier ** attempt)
        delay = min(delay, self.max_delay)
        
        # ランダムジッター（±20%）
        jitter = delay * 0.2 * (random.random() - 0.5)
        delay += jitter
        
        return max(delay, 0.1)  # 最小0.1秒

    async def _log_retry_attempt(self, service_name: str, attempt: int, error: Exception):
        """
        リトライ試行ログの出力
        
        Args:
            service_name: サービス名
            attempt: 試行回数
            error: 発生したエラー
        """
        error_type = self._classify_error(error)
        delay = self._calculate_delay(attempt - 1)
        
        logger.warning(f"{service_name}: リトライ{attempt}/{self.max_retries} "
                      f"エラー種別: {error_type.value}, "
                      f"次の試行まで {delay:.1f}秒待機, "
                      f"エラー: {str(error)[:100]}")

    async def take_error_screenshot(self, page: Page, service_name: str, error: str) -> str:
        """
        エラー時のスクリーンショット撮影
        
        Args:
            page: Playwrightページ
            service_name: サービス名
            error: エラー内容
            
        Returns:
            str: スクリーンショットファイルパス
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_{service_name}_{timestamp}.png"
            filepath = f"logs/screenshots/{filename}"
            
            # ディレクトリ作成
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            await page.screenshot(path=filepath, full_page=True)
            logger.info(f"エラー時スクリーンショット保存: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"スクリーンショット撮影に失敗: {e}")
            return ""

    def _is_circuit_closed(self, service_name: str) -> bool:
        """
        サーキットブレーカーが閉じているかチェック
        
        Args:
            service_name: サービス名
            
        Returns:
            bool: サーキットが閉じているかどうか
        """
        state = self.circuit_states.get(service_name, CircuitState.CLOSED)
        
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            # 回復タイムアウトチェック
            last_failure = self.last_failure_times.get(service_name)
            if last_failure and datetime.now() - last_failure > timedelta(seconds=self.recovery_timeout):
                # 半開状態に移行
                self.circuit_states[service_name] = CircuitState.HALF_OPEN
                logger.info(f"{service_name}: サーキットブレーカーを半開状態に移行")
                return True
            return False
        elif state == CircuitState.HALF_OPEN:
            return True
        
        return False

    def _record_success(self, service_name: str):
        """
        成功を記録（サーキットブレーカーリセット）
        
        Args:
            service_name: サービス名
        """
        if service_name in self.circuit_states:
            self.circuit_states[service_name] = CircuitState.CLOSED
            self.failure_counts[service_name] = 0
            logger.debug(f"{service_name}: サーキットブレーカーをリセット")

    def _record_failure(self, service_name: str):
        """
        失敗を記録（サーキットブレーカー更新）
        
        Args:
            service_name: サービス名
        """
        self.failure_counts[service_name] = self.failure_counts.get(service_name, 0) + 1
        self.last_failure_times[service_name] = datetime.now()
        
        if self.failure_counts[service_name] >= self.failure_threshold:
            self.circuit_states[service_name] = CircuitState.OPEN
            logger.warning(f"{service_name}: サーキットブレーカーを開放状態に移行 "
                          f"(連続失敗: {self.failure_counts[service_name]})")

    def get_retry_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        リトライ統計情報を取得
        
        Returns:
            Dict[str, Dict[str, Any]]: サービス別統計情報
        """
        stats = {}
        for service_name in set(list(self.circuit_states.keys()) + list(self.failure_counts.keys())):
            stats[service_name] = {
                "circuit_state": self.circuit_states.get(service_name, CircuitState.CLOSED).value,
                "failure_count": self.failure_counts.get(service_name, 0),
                "last_failure": self.last_failure_times.get(service_name)
            }
        return stats

    async def reset_circuit_breaker(self, service_name: str):
        """
        サーキットブレーカーを手動リセット
        
        Args:
            service_name: サービス名
        """
        self.circuit_states[service_name] = CircuitState.CLOSED
        self.failure_counts[service_name] = 0
        if service_name in self.last_failure_times:
            del self.last_failure_times[service_name]
        
        logger.info(f"{service_name}: サーキットブレーカーを手動リセットしました")