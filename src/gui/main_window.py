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
        section_frame = ttk.LabelFrame(parent, text="AI設定", padding="5")
        section_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        
        # 選択モード
        mode_frame = ttk.Frame(section_frame)
        mode_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.ai_mode_var = tk.StringVar(value="simple")
        ttk.Radiobutton(mode_frame, text="シンプル選択", variable=self.ai_mode_var, 
                       value="simple", command=self.toggle_ai_mode).grid(row=0, column=0, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="列毎設定", variable=self.ai_mode_var, 
                       value="column", command=self.toggle_ai_mode).grid(row=0, column=1, padx=(0, 20))
        
        # シンプル選択フレーム
        self.simple_ai_frame = ttk.Frame(section_frame)
        self.simple_ai_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
                "google_ai_studio": "Google AI Studio",
                "perplexity": "Perplexity AI"
            }
            display_name = display_names.get(ai_name, ai_name.title())
            
            var = tk.BooleanVar()
            self.ai_selection_vars[ai_name] = var
            
            checkbox = ttk.Checkbutton(self.simple_ai_frame, text=display_name, variable=var)
            checkbox.grid(row=row_count, column=col_count, sticky=tk.W, padx=(0, 20), pady=2)
            
            col_count += 1
            if col_count >= 3:  # 3列で改行
                col_count = 0
                row_count += 1
        
        # 全選択・全解除ボタン
        simple_button_frame = ttk.Frame(self.simple_ai_frame)
        simple_button_frame.grid(row=row_count + 1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        
        ttk.Button(simple_button_frame, text="全選択", command=self.select_all_ais, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(simple_button_frame, text="全解除", command=self.deselect_all_ais, width=10).grid(row=0, column=1)
        
        # 列毎設定フレーム
        self.column_ai_frame = ttk.Frame(section_frame)
        self.column_ai_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # 列毎設定説明
        ttk.Label(self.column_ai_frame, text="スプレッドシートの各列に個別のAI設定を適用できます", 
                 foreground="gray").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 列毎設定ボタン
        column_button_frame = ttk.Frame(self.column_ai_frame)
        column_button_frame.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        ttk.Button(column_button_frame, text="列毎AI設定を開く", 
                  command=self.open_column_ai_settings, width=20).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(column_button_frame, text="最新AI情報を取得", 
                  command=self.refresh_ai_info, width=20).grid(row=0, column=1)
        
        # 設定状況表示
        self.column_status_label = ttk.Label(self.column_ai_frame, text="列毎設定: 未設定", 
                                           foreground="gray")
        self.column_status_label.grid(row=2, column=0, sticky=tk.W)
        
        # 初期状態は列毎設定を非表示
        self.column_ai_frame.grid_remove()
        
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
                
            # AI設定モード
            ai_mode = self.config.get("ai_mode", "simple")
            self.ai_mode_var.set(ai_mode)
            self.toggle_ai_mode()
            
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
            
            # AI設定モード
            self.config.set("ai_mode", self.ai_mode_var.get())
            
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
                
        except FileNotFoundError as e:
            logger.error(f"認証ファイルが見つかりません: {e}")
            self.add_log("ERROR", "Google Sheets認証ファイルが見つかりません")
            messagebox.showerror("認証エラー", 
                "Google Sheets APIの認証ファイルが見つかりません。\n\n" +
                "config/credentials.json ファイルが存在することを確認してください。\n" +
                "詳細はドキュメントの「sheets_setup_guide.md」を参照してください。")
        except PermissionError as e:
            logger.error(f"アクセス権限エラー: {e}")
            self.add_log("ERROR", "スプレッドシートへのアクセス権限がありません")
            messagebox.showerror("権限エラー", 
                "指定されたスプレッドシートへのアクセス権限がありません。\n\n" +
                "以下を確認してください：\n" +
                "1. スプレッドシートが共有されている\n" +
                "2. サービスアカウントに編集権限が付与されている")
        except Exception as e:
            logger.error(f"シート名取得エラー: {e}")
            self.add_log("ERROR", f"シート名取得エラー: {str(e)}")
            messagebox.showerror("エラー", 
                f"シート名の取得に失敗しました。\n\n" +
                f"エラー内容: {str(e)}\n\n" +
                "URLが正しいか確認してください。")
            
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
        spreadsheet_url = self.spreadsheet_url_var.get().strip()
        if not spreadsheet_url:
            messagebox.showwarning("入力エラー", 
                "スプレッドシートURLを入力してください。\n\n" +
                "例: https://docs.google.com/spreadsheets/d/xxxxx/edit")
            self.url_entry.focus_set()
            return
        
        # URL形式の検証
        if not spreadsheet_url.startswith("https://docs.google.com/spreadsheets/d/"):
            messagebox.showwarning("URL形式エラー", 
                "有効なGoogleスプレッドシートのURLを入力してください。\n\n" +
                "正しい形式: https://docs.google.com/spreadsheets/d/xxxxx/edit")
            self.url_entry.focus_set()
            return
            
        sheet_name = self.sheet_name_var.get().strip()
        if not sheet_name:
            messagebox.showwarning("選択エラー", 
                "シート名を選択してください。\n\n" +
                "ヒント: まず[取得]ボタンをクリックしてシート一覧を取得してください。")
            self.sheet_combo.focus_set()
            return
        
        # AI設定モードに応じた検証
        ai_mode = self.ai_mode_var.get()
        if ai_mode == "simple":
            # シンプル選択モードの場合
            selected_ais = self.get_selected_ais()
            if not selected_ais:
                messagebox.showwarning("選択エラー", 
                    "少なくとも1つのAIサービスを選択してください。\n\n" +
                    "処理に使用するAIサービスにチェックを入れてください。")
                return
        else:
            # 列毎設定モードの場合
            column_settings = self.config.get("column_ai_settings", {})
            if not column_settings:
                messagebox.showwarning("設定エラー", 
                    "列毎AI設定を行ってください。\n\n" +
                    "[列毎AI設定を開く]ボタンをクリックして、\n" +
                    "各列で使用するAIサービスを設定してください。")
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
            "ai_mode": ai_mode
        }
        
        if ai_mode == "simple":
            config["selected_ais"] = selected_ais
        else:
            config["column_ai_settings"] = self.config.get("column_ai_settings", {})
        
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
            ai_mode = self.ai_mode_var.get()
            
            if ai_mode == "column":
                # 列毎AI設定モードの場合
                self._run_column_automation(config)
            else:
                # シンプル選択モードの場合（従来の処理）
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
    
    def _run_column_automation(self, config: Dict):
        """列毎AI設定モードでの自動化処理"""
        try:
            import asyncio
            from src.automation.automation_controller import AutomationController
            from src.sheets.sheets_client import create_sheets_client
            
            self.root.after(0, self.add_log, "INFO", "列毎AI設定モードで自動化を開始します")
            
            # 非同期処理を実行
            async def run_column_automation():
                try:
                    # Sheetsクライアントを作成
                    sheets_client = create_sheets_client()
                    
                    # AutomationControllerを初期化
                    automation_controller = AutomationController()
                    await automation_controller.initialize()
                    
                    # 列毎AI設定からタスクを作成
                    tasks = await automation_controller.create_tasks_from_sheet(
                        config["spreadsheet_url"],
                        config["sheet_name"],
                        sheets_client
                    )
                    
                    if not tasks:
                        self.root.after(0, self.add_log, "WARNING", "処理対象タスクが見つかりませんでした")
                        return
                    
                    # 必要なAIサービスを特定
                    required_ais = list(set(task.ai_service for task in tasks))
                    self.root.after(0, self.add_log, "INFO", f"必要なAIサービス: {required_ais}")
                    
                    # AIハンドラーをセットアップ
                    setup_results = await automation_controller.setup_ai_handlers(required_ais)
                    failed_ais = [ai for ai, success in setup_results.items() if not success]
                    
                    if failed_ais:
                        self.root.after(0, self.add_log, "WARNING", f"セットアップに失敗したAI: {failed_ais}")
                    
                    # 自動化処理開始
                    def progress_callback(current, total, message):
                        self.root.after(0, self.update_progress_callback, current, total, message)
                    
                    def log_callback(level, message):
                        self.root.after(0, self.add_log, level, message)
                    
                    success = await automation_controller.start_automation(
                        tasks, progress_callback, log_callback
                    )
                    
                    if success:
                        self.root.after(0, self.add_log, "INFO", "列毎AI自動化処理が完了しました")
                    else:
                        self.root.after(0, self.add_log, "ERROR", "列毎AI自動化処理に失敗しました")
                    
                    # クリーンアップ
                    await automation_controller.shutdown()
                    
                except Exception as e:
                    self.root.after(0, self.add_log, "ERROR", f"列毎AI自動化でエラー: {e}")
                    logger.error(f"列毎AI自動化エラー: {e}")
            
            # イベントループで実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_column_automation())
            loop.close()
            
        except Exception as e:
            self.root.after(0, self.add_log, "ERROR", f"列毎AI自動化の初期化エラー: {e}")
            logger.error(f"列毎AI自動化初期化エラー: {e}")
            
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
        
    def toggle_ai_mode(self):
        """AI設定モードを切り替え"""
        mode = self.ai_mode_var.get()
        
        if mode == "simple":
            self.simple_ai_frame.grid()
            self.column_ai_frame.grid_remove()
        else:  # column
            self.simple_ai_frame.grid_remove()
            self.column_ai_frame.grid()
            self.update_column_status()
            
    def open_column_ai_settings(self):
        """列毎AI設定ダイアログを開く"""
        try:
            # スプレッドシートの列情報を取得
            sheet_columns = self.get_sheet_columns()
            
            from src.gui.column_ai_settings import ColumnAISettingsDialog
            dialog = ColumnAISettingsDialog(self.root, self.config, sheet_columns)
            self.root.wait_window(dialog.dialog)
            
            # 設定状況を更新
            self.update_column_status()
            
        except ImportError as e:
            messagebox.showerror("エラー", f"列毎設定ダイアログの読み込みに失敗しました: {e}")
        except Exception as e:
            messagebox.showerror("エラー", f"列毎設定ダイアログを開けませんでした: {e}")
            
    def get_sheet_columns(self) -> List[str]:
        """スプレッドシートの列情報を取得"""
        try:
            # 実際のスプレッドシートから「コピー」列を検出
            spreadsheet_url = self.spreadsheet_url_var.get().strip()
            sheet_name = self.sheet_name_var.get().strip()
            
            if not spreadsheet_url or not sheet_name:
                # スプレッドシート情報が不完全な場合はデフォルト
                return ["C", "D", "E", "F", "G", "H", "I", "J"]
            
            # DataHandlerを使用して実際の「コピー」列を検出
            from src.sheets.sheets_client import create_sheets_client
            from src.sheets.data_handler import DataHandler
            from src.sheets.models import SheetConfig
            from src.utils.column_utils import column_number_to_letter
            
            sheets_client = create_sheets_client()
            data_handler = DataHandler(sheets_client)
            
            # シート設定を作成
            sheet_config = SheetConfig(
                spreadsheet_url=spreadsheet_url,
                sheet_name=sheet_name,
                spreadsheet_id=""  # __post_init__で自動設定される
            )
            
            # スプレッドシートデータを読み込み
            sheet_data = data_handler.load_and_validate_sheet(sheet_config)
            
            # 「コピー」列を検出
            copy_columns = data_handler.find_copy_columns(sheet_data)
            
            if copy_columns:
                # 実際の「コピー」列を列記号に変換
                column_letters = [column_number_to_letter(col) for col in copy_columns]
                self.add_log("INFO", f"検出された「コピー」列: {column_letters}")
                return column_letters
            else:
                # 「コピー」列が見つからない場合は一般的な位置を提案
                suggested_columns = ["C", "E", "G", "I"]  # C列から奇数列
                self.add_log("WARNING", f"「コピー」列が見つかりません。推奨位置: {suggested_columns}")
                return suggested_columns
                
        except Exception as e:
            logger.warning(f"列情報取得エラー: {e}")
            self.add_log("WARNING", f"列情報取得エラー: {e}")
            # エラー時はデフォルトの列を返す
            return ["C", "D", "E", "F", "G", "H", "I", "J"]
        
    def refresh_ai_info(self):
        """最新のAI情報を取得"""
        try:
            # Playwrightを使用して最新情報を取得
            self.add_log("INFO", "最新AI情報の取得を開始しています...")
            
            # 別スレッドで実行
            import threading
            
            def refresh_thread():
                try:
                    from src.utils.playwright_search import search_ai_models_sync
                    
                    ai_services = ["chatgpt", "claude", "gemini", "perplexity", "genspark"]
                    results = search_ai_models_sync(ai_services, headless=True)
                    
                    self.root.after(0, self._on_ai_info_refreshed, results)
                    
                except Exception as e:
                    self.root.after(0, self.add_log, "ERROR", f"AI情報取得エラー: {e}")
                    
            thread = threading.Thread(target=refresh_thread, daemon=True)
            thread.start()
            
        except ImportError:
            messagebox.showinfo("情報", "Playwright検索機能は未インストールです。")
        except Exception as e:
            self.add_log("ERROR", f"AI情報取得の開始に失敗しました: {e}")
            
    def _on_ai_info_refreshed(self, results):
        """AI情報取得完了時の処理"""
        if "batch_search_results" in results:
            success_count = sum(1 for info in results["batch_search_results"].values() 
                              if "error" not in info)
            total_count = len(results["batch_search_results"])
            
            self.add_log("INFO", f"AI情報取得完了: {success_count}/{total_count} サービス")
            
            # 取得した情報を設定に反映（今後実装）
            # self.update_ai_configs_from_search(results)
        else:
            self.add_log("WARNING", "AI情報の取得に失敗しました")
            
    def update_column_status(self):
        """列毎設定の状況を更新"""
        column_settings = self.config.get("column_ai_settings", {})
        
        if column_settings:
            count = len(column_settings)
            self.column_status_label.config(
                text=f"列毎設定: {count}列設定済み", 
                foreground="green"
            )
        else:
            self.column_status_label.config(
                text="列毎設定: 未設定", 
                foreground="gray"
            )
            
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