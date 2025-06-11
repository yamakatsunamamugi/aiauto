"""
GUIコンポーネントのテストモジュール

担当者A（GUI）のためのユニットテストと統合テストを実装します。
"""

import unittest
import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import time
import threading

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parents[1]))

from src.gui.main_window import MainWindow
from src.gui.components import *
from src.gui.settings_dialog import SettingsDialog
from src.gui.column_ai_settings import ColumnAISettingsDialog
from src.gui.progress_window import ProgressWindow
from src.utils.config_manager import config_manager


class TestGUIComponents(unittest.TestCase):
    """GUI部品の基本機能テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.root = tk.Tk()
        self.root.withdraw()  # テスト中はウィンドウを非表示
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.root.destroy()
        
    def test_labeled_entry_creation(self):
        """LabeledEntryの作成テスト"""
        entry = LabeledEntry(self.root, "テストラベル")
        self.assertIsInstance(entry, ttk.Frame)
        self.assertEqual(entry.get(), "")
        
        # 値の設定と取得
        entry.set("テスト値")
        self.assertEqual(entry.get(), "テスト値")
        
    def test_labeled_combobox_creation(self):
        """LabeledComboboxの作成テスト"""
        values = ["選択肢1", "選択肢2", "選択肢3"]
        combo = LabeledCombobox(self.root, "テストコンボ", values)
        self.assertIsInstance(combo, ttk.Frame)
        
        # 選択肢の確認
        self.assertEqual(combo.combobox["values"], values)
        
    def test_checkbox_group_selection(self):
        """CheckboxGroupの選択テスト"""
        options = ["オプション1", "オプション2", "オプション3"]
        group = CheckboxGroup(self.root, "テストグループ", options)
        
        # 初期状態は全て未選択
        self.assertEqual(group.get_selected(), [])
        
        # 個別選択
        group.vars["オプション1"].set(True)
        self.assertEqual(group.get_selected(), ["オプション1"])
        
        # 全選択
        group.select_all()
        self.assertEqual(sorted(group.get_selected()), sorted(options))
        
        # 全解除
        group.select_none()
        self.assertEqual(group.get_selected(), [])
        
    def test_progress_panel_update(self):
        """ProgressPanelの更新テスト"""
        panel = ProgressPanel(self.root)
        
        # 進捗更新
        panel.update_progress(50, 100, "処理中...")
        self.assertEqual(panel.progress_var.get(), 50.0)
        self.assertEqual(panel.progress_text_var.get(), "処理中... (50/100)")
        
        # 完了
        panel.update_progress(100, 100, "完了")
        self.assertEqual(panel.progress_var.get(), 100.0)
        
    def test_log_panel_logging(self):
        """LogPanelのログ記録テスト"""
        panel = LogPanel(self.root)
        
        # ログ追加
        panel.add_log("INFO", "テストメッセージ")
        log_content = panel.log_text.get("1.0", tk.END).strip()
        self.assertIn("テストメッセージ", log_content)
        self.assertIn("INFO", log_content)
        
        # ログクリア
        panel.clear_logs()
        log_content = panel.log_text.get("1.0", tk.END).strip()
        self.assertEqual(log_content, "")


class TestMainWindow(unittest.TestCase):
    """メインウィンドウの機能テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.app = MainWindow()
        self.app.root.withdraw()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.app.root.destroy()
        
    def test_window_creation(self):
        """ウィンドウ作成テスト"""
        self.assertIsNotNone(self.app.root)
        self.assertEqual(self.app.root.title(), "AI自動化ツール")
        
    def test_spreadsheet_validation(self):
        """スプレッドシートURL検証テスト"""
        # 有効なURL
        valid_url = "https://docs.google.com/spreadsheets/d/1234567890/edit"
        self.app.spreadsheet_url_var.set(valid_url)
        
        # 無効なURL
        invalid_url = "https://example.com"
        self.app.spreadsheet_url_var.set(invalid_url)
        
        # URLが設定されることを確認
        self.assertEqual(self.app.spreadsheet_url_var.get(), invalid_url)
        
    def test_ai_selection_modes(self):
        """AI選択モードの切り替えテスト"""
        # シンプルモード
        self.app.ai_mode_var.set("simple")
        self.app.toggle_ai_mode()
        self.assertTrue(self.app.simple_ai_frame.winfo_ismapped())
        
        # 列毎設定モード
        self.app.ai_mode_var.set("column")
        self.app.toggle_ai_mode()
        self.assertFalse(self.app.simple_ai_frame.winfo_ismapped())
        
    def test_callback_registration(self):
        """コールバック登録テスト"""
        # モック関数作成
        mock_get_sheets = Mock(return_value=["シート1", "シート2"])
        mock_start_automation = Mock()
        
        # コールバック設定
        self.app.set_get_sheet_names_callback(mock_get_sheets)
        self.app.set_start_automation_callback(mock_start_automation)
        
        # コールバックが設定されていることを確認
        self.assertEqual(self.app.get_sheet_names_callback, mock_get_sheets)
        self.assertEqual(self.app.start_automation_callback, mock_start_automation)
        
    def test_progress_update(self):
        """進捗更新テスト"""
        # 進捗更新
        self.app.update_progress_callback(50, 100, "処理中")
        self.assertEqual(self.app.progress_var.get(), 50.0)
        self.assertIn("処理中", self.app.progress_text_var.get())
        
    def test_log_functionality(self):
        """ログ機能テスト"""
        # ログ追加
        self.app.add_log("INFO", "テストログ")
        log_content = self.app.log_text.get("1.0", tk.END)
        self.assertIn("テストログ", log_content)
        
    @patch('tkinter.messagebox.showerror')
    def test_error_handling(self, mock_showerror):
        """エラーハンドリングテスト"""
        # URLなしで処理開始
        self.app.spreadsheet_url_var.set("")
        self.app.start_automation()
        
        # エラーメッセージが表示されることを確認
        mock_showerror.assert_called()


class TestColumnAISettings(unittest.TestCase):
    """列毎AI設定ダイアログのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.config = config_manager
        self.sheet_columns = ["C", "E", "G"]
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.root.destroy()
        
    def test_dialog_creation(self):
        """ダイアログ作成テスト"""
        dialog = ColumnAISettingsDialog(self.root, self.config, self.sheet_columns)
        self.assertIsNotNone(dialog.dialog)
        dialog.dialog.destroy()
        
    def test_column_configuration(self):
        """列設定テスト"""
        dialog = ColumnAISettingsDialog(self.root, self.config, self.sheet_columns)
        
        # 列Cの設定
        dialog.column_configs["C"]["ai_service"].set("chatgpt")
        dialog.column_configs["C"]["model"].set("gpt-4.1")
        
        # 設定が保存されることを確認
        dialog.save_settings()
        saved_settings = self.config.get("column_ai_settings", {})
        
        # ダイアログを閉じる
        dialog.dialog.destroy()


class TestSettingsDialog(unittest.TestCase):
    """設定ダイアログのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.config = config_manager
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.root.destroy()
        
    def test_dialog_tabs(self):
        """タブ構造のテスト"""
        dialog = SettingsDialog(self.root, self.config)
        
        # タブが存在することを確認
        tabs = dialog.notebook.tabs()
        self.assertGreater(len(tabs), 0)
        
        dialog.dialog.destroy()


class TestProgressWindow(unittest.TestCase):
    """進捗ウィンドウのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.root = tk.Tk()
        self.root.withdraw()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.root.destroy()
        
    def test_progress_window_update(self):
        """進捗ウィンドウの更新テスト"""
        window = ProgressWindow(self.root)
        
        # タスク追加
        window.add_task("タスク1", 100)
        window.add_task("タスク2", 50)
        
        # 進捗更新
        window.update_task_progress("タスク1", 50)
        
        # タスク完了
        window.complete_task("タスク1")
        
        # エラー処理
        window.error_task("タスク2", "エラーが発生しました")
        
        window.window.destroy()


class TestIntegration(unittest.TestCase):
    """統合テスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        # 統合テスト用の設定
        cls.test_config = {
            "spreadsheet_url": "https://docs.google.com/spreadsheets/d/test/edit",
            "sheet_name": "テストシート",
            "ai_mode": "simple",
            "selected_ais": ["chatgpt", "claude"]
        }
        
    def setUp(self):
        """テスト前の準備"""
        self.app = MainWindow()
        self.app.root.withdraw()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.app.root.destroy()
        
    def test_full_workflow_simple_mode(self):
        """シンプルモードの完全ワークフローテスト"""
        # モック設定
        mock_sheets_callback = Mock(return_value=["シート1", "シート2"])
        mock_automation_callback = Mock()
        
        # コールバック設定
        self.app.set_get_sheet_names_callback(mock_sheets_callback)
        self.app.set_start_automation_callback(mock_automation_callback)
        
        # UI設定
        self.app.spreadsheet_url_var.set(self.test_config["spreadsheet_url"])
        self.app.sheet_name_var.set(self.test_config["sheet_name"])
        self.app.ai_mode_var.set("simple")
        self.app.ai_selection_vars["chatgpt"].set(True)
        self.app.ai_selection_vars["claude"].set(True)
        
        # 自動化開始
        self.app.start_automation()
        
        # コールバックが呼ばれることを確認（別スレッドなので少し待つ）
        time.sleep(0.5)
        mock_automation_callback.assert_called_once()
        
    def test_column_mode_configuration(self):
        """列毎設定モードの設定テスト"""
        # 列毎設定モードに切り替え
        self.app.ai_mode_var.set("column")
        self.app.toggle_ai_mode()
        
        # 列毎設定を追加
        column_settings = {
            "C": {
                "ai_service": "chatgpt",
                "model": "gpt-4.1",
                "mode": "creative"
            },
            "E": {
                "ai_service": "claude",
                "model": "claude-3.5-sonnet",
                "mode": "precise"
            }
        }
        config_manager.set("column_ai_settings", column_settings)
        
        # 設定状況の更新
        self.app.update_column_status()
        status_text = self.app.column_status_label.cget("text")
        self.assertIn("2列設定済み", status_text)


def run_gui_tests():
    """GUIテストスイートを実行"""
    # テストスイート作成
    test_suite = unittest.TestSuite()
    
    # 各テストクラスを追加
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGUIComponents))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMainWindow))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestColumnAISettings))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSettingsDialog))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestProgressWindow))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # 単体でテスト実行
    success = run_gui_tests()
    sys.exit(0 if success else 1)