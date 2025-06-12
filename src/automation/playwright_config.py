"""
Playwright設定管理（テスト用実装）
担当者：AI-C
作成日：2024年6月12日
"""

from typing import Dict, Any, Optional


class PlaywrightConfig:
    """Playwright自動化システム設定管理クラス"""

    def __init__(self, config: Optional[Dict] = None):
        """初期化"""
        self.config = config or {}
        self._load_default_config()

    def _load_default_config(self):
        """デフォルト設定をロード"""
        default_config = {
            # ブラウザ設定
            'headless': False,
            'browser_type': 'chromium',
            
            # 並列処理設定
            'max_concurrent_tasks': 3,
            'max_ai_service_concurrent': 2,
            
            # タイムアウト設定
            'task_timeout': 60,
            'page_load_timeout': 30,
            
            # デバッグ設定
            'save_screenshots': True,
            'debug_mode': True,
        }
        
        # デフォルト設定とユーザー設定をマージ
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return self.config.get(key, default)

    def get_ai_config(self, ai_service: str) -> Dict[str, Any]:
        """指定されたAIサービスの設定を取得"""
        ai_configs = {
            'chatgpt': {
                'base_url': 'https://chat.openai.com',
                'timeout': 60,
                'rate_limit_delay': 1.0
            },
            'claude': {
                'base_url': 'https://claude.ai',
                'timeout': 90,
                'rate_limit_delay': 2.0
            },
            'gemini': {
                'base_url': 'https://gemini.google.com',
                'timeout': 60,
                'rate_limit_delay': 1.5
            }
        }
        
        return ai_configs.get(ai_service, {})

    def to_dict(self) -> Dict[str, Any]:
        """設定辞書を取得"""
        return self.config.copy()