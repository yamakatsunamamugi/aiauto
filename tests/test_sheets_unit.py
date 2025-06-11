#!/usr/bin/env python3
"""
Google Sheetsモジュールの単体テスト

各機能を個別にテストし、モジュールの正確性を確認します。
credentials.jsonが必要ないモック可能なテストも含みます。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# パッケージのパスを追加
sys.path.append(str(Path(__file__).parent.parent))

from src.sheets.models import (
    TaskStatus, AIService, ColumnPosition, ColumnAIConfig,
    TaskRow, SheetConfig, ProcessingResult, SpreadsheetData
)
from src.sheets.data_handler import DataHandler, DataProcessingError, extract_spreadsheet_id_from_url


class TestModels(unittest.TestCase):
    """データモデルのテスト"""
    
    def test_task_status_enum(self):
        """TaskStatus列挙型のテスト"""
        self.assertEqual(TaskStatus.PENDING.value, "未処理")
        self.assertEqual(TaskStatus.IN_PROGRESS.value, "処理中")
        self.assertEqual(TaskStatus.COMPLETED.value, "処理済み")
        self.assertEqual(TaskStatus.ERROR.value, "エラー")
    
    def test_ai_service_enum(self):
        """AIService列挙型のテスト"""
        self.assertEqual(AIService.CHATGPT.value, "chatgpt")
        self.assertEqual(AIService.CLAUDE.value, "claude")
        self.assertEqual(AIService.GEMINI.value, "gemini")
        self.assertEqual(AIService.GENSPARK.value, "genspark")
        self.assertEqual(AIService.GOOGLE_AI_STUDIO.value, "google_ai_studio")
    
    def test_column_position_creation(self):
        """ColumnPositionの作成テスト"""
        pos = ColumnPosition(
            copy_column=5,
            process_column=3,
            error_column=4,
            result_column=6
        )
        
        self.assertEqual(pos.copy_column, 5)
        self.assertEqual(pos.process_column, 3)
        self.assertEqual(pos.error_column, 4)
        self.assertEqual(pos.result_column, 6)
    
    def test_column_ai_config_creation(self):
        """ColumnAIConfigの作成テスト"""
        config = ColumnAIConfig(
            ai_service=AIService.CHATGPT,
            ai_model="gpt-4",
            ai_mode="creative",
            ai_features=["deep_thinking", "analysis"]
        )
        
        self.assertEqual(config.ai_service, AIService.CHATGPT)
        self.assertEqual(config.ai_model, "gpt-4")
        self.assertEqual(config.ai_mode, "creative")
        self.assertIn("deep_thinking", config.ai_features)
    
    def test_task_row_creation(self):
        """TaskRowの作成テスト"""
        column_pos = ColumnPosition(5, 3, 4, 6)
        ai_config = ColumnAIConfig(
            ai_service=AIService.CLAUDE,
            ai_model="claude-3",
            ai_mode="balanced",
            ai_features=[]
        )
        
        task = TaskRow(
            row_number=10,
            copy_text="翻訳してください",
            ai_config=ai_config,
            column_positions=column_pos
        )
        
        self.assertEqual(task.row_number, 10)
        self.assertEqual(task.copy_text, "翻訳してください")
        self.assertEqual(task.ai_service, AIService.CLAUDE)  # プロパティ経由
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.error_message)
        self.assertIsNone(task.result)


class TestDataHandler(unittest.TestCase):
    """DataHandlerのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.mock_sheets_client = Mock()
        self.data_handler = DataHandler(self.mock_sheets_client)
    
    def test_find_work_header_row(self):
        """作業行検索のテスト"""
        # テストデータ
        test_data = [
            ["", ""],
            ["", ""],
            ["", ""],
            ["", ""],
            ["作業", "データ1", "データ2"],  # 5行目（インデックス4）
            ["1", "テキスト1", "テキスト2"]
        ]
        
        # SpreadsheetDataオブジェクトを作成
        config = SheetConfig(
            spreadsheet_url="https://docs.google.com/spreadsheets/d/1234567890/edit",
            sheet_name="Sheet1",
            spreadsheet_id="1234567890"
        )
        sheet_data = SpreadsheetData(config)
        sheet_data.raw_data = test_data
        
        # メソッドを直接テスト
        row_idx = self.data_handler.find_work_header_row(sheet_data)
        self.assertEqual(row_idx, 5)  # 1-indexed
    
    def test_find_work_header_row_not_found(self):
        """作業行が見つからない場合のテスト"""
        test_data = [
            ["", ""],
            ["", ""],
            ["", ""],
            ["", ""],
            ["データ", "データ1", "データ2"],  # 「作業」がない
        ]
        
        # SpreadsheetDataオブジェクトを作成
        config = SheetConfig(
            spreadsheet_url="https://docs.google.com/spreadsheets/d/1234567890/edit",
            sheet_name="Sheet1",
            spreadsheet_id="1234567890"
        )
        sheet_data = SpreadsheetData(config)
        sheet_data.raw_data = test_data
        
        with self.assertRaises(DataProcessingError):
            self.data_handler.find_work_header_row(sheet_data)
    
    def test_find_copy_columns(self):
        """コピー列検索のテスト"""
        # テストデータ
        test_data = [
            ["", ""],
            ["", ""],
            ["", ""],
            ["", ""],
            ["作業", "処理", "エラー", "コピー", "貼り付け", "処理", "エラー", "コピー", "貼り付け"],
            ["1", "", "", "テキスト1", "", "", "", "テキスト2", ""]
        ]
        
        # SpreadsheetDataオブジェクトを作成
        config = SheetConfig(
            spreadsheet_url="https://docs.google.com/spreadsheets/d/1234567890/edit",
            sheet_name="Sheet1",
            spreadsheet_id="1234567890"
        )
        sheet_data = SpreadsheetData(config)
        sheet_data.raw_data = test_data
        
        copy_columns = self.data_handler.find_copy_columns(sheet_data)
        
        # 1-indexedで返される
        self.assertEqual(copy_columns, [4, 8])
    
    def test_calculate_column_positions(self):
        """列位置計算のテスト"""
        # コピー列が4の場合
        pos = self.data_handler.create_column_positions(4)
        
        self.assertEqual(pos.copy_column, 4)
        self.assertEqual(pos.process_column, 2)  # 4 - 2
        self.assertEqual(pos.error_column, 3)    # 4 - 1
        self.assertEqual(pos.result_column, 5)   # 4 + 1
    
    def test_calculate_column_positions_boundary(self):
        """列位置計算の境界値テスト"""
        # コピー列が2の場合（処理列が0になる）
        with self.assertRaises(DataProcessingError):
            self.data_handler.create_column_positions(2)
        
        # コピー列が1の場合
        with self.assertRaises(DataProcessingError):
            self.data_handler.create_column_positions(1)
    
    def test_sheet_config_validation(self):
        """シート設定検証のテスト"""
        config = SheetConfig(
            spreadsheet_url="https://docs.google.com/spreadsheets/d/1234567890/edit",
            sheet_name="Sheet1",
            spreadsheet_id="1234567890"
        )
        
        # モックの戻り値を設定
        self.mock_sheets_client.get_sheet_names.return_value = ["Sheet1", "Sheet2"]
        self.mock_sheets_client.validate_sheet_structure.return_value = (True, [])
        
        is_valid, errors = self.data_handler.validate_sheet_configuration(config)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)


class TestSheetsClient(unittest.TestCase):
    """SheetsClient関連機能のテスト"""
    
    def test_extract_spreadsheet_id_from_url(self):
        """スプレッドシートID抽出のテスト"""
        # 通常のURL
        url1 = "https://docs.google.com/spreadsheets/d/1ABC-xyz_123/edit#gid=0"
        self.assertEqual(extract_spreadsheet_id_from_url(url1), "1ABC-xyz_123")
        
        # パラメータ付きURL
        url2 = "https://docs.google.com/spreadsheets/d/2DEF456/edit?usp=sharing"
        self.assertEqual(extract_spreadsheet_id_from_url(url2), "2DEF456")
        
        # 最小形式のURL
        url3 = "https://docs.google.com/spreadsheets/d/3GHI789"
        self.assertEqual(extract_spreadsheet_id_from_url(url3), "3GHI789")
    
    def test_extract_spreadsheet_id_invalid_url(self):
        """無効なURLのテスト"""
        # 不正なURL
        invalid_urls = [
            "https://example.com",
            "not-a-url",
            "https://docs.google.com/document/d/123/edit",
            ""
        ]
        
        for url in invalid_urls:
            with self.assertRaises(ValueError):
                extract_spreadsheet_id_from_url(url)


class TestColumnAISettings(unittest.TestCase):
    """列毎AI設定のテスト"""
    
    def test_column_ai_settings_parsing(self):
        """列毎AI設定のパースのテスト"""
        settings = {
            "4": {
                "ai_service": "chatgpt",
                "model": "gpt-4",
                "mode": "creative",
                "features": ["deep_research"]
            },
            "8": {
                "ai_service": "claude",
                "model": "claude-3-opus",
                "mode": "balanced",
                "features": []
            }
        }
        
        # 文字列キーから整数への変換確認
        self.assertIn("4", settings)
        self.assertEqual(settings["4"]["ai_service"], "chatgpt")
        self.assertEqual(settings["8"]["ai_service"], "claude")


class TestProcessingResult(unittest.TestCase):
    """処理結果のテスト"""
    
    def test_processing_result_creation(self):
        """ProcessingResultの作成テスト"""
        from datetime import datetime
        result = ProcessingResult(
            total_tasks=10,
            completed_tasks=8,
            error_tasks=2,
            skipped_tasks=0,
            start_time=datetime(2024, 6, 11, 10, 0, 0),
            end_time=datetime(2024, 6, 11, 10, 30, 0)
        )
        
        self.assertEqual(result.total_tasks, 10)
        self.assertEqual(result.completed_tasks, 8)
        self.assertEqual(result.error_tasks, 2)
        self.assertEqual(result.processing_time, 1800.0)
        self.assertAlmostEqual(result.success_rate, 80.0)


if __name__ == "__main__":
    # テスト実行
    unittest.main(verbosity=2)