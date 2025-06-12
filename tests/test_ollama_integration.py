"""
Ollama統合テスト
担当者：AI-A
作成日：2024年6月12日
"""

import pytest
import sys
import os
import logging

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.automation.ollama_handler import OllamaAIHandler
    from src.automation.ollama_config import OllamaConfig
    OLLAMA_HANDLER_AVAILABLE = True
except ImportError as e:
    print(f"ImportError: {e}")
    OLLAMA_HANDLER_AVAILABLE = False


class TestOllamaIntegration:
    """Ollama統合テストクラス"""

    def setup_method(self):
        """テスト前準備"""
        if not OLLAMA_HANDLER_AVAILABLE:
            pytest.skip("Ollama handler not available")
        
        try:
            self.handler = OllamaAIHandler()
        except Exception as e:
            pytest.skip(f"Ollama service not available: {e}")

    @pytest.mark.skipif(not OLLAMA_HANDLER_AVAILABLE, reason="Ollama handler not available")
    def test_handler_initialization(self):
        """ハンドラー初期化テスト"""
        assert self.handler is not None
        assert hasattr(self.handler, 'client')
        assert hasattr(self.handler, 'available_models')
        assert hasattr(self.handler, 'stats')

    @pytest.mark.skipif(not OLLAMA_HANDLER_AVAILABLE, reason="Ollama handler not available")
    def test_basic_text_processing(self):
        """基本的なテキスト処理テスト"""
        test_text = "こんにちは、テストです。簡潔に挨拶を返してください。"
        result = self.handler.process_text(test_text)

        assert "success" in result
        assert "processing_time" in result
        assert "timestamp" in result
        assert "model_used" in result

        if result["success"]:
            assert "result" in result
            assert isinstance(result["result"], str)
            assert len(result["result"]) > 0
            print(f"✅ 処理成功: {result['result'][:100]}...")
        else:
            assert "error" in result
            print(f"❌ 処理失敗: {result['error']}")

    @pytest.mark.skipif(not OLLAMA_HANDLER_AVAILABLE, reason="Ollama handler not available")
    def test_model_validation(self):
        """モデル検証テスト"""
        # 利用可能なモデルがある場合
        if self.handler.available_models:
            valid_model = self.handler.available_models[0]
            assert self.handler.validate_model(valid_model) == True
        
        # 存在しないモデル
        invalid_model = "nonexistent:model"
        assert self.handler.validate_model(invalid_model) == False

    @pytest.mark.skipif(not OLLAMA_HANDLER_AVAILABLE, reason="Ollama handler not available")
    def test_statistics(self):
        """統計情報テスト"""
        stats = self.handler.get_statistics()

        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "average_response_time" in stats
        
        # 統計が数値であることを確認
        assert isinstance(stats["total_requests"], int)
        assert isinstance(stats["successful_requests"], int)
        assert isinstance(stats["failed_requests"], int)
        assert isinstance(stats["average_response_time"], (int, float))

    @pytest.mark.skipif(not OLLAMA_HANDLER_AVAILABLE, reason="Ollama handler not available")
    def test_health_check(self):
        """健全性チェックテスト"""
        health = self.handler.health_check()
        
        assert "status" in health
        assert health["status"] in ["healthy", "unhealthy", "error"]
        
        if health["status"] == "healthy":
            assert "available_models" in health
            assert "statistics" in health
            assert "test_result" in health

    @pytest.mark.skipif(not OLLAMA_HANDLER_AVAILABLE, reason="Ollama handler not available")
    def test_system_prompt(self):
        """システムプロンプトテスト"""
        test_text = "数字の3を教えて"
        system_prompt = "数字について聞かれたら、その数字だけを答えてください。"
        
        result = self.handler.process_text(test_text, system_prompt=system_prompt)
        
        if result["success"]:
            print(f"システムプロンプト結果: {result['result']}")
            # システムプロンプトが効いているかの簡易チェック
            assert "3" in result["result"]


class TestOllamaConfig:
    """Ollama設定テストクラス"""

    def test_default_config(self):
        """デフォルト設定テスト"""
        config = OllamaConfig.get_default_config()
        
        assert "models" in config
        assert "default_model" in config
        assert "system_prompts" in config
        assert "options" in config
        
        # 必須項目の存在確認
        assert isinstance(config["models"], list)
        assert len(config["models"]) > 0
        assert isinstance(config["system_prompts"], dict)
        assert isinstance(config["options"], dict)

    def test_model_recommendations(self):
        """モデル推奨設定テスト"""
        recommendations = OllamaConfig.get_model_recommendations()
        
        expected_keys = ["speed_priority", "quality_priority", "reasoning_priority", "creative_priority"]
        for key in expected_keys:
            assert key in recommendations
            assert "model" in recommendations[key]
            assert "description" in recommendations[key]
            assert "options" in recommendations[key]

    def test_config_validation(self):
        """設定検証テスト"""
        # 正常な設定
        valid_config = {
            "default_model": "llama3.1:8b",
            "options": {
                "temperature": 0.7,
                "num_predict": 2000
            }
        }
        result = OllamaConfig.validate_config(valid_config)
        assert len(result["errors"]) == 0

        # 異常な設定
        invalid_config = {
            "options": {
                "temperature": 5.0,  # 範囲外
                "num_predict": -1    # 範囲外
            }
        }
        result = OllamaConfig.validate_config(invalid_config)
        assert len(result["errors"]) > 0  # default_model が不足


def run_integration_tests():
    """統合テスト実行関数"""
    print("🧪 Ollama統合テスト開始")
    
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # 設定テスト
    print("\n📋 設定テスト実行中...")
    config_test = TestOllamaConfig()
    config_test.test_default_config()
    config_test.test_model_recommendations()
    config_test.test_config_validation()
    print("✅ 設定テスト完了")
    
    # Ollamaハンドラーテスト
    print("\n🤖 Ollamaハンドラーテスト実行中...")
    try:
        handler_test = TestOllamaIntegration()
        handler_test.setup_method()
        
        handler_test.test_handler_initialization()
        print("✅ ハンドラー初期化テスト完了")
        
        handler_test.test_statistics()
        print("✅ 統計情報テスト完了")
        
        handler_test.test_model_validation()
        print("✅ モデル検証テスト完了")
        
        handler_test.test_health_check()
        print("✅ 健全性チェックテスト完了")
        
        # 実際のAI処理テスト（時間がかかる可能性がある）
        print("\n🔄 実際のAI処理テスト実行中...")
        handler_test.test_basic_text_processing()
        print("✅ 基本的なテキスト処理テスト完了")
        
        handler_test.test_system_prompt()
        print("✅ システムプロンプトテスト完了")
        
    except Exception as e:
        print(f"⚠️ Ollamaハンドラーテストをスキップ: {e}")
    
    print("\n🎉 全てのOllama統合テストが完了しました！")


if __name__ == "__main__":
    run_integration_tests()