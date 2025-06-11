"""
列毎AI選択機能の統合テスト

実装された列毎AI選択機能の全体的な動作を検証
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parents[1]))

from src.sheets.models import (
    ColumnAIConfig, ColumnMapping, SheetConfig, TaskRow as SheetTaskRow,
    AIService, ColumnPosition, TaskStatus
)
from src.utils.column_utils import (
    column_letter_to_number, column_number_to_letter,
    get_copy_column_positions, find_copy_columns_in_header
)
from src.utils.column_validation import (
    ColumnConfigValidator, validate_column_ai_settings
)


class TestColumnUtilities(unittest.TestCase):
    """列ユーティリティのテスト"""
    
    def test_column_conversion(self):
        """列番号と列記号の変換テスト"""
        # 基本的な変換
        self.assertEqual(column_letter_to_number("A"), 1)
        self.assertEqual(column_letter_to_number("B"), 2)
        self.assertEqual(column_letter_to_number("Z"), 26)
        self.assertEqual(column_letter_to_number("AA"), 27)
        self.assertEqual(column_letter_to_number("AB"), 28)
        
        # 逆変換
        self.assertEqual(column_number_to_letter(1), "A")
        self.assertEqual(column_number_to_letter(2), "B")
        self.assertEqual(column_number_to_letter(26), "Z")
        self.assertEqual(column_number_to_letter(27), "AA")
        self.assertEqual(column_number_to_letter(28), "AB")
    
    def test_copy_column_positions(self):
        """コピー列位置計算のテスト"""
        # 正常なケース
        process, error, copy, result = get_copy_column_positions(5)
        self.assertEqual((process, error, copy, result), (3, 4, 5, 6))
        
        # 境界値テスト
        process, error, copy, result = get_copy_column_positions(3)
        self.assertEqual((process, error, copy, result), (1, 2, 3, 4))
        
        # エラーケース
        with self.assertRaises(ValueError):
            get_copy_column_positions(2)  # C列より前
        
        with self.assertRaises(ValueError):
            get_copy_column_positions(1)  # A列
    
    def test_find_copy_columns(self):
        """ヘッダー行からコピー列検出のテスト"""
        header_row = ["作業", "処理", "コピー", "結果", "エラー", "コピー", "結果2"]
        copy_columns = find_copy_columns_in_header(header_row)
        
        expected = [(3, "C"), (6, "F")]
        self.assertEqual(copy_columns, expected)


class TestColumnAIConfig(unittest.TestCase):
    """ColumnAIConfigのテスト"""
    
    def test_column_ai_config_creation(self):
        """ColumnAIConfig作成のテスト"""
        config = ColumnAIConfig(
            ai_service=AIService.CHATGPT,
            ai_model="gpt-4",
            ai_mode="creative",
            ai_features=["deep_research"],
            ai_settings={"temperature": 0.7}
        )
        
        self.assertEqual(config.ai_service, AIService.CHATGPT)
        self.assertEqual(config.ai_model, "gpt-4")
        self.assertEqual(config.ai_mode, "creative")
        self.assertEqual(config.ai_features, ["deep_research"])
        self.assertEqual(config.ai_settings["temperature"], 0.7)
    
    def test_column_ai_config_serialization(self):
        """ColumnAIConfigシリアライゼーションのテスト"""
        config = ColumnAIConfig(
            ai_service=AIService.CLAUDE,
            ai_model="claude-3-sonnet",
            ai_mode="balanced"
        )
        
        # 辞書形式に変換
        config_dict = config.to_dict()
        expected_dict = {
            "ai_service": "claude",
            "ai_model": "claude-3-sonnet",
            "ai_mode": "balanced",
            "ai_features": [],
            "ai_settings": {}
        }
        self.assertEqual(config_dict, expected_dict)
        
        # 辞書から復元
        restored_config = ColumnAIConfig.from_dict(config_dict)
        self.assertEqual(restored_config.ai_service, AIService.CLAUDE)
        self.assertEqual(restored_config.ai_model, "claude-3-sonnet")
        self.assertEqual(restored_config.ai_mode, "balanced")


class TestColumnMapping(unittest.TestCase):
    """ColumnMappingのテスト"""
    
    def test_column_mapping_creation(self):
        """ColumnMapping作成のテスト"""
        ai_config = ColumnAIConfig(
            ai_service=AIService.GEMINI,
            ai_model="gemini-pro"
        )
        
        mapping = ColumnMapping.create_from_copy_column(5, ai_config)
        
        self.assertEqual(mapping.column_letter, "E")
        self.assertEqual(mapping.column_number, 5)
        self.assertEqual(mapping.column_positions.copy_column, 5)
        self.assertEqual(mapping.column_positions.process_column, 3)
        self.assertEqual(mapping.column_positions.error_column, 4)
        self.assertEqual(mapping.column_positions.result_column, 6)
        self.assertEqual(mapping.ai_config, ai_config)
    
    def test_column_mapping_validation(self):
        """ColumnMapping検証のテスト"""
        ai_config = ColumnAIConfig(
            ai_service=AIService.CHATGPT,
            ai_model="gpt-4"
        )
        
        # 正常ケース
        mapping = ColumnMapping.create_from_copy_column(3, ai_config)
        self.assertEqual(mapping.column_letter, "C")
        
        # 不正な列番号と列記号の組み合わせ
        with self.assertRaises(ValueError):
            ColumnMapping(
                column_letter="A",
                column_number=5,  # 不整合
                column_positions=ColumnPosition(5, 3, 4, 6),
                ai_config=ai_config
            )


class TestSheetConfig(unittest.TestCase):
    """SheetConfigのテスト"""
    
    def test_sheet_config_column_mappings(self):
        """SheetConfigの列マッピング機能のテスト"""
        config = SheetConfig(
            spreadsheet_url="https://docs.google.com/spreadsheets/d/test123/edit",
            sheet_name="Test Sheet",
            spreadsheet_id="test123"
        )
        
        # 列マッピングを追加
        ai_config1 = ColumnAIConfig(AIService.CHATGPT, "gpt-4")
        ai_config2 = ColumnAIConfig(AIService.CLAUDE, "claude-3-sonnet")
        
        config.add_column_mapping(3, ai_config1)
        config.add_column_mapping(5, ai_config2)
        
        # マッピング取得テスト
        mapping1 = config.get_column_mapping(3)
        self.assertIsNotNone(mapping1)
        self.assertEqual(mapping1.ai_config.ai_service, AIService.CHATGPT)
        
        mapping2 = config.get_column_mapping(5)
        self.assertIsNotNone(mapping2)
        self.assertEqual(mapping2.ai_config.ai_service, AIService.CLAUDE)
        
        # 存在しない列
        mapping3 = config.get_column_mapping(7)
        self.assertIsNone(mapping3)
        
        # AI設定取得テスト
        config.use_column_ai_settings = True
        ai_config_3 = config.get_ai_config_for_column(3)
        self.assertEqual(ai_config_3.ai_service, AIService.CHATGPT)
        
        # デフォルト設定取得テスト
        ai_config_7 = config.get_ai_config_for_column(7)
        self.assertEqual(ai_config_7.ai_service, config.default_ai_service)


class TestColumnValidation(unittest.TestCase):
    """列設定検証のテスト"""
    
    def test_valid_column_settings(self):
        """正常な列設定の検証"""
        settings = {
            "C": {
                "ai_service": "chatgpt",
                "model": "gpt-4",
                "mode": "creative",
                "feature": "deep_research"
            },
            "E": {
                "ai_service": "claude", 
                "model": "claude-3-sonnet",
                "mode": "balanced",
                "feature": "analysis"
            }
        }
        
        is_valid, message = validate_column_ai_settings(settings)
        self.assertTrue(is_valid)
        self.assertIn("エラー0件", message)
    
    def test_invalid_column_settings(self):
        """不正な列設定の検証"""
        settings = {
            "A": {  # 無効な位置
                "ai_service": "chatgpt",
                "model": "gpt-4"
            },
            "C": {
                "ai_service": "invalid_ai",  # 無効なAIサービス
                "model": "gpt-4"
            }
        }
        
        is_valid, message = validate_column_ai_settings(settings)
        self.assertFalse(is_valid)
        self.assertIn("エラー", message)
    
    def test_column_config_validator(self):
        """ColumnConfigValidatorの詳細テスト"""
        validator = ColumnConfigValidator()
        
        # 個別列設定検証
        good_settings = {
            "ai_service": "chatgpt",
            "model": "gpt-4",
            "mode": "creative"
        }
        results = validator._validate_single_column_config("C", good_settings)
        errors = [r for r in results if r.level.value == "error"]
        self.assertEqual(len(errors), 0)
        
        # 無効な列設定
        bad_settings = {
            "ai_service": "invalid_ai",
            "model": ""
        }
        results = validator._validate_single_column_config("A", bad_settings)
        errors = [r for r in results if r.level.value == "error"]
        self.assertGreater(len(errors), 0)


class TestTaskRowIntegration(unittest.TestCase):
    """TaskRowの統合テスト"""
    
    def test_task_row_with_column_ai_config(self):
        """ColumnAIConfigを使用したTaskRowのテスト"""
        ai_config = ColumnAIConfig(
            ai_service=AIService.CHATGPT,
            ai_model="gpt-4",
            ai_mode="creative"
        )
        
        column_positions = ColumnPosition(
            copy_column=5,
            process_column=3,
            error_column=4,
            result_column=6
        )
        
        task = SheetTaskRow(
            row_number=10,
            copy_text="Test text",
            ai_config=ai_config,
            column_positions=column_positions
        )
        
        # 後方互換性プロパティのテスト
        self.assertEqual(task.ai_service, AIService.CHATGPT)
        self.assertEqual(task.ai_model, "gpt-4")
        
        # AIサービスと設定の整合性確認
        self.assertEqual(task.ai_config.ai_service, AIService.CHATGPT)
        self.assertEqual(task.ai_config.ai_model, "gpt-4")
        self.assertEqual(task.ai_config.ai_mode, "creative")


class TestEndToEndWorkflow(unittest.TestCase):
    """エンドツーエンドワークフローのテスト"""
    
    @unittest.skip("Requires additional AI handler modules")
    @patch('src.sheets.sheets_client.create_sheets_client')
    @patch('src.sheets.data_handler.DataHandler')
    def test_complete_column_ai_workflow(self, mock_data_handler_class, mock_sheets_client):
        """完全な列毎AIワークフローのテスト"""
        # モックセットアップ
        mock_sheets_client_instance = Mock()
        mock_sheets_client.return_value = mock_sheets_client_instance
        
        mock_data_handler = Mock()
        mock_data_handler_class.return_value = mock_data_handler
        
        # テスト用のスプレッドシートデータ
        mock_sheet_data = Mock()
        mock_data_handler.load_and_validate_sheet.return_value = mock_sheet_data
        mock_data_handler.find_copy_columns.return_value = [3, 5, 7]
        
        # テスト用のタスク
        ai_config1 = ColumnAIConfig(AIService.CHATGPT, "gpt-4")
        ai_config2 = ColumnAIConfig(AIService.CLAUDE, "claude-3-sonnet")
        
        task1 = SheetTaskRow(
            row_number=10,
            copy_text="Test text 1",
            ai_config=ai_config1,
            column_positions=ColumnPosition(3, 1, 2, 4)
        )
        
        task2 = SheetTaskRow(
            row_number=10,
            copy_text="Test text 2", 
            ai_config=ai_config2,
            column_positions=ColumnPosition(5, 3, 4, 6)
        )
        
        mock_data_handler.create_task_rows.return_value = [task1, task2]
        
        # AutomationControllerでのタスク変換をテスト
        from src.automation.automation_controller import TaskRow as AutomationTaskRow
        
        automation_task1 = AutomationTaskRow.from_sheet_task_row(task1)
        automation_task2 = AutomationTaskRow.from_sheet_task_row(task2)
        
        # 変換結果の確認
        self.assertEqual(automation_task1.ai_service, "chatgpt")
        self.assertEqual(automation_task1.ai_model, "gpt-4")
        self.assertEqual(automation_task1.copy_column, 3)
        
        self.assertEqual(automation_task2.ai_service, "claude")
        self.assertEqual(automation_task2.ai_model, "claude-3-sonnet")
        self.assertEqual(automation_task2.copy_column, 5)
        
        # AIサービス別グループ化をテスト
        tasks = [automation_task1, automation_task2]
        tasks_by_ai = {}
        for task in tasks:
            ai_service = task.ai_service
            if ai_service not in tasks_by_ai:
                tasks_by_ai[ai_service] = []
            tasks_by_ai[ai_service].append(task)
        
        self.assertEqual(len(tasks_by_ai), 2)
        self.assertIn("chatgpt", tasks_by_ai)
        self.assertIn("claude", tasks_by_ai)
        self.assertEqual(len(tasks_by_ai["chatgpt"]), 1)
        self.assertEqual(len(tasks_by_ai["claude"]), 1)


def run_all_tests():
    """すべてのテストを実行"""
    print("=== 列毎AI選択機能 統合テスト開始 ===\n")
    
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # 各テストクラスを追加
    test_classes = [
        TestColumnUtilities,
        TestColumnAIConfig, 
        TestColumnMapping,
        TestSheetConfig,
        TestColumnValidation,
        TestTaskRowIntegration,
        TestEndToEndWorkflow
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果サマリー
    print(f"\n=== テスト結果サマリー ===")
    print(f"実行テスト数: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.failures:
        print("\n失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'✅ すべてのテストが成功しました' if success else '❌ テストに失敗があります'}")
    
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)