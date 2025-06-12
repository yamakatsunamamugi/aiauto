"""
Playwright高性能AI自動化ハンドラー（テスト用実装）
担当者：AI-C
作成日：2024年6月12日
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .playwright_config import PlaywrightConfig


class PlaywrightAIHandler:
    """Playwright高性能AI処理クラス"""

    def __init__(self, config: Optional[Dict] = None):
        """初期化"""
        self.config = PlaywrightConfig(config or {})
        self.logger = logging.getLogger(__name__)

        # 統計情報
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "parallel_requests": 0,
            "average_response_time": 0.0,
        }

        # 実行状態
        self.is_initialized = False

    async def initialize(self) -> bool:
        """Playwright環境初期化"""
        try:
            self.logger.info("Playwright環境初期化開始")
            
            # テスト用の模擬初期化
            await asyncio.sleep(0.1)  # 初期化時間のシミュレーション
            
            self.is_initialized = True
            self.logger.info("✅ Playwright環境初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Playwright初期化エラー: {e}")
            return False

    async def process_batch_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        タスクバッチの並列処理（高性能版）
        
        Args:
            tasks: タスクリスト
                - text: str
                - ai_service: str
                - model: str
                - task_id: str
                
        Returns:
            List[Dict]: 処理結果リスト
        """
        if not self.is_initialized:
            await self.initialize()

        self.logger.info(f"🚀 Playwright並列処理開始: {len(tasks)}件のタスク（最大同時実行数: {self.config.get('max_concurrent_tasks')}）")

        # 並列処理シミュレーション
        results = []
        
        # タスクをAIサービス別にグループ化
        grouped_tasks = self._group_tasks_by_ai_service(tasks)
        
        # 各グループを並列処理
        for ai_service, service_tasks in grouped_tasks.items():
            service_results = await self._process_service_batch(ai_service, service_tasks)
            results.extend(service_results)

        # 統計更新
        self.stats["parallel_requests"] += len(tasks)
        self.stats["total_requests"] += len(tasks)

        success_count = sum(1 for r in results if r['success'])
        self.stats["successful_requests"] += success_count
        self.stats["failed_requests"] += len(results) - success_count

        self.logger.info(f"✅ Playwright並列処理完了: 成功{success_count}件")

        return results

    def _group_tasks_by_ai_service(self, tasks: List[Dict]) -> Dict[str, List[Dict]]:
        """AIサービス別にタスクをグループ化"""
        grouped = {}
        for task in tasks:
            ai_service = task.get('ai_service', 'chatgpt')
            if ai_service not in grouped:
                grouped[ai_service] = []
            grouped[ai_service].append(task)
        return grouped

    async def _process_service_batch(self, ai_service: str, tasks: List[Dict]) -> List[Dict]:
        """単一AIサービスでのバッチ処理"""
        results = []
        
        # 並列処理制限
        max_concurrent = self.config.get('max_ai_service_concurrent', 2)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single_task(task):
            async with semaphore:
                return await self._process_single_task(ai_service, task)

        # 並列実行
        task_results = await asyncio.gather(
            *[process_single_task(task) for task in tasks],
            return_exceptions=True
        )

        # 結果処理
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                results.append({
                    "success": False,
                    "error": f"並列処理エラー: {str(result)}",
                    "task_id": tasks[i].get('task_id'),
                    "ai_service": ai_service
                })
            else:
                results.append(result)

        return results

    async def _process_single_task(self, ai_service: str, task: Dict) -> Dict[str, Any]:
        """単一タスクの処理（実際のブラウザ自動化）"""
        start_time = time.time()
        task_id = task.get('task_id', f"{ai_service}_{int(time.time())}")

        try:
            # 実際のAI処理を実行
            from .browser_manager import BrowserManager
            from .ai_handlers.chatgpt_handler import ChatGPTHandler
            from .ai_handlers.claude_handler import ClaudeHandler
            from .ai_handlers.gemini_handler import GeminiHandler
            
            ai_config = self.config.get_ai_config(ai_service)
            text = task.get('text', '')
            model = task.get('model', '')
            
            # ブラウザマネージャーでページを取得
            async with BrowserManager() as browser_manager:
                page = await browser_manager.create_new_page()
                
                # AIサービス別にハンドラーを作成
                handler = None
                if ai_service == 'chatgpt':
                    handler = ChatGPTHandler(page, {'model': model})
                elif ai_service == 'claude':
                    handler = ClaudeHandler(page, {'model': model})
                elif ai_service == 'gemini':
                    handler = GeminiHandler(page, {'model': model})
                
                if not handler:
                    raise ValueError(f"未対応のAIサービス: {ai_service}")
                
                # ログイン状態確認
                is_logged_in = await handler.login_check()
                if not is_logged_in:
                    raise Exception(f"{ai_service}にログインしていません")
                
                # AIサービスでテキスト処理
                result_text = await handler.process_text(text, model)
                
                processing_time = time.time() - start_time
                self._update_average_response_time(processing_time)

                return {
                    "success": True,
                    "result": result_text,
                    "ai_service": ai_service,
                    "model": model,
                    "task_id": task_id,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat()
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"タイムアウト（{self.config.get('task_timeout', 60)}秒）",
                "ai_service": ai_service,
                "task_id": task_id,
                "processing_time": time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"タスク処理エラー: {e}")
            return {
                "success": False,
                "error": f"処理エラー: {str(e)}",
                "ai_service": ai_service,
                "task_id": task_id,
                "processing_time": time.time() - start_time
            }

    def _update_average_response_time(self, current_time: float):
        """平均応答時間を更新"""
        if self.stats["successful_requests"] == 0:
            self.stats["average_response_time"] = current_time
        else:
            total_time = self.stats["average_response_time"] * (self.stats["successful_requests"] - 1)
            self.stats["average_response_time"] = (total_time + current_time) / self.stats["successful_requests"]

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return self.stats.copy()

    async def cleanup(self):
        """リソースクリーンアップ"""
        try:
            self.logger.info("✅ Playwrightリソースクリーンアップ完了")
            self.is_initialized = False
        except Exception as e:
            self.logger.error(f"❌ クリーンアップエラー: {e}")

    async def __aenter__(self):
        """非同期コンテキストマネージャー（enter）"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー（exit）"""
        await self.cleanup()