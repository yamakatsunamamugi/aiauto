"""
自動化制御モジュール

全体的な自動化プロセスの制御と管理
各AIハンドラーの統合、タスクスケジューリング、進捗管理を実装
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from src.utils.logger import logger
from src.utils.config_manager import config_manager
from src.utils.column_utils import column_number_to_letter, create_cell_reference
from src.sheets.models import TaskRow as SheetTaskRow, ColumnAIConfig, AIService
from src.sheets.data_handler import DataHandler
from .browser_manager import BrowserManager
from .retry_manager import RetryManager
from .session_manager import SessionManager
from .ai_handlers.base_handler import BaseAIHandler, SessionExpiredError
from .ai_handlers.chatgpt_handler import ChatGPTHandler
from .ai_handlers.claude_handler import ClaudeHandler
from .ai_handlers.gemini_handler import GeminiHandler
from .ai_handlers.genspark_handler import GensparkHandler
from .ai_handlers.google_ai_studio_handler import GoogleAIStudioHandler


@dataclass
class TaskRow:
    """タスク行のデータ構造（Automation Controller用）"""
    row_number: int
    copy_text: str
    ai_config: ColumnAIConfig  # 新しい統合されたAI設定
    copy_column: int
    process_column: int
    error_column: int
    result_column: int
    status: str = "未処理"
    result: Optional[str] = None
    error_message: Optional[str] = None
    
    @property
    def ai_service(self) -> str:
        """後方互換性のためのai_service プロパティ"""
        return self.ai_config.ai_service.value
    
    @property 
    def ai_model(self) -> str:
        """後方互換性のためのai_model プロパティ"""
        return self.ai_config.ai_model
    
    @classmethod
    def from_sheet_task_row(cls, sheet_task: SheetTaskRow) -> 'TaskRow':
        """SheetTaskRowからTaskRowを作成"""
        return cls(
            row_number=sheet_task.row_number,
            copy_text=sheet_task.copy_text,
            ai_config=sheet_task.ai_config,
            copy_column=sheet_task.column_positions.copy_column,
            process_column=sheet_task.column_positions.process_column,
            error_column=sheet_task.column_positions.error_column,
            result_column=sheet_task.column_positions.result_column,
            status="未処理"
        )


@dataclass
class ProcessingResult:
    """処理結果のデータ構造"""
    success: bool
    result_text: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    retry_count: int = 0


class AutomationController:
    """自動化制御クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        自動化制御の初期化
        
        Args:
            config: 自動化設定
        """
        self.config = config or config_manager.get('automation', {})
        
        # コンポーネント初期化
        self.browser_manager: Optional[BrowserManager] = None
        self.retry_manager = RetryManager(
            max_retries=self.config.get('retry_count', 5),
            base_delay=self.config.get('retry_delay', 1.0)
        )
        self.session_manager = SessionManager()
        
        # AIハンドラー管理
        self.ai_handlers: Dict[str, BaseAIHandler] = {}
        self.available_ais = {
            'chatgpt': ChatGPTHandler,
            'claude': ClaudeHandler,
            'gemini': GeminiHandler,
            'genspark': GensparkHandler,
            'google_ai_studio': GoogleAIStudioHandler
        }
        
        # 処理状態管理
        self.is_running = False
        self.current_tasks: List[TaskRow] = []
        self.data_handler: Optional[DataHandler] = None
        self.processing_stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None,
            'current_task': None
        }
        
        # コールバック関数
        self.progress_callback: Optional[Callable] = None
        self.log_callback: Optional[Callable] = None
        
        logger.info("AutomationControllerを初期化しました")

    async def initialize(self) -> bool:
        """
        システム初期化
        
        Returns:
            bool: 初期化成功の可否
        """
        try:
            logger.info("自動化システム初期化開始")
            
            # ブラウザマネージャー初期化
            self.browser_manager = BrowserManager(self.config)
            await self.browser_manager.launch_browser()
            
            # 期限切れセッションのクリーンアップ
            cleaned_sessions = await self.session_manager.cleanup_expired_sessions()
            if cleaned_sessions > 0:
                logger.info(f"期限切れセッション {cleaned_sessions}件をクリーンアップしました")
            
            logger.info("自動化システム初期化完了")
            return True
            
        except Exception as e:
            logger.error(f"自動化システム初期化でエラー: {e}")
            return False

    async def setup_ai_handlers(self, selected_ais: List[str]) -> Dict[str, bool]:
        """
        選択されたAIハンドラーをセットアップ
        
        Args:
            selected_ais: 選択されたAIサービスのリスト
            
        Returns:
            Dict[str, bool]: 各AIの初期化結果
        """
        setup_results = {}
        
        for ai_service in selected_ais:
            try:
                logger.info(f"{ai_service}ハンドラーのセットアップ開始")
                
                # AIハンドラークラス取得
                handler_class = self.available_ais.get(ai_service.lower())
                if not handler_class:
                    logger.error(f"{ai_service}: ハンドラークラスが見つかりません")
                    setup_results[ai_service] = False
                    continue
                
                # 新しいページ作成
                page = await self.browser_manager.create_new_page()
                
                # AIハンドラー初期化
                ai_config = self.config.get('ai_configs', {}).get(ai_service, {})
                handler = handler_class(page, ai_config)
                
                # セッション復元
                await self.session_manager.restore_session(ai_service, self.browser_manager.browser)
                
                # ログイン状態確認
                is_logged_in = await handler.ensure_logged_in()
                if not is_logged_in:
                    logger.error(f"{ai_service}: ログインが必要です")
                    setup_results[ai_service] = False
                    continue
                
                # ハンドラー登録
                self.ai_handlers[ai_service] = handler
                setup_results[ai_service] = True
                
                logger.info(f"{ai_service}ハンドラーのセットアップ完了")
                
            except Exception as e:
                logger.error(f"{ai_service}ハンドラーセットアップでエラー: {e}")
                setup_results[ai_service] = False
        
        return setup_results

    async def create_tasks_from_sheet(self, 
                                     spreadsheet_url: str, 
                                     sheet_name: str,
                                     sheets_client) -> List[TaskRow]:
        """
        スプレッドシートから列毎AI設定を使用してタスクを作成
        
        Args:
            spreadsheet_url: スプレッドシートURL
            sheet_name: シート名
            sheets_client: Sheetsクライアント
            
        Returns:
            List[TaskRow]: 作成されたタスクのリスト
        """
        try:
            # DataHandlerを初期化
            if not self.data_handler:
                self.data_handler = DataHandler(sheets_client)
            
            # シート設定を作成
            from src.sheets.models import SheetConfig
            sheet_config = SheetConfig(
                spreadsheet_url=spreadsheet_url,
                sheet_name=sheet_name,
                spreadsheet_id=""  # __post_init__で自動設定される
            )
            
            # 列毎AI設定を読み込み
            self.data_handler.load_column_ai_settings_from_config(sheet_config, config_manager)
            
            # スプレッドシートデータを読み込みと検証
            sheet_data = self.data_handler.load_and_validate_sheet(sheet_config)
            
            # タスクを生成
            sheet_tasks = self.data_handler.create_task_rows(sheet_data)
            
            # AutomationController用のTaskRowに変換
            automation_tasks = [TaskRow.from_sheet_task_row(task) for task in sheet_tasks]
            
            logger.info(f"シートから{len(automation_tasks)}個のタスクを作成しました")
            
            # タスクの詳細をログ出力
            ai_service_counts = {}
            for task in automation_tasks:
                ai_service = task.ai_service
                ai_service_counts[ai_service] = ai_service_counts.get(ai_service, 0) + 1
            
            for ai_service, count in ai_service_counts.items():
                logger.info(f"  {ai_service}: {count}個のタスク")
            
            return automation_tasks
            
        except Exception as e:
            logger.error(f"シートからのタスク作成でエラー: {e}")
            return []

    async def start_automation(self, 
                              tasks: List[TaskRow],
                              progress_callback: Optional[Callable] = None,
                              log_callback: Optional[Callable] = None) -> bool:
        """
        自動化処理開始
        
        Args:
            tasks: 処理対象タスクのリスト
            progress_callback: 進捗更新コールバック
            log_callback: ログ出力コールバック
            
        Returns:
            bool: 処理開始成功の可否
        """
        try:
            if self.is_running:
                logger.warning("既に自動化処理が実行中です")
                return False
            
            self.is_running = True
            self.current_tasks = tasks
            self.progress_callback = progress_callback
            self.log_callback = log_callback
            
            # 処理統計初期化
            self.processing_stats = {
                'total_tasks': len(tasks),
                'completed_tasks': 0,
                'failed_tasks': 0,
                'start_time': datetime.now(),
                'current_task': None
            }
            
            logger.info(f"自動化処理開始: {len(tasks)}件のタスクを処理します")
            self._update_progress(0, len(tasks), "自動化処理を開始しています...")
            
            # タスク処理実行
            await self._process_task_batch(tasks)
            
            # 完了通知
            completed = self.processing_stats['completed_tasks']
            failed = self.processing_stats['failed_tasks']
            total_time = (datetime.now() - self.processing_stats['start_time']).total_seconds()
            
            logger.info(f"自動化処理完了: 成功{completed}件、失敗{failed}件、処理時間{total_time:.1f}秒")
            self._update_progress(len(tasks), len(tasks), f"処理完了: 成功{completed}件、失敗{failed}件")
            
            return True
            
        except Exception as e:
            logger.error(f"自動化処理でエラー: {e}")
            return False
        finally:
            self.is_running = False

    async def _process_task_batch(self, tasks: List[TaskRow]):
        """
        タスクバッチの処理（列毎AI設定対応）
        
        Args:
            tasks: 処理対象タスクのリスト
        """
        # AIサービス別にタスクをグループ化して効率的に処理
        tasks_by_ai = {}
        for task in tasks:
            ai_service = task.ai_service
            if ai_service not in tasks_by_ai:
                tasks_by_ai[ai_service] = []
            tasks_by_ai[ai_service].append(task)
        
        logger.info(f"タスクを{len(tasks_by_ai)}種類のAIサービスで処理します: {list(tasks_by_ai.keys())}")
        
        task_index = 0
        
        # AIサービス別に順次処理
        for ai_service, ai_tasks in tasks_by_ai.items():
            if not self.is_running:
                logger.info("自動化処理が停止されました")
                break
            
            logger.info(f"{ai_service}で{len(ai_tasks)}個のタスクを処理開始")
            
            # 該当AIサービスのハンドラーが利用可能か確認
            if ai_service.lower() not in self.ai_handlers:
                logger.error(f"{ai_service}のハンドラーが利用できません")
                for task in ai_tasks:
                    task.status = "エラー"
                    task.error_message = f"{ai_service}のハンドラーが利用できません"
                    self.processing_stats['failed_tasks'] += 1
                continue
            
            # AIサービス別のタスクを処理
            for task in ai_tasks:
                if not self.is_running:
                    break
                
                task_index += 1
                self.processing_stats['current_task'] = task
                
                # 進捗更新
                self._update_progress(task_index - 1, len(tasks), 
                                    f"行{task.row_number} ({task.ai_service}) を処理中...")
                self._log_message("INFO", 
                                f"行{task.row_number}: {task.ai_service} ({task.ai_model}) でタスク処理開始")
                
                try:
                    # タスク処理実行
                    result = await self._process_single_task(task)
                    
                    if result.success:
                        task.status = "処理済み"
                        task.result = result.result_text
                        self.processing_stats['completed_tasks'] += 1
                        self._log_message("INFO", f"行{task.row_number}: 処理完了")
                    else:
                        task.status = "エラー"
                        task.error_message = result.error_message
                        self.processing_stats['failed_tasks'] += 1
                        self._log_message("ERROR", f"行{task.row_number}: 処理失敗 - {result.error_message}")
                    
                    # 結果をスプレッドシートに反映
                    await self._update_spreadsheet_result(task)
                    
                except Exception as e:
                    task.status = "エラー"
                    task.error_message = str(e)
                    self.processing_stats['failed_tasks'] += 1
                    logger.error(f"行{task.row_number}: 予期しないエラー: {e}")
                
                # タスク間の待機時間
                await asyncio.sleep(self.config.get('task_interval', 2))

    async def _process_single_task(self, task: TaskRow) -> ProcessingResult:
        """
        単一タスクの処理（列毎AI設定対応）
        
        Args:
            task: 処理対象タスク
            
        Returns:
            ProcessingResult: 処理結果
        """
        start_time = datetime.now()
        
        try:
            # AIハンドラー取得
            handler = self.ai_handlers.get(task.ai_service.lower())
            if not handler:
                return ProcessingResult(
                    success=False,
                    error_message=f"AIハンドラーが見つかりません: {task.ai_service}"
                )
            
            # AI設定をハンドラーに適用
            try:
                await self._apply_ai_config_to_handler(handler, task.ai_config)
            except Exception as e:
                logger.warning(f"AI設定の適用に失敗: {e}")
                # 設定適用に失敗してもタスクは続行
            
            # タスク処理のコンテキスト情報を準備
            task_context = {
                'task_id': f"row_{task.row_number}_col_{task.copy_column}",
                'ai_service': task.ai_service,
                'ai_model': task.ai_model,
                'ai_mode': task.ai_config.ai_mode,
                'features': task.ai_config.ai_features
            }
            
            # リトライ機能付きでタスク実行
            result_text = await self.retry_manager.retry_with_backoff(
                handler.process_request,
                task.ai_service,
                task.copy_text,
                task_context
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=True,
                result_text=result_text,
                processing_time=processing_time
            )
            
        except SessionExpiredError as e:
            return ProcessingResult(
                success=False,
                error_message=f"セッション切れ: {str(e)}"
            )
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    async def _apply_ai_config_to_handler(self, handler: BaseAIHandler, ai_config: ColumnAIConfig):
        """
        AI設定をハンドラーに適用
        
        Args:
            handler: AIハンドラー
            ai_config: AI設定
        """
        try:
            # モデル設定
            if hasattr(handler, 'set_model') and ai_config.ai_model:
                await handler.set_model(ai_config.ai_model)
            
            # モード設定（創造性、正確性等）
            if hasattr(handler, 'set_mode') and ai_config.ai_mode:
                await handler.set_mode(ai_config.ai_mode)
            
            # 機能設定
            if hasattr(handler, 'enable_features') and ai_config.ai_features:
                await handler.enable_features(ai_config.ai_features)
            
            # カスタム設定
            if hasattr(handler, 'apply_custom_settings') and ai_config.ai_settings:
                await handler.apply_custom_settings(ai_config.ai_settings)
                
            logger.debug(f"AI設定を適用: {ai_config.ai_service.value}, モデル: {ai_config.ai_model}")
            
        except Exception as e:
            logger.warning(f"AI設定適用エラー: {e}")
            # エラーが発生してもタスク処理は続行

    async def _update_spreadsheet_result(self, task: TaskRow):
        """
        スプレッドシートに結果を更新
        
        Args:
            task: 更新対象タスク
        """
        # TODO: 担当者Bのスプレッドシート連携モジュールと統合
        # この部分は他のモジュールとの連携が必要
        logger.debug(f"スプレッドシート更新: 行{task.row_number}")

    def _update_progress(self, current: int, total: int, message: str):
        """
        進捗更新
        
        Args:
            current: 現在の進捗
            total: 総数
            message: 進捗メッセージ
        """
        if self.progress_callback:
            try:
                self.progress_callback(current, total, message)
            except Exception as e:
                logger.error(f"進捗更新コールバックでエラー: {e}")

    def _log_message(self, level: str, message: str):
        """
        ログメッセージ出力
        
        Args:
            level: ログレベル
            message: メッセージ
        """
        if self.log_callback:
            try:
                self.log_callback(level, message)
            except Exception as e:
                logger.error(f"ログコールバックでエラー: {e}")

    async def stop_automation(self):
        """自動化処理停止"""
        self.is_running = False
        logger.info("自動化処理の停止が要求されました")

    def get_available_ais(self) -> Dict[str, List[str]]:
        """
        利用可能なAIサービスとモデルを取得
        
        Returns:
            Dict[str, List[str]]: AIサービス別のモデルリスト
        """
        available_services = {}
        
        for ai_service, handler_class in self.available_ais.items():
            # デフォルトモデルリスト（実際のモデル取得は各ハンドラーで実装）
            available_services[ai_service] = ['default']
        
        return available_services

    async def check_ai_login_status(self, ai_services: List[str]) -> Dict[str, bool]:
        """
        AIサービスのログイン状態を一括確認
        
        Args:
            ai_services: 確認対象のAIサービスリスト
            
        Returns:
            Dict[str, bool]: 各AIサービスのログイン状態
        """
        login_status = {}
        
        for ai_service in ai_services:
            try:
                handler = self.ai_handlers.get(ai_service.lower())
                if handler:
                    is_logged_in = await handler.login_check()
                    login_status[ai_service] = is_logged_in
                else:
                    login_status[ai_service] = False
                    
            except Exception as e:
                logger.error(f"{ai_service}のログイン状態確認でエラー: {e}")
                login_status[ai_service] = False
        
        return login_status

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        処理統計情報を取得
        
        Returns:
            Dict[str, Any]: 処理統計情報
        """
        stats = self.processing_stats.copy()
        
        if stats['start_time']:
            elapsed_time = (datetime.now() - stats['start_time']).total_seconds()
            stats['elapsed_time'] = elapsed_time
            
            # 完了予想時間計算
            if stats['completed_tasks'] > 0:
                avg_time_per_task = elapsed_time / stats['completed_tasks']
                remaining_tasks = stats['total_tasks'] - stats['completed_tasks'] - stats['failed_tasks']
                estimated_remaining_time = avg_time_per_task * remaining_tasks
                stats['estimated_remaining_time'] = estimated_remaining_time
        
        # リトライ統計も含める
        stats['retry_stats'] = self.retry_manager.get_retry_stats()
        
        return stats

    async def shutdown(self):
        """システム終了処理"""
        try:
            logger.info("自動化システム終了処理開始")
            
            # 実行中の処理停止
            if self.is_running:
                await self.stop_automation()
                await asyncio.sleep(2)  # 停止処理の完了待機
            
            # セッション保存
            for ai_service, handler in self.ai_handlers.items():
                try:
                    await self.session_manager.save_session(ai_service, self.browser_manager.browser)
                except Exception as e:
                    logger.error(f"{ai_service}のセッション保存でエラー: {e}")
            
            # ブラウザ終了
            if self.browser_manager:
                await self.browser_manager.close_browser()
            
            logger.info("自動化システム終了処理完了")
            
        except Exception as e:
            logger.error(f"システム終了処理でエラー: {e}")

    async def __aenter__(self):
        """非同期コンテキストマネージャー（enter）"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー（exit）"""
        await self.shutdown()