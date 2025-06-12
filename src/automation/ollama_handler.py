"""
Ollama AI処理ハンドラー
担当者：AI-A
作成日：2024年6月12日
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class OllamaAIHandler:
    """Ollama専用AI処理クラス"""

    def __init__(self):
        """初期化"""
        if not OLLAMA_AVAILABLE:
            raise ImportError("ollama library is not installed. Please install it with: pip install ollama")
        
        try:
            self.client = ollama.Client()
            self.logger = logging.getLogger(__name__)
            self.available_models = self._get_available_models()
            self.stats = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time": 0.0
            }
            self.logger.info(f"OllamaAIHandler初期化完了。利用可能モデル: {self.available_models}")
        except Exception as e:
            self.logger.error(f"Ollama接続エラー: {e}")
            raise

    def _get_available_models(self) -> List[str]:
        """利用可能なモデル一覧を取得"""
        try:
            models = self.client.list()
            model_names = [model['name'] for model in models['models']]
            self.logger.info(f"利用可能なモデル: {model_names}")
            return model_names
        except Exception as e:
            self.logger.error(f"モデル一覧取得エラー: {e}")
            return ["llama3.1:8b"]  # デフォルト

    def process_text(self, text: str, model: str = "llama3.1:8b", 
                    system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        テキスト処理メイン関数
        
        Args:
            text: 処理対象テキスト
            model: 使用モデル名
            system_prompt: システムプロンプト（オプション）
            
        Returns:
            Dict: 処理結果
                - success: bool
                - result: str（成功時）
                - error: str（失敗時）
                - model_used: str
                - processing_time: float
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # モデルの有効性チェック
            if not self.validate_model(model):
                self.logger.warning(f"指定されたモデル '{model}' が利用できません。デフォルトモデルを使用します。")
                model = self._get_default_model()

            # メッセージ構築
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": text})

            self.logger.info(f"Ollama処理開始: model={model}, text_length={len(text)}")

            # Ollama API呼び出し
            response = self.client.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "num_predict": 2000,
                    "top_p": 0.9
                }
            )

            processing_time = time.time() - start_time
            self.stats["successful_requests"] += 1
            self._update_average_response_time(processing_time)

            result_text = response['message']['content']
            self.logger.info(f"Ollama処理成功: {processing_time:.2f}秒, response_length={len(result_text)}")

            return {
                "success": True,
                "result": result_text,
                "model_used": model,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self.stats["failed_requests"] += 1

            error_msg = f"Ollama処理エラー: {str(e)}"
            self.logger.error(error_msg)

            return {
                "success": False,
                "error": error_msg,
                "model_used": model,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }

    def _update_average_response_time(self, current_time: float):
        """平均応答時間を更新"""
        if self.stats["successful_requests"] == 1:
            self.stats["average_response_time"] = current_time
        else:
            total_time = self.stats["average_response_time"] * (self.stats["successful_requests"] - 1)
            self.stats["average_response_time"] = (total_time + current_time) / self.stats["successful_requests"]

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return self.stats.copy()

    def validate_model(self, model: str) -> bool:
        """モデルの有効性を確認"""
        return model in self.available_models

    def _get_default_model(self) -> str:
        """デフォルトモデルを取得"""
        if self.available_models:
            return self.available_models[0]
        return "llama3.1:8b"

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """モデル情報を取得"""
        try:
            info = self.client.show(model)
            return {
                "name": model,
                "size": info.get("size", "Unknown"),
                "family": info.get("details", {}).get("family", "Unknown"),
                "parameters": info.get("details", {}).get("parameter_size", "Unknown"),
                "modified_at": info.get("modified_at", "Unknown")
            }
        except Exception as e:
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Ollama接続とモデルの健全性チェック"""
        try:
            # 簡単なテスト処理
            test_result = self.process_text("Hello", self._get_default_model())
            
            return {
                "status": "healthy" if test_result["success"] else "unhealthy",
                "available_models": self.available_models,
                "statistics": self.get_statistics(),
                "test_result": test_result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def refresh_models(self) -> List[str]:
        """モデル一覧を再取得"""
        self.available_models = self._get_available_models()
        return self.available_models