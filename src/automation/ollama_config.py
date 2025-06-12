"""
Ollama設定管理
担当者：AI-A
作成日：2024年6月12日
"""

from typing import Dict, List
import json
import os


class OllamaConfig:
    """Ollama設定管理クラス"""

    DEFAULT_MODELS = [
        "llama3.1:8b",
        "llama3.2:3b",
        "phi-4:14b",
        "gemma2:9b",
        "deepseek-r1:7b",
        "qwen2.5:7b"
    ]

    DEFAULT_SYSTEM_PROMPTS = {
        "default": "あなたは優秀なアシスタントです。丁寧に回答してください。",
        "creative": "あなたはクリエイティブなアシスタントです。創造性を発揮して回答してください。",
        "analytical": "あなたは分析的なアシスタントです。論理的に分析して回答してください。",
        "professional": "あなたはプロフェッショナルなアシスタントです。ビジネス向けの正確で適切な回答をしてください。",
        "casual": "あなたはフレンドリーなアシスタントです。親しみやすく回答してください。"
    }

    DEFAULT_OPTIONS = {
        "temperature": 0.7,
        "num_predict": 2000,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1
    }

    @classmethod
    def get_default_config(cls) -> Dict:
        """デフォルト設定を取得"""
        return {
            "models": cls.DEFAULT_MODELS,
            "default_model": "llama3.1:8b",
            "system_prompts": cls.DEFAULT_SYSTEM_PROMPTS,
            "default_system_prompt": "default",
            "options": cls.DEFAULT_OPTIONS,
            "retry_count": 3,
            "retry_delay": 1.0,
            "timeout": 300
        }

    @classmethod
    def get_model_recommendations(cls) -> Dict[str, Dict]:
        """用途別のモデル推奨設定"""
        return {
            "speed_priority": {
                "model": "llama3.2:3b",
                "description": "高速処理重視（軽量モデル）",
                "options": {
                    "temperature": 0.5,
                    "num_predict": 1000
                }
            },
            "quality_priority": {
                "model": "llama3.1:8b",
                "description": "品質重視（標準モデル）",
                "options": {
                    "temperature": 0.7,
                    "num_predict": 2000
                }
            },
            "reasoning_priority": {
                "model": "deepseek-r1:7b",
                "description": "論理的思考重視",
                "options": {
                    "temperature": 0.3,
                    "num_predict": 3000
                }
            },
            "creative_priority": {
                "model": "llama3.1:8b",
                "description": "創造性重視",
                "options": {
                    "temperature": 0.9,
                    "num_predict": 2500
                }
            }
        }

    @classmethod
    def validate_config(cls, config: Dict) -> Dict[str, List[str]]:
        """設定の検証を行う"""
        errors = []
        warnings = []

        # 必須フィールドのチェック
        required_fields = ["default_model", "options"]
        for field in required_fields:
            if field not in config:
                errors.append(f"必須フィールド '{field}' が不足しています")

        # オプション値の検証
        if "options" in config:
            options = config["options"]
            
            # temperature の範囲チェック
            if "temperature" in options:
                temp = options["temperature"]
                if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                    warnings.append("temperature は 0.0-2.0 の範囲で設定することを推奨します")
            
            # num_predict の範囲チェック
            if "num_predict" in options:
                num_pred = options["num_predict"]
                if not isinstance(num_pred, int) or num_pred < 1 or num_pred > 4096:
                    warnings.append("num_predict は 1-4096 の範囲で設定することを推奨します")

        return {
            "errors": errors,
            "warnings": warnings
        }

    @classmethod
    def save_config(cls, config: Dict, file_path: str) -> bool:
        """設定をファイルに保存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定保存エラー: {e}")
            return False

    @classmethod
    def load_config(cls, file_path: str) -> Dict:
        """設定をファイルから読み込み"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
        
        # デフォルト設定を返す
        return cls.get_default_config()

    @classmethod
    def merge_configs(cls, base_config: Dict, override_config: Dict) -> Dict:
        """設定をマージ（override_config が優先）"""
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = cls.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged