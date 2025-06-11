"""
設定管理モジュール

アプリケーションの設定ファイルの読み込み・保存・管理を行います。
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logger import logger


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        """
        設定管理の初期化
        
        Args:
            config_path (str): 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.config_data = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        設定ファイルを読み込み
        
        Returns:
            Dict[str, Any]: 設定データ
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                logger.info(f"設定ファイルを読み込みました: {self.config_path}")
            else:
                logger.warning(f"設定ファイルが見つかりません: {self.config_path}")
                self.config_data = self._get_default_config()
                self.save_config()
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            self.config_data = self._get_default_config()
        
        return self.config_data
    
    def save_config(self) -> bool:
        """
        設定ファイルを保存
        
        Returns:
            bool: 保存成功の可否
        """
        try:
            # ディレクトリが存在しない場合は作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"設定ファイルを保存しました: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"設定ファイルの保存に失敗しました: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key (str): 設定キー（ドット記法対応: "ai_configs.chatgpt.model"）
            default (Any): デフォルト値
            
        Returns:
            Any: 設定値
        """
        try:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                value = value[k]
            
            return value
        except (KeyError, TypeError):
            logger.debug(f"設定キーが見つかりません: {key}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        設定値を設定
        
        Args:
            key (str): 設定キー（ドット記法対応）
            value (Any): 設定値
            
        Returns:
            bool: 設定成功の可否
        """
        try:
            keys = key.split('.')
            target = self.config_data
            
            # 最後のキー以外は辞書を作成/取得
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            
            # 最後のキーに値を設定
            target[keys[-1]] = value
            logger.info(f"設定を更新しました: {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"設定の更新に失敗しました: {key} = {value}, エラー: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            "spreadsheet_url": "",
            "sheet_name": "",
            "ai_configs": {
                "chatgpt": {
                    "url": "https://chat.openai.com",
                    "model": "gpt-4",
                    "settings": {}
                }
            },
            "automation": {
                "retry_count": 5,
                "retry_delay": 10,
                "browser": "chrome",
                "headless": False,
                "timeout": 30
            },
            "logging": {
                "level": "INFO",
                "file": "logs/app.log"
            }
        }


# グローバル設定管理インスタンス
config_manager = ConfigManager()