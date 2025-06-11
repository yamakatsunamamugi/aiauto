"""
設定画面モジュール

アプリケーションの各種設定を管理するダイアログを提供します。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional
import json
import os
from pathlib import Path

from src.gui.components import (
    LabeledEntry, LabeledCombobox, ValidationMixin, TooltipMixin
)


class SettingsDialog(ValidationMixin, TooltipMixin):
    """設定ダイアログクラス"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.config_data = config_manager.config_data.copy()
        
        # ダイアログ作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("設定")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 親ウィンドウの中央に配置
        self.center_window()
        
        # UI構築
        self.setup_ui()
        self.load_settings()
        
    def center_window(self):
        """ウィンドウを親ウィンドウの中央に配置"""
        self.dialog.update_idletasks()
        
        # 親ウィンドウの位置とサイズを取得
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # ダイアログのサイズを取得
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        # 中央位置を計算
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
    def setup_ui(self):
        """UI構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ダイアログのリサイズ設定
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # タブウィジェット
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(0, weight=1)
        
        # 各タブを作成
        self.create_general_tab()
        self.create_ai_tab()
        self.create_automation_tab()
        self.create_logging_tab()
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # ボタン配置
        ttk.Button(button_frame, text="OK", command=self.save_and_close, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="適用", command=self.apply_settings, width=10).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="キャンセル", command=self.cancel, width=10).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_frame, text="デフォルト", command=self.reset_to_default, width=10).grid(row=0, column=3)
        
        # 右寄せ
        button_frame.columnconfigure(4, weight=1)
        
    def create_general_tab(self):
        """一般設定タブ"""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text="一般")
        
        # スプレッドシート設定
        sheet_frame = ttk.LabelFrame(tab_frame, text="スプレッドシート設定", padding="10")
        sheet_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        sheet_frame.columnconfigure(0, weight=1)
        
        # スプレッドシートURL
        self.url_entry = LabeledEntry(
            sheet_frame, 
            "スプレッドシートURL:", 
            width=50,
            validate_func=self.validate_url,
            tooltip_text="Google SheetsのURLを入力してください"
        )
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # シート名
        self.sheet_name_entry = LabeledEntry(
            sheet_frame,
            "シート名:",
            width=30,
            tooltip_text="作業対象のシート名を入力してください"
        )
        self.sheet_name_entry.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # 作業列設定
        work_frame = ttk.LabelFrame(tab_frame, text="作業設定", padding="10")
        work_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        work_frame.columnconfigure(0, weight=1)
        
        # 作業開始行
        self.start_row_entry = LabeledEntry(
            work_frame,
            "作業開始行:",
            width=10,
            tooltip_text="作業を開始する行番号（デフォルト: 6）"
        )
        self.start_row_entry.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # コピー列検索文字列
        self.copy_column_entry = LabeledEntry(
            work_frame,
            "コピー列検索文字列:",
            width=20,
            tooltip_text="コピー列を特定するための文字列（デフォルト: 'コピー'）"
        )
        self.copy_column_entry.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        tab_frame.columnconfigure(0, weight=1)
        
    def create_ai_tab(self):
        """AI設定タブ"""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text="AI設定")
        
        # スクロール可能フレーム
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        tab_frame.columnconfigure(0, weight=1)
        tab_frame.rowconfigure(0, weight=1)
        
        # AI設定エントリー
        self.ai_entries = {}
        
        ai_configs = self.config_data.get("ai_configs", {})
        for i, (ai_name, ai_config) in enumerate(ai_configs.items()):
            # AI名の表示名
            display_names = {
                "chatgpt": "ChatGPT",
                "claude": "Claude",
                "gemini": "Gemini",
                "genspark": "Genspark",
                "google_ai_studio": "Google AI Studio"
            }
            display_name = display_names.get(ai_name, ai_name.title())
            
            # AIごとのフレーム
            ai_frame = ttk.LabelFrame(scrollable_frame, text=display_name, padding="10")
            ai_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            ai_frame.columnconfigure(0, weight=1)
            
            # URL設定
            url_entry = LabeledEntry(
                ai_frame,
                "URL:",
                width=50,
                validate_func=self.validate_url,
                tooltip_text=f"{display_name}のURLを入力してください"
            )
            url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
            url_entry.set(ai_config.get("url", ""))\n            
            # モデル設定
            model_entry = LabeledEntry(
                ai_frame,
                "モデル:",
                width=30,
                tooltip_text=f"{display_name}で使用するモデル名を入力してください"
            )
            model_entry.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
            model_entry.set(ai_config.get("model", ""))
            
            # 設定情報を保存
            self.ai_entries[ai_name] = {
                "url": url_entry,
                "model": model_entry
            }
            
        scrollable_frame.columnconfigure(0, weight=1)
        
    def create_automation_tab(self):
        """自動化設定タブ"""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text="自動化")
        
        # ブラウザ設定
        browser_frame = ttk.LabelFrame(tab_frame, text="ブラウザ設定", padding="10")
        browser_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        browser_frame.columnconfigure(0, weight=1)
        
        # ブラウザ選択
        self.browser_combo = LabeledCombobox(
            browser_frame,
            "ブラウザ:",
            values=["chrome", "firefox", "edge"],
            width=20,
            tooltip_text="使用するブラウザを選択してください"
        )
        self.browser_combo.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # ヘッドレスモード
        self.headless_var = tk.BooleanVar()
        headless_check = ttk.Checkbutton(
            browser_frame,
            text="ヘッドレスモード（ブラウザ画面を表示しない）",
            variable=self.headless_var
        )
        headless_check.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.create_tooltip(headless_check, "ブラウザを非表示で実行します")
        
        # タイムアウト設定
        timeout_frame = ttk.LabelFrame(tab_frame, text="タイムアウト設定", padding="10")
        timeout_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        timeout_frame.columnconfigure(0, weight=1)
        
        # ページタイムアウト
        self.page_timeout_entry = LabeledEntry(
            timeout_frame,
            "ページタイムアウト（秒）:",
            width=10,
            tooltip_text="ページ読み込みのタイムアウト時間"
        )
        self.page_timeout_entry.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 応答タイムアウト
        self.response_timeout_entry = LabeledEntry(
            timeout_frame,
            "応答タイムアウト（秒）:",
            width=10,
            tooltip_text="AI応答の待機タイムアウト時間"
        )
        self.response_timeout_entry.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # リトライ設定
        retry_frame = ttk.LabelFrame(tab_frame, text="リトライ設定", padding="10")
        retry_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        retry_frame.columnconfigure(0, weight=1)
        
        # リトライ回数
        self.retry_count_entry = LabeledEntry(
            retry_frame,
            "リトライ回数:",
            width=10,
            tooltip_text="エラー時のリトライ回数"
        )
        self.retry_count_entry.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # リトライ間隔
        self.retry_delay_entry = LabeledEntry(
            retry_frame,
            "リトライ間隔（秒）:",
            width=10,
            tooltip_text="リトライ間の待機時間"
        )
        self.retry_delay_entry.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        tab_frame.columnconfigure(0, weight=1)
        
    def create_logging_tab(self):
        """ログ設定タブ"""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text="ログ")
        
        # ログレベル設定
        level_frame = ttk.LabelFrame(tab_frame, text="ログレベル", padding="10")
        level_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        level_frame.columnconfigure(0, weight=1)
        
        # レベル選択
        self.log_level_combo = LabeledCombobox(
            level_frame,
            "ログレベル:",
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            width=15,
            tooltip_text="出力するログレベルを選択してください"
        )
        self.log_level_combo.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # ログファイル設定
        file_frame = ttk.LabelFrame(tab_frame, text="ログファイル", padding="10")
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        # ログファイルパス
        log_file_frame = ttk.Frame(file_frame)
        log_file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        log_file_frame.columnconfigure(0, weight=1)
        
        ttk.Label(log_file_frame, text="ログファイル:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.log_file_var = tk.StringVar()
        self.log_file_entry = ttk.Entry(log_file_frame, textvariable=self.log_file_var, width=40)
        self.log_file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(log_file_frame, text="参照", command=self.browse_log_file, width=8).grid(row=0, column=2)
        
        # ログローテーション設定
        self.log_rotation_var = tk.BooleanVar()
        rotation_check = ttk.Checkbutton(
            file_frame,
            text="ログローテーション（ファイルサイズ制限）",
            variable=self.log_rotation_var
        )
        rotation_check.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # 最大ファイルサイズ
        self.max_file_size_entry = LabeledEntry(
            file_frame,
            "最大ファイルサイズ（MB）:",
            width=10,
            tooltip_text="ログファイルの最大サイズ"
        )
        self.max_file_size_entry.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        tab_frame.columnconfigure(0, weight=1)
        
    def browse_log_file(self):
        """ログファイルを参照"""
        filename = filedialog.asksaveasfilename(
            title="ログファイルを選択",
            defaultextension=".log",
            filetypes=[("ログファイル", "*.log"), ("全てのファイル", "*.*")]
        )
        if filename:
            self.log_file_var.set(filename)
            
    def load_settings(self):
        """設定を読み込み"""
        try:
            # 一般設定
            self.url_entry.set(self.config_data.get("spreadsheet_url", ""))
            self.sheet_name_entry.set(self.config_data.get("sheet_name", ""))
            self.start_row_entry.set(str(self.config_data.get("start_row", 6)))
            self.copy_column_entry.set(self.config_data.get("copy_column_text", "コピー"))
            
            # AI設定
            ai_configs = self.config_data.get("ai_configs", {})
            for ai_name, entries in self.ai_entries.items():
                if ai_name in ai_configs:
                    ai_config = ai_configs[ai_name]
                    entries["url"].set(ai_config.get("url", ""))
                    entries["model"].set(ai_config.get("model", ""))
            
            # 自動化設定
            automation_config = self.config_data.get("automation", {})
            self.browser_combo.set(automation_config.get("browser", "chrome"))
            self.headless_var.set(automation_config.get("headless", False))
            self.page_timeout_entry.set(str(automation_config.get("timeout", 30)))
            self.response_timeout_entry.set(str(automation_config.get("response_timeout", 120)))
            self.retry_count_entry.set(str(automation_config.get("retry_count", 5)))
            self.retry_delay_entry.set(str(automation_config.get("retry_delay", 10)))
            
            # ログ設定
            logging_config = self.config_data.get("logging", {})
            self.log_level_combo.set(logging_config.get("level", "INFO"))
            self.log_file_var.set(logging_config.get("file", "logs/app.log"))
            self.log_rotation_var.set(logging_config.get("rotation", False))
            self.max_file_size_entry.set(str(logging_config.get("max_file_size", 10)))
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定読み込みエラー: {e}")
            
    def save_settings(self) -> bool:
        """設定を保存"""
        try:
            # 入力検証
            if not self._validate_inputs():
                return False
                
            # 一般設定
            self.config_data["spreadsheet_url"] = self.url_entry.get()
            self.config_data["sheet_name"] = self.sheet_name_entry.get()
            self.config_data["start_row"] = int(self.start_row_entry.get() or 6)
            self.config_data["copy_column_text"] = self.copy_column_entry.get() or "コピー"
            
            # AI設定
            ai_configs = self.config_data.setdefault("ai_configs", {})
            for ai_name, entries in self.ai_entries.items():
                if ai_name not in ai_configs:
                    ai_configs[ai_name] = {}
                ai_configs[ai_name]["url"] = entries["url"].get()
                ai_configs[ai_name]["model"] = entries["model"].get()
            
            # 自動化設定
            automation_config = self.config_data.setdefault("automation", {})
            automation_config["browser"] = self.browser_combo.get()
            automation_config["headless"] = self.headless_var.get()
            automation_config["timeout"] = int(self.page_timeout_entry.get() or 30)
            automation_config["response_timeout"] = int(self.response_timeout_entry.get() or 120)
            automation_config["retry_count"] = int(self.retry_count_entry.get() or 5)
            automation_config["retry_delay"] = int(self.retry_delay_entry.get() or 10)
            
            # ログ設定
            logging_config = self.config_data.setdefault("logging", {})
            logging_config["level"] = self.log_level_combo.get()
            logging_config["file"] = self.log_file_var.get()
            logging_config["rotation"] = self.log_rotation_var.get()
            logging_config["max_file_size"] = int(self.max_file_size_entry.get() or 10)
            
            return True
            
        except ValueError as e:
            messagebox.showerror("エラー", f"数値入力エラー: {e}")
            return False
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存エラー: {e}")
            return False
            
    def _validate_inputs(self) -> bool:
        """入力値の検証"""
        # URL檢証
        url = self.url_entry.get()
        if url and not self.validate_url(url):
            messagebox.showerror("エラー", "無効なスプレッドシートURLです。")
            return False
            
        # 数値入力の検証
        try:
            int(self.start_row_entry.get() or 6)
            int(self.page_timeout_entry.get() or 30)
            int(self.response_timeout_entry.get() or 120)
            int(self.retry_count_entry.get() or 5)
            int(self.retry_delay_entry.get() or 10)
            int(self.max_file_size_entry.get() or 10)
        except ValueError:
            messagebox.showerror("エラー", "数値入力に無効な値が含まれています。")
            return False
            
        return True
        
    def apply_settings(self):
        """設定を適用"""
        if self.save_settings():
            # 設定マネージャーに反映
            self.config_manager.config_data = self.config_data.copy()
            if self.config_manager.save_config():
                messagebox.showinfo("情報", "設定を適用しました。")
            else:
                messagebox.showerror("エラー", "設定ファイルの保存に失敗しました。")
                
    def save_and_close(self):
        """設定を保存して閉じる"""
        if self.save_settings():
            self.config_manager.config_data = self.config_data.copy()
            if self.config_manager.save_config():
                self.dialog.destroy()
            else:
                messagebox.showerror("エラー", "設定ファイルの保存に失敗しました。")
                
    def cancel(self):
        """キャンセル"""
        self.dialog.destroy()
        
    def reset_to_default(self):
        """デフォルト設定に戻す"""
        if messagebox.askyesno("確認", "設定をデフォルトに戻しますか？"):
            self.config_data = self.config_manager._get_default_config()
            self.load_settings()


if __name__ == "__main__":
    # テスト実行
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを隠す
    
    from src.utils.config_manager import ConfigManager
    config = ConfigManager()
    
    dialog = SettingsDialog(root, config)
    root.wait_window(dialog.dialog)
    
    root.destroy()