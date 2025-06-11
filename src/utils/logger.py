"""
ログ管理モジュール

アプリケーション全体で使用するログ機能を提供します。
詳細なログ出力により、エラーの特定と解決を支援します。
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


class AppLogger:
    """アプリケーション用ログクラス"""
    
    def __init__(self, name: str = "AIAutomation"):
        """
        ログ初期化
        
        Args:
            name (str): ログ名
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # ログディレクトリ作成
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # ハンドラーが既に設定されている場合はスキップ
        if not self.logger.handlers:
            self._setup_handlers(log_dir)
    
    def _setup_handlers(self, log_dir: Path):
        """ログハンドラーの設定"""
        # ファイルハンドラー（回転ログ）
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # フォーマッター
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """ログインスタンスを取得"""
        return self.logger


# グローバルログインスタンス
app_logger = AppLogger()
logger = app_logger.get_logger()


def log_operation(operation_name: str):
    """操作ログのデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"開始: {operation_name}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"完了: {operation_name}")
                return result
            except Exception as e:
                logger.error(f"エラー: {operation_name} - {str(e)}")
                raise
        return wrapper
    return decorator