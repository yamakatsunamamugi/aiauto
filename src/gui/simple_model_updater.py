"""
シンプルなモデル更新機能
検証済みJSONファイルからモデル情報を読み込む
"""

import json
import os
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleModelUpdater:
    """シンプルなモデル更新クラス"""
    
    def __init__(self):
        self.config_path = "config/ai_models_verified.json"
        self.models_cache = None
        
    def update_all_models(self) -> Dict[str, Dict]:
        """モデル情報を更新（JSONファイルから読み込み）"""
        try:
            # JSONファイルを読み込む
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # キャッシュに保存
                self.models_cache = data.get("models", {})
                
                # 結果を返す
                results = {}
                for service, models in self.models_cache.items():
                    results[service] = {
                        "models": models,
                        "source": "verified_json",
                        "last_updated": data.get("last_verified", "unknown")
                    }
                
                logger.info(f"モデル情報を読み込みました: {self.config_path}")
                return results
            else:
                logger.error(f"設定ファイルが見つかりません: {self.config_path}")
                return self._get_default_models()
                
        except Exception as e:
            logger.error(f"モデル情報読み込みエラー: {e}")
            return self._get_default_models()
    
    def get_cached_info(self) -> Dict:
        """キャッシュされた情報を取得"""
        if self.models_cache:
            return {"ai_services": {
                service: {"models": models}
                for service, models in self.models_cache.items()
            }}
        
        # キャッシュがない場合は読み込む
        self.update_all_models()
        return self.get_cached_info() if self.models_cache else {}
    
    def _get_default_models(self) -> Dict[str, Dict]:
        """デフォルトのモデル情報"""
        default = {
            "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "claude": ["claude-3.5-sonnet", "claude-3-opus"],
            "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "genspark": ["default"],
            "google_ai_studio": ["gemini-1.5-pro"]
        }
        
        return {
            service: {
                "models": models,
                "source": "default",
                "error": "設定ファイルが見つかりません"
            }
            for service, models in default.items()
        }

def update_models_sync() -> Dict[str, Dict]:
    """同期的にモデル情報を更新（GUI用）"""
    updater = SimpleModelUpdater()
    return updater.update_all_models()


# AI Model Updaterとの互換性のため
AIModelUpdater = SimpleModelUpdater