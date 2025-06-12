"""
Chrome拡張機能統合テスト
担当者：AI-B

ExtensionBridgeクラスとChrome拡張機能の統合テスト
"""

import unittest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
import os

# テスト実行時のパス設定
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
sys.path.insert(0, project_root)

from src.automation.extension_bridge import ExtensionBridge, ExtensionConfig


class TestExtensionBridge(unittest.TestCase):
    """ExtensionBridgeクラスのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.bridge = ExtensionBridge()
        self.test_text = "テスト用のプロンプトです。この文章に対して適切な応答をしてください。"

    def tearDown(self):
        """テストクリーンアップ"""
        self.bridge.cleanup()

    def test_bridge_initialization(self):
        """ExtensionBridge初期化テスト"""
        self.assertIsNotNone(self.bridge)
        self.assertTrue(self.bridge.temp_dir.exists())
        self.assertEqual(self.bridge.request_timeout, 120)

    def test_supported_ai_services(self):
        """対応AIサービス確認テスト"""
        services = self.bridge.get_supported_ai_services()
        expected_services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
        
        self.assertEqual(set(services), set(expected_services))
        self.assertEqual(len(services), 5)

    def test_extension_status_check(self):
        """拡張機能状態確認テスト"""
        status = self.bridge.check_extension_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn("status", status)
        self.assertIn("message", status)
        
        # 状態は ready, active, missing, invalid, error のいずれか
        valid_statuses = ["ready", "active", "missing", "invalid", "error"]
        self.assertIn(status["status"], valid_statuses)

    def test_statistics_initialization(self):
        """統計情報初期化テスト"""
        stats = self.bridge.get_statistics()
        
        expected_keys = ["total_requests", "successful_requests", "failed_requests", 
                        "average_response_time", "success_rate", "error_history"]
        
        for key in expected_keys:
            self.assertIn(key, stats)
        
        self.assertEqual(stats["total_requests"], 0)
        self.assertEqual(stats["successful_requests"], 0)
        self.assertEqual(stats["failed_requests"], 0)

    @patch('src.automation.extension_bridge.subprocess.Popen')
    def test_chrome_launch_attempt(self, mock_popen):
        """Chrome起動テスト"""
        # Chrome起動のモック
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        # 実際のテストでは拡張機能が見つからないことを想定
        result = self.bridge.process_with_extension(
            text=self.test_text,
            ai_service="chatgpt",
            model="gpt-4o"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("ai_service", result)
        self.assertEqual(result["ai_service"], "chatgpt")

    def test_invalid_ai_service(self):
        """無効なAIサービステスト"""
        result = self.bridge.process_with_extension(
            text=self.test_text,
            ai_service="invalid_service",
            model="test_model"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("未対応のAIサービス", result["error"])

    def test_request_file_creation(self):
        """リクエストファイル作成テスト"""
        # プライベートメソッドをテスト
        request_id = "test_request_123"
        
        # _execute_browser_automation の一部をテスト
        request_file = self.bridge.temp_dir / f"request_{request_id}.json"
        request_data = {
            "text": self.test_text,
            "ai_service": "chatgpt",
            "model": "gpt-4o",
            "request_id": request_id,
            "action": "processAI"
        }
        
        # ファイル作成
        with open(request_file, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, ensure_ascii=False, indent=2)
        
        # ファイル存在確認
        self.assertTrue(request_file.exists())
        
        # ファイル内容確認
        with open(request_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data["text"], self.test_text)
        self.assertEqual(loaded_data["ai_service"], "chatgpt")
        self.assertEqual(loaded_data["request_id"], request_id)
        
        # クリーンアップ
        request_file.unlink()


class TestExtensionConfig(unittest.TestCase):
    """ExtensionConfigクラスのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.temp_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.config_path = Path(self.temp_config_file.name)
        self.temp_config_file.close()

    def tearDown(self):
        """テストクリーンアップ"""
        if self.config_path.exists():
            self.config_path.unlink()

    def test_default_config_creation(self):
        """デフォルト設定作成テスト"""
        config = ExtensionConfig(self.config_path)
        
        # 基本構造確認
        self.assertIn("extension", config.config)
        self.assertIn("ai_services", config.config)
        
        # 拡張機能設定確認
        ext_config = config.config["extension"]
        self.assertEqual(ext_config["timeout"], 120)
        self.assertEqual(ext_config["retry_count"], 3)
        self.assertFalse(ext_config["debug_mode"])
        
        # AIサービス設定確認
        ai_services = config.config["ai_services"]
        expected_services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
        
        for service in expected_services:
            self.assertIn(service, ai_services)
            self.assertTrue(ai_services[service]["enabled"])

    def test_config_get_method(self):
        """設定値取得テスト"""
        config = ExtensionConfig(self.config_path)
        
        # ドット記法での取得
        timeout = config.get("extension.timeout")
        self.assertEqual(timeout, 120)
        
        # 存在しない設定
        nonexistent = config.get("nonexistent.key", "default_value")
        self.assertEqual(nonexistent, "default_value")
        
        # AIサービス設定
        chatgpt_model = config.get("ai_services.chatgpt.default_model")
        self.assertEqual(chatgpt_model, "gpt-4o")

    def test_config_save_and_load(self):
        """設定保存・読み込みテスト"""
        # 設定作成・保存
        config = ExtensionConfig(self.config_path)
        config.config["extension"]["timeout"] = 180
        config.save_config()
        
        # 新しいインスタンスで読み込み
        config2 = ExtensionConfig(self.config_path)
        
        # 変更された値が正しく読み込まれているか確認
        self.assertEqual(config2.get("extension.timeout"), 180)


class TestExtensionIntegration(unittest.TestCase):
    """拡張機能統合テスト"""

    def setUp(self):
        """テストセットアップ"""
        self.bridge = ExtensionBridge()

    def tearDown(self):
        """テストクリーンアップ"""
        self.bridge.cleanup()

    def test_end_to_end_simulation(self):
        """エンドツーエンドシミュレーションテスト"""
        # レスポンスファイルを手動作成してシミュレート
        request_id = "simulation_test_123"
        response_file = self.bridge.temp_dir / f"response_{request_id}.json"
        
        # シミュレーション用レスポンス
        mock_response = {
            "success": True,
            "result": "これはテスト用の応答です。",
            "request_id": request_id,
            "site": "chatgpt",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # レスポンスファイル作成
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(mock_response, f, ensure_ascii=False, indent=2)
        
        # _wait_for_extension_response の動作確認
        result = self.bridge._wait_for_extension_response(response_file, request_id)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "これはテスト用の応答です。")
        self.assertEqual(result["request_id"], request_id)

    @patch('webbrowser.open')
    def test_chrome_executable_detection(self, mock_webbrowser):
        """Chrome実行ファイル検出テスト"""
        # Chrome実行ファイルパス取得
        chrome_path = self.bridge._get_chrome_executable()
        
        # パスが文字列であることを確認
        self.assertIsInstance(chrome_path, str)
        self.assertTrue(len(chrome_path) > 0)

    def test_statistics_update(self):
        """統計情報更新テスト"""
        # 初期統計確認
        initial_stats = self.bridge.get_statistics()
        self.assertEqual(initial_stats["total_requests"], 0)
        
        # 手動でリクエスト統計を更新
        self.bridge.stats["total_requests"] = 5
        self.bridge.stats["successful_requests"] = 3
        self.bridge.stats["failed_requests"] = 2
        
        # 平均応答時間更新のテスト
        self.bridge._update_average_response_time(2.5)
        self.assertEqual(self.bridge.stats["average_response_time"], 2.5)
        
        self.bridge._update_average_response_time(3.5)
        expected_avg = (2.5 + 3.5) / 2
        self.assertEqual(self.bridge.stats["average_response_time"], expected_avg)
        
        # 最終統計確認
        final_stats = self.bridge.get_statistics()
        self.assertEqual(final_stats["success_rate"], 60.0)  # 3/5 * 100

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        # エラー履歴追加
        error_msg = "テスト用エラーメッセージ"
        self.bridge._add_error_to_history(error_msg)
        
        stats = self.bridge.get_statistics()
        self.assertEqual(len(stats["error_history"]), 1)
        self.assertEqual(stats["error_history"][0]["error"], error_msg)
        
        # エラー履歴上限テスト
        for i in range(150):  # 上限100を超えて追加
            self.bridge._add_error_to_history(f"Error {i}")
        
        stats = self.bridge.get_statistics()
        self.assertLessEqual(len(stats["error_history"]), 100)


def run_extension_tests():
    """Chrome拡張機能テスト実行"""
    print("🧪 Chrome拡張機能統合テスト開始")
    print("=" * 50)
    
    # テストスイート作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # テストクラス追加
    suite.addTests(loader.loadTestsFromTestCase(TestExtensionBridge))
    suite.addTests(loader.loadTestsFromTestCase(TestExtensionConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestExtensionIntegration))
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print(f"📊 テスト結果サマリー:")
    print(f"   実行: {result.testsRun}")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   失敗: {len(result.failures)}")
    print(f"   エラー: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失敗したテスト:")
        for test, trace in result.failures:
            print(f"   - {test}")
    
    if result.errors:
        print("\n💥 エラーが発生したテスト:")
        for test, trace in result.errors:
            print(f"   - {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        print("\n🎉 全てのテストが成功しました！")
    else:
        print("\n⚠️ 一部のテストで問題が発生しました。")
    
    return success


if __name__ == "__main__":
    success = run_extension_tests()
    exit(0 if success else 1)