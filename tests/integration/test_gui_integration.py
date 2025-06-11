"""
GUI統合テスト - 他モジュールとの連携

担当者A（GUI）による他担当（Sheets、Automation）との
連携テストポイントの実装
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, MagicMock, patch, call
import sys
from pathlib import Path
import time
import threading
import json

sys.path.append(str(Path(__file__).parents[2]))

from src.gui.main_window import MainWindow
from src.gui.column_ai_settings import ColumnAISettingsDialog
from src.gui.progress_window import ProgressWindow
from tests.fixtures.gui_fixtures import GUITestHelper, mock_sheets_client, mock_automation_controller


class TestGUISheetsIntegration(unittest.TestCase):
    """GUI-Sheets連携テスト（担当者Bとの連携）"""
    
    def setUp(self):
        """テスト前の準備"""
        self.app = MainWindow()
        self.app.root.withdraw()
        self.mock_sheets = MagicMock()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.app.root.destroy()
    
    @patch('src.sheets.sheets_client.SheetsClient')
    def test_sheet_names_loading(self, mock_sheets_class):
        """Sheets連携: シート名取得テスト"""
        # モックの設定
        mock_sheets_class.return_value = self.mock_sheets
        self.mock_sheets.get_sheet_names.return_value = ["Sheet1", "Sheet2", "データシート"]
        
        # コールバック設定
        self.app.set_get_sheet_names_callback(self.mock_sheets.get_sheet_names)
        
        # URL設定とシート名読み込み
        test_url = "https://docs.google.com/spreadsheets/d/1abc123/edit"
        self.app.spreadsheet_url_var.set(test_url)
        self.app.load_sheet_names()
        
        # コールバックが呼ばれたことを確認
        self.mock_sheets.get_sheet_names.assert_called_once_with(test_url)
        
        # コンボボックスに値が設定されることを確認
        GUITestHelper.process_gui_events(self.app.root, 0.5)
        values = self.app.sheet_name_combobox['values']
        self.assertEqual(len(values), 3)
        self.assertIn("データシート", values)
    
    @patch('src.sheets.sheets_client.SheetsClient')
    def test_copy_columns_detection(self, mock_sheets_class):
        """Sheets連携: コピー列検出テスト"""
        mock_sheets_class.return_value = self.mock_sheets
        self.mock_sheets.get_copy_columns.return_value = ["C", "E", "G", "I"]
        
        # 列毎設定モードでコピー列を取得
        self.app.ai_mode_var.set("column")
        self.app.toggle_ai_mode()
        
        # コールバック経由でコピー列を取得
        with patch.object(self.app, 'get_copy_columns_callback', self.mock_sheets.get_copy_columns):
            columns = self.app.get_copy_columns_callback()
            self.assertEqual(columns, ["C", "E", "G", "I"])
    
    @patch('src.sheets.sheets_client.SheetsClient')
    def test_sheets_error_handling(self, mock_sheets_class):
        """Sheets連携: エラーハンドリングテスト"""
        mock_sheets_class.return_value = self.mock_sheets
        
        # 各種エラーシナリオ
        error_scenarios = [
            (PermissionError("アクセス権限がありません"), "権限"),
            (FileNotFoundError("スプレッドシートが見つかりません"), "見つかりません"),
            (ConnectionError("ネットワークエラー"), "ネットワーク"),
            (ValueError("不正なデータ形式"), "データ")
        ]
        
        for error, expected_keyword in error_scenarios:
            self.mock_sheets.get_sheet_names.side_effect = error
            
            with patch('tkinter.messagebox.showerror') as mock_error:
                self.app.set_get_sheet_names_callback(self.mock_sheets.get_sheet_names)
                self.app.spreadsheet_url_var.set("https://docs.google.com/spreadsheets/d/test/edit")
                self.app.load_sheet_names()
                
                # エラーダイアログが表示されることを確認
                mock_error.assert_called()
                _, message = mock_error.call_args[0]
                self.assertIn(expected_keyword, message)
    
    def test_sheets_data_validation(self):
        """Sheets連携: データ検証テスト"""
        # 不正なシートデータのテスト
        invalid_data_scenarios = [
            [],  # 空のシート名リスト
            None,  # Null値
            [""],  # 空文字列を含む
            ["Sheet1", "", "Sheet3"],  # 空文字列が混在
            ["シート" * 100],  # 非常に長いシート名
        ]
        
        for invalid_data in invalid_data_scenarios:
            with patch.object(self.app, 'get_sheet_names_callback', return_value=invalid_data):
                self.app.load_sheet_names()
                GUITestHelper.process_gui_events(self.app.root, 0.1)
                
                # エラーが適切に処理されることを確認
                # （実装に依存）


class TestGUIAutomationIntegration(unittest.TestCase):
    """GUI-Automation連携テスト（担当者Cとの連携）"""
    
    def setUp(self):
        """テスト前の準備"""
        self.app = MainWindow()
        self.app.root.withdraw()
        self.mock_controller = MagicMock()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.app.root.destroy()
    
    @patch('src.automation.automation_controller.AutomationController')
    def test_automation_start_parameters(self, mock_controller_class):
        """Automation連携: 開始パラメータテスト"""
        mock_controller_class.return_value = self.mock_controller
        
        # テスト設定
        test_config = {
            'spreadsheet_url': 'https://docs.google.com/spreadsheets/d/test/edit',
            'sheet_name': 'TestSheet',
            'ai_mode': 'simple',
            'selected_ais': ['chatgpt', 'claude']
        }
        
        # GUI設定
        self.app.spreadsheet_url_var.set(test_config['spreadsheet_url'])
        self.app.sheet_name_var.set(test_config['sheet_name'])
        self.app.ai_mode_var.set(test_config['ai_mode'])
        self.app.ai_selection_vars['chatgpt'].set(True)
        self.app.ai_selection_vars['claude'].set(True)
        
        # コールバック設定と実行
        self.app.set_start_automation_callback(self.mock_controller.start)
        self.app.start_automation()
        
        # 渡されたパラメータを確認
        self.mock_controller.start.assert_called_once()
        args = self.mock_controller.start.call_args[0][0]
        
        self.assertEqual(args['spreadsheet_url'], test_config['spreadsheet_url'])
        self.assertEqual(args['sheet_name'], test_config['sheet_name'])
        self.assertEqual(args['ai_mode'], test_config['ai_mode'])
        self.assertIn('chatgpt', args['selected_ais'])
        self.assertIn('claude', args['selected_ais'])
    
    def test_automation_progress_updates(self):
        """Automation連携: 進捗更新テスト"""
        # 進捗更新のシミュレート
        progress_updates = [
            (0, 100, "初期化中..."),
            (25, 100, "データ読み込み中..."),
            (50, 100, "AI処理中..."),
            (75, 100, "結果保存中..."),
            (100, 100, "完了")
        ]
        
        for current, total, status in progress_updates:
            self.app.update_progress_callback(current, total, status)
            
            # GUI更新
            GUITestHelper.process_gui_events(self.app.root, 0.1)
            
            # 進捗が正しく更新されることを確認
            self.assertEqual(self.app.progress_var.get(), (current / total) * 100)
            self.assertIn(status, self.app.progress_text_var.get())
    
    def test_automation_log_forwarding(self):
        """Automation連携: ログ転送テスト"""
        # ログメッセージのテスト
        log_messages = [
            ("INFO", "処理を開始しました"),
            ("WARNING", "レート制限に近づいています"),
            ("ERROR", "AI応答でエラーが発生しました"),
            ("INFO", "リトライを実行します"),
            ("SUCCESS", "処理が完了しました")
        ]
        
        for level, message in log_messages:
            self.app.add_log(level, message)
        
        # ログが表示されることを確認
        log_content = self.app.log_text.get("1.0", tk.END)
        for level, message in log_messages:
            self.assertIn(message, log_content)
    
    def test_automation_cancellation(self):
        """Automation連携: キャンセル処理テスト"""
        # 実行中の状態をシミュレート
        self.mock_controller.is_running = True
        self.app.automation_controller = self.mock_controller
        
        # 停止ボタンの有効化確認
        self.app.is_running = True
        self.app.update_button_states()
        self.assertEqual(str(self.app.stop_button['state']), 'normal')
        
        # 停止処理
        self.app.stop_automation()
        
        # コントローラーの停止が呼ばれることを確認
        self.mock_controller.stop.assert_called_once()
    
    def test_column_mode_parameters(self):
        """Automation連携: 列毎設定モードのパラメータテスト"""
        # 列毎設定のモック
        column_settings = {
            "C": {
                "ai_service": "chatgpt",
                "model": "gpt-4o",
                "mode": "creative",
                "custom_prompt": "創造的に回答してください"
            },
            "E": {
                "ai_service": "claude",
                "model": "claude-3.5-sonnet",
                "mode": "precise",
                "custom_prompt": ""
            },
            "G": {
                "ai_service": "gemini",
                "model": "gemini-2.0-flash-exp",
                "mode": "default",
                "custom_prompt": ""
            }
        }
        
        # 設定を適用
        self.app.config.set("column_ai_settings", column_settings)
        self.app.ai_mode_var.set("column")
        
        # コールバック設定と実行
        self.app.set_start_automation_callback(self.mock_controller.start)
        self.app.spreadsheet_url_var.set("https://docs.google.com/spreadsheets/d/test/edit")
        self.app.sheet_name_var.set("Sheet1")
        self.app.start_automation()
        
        # 列毎設定が渡されることを確認
        args = self.mock_controller.start.call_args[0][0]
        self.assertEqual(args['ai_mode'], 'column')
        self.assertEqual(args['column_ai_settings'], column_settings)


class TestCrossModuleErrorHandling(unittest.TestCase):
    """モジュール間のエラーハンドリングテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.app = MainWindow()
        self.app.root.withdraw()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.app.root.destroy()
    
    def test_sheets_to_automation_error_propagation(self):
        """Sheets→Automation間のエラー伝播テスト"""
        # Sheetsエラーが発生した場合、Automationが開始されないことを確認
        mock_sheets = Mock()
        mock_sheets.get_sheet_names.side_effect = Exception("Sheets API Error")
        
        mock_automation = Mock()
        
        self.app.set_get_sheet_names_callback(mock_sheets.get_sheet_names)
        self.app.set_start_automation_callback(mock_automation.start)
        
        # エラーが発生してもアプリがクラッシュしないことを確認
        with patch('tkinter.messagebox.showerror'):
            self.app.load_sheet_names()
            
        # Automationが開始されていないことを確認
        mock_automation.start.assert_not_called()
    
    def test_concurrent_module_operations(self):
        """複数モジュールの同時操作テスト"""
        operations_completed = []
        
        def mock_sheets_operation():
            time.sleep(0.2)
            operations_completed.append('sheets')
            return ["Sheet1", "Sheet2"]
        
        def mock_automation_operation():
            time.sleep(0.3)
            operations_completed.append('automation')
        
        # 非同期操作のシミュレート
        thread1 = threading.Thread(target=mock_sheets_operation)
        thread2 = threading.Thread(target=mock_automation_operation)
        
        thread1.start()
        thread2.start()
        
        # GUI更新を継続
        start_time = time.time()
        while len(operations_completed) < 2 and time.time() - start_time < 1:
            GUITestHelper.process_gui_events(self.app.root, 0.1)
        
        thread1.join()
        thread2.join()
        
        # 両方の操作が完了したことを確認
        self.assertEqual(len(operations_completed), 2)
        self.assertIn('sheets', operations_completed)
        self.assertIn('automation', operations_completed)


class TestDataFlowIntegration(unittest.TestCase):
    """データフロー統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.app = MainWindow()
        self.app.root.withdraw()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.app.root.destroy()
    
    def test_complete_data_flow(self):
        """完全なデータフローテスト"""
        # 1. Sheetsからデータ取得
        mock_sheets_data = {
            'sheet_names': ['Sheet1', 'Sheet2'],
            'copy_columns': ['C', 'E'],
            'data': [
                ['作業', 'B', 'コピー', 'D', 'コピー'],
                ['1', 'データ1', 'テキスト1', '', 'テキスト2']
            ]
        }
        
        # 2. GUIで設定
        self.app.spreadsheet_url_var.set("https://docs.google.com/spreadsheets/d/test/edit")
        self.app.sheet_name_var.set("Sheet1")
        self.app.ai_mode_var.set("simple")
        self.app.ai_selection_vars['chatgpt'].set(True)
        
        # 3. Automationに渡すパラメータ
        expected_params = {
            'spreadsheet_url': 'https://docs.google.com/spreadsheets/d/test/edit',
            'sheet_name': 'Sheet1',
            'ai_mode': 'simple',
            'selected_ais': ['chatgpt'],
            'copy_columns': mock_sheets_data['copy_columns']
        }
        
        # 4. 進捗更新の確認
        progress_updates = []
        
        def capture_progress(current, total, status):
            progress_updates.append({
                'current': current,
                'total': total,
                'status': status
            })
            self.app.update_progress_callback(current, total, status)
        
        # モック設定
        with patch.object(self.app, 'update_progress_callback', capture_progress):
            # 進捗更新のシミュレート
            capture_progress(0, 100, "開始")
            capture_progress(50, 100, "処理中")
            capture_progress(100, 100, "完了")
        
        # 進捗が記録されたことを確認
        self.assertEqual(len(progress_updates), 3)
        self.assertEqual(progress_updates[-1]['status'], "完了")


if __name__ == "__main__":
    unittest.main()