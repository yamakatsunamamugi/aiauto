"""
メインGUIウィンドウモジュール

AI自動化ツールのメインユーザーインターフェースを提供します。
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter.messagebox import showerror, showinfo
from typing import List, Dict, Callable, Optional
import threading
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parents[2]))

from src.utils.config_manager import config_manager
from src.utils.logger import logger


class MainWindow:
    """メインGUIウィンドウクラス"""
    
    def __init__(self):
        """MainWindowの初期化"""
        self.root = tk.Tk()
        self.config = config_manager
        
        # 状態管理
        self.is_running = False
        self.automation_thread = None
        
        # コールバック関数（他モジュールとの連携用）
        self.get_sheet_names_callback: Optional[Callable[[str], List[str]]] = None
        self.start_automation_callback: Optional[Callable[[Dict, Callable], None]] = None
        
        # GUI部品の参照
        self.spreadsheet_url_var = tk.StringVar()
        self.sheet_name_var = tk.StringVar()
        self.ai_selection_vars = {}
        self.progress_var = tk.DoubleVar()
        self.progress_text_var = tk.StringVar(value="待機中...")
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """UIの初期設定"""
        # ウィンドウ設定
        self.root.title("AI自動化ツール")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ウィンドウのリサイズ設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # スプレッドシート設定セクション
        self._create_spreadsheet_section(main_frame, 0)
        
        # AI選択セクション
        self._create_ai_selection_section(main_frame, 1)
        
        # 制御ボタンセクション
        self._create_control_section(main_frame, 2)
        
        # 進捗表示セクション
        self._create_progress_section(main_frame, 3)
        
        # ログ表示セクション
        self._create_log_section(main_frame, 4)
        
    def _create_spreadsheet_section(self, parent: ttk.Frame, row: int):
        """スプレッドシート設定セクションを作成"""
        # セクションフレーム
        section_frame = ttk.LabelFrame(parent, text="スプレッドシート設定", padding="5")
        section_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        section_frame.columnconfigure(1, weight=1)
        
        # スプレッドシートURL
        ttk.Label(section_frame, text="スプレッドシートURL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        url_frame = ttk.Frame(section_frame)
        url_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_frame, textvariable=self.spreadsheet_url_var, width=50)
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(url_frame, text="取得", command=self.load_sheet_names, width=8).grid(row=0, column=1)
        
        # シート名選択
        ttk.Label(section_frame, text="シート名:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.sheet_combo = ttk.Combobox(section_frame, textvariable=self.sheet_name_var, state="readonly", width=30)
        self.sheet_combo.grid(row=1, column=1, sticky=tk.W, pady=(0, 5))
        
    def _create_ai_selection_section(self, parent: ttk.Frame, row: int):
        """AI選択セクションを作成"""
        # セクションフレーム
        section_frame = ttk.LabelFrame(parent, text="AI選択", padding="5")
        section_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        
        # AI選択チェックボックス
        ai_configs = self.config.get("ai_configs", {})
        row_count = 0
        col_count = 0
        
        for ai_name, ai_config in ai_configs.items():
            # 表示名を日本語に変換
            display_names = {
                "chatgpt": "ChatGPT",
                "claude": "Claude",
                "gemini": "Gemini",
                "genspark": "Genspark",
                "google_ai_studio": "Google AI Studio"
            }
            display_name = display_names.get(ai_name, ai_name.title())
            
            var = tk.BooleanVar()
            self.ai_selection_vars[ai_name] = var
            
            checkbox = ttk.Checkbutton(section_frame, text=display_name, variable=var)
            checkbox.grid(row=row_count, column=col_count, sticky=tk.W, padx=(0, 20), pady=2)
            
            col_count += 1
            if col_count >= 3:  # 3列で改行
                col_count = 0
                row_count += 1
        
        # 全選択・全解除ボタン
        button_frame = ttk.Frame(section_frame)
        button_frame.grid(row=row_count + 1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        
        ttk.Button(button_frame, text="全選択", command=self.select_all_ais, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="全解除", command=self.deselect_all_ais, width=10).grid(row=0, column=1)
        
    def _create_control_section(self, parent: ttk.Frame, row: int):
        """制御ボタンセクションを作成"""
        # セクションフレーム
        section_frame = ttk.Frame(parent)
        section_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # ボタンフレーム（中央寄せ）
        button_frame = ttk.Frame(section_frame)
        button_frame.pack(anchor="center")
        
        # 開始ボタン
        self.start_button = ttk.Button(button_frame, text="処理開始", command=self.start_automation, width=15)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # 停止ボタン
        self.stop_button = ttk.Button(button_frame, text="処理停止", command=self.stop_automation, width=15, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        # 設定ボタン
        ttk.Button(button_frame, text="設定", command=self.open_settings, width=10).grid(row=0, column=2)
        
    def _create_progress_section(self, parent: ttk.Frame, row: int):
        """進捗表示セクションを作成"""
        # セクションフレーム
        section_frame = ttk.LabelFrame(parent, text="進捗状況", padding="5")
        section_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        section_frame.columnconfigure(0, weight=1)
        
        # 進捗バー
        self.progress_bar = ttk.Progressbar(section_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 進捗テキスト
        self.progress_label = ttk.Label(section_frame, textvariable=self.progress_text_var)
        self.progress_label.grid(row=1, column=0, sticky=tk.W)
        
    def _create_log_section(self, parent: ttk.Frame, row: int):
        """ログ表示セクションを作成"""
        # セクションフレーム
        section_frame = ttk.LabelFrame(parent, text="ログ", padding="5")
        section_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        section_frame.columnconfigure(0, weight=1)
        section_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
        
        # ログテキストエリア
        self.log_text = scrolledtext.ScrolledText(section_frame, height=10, width=80, wrap=tk.WORD, state="disabled")
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ログクリアボタン
        button_frame = ttk.Frame(section_frame)
        button_frame.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(button_frame, text="ログクリア", command=self.clear_log, width=12).grid(row=0, column=0)
        
    def load_settings(self):
        """設定を読み込んでUIに反映"""
        try:
            # スプレッドシートURL
            url = self.config.get("spreadsheet_url", "")
            self.spreadsheet_url_var.set(url)
            
            # シート名
            sheet_name = self.config.get("sheet_name", "")
            self.sheet_name_var.set(sheet_name)
            
            # AI選択状態（デフォルトでChatGPTのみ選択）
            selected_ais = self.config.get("selected_ais", ["chatgpt"])
            for ai_name, var in self.ai_selection_vars.items():
                var.set(ai_name in selected_ais)
            
            logger.info("設定を読み込みました")
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
            self.add_log("ERROR", f"設定読み込みエラー: {e}")
            
    def save_settings(self):
        """現在の設定を保存"""
        try:
            # スプレッドシート設定
            self.config.set("spreadsheet_url", self.spreadsheet_url_var.get())
            self.config.set("sheet_name", self.sheet_name_var.get())
            
            # AI選択状態
            selected_ais = [ai_name for ai_name, var in self.ai_selection_vars.items() if var.get()]
            self.config.set("selected_ais", selected_ais)
            
            # 設定ファイル保存
            self.config.save_config()
            
            logger.info("設定を保存しました")
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
            self.add_log("ERROR", f"設定保存エラー: {e}")
            
    def load_sheet_names(self):
        """スプレッドシートからシート名一覧を取得"""
        url = self.spreadsheet_url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "スプレッドシートURLを入力してください。")
            return
            
        try:
            # 他モジュールのコールバック関数を呼び出し
            if self.get_sheet_names_callback:
                sheet_names = self.get_sheet_names_callback(url)
                self.sheet_combo['values'] = sheet_names
                if sheet_names:
                    self.sheet_combo.current(0)
                    self.add_log("INFO", f"シート名を取得しました: {len(sheet_names)}個")
                else:
                    self.add_log("WARNING", "シートが見つかりませんでした")
            else:
                # 開発用のダミーデータ
                dummy_sheets = ["Sheet1", "作業データ", "結果"]
                self.sheet_combo['values'] = dummy_sheets
                self.sheet_combo.current(0)
                self.add_log("INFO", "ダミーシート名を設定しました（開発用）")
                
        except Exception as e:
            logger.error(f"シート名取得エラー: {e}")
            self.add_log("ERROR", f"シート名取得エラー: {e}")
            messagebox.showerror("エラー", f"シート名の取得に失敗しました。\n{e}")
            
    def select_all_ais(self):
        """全AIを選択"""
        for var in self.ai_selection_vars.values():
            var.set(True)
            
    def deselect_all_ais(self):
        """全AIの選択を解除"""
        for var in self.ai_selection_vars.values():
            var.set(False)
            
    def get_selected_ais(self) -> List[str]:
        """選択されたAIのリストを取得"""
        return [ai_name for ai_name, var in self.ai_selection_vars.items() if var.get()]
        
    def start_automation(self):
        """自動化処理を開始"""
        if self.is_running:
            return
            
        # 入力検証
        if not self.spreadsheet_url_var.get().strip():
            messagebox.showwarning("警告", "スプレッドシートURLを入力してください。")
            return
            
        if not self.sheet_name_var.get().strip():
            messagebox.showwarning("警告", "シート名を選択してください。")
            return
            
        selected_ais = self.get_selected_ais()
        if not selected_ais:
            messagebox.showwarning("警告", "少なくとも1つのAIを選択してください。")
            return
            
        # 設定保存
        self.save_settings()
        
        # UI状態変更
        self.is_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_var.set(0)
        self.progress_text_var.set("処理を開始しています...")
        
        # 設定オブジェクト作成
        config = {
            "spreadsheet_url": self.spreadsheet_url_var.get(),
            "sheet_name": self.sheet_name_var.get(),
            "selected_ais": selected_ais
        }
        
        # 別スレッドで自動化処理実行
        self.automation_thread = threading.Thread(
            target=self._run_automation_thread,
            args=(config,),
            daemon=True
        )
        self.automation_thread.start()
        
        self.add_log("INFO", "自動化処理を開始しました")
        
    def _run_automation_thread(self, config: Dict):
        """別スレッドで自動化処理を実行"""
        try:
            if self.start_automation_callback:
                self.start_automation_callback(config, self.update_progress_callback)
            else:
                # 開発用のダミー処理
                import time
                for i in range(101):
                    if not self.is_running:
                        break
                    time.sleep(0.1)
                    self.root.after(0, self.update_progress_callback, i, 100, f"処理中... {i}%")
                
        except Exception as e:
            logger.error(f"自動化処理エラー: {e}")
            self.root.after(0, self.add_log, "ERROR", f"自動化処理エラー: {e}")
        finally:
            self.root.after(0, self._automation_finished)
            
    def stop_automation(self):
        """自動化処理を停止"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.progress_text_var.set("処理を停止しています...")
        self.add_log("INFO", "自動化処理の停止を要求しました")
        
    def _automation_finished(self):
        """自動化処理完了時の処理"""
        self.is_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_text_var.set("処理完了")
        self.add_log("INFO", "自動化処理が完了しました")
        
    def update_progress_callback(self, current: int, total: int, message: str = ""):
        """進捗更新コールバック（他モジュールから呼び出される）"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
            
        if message:
            self.progress_text_var.set(message)
            
        # UIを更新
        self.root.update_idletasks()
        
    def add_log(self, level: str, message: str):
        """ログを追加"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}\n"
        
        # ログテキストエリアに追加
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        
        # 系統ログにも出力
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
            
    def clear_log(self):
        """ログをクリア"""
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        
    def open_settings(self):
        """設定画面を開く"""
        try:
            from src.gui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.root, self.config)
            self.root.wait_window(dialog.dialog)
        except ImportError:
            # 設定画面が未実装の場合
            messagebox.showinfo("情報", "設定画面は開発中です。")
            
    def set_get_sheet_names_callback(self, callback: Callable[[str], List[str]]):
        """シート名取得コールバックを設定"""
        self.get_sheet_names_callback = callback
        
    def set_start_automation_callback(self, callback: Callable[[Dict, Callable], None]):
        """自動化開始コールバックを設定"""
        self.start_automation_callback = callback
        
    def run(self):
        """メインループを開始"""
        try:
            self.add_log("INFO", "AI自動化ツールを起動しました")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            logger.error(f"アプリケーション実行エラー: {e}")
            messagebox.showerror("エラー", f"アプリケーションエラーが発生しました。\n{e}")
            
    def on_closing(self):
        """アプリケーション終了時の処理"""
        if self.is_running:
            if messagebox.askokcancel("確認", "処理中です。終了しますか？"):
                self.stop_automation()
            else:
                return
                
        self.save_settings()
        self.add_log("INFO", "AI自動化ツールを終了しました")
        self.root.destroy()


if __name__ == "__main__":
    # テスト実行
    app = MainWindow()
    app.run()