#!/usr/bin/env python3
"""
メインGUIウィンドウ
AI自動化システムのメインインターフェース
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import asyncio
import threading
from typing import Dict, List, Optional, Callable
import logging
from datetime import datetime

from src.automation.automation_controller import AutomationController
from src.sheets.models import AIService, ColumnAIConfig
from src.sheets.data_handler import DataHandler
from src.utils.logger import logger
from src.gui.column_ai_config import ColumnAIConfigDialog
from src.gui.simple_model_updater import update_models_sync, SimpleModelUpdater as AIModelUpdater


class MainWindow:
    """メインGUIウィンドウクラス"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.automation_controller = None
        self.automation_thread = None
        self.is_running = False
        
        # Sheets統合
        self.data_handler = DataHandler()
        self.current_sheet_structure = None
        self.current_task_rows = None
        self.available_sheets = []
        
        # GUI状態管理
        self.status_text = tk.StringVar(value="待機中")
        self.progress_var = tk.DoubleVar()
        self.log_buffer = []
        
        self.setup_ui()
        self.setup_logging()
        
    def setup_ui(self):
        """UIセットアップ"""
        self.root.title("AI自動化システム v1.0")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ウィンドウリサイズ対応
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # === スプレッドシート設定セクション ===
        self.create_spreadsheet_section(main_frame, 0)
        
        # === データプレビューセクション ===
        self.create_data_preview_section(main_frame, 1)
        
        # === AI設定セクション ===
        self.create_ai_section(main_frame, 2)
        
        # === 制御セクション ===
        self.create_control_section(main_frame, 3)
        
        # === ログセクション ===
        self.create_log_section(main_frame, 4)
        
        # === ステータスバー ===
        self.create_status_bar(main_frame, 5)
        
    def create_spreadsheet_section(self, parent, row):
        """スプレッドシート設定セクション"""
        # フレーム
        frame = ttk.LabelFrame(parent, text="📊 Googleスプレッドシート設定", padding="5")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        frame.columnconfigure(1, weight=1)
        
        # スプレッドシートURL
        ttk.Label(frame, text="スプレッドシートURL:").grid(row=0, column=0, sticky=tk.W, padx=5)
        # テスト用URLをデフォルトで設定
        self.sheet_url_var = tk.StringVar(value="https://docs.google.com/spreadsheets/d/1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg/edit?gid=1633283608#gid=1633283608")
        url_entry = ttk.Entry(frame, textvariable=self.sheet_url_var, width=60)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # シート名選択
        ttk.Label(frame, text="シート名:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        # テスト用シート名をデフォルトで設定
        self.sheet_name_var = tk.StringVar(value="1.原稿本文作成")
        self.sheet_name_combo = ttk.Combobox(frame, textvariable=self.sheet_name_var, state="readonly")
        self.sheet_name_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.sheet_name_combo.bind("<<ComboboxSelected>>", self.on_sheet_selected)
        
        # シート情報読込ボタン
        self.load_sheet_btn = ttk.Button(frame, text="📋 シート情報読込", command=self.load_sheet_info)
        self.load_sheet_btn.grid(row=0, column=2, padx=5)
        
    def create_ai_section(self, parent, row):
        """AI設定セクション"""
        # フレーム
        frame = ttk.LabelFrame(parent, text="🤖 AI設定", padding="5")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        frame.columnconfigure(1, weight=1)
        
        # AI選択
        ttk.Label(frame, text="使用AI:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ai_service_var = tk.StringVar(value="chatgpt")
        ai_combo = ttk.Combobox(frame, textvariable=self.ai_service_var, 
                               values=["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"],
                               state="readonly")
        ai_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ai_combo.bind("<<ComboboxSelected>>", self.on_ai_service_changed)
        
        # モデル選択
        ttk.Label(frame, text="モデル:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ai_model_var = tk.StringVar()
        self.ai_model_combo = ttk.Combobox(frame, textvariable=self.ai_model_var, state="readonly")
        self.ai_model_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 設定オプション
        self.ai_features_frame = ttk.Frame(frame)
        self.ai_features_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # ログイン状態
        ttk.Label(frame, text="ログイン状態:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.login_status_var = tk.StringVar(value="未確認")
        self.login_status_label = ttk.Label(frame, textvariable=self.login_status_var, foreground="orange")
        self.login_status_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # ボタンフレーム
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=2, columnspan=2, padx=5, pady=5)
        
        # ログイン確認ボタン
        self.check_login_btn = ttk.Button(btn_frame, text="🔐 ログイン確認", command=self.check_login_status)
        self.check_login_btn.pack(side=tk.LEFT, padx=2)
        
        # 最新情報更新ボタン
        self.update_models_btn = ttk.Button(btn_frame, text="🔄 最新情報更新", command=self.update_ai_models)
        self.update_models_btn.pack(side=tk.LEFT, padx=2)
        
        # モデル編集ボタン
        self.edit_models_btn = ttk.Button(btn_frame, text="📝 モデル編集", command=self.edit_model_json)
        self.edit_models_btn.pack(side=tk.LEFT, padx=2)
        
    def create_control_section(self, parent, row):
        """制御セクション"""
        # フレーム
        frame = ttk.LabelFrame(parent, text="⚙️ 実行制御", padding="5")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # ボタンフレーム
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=0, column=0, columnspan=2, pady=5)
        
        # 開始ボタン
        self.start_btn = ttk.Button(btn_frame, text="▶️ 自動化開始", command=self.start_automation)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        # 停止ボタン
        self.stop_btn = ttk.Button(btn_frame, text="⏹️ 停止", command=self.stop_automation, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        # 設定保存ボタン
        self.save_config_btn = ttk.Button(btn_frame, text="💾 設定保存", command=self.save_config)
        self.save_config_btn.grid(row=0, column=2, padx=5)
        
        # 設定読込ボタン
        self.load_config_btn = ttk.Button(btn_frame, text="📁 設定読込", command=self.load_config)
        self.load_config_btn.grid(row=0, column=3, padx=5)
        
        # 進捗バー
        ttk.Label(frame, text="進捗:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        frame.columnconfigure(1, weight=1)
        
    def create_log_section(self, parent, row):
        """ログセクション"""
        # フレーム
        frame = ttk.LabelFrame(parent, text="📝 実行ログ", padding="5")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # ログテキストエリア
        self.log_text = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ログクリアボタン
        clear_log_btn = ttk.Button(frame, text="🗑️ ログクリア", command=self.clear_log)
        clear_log_btn.grid(row=1, column=0, pady=5)
        
        # メインフレームの行の重みを設定（ログセクションが伸縮可能）
        parent.rowconfigure(row, weight=1)
        
    def create_status_bar(self, parent, row):
        """ステータスバー"""
        # フレーム
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        frame.columnconfigure(1, weight=1)
        
        # ステータス
        ttk.Label(frame, text="状態:").grid(row=0, column=0, padx=5)
        status_label = ttk.Label(frame, textvariable=self.status_text, foreground="blue")
        status_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 時刻表示
        self.time_var = tk.StringVar()
        time_label = ttk.Label(frame, textvariable=self.time_var)
        time_label.grid(row=0, column=2, padx=5)
        
        # 時刻更新
        self.update_time()
        
    def setup_logging(self):
        """ログ設定"""
        # カスタムログハンドラーでGUIに出力
        class GUILogHandler(logging.Handler):
            def __init__(self, gui_window):
                super().__init__()
                self.gui_window = gui_window
                
            def emit(self, record):
                log_entry = self.format(record)
                self.gui_window.add_log_entry(log_entry)
        
        # ハンドラー追加
        gui_handler = GUILogHandler(self)
        gui_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(formatter)
        
        # ルートロガーに追加
        root_logger = logging.getLogger()
        root_logger.addHandler(gui_handler)
        
    def add_log_entry(self, message):
        """ログエントリ追加"""
        def update_log():
            self.log_text.insert(tk.END, message + "\\n")
            self.log_text.see(tk.END)
            
        # メインスレッドで実行
        self.root.after(0, update_log)
        
    def update_time(self):
        """時刻更新"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(current_time)
        self.root.after(1000, self.update_time)
        
    def create_data_preview_section(self, parent, row):
        """データプレビューセクション"""
        # フレーム
        frame = ttk.LabelFrame(parent, text="📋 データプレビューと列ごとのAI設定", padding="5")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)  # 列AI設定セクションのために変更
        
        # 情報表示
        info_frame = ttk.Frame(frame)
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        info_frame.columnconfigure(1, weight=1)
        
        # シート構造情報
        ttk.Label(info_frame, text="作業ヘッダー行:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.header_row_var = tk.StringVar(value="未検出")
        ttk.Label(info_frame, textvariable=self.header_row_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(info_frame, text="コピー列数:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.copy_columns_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.copy_columns_var).grid(row=0, column=3, sticky=tk.W, padx=5)
        
        ttk.Label(info_frame, text="処理対象行数:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.task_rows_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.task_rows_var).grid(row=0, column=5, sticky=tk.W, padx=5)
        
        # 列ごとのAI設定セクション（プレビューの前に配置）
        self.create_column_ai_section(frame, 1)
        
        # プレビューテーブル
        columns = ("行", "コピー列", "コピーテキスト", "AI設定", "状態")
        self.preview_tree = ttk.Treeview(frame, columns=columns, show="headings", height=5)
        
        # 列ごとのAI設定を保存
        self.column_ai_config = {}
        
        # 列設定
        self.preview_tree.heading("行", text="行")
        self.preview_tree.heading("コピー列", text="コピー列")
        self.preview_tree.heading("コピーテキスト", text="コピーテキスト")
        self.preview_tree.heading("AI設定", text="AI設定")
        self.preview_tree.heading("状態", text="状態")
        
        self.preview_tree.column("行", width=50)
        self.preview_tree.column("コピー列", width=80)
        self.preview_tree.column("コピーテキスト", width=300)
        self.preview_tree.column("AI設定", width=120)
        self.preview_tree.column("状態", width=80)
        
        # スクロールバー
        preview_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=preview_scroll.set)
        
        self.preview_tree.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_scroll.grid(row=2, column=1, sticky=(tk.N, tk.S))
        
        # メインフレームの行の重みを設定
        parent.rowconfigure(row, weight=1)
        
    def load_sheet_info(self):
        """シート情報読込"""
        url = self.sheet_url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "スプレッドシートURLを入力してください")
            return
            
        def load_async():
            try:
                self.root.after(0, lambda: self.add_log_entry("🔄 Google Sheets API認証中..."))
                
                # 認証
                auth_success = self.data_handler.authenticate()
                if not auth_success:
                    self.root.after(0, lambda: self.add_log_entry("❌ Google Sheets API認証に失敗しました"))
                    self.root.after(0, lambda: messagebox.showerror("エラー", "Google Sheets API認証に失敗しました\\n\\nconfig/credentials.json を確認してください"))
                    return
                
                self.root.after(0, lambda: self.add_log_entry("✅ Google Sheets API認証成功"))
                self.root.after(0, lambda: self.add_log_entry("🔄 シート一覧を取得中..."))
                
                # シート一覧取得
                sheets = self.data_handler.get_available_sheets(url)
                if not sheets:
                    self.root.after(0, lambda: self.add_log_entry("❌ シート一覧の取得に失敗しました"))
                    self.root.after(0, lambda: messagebox.showerror("エラー", "シート一覧の取得に失敗しました\\n\\nURLとアクセス権限を確認してください"))
                    return
                
                # UI更新
                sheet_names = [sheet['title'] for sheet in sheets]
                self.available_sheets = sheets
                
                self.root.after(0, lambda: self._update_sheet_combo(sheet_names))
                self.root.after(0, lambda: self.add_log_entry(f"✅ シート一覧取得完了: {len(sheets)}個のシート"))
                
                # 最初のシートを自動選択して解析
                if sheets:
                    first_sheet = sheets[0]['title']
                    self.root.after(0, lambda: self.sheet_name_var.set(first_sheet))
                    self.root.after(0, lambda: self.analyze_selected_sheet())
                    
            except Exception as e:
                error_msg = f"シート情報読込エラー: {e}"
                self.root.after(0, lambda: self.add_log_entry(f"❌ {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("エラー", error_msg))
        
        # 非同期実行
        threading.Thread(target=load_async, daemon=True).start()
        
    def _update_sheet_combo(self, sheet_names):
        """シートコンボボックス更新"""
        self.sheet_name_combo['values'] = sheet_names
        self.sheet_name_combo['state'] = 'readonly'
        
    def analyze_selected_sheet(self):
        """選択されたシートを解析"""
        url = self.sheet_url_var.get().strip()
        sheet_name = self.sheet_name_var.get()
        
        if not url or not sheet_name:
            return
            
        def analyze_async():
            try:
                self.root.after(0, lambda: self.add_log_entry(f"🔍 シート解析中: {sheet_name}"))
                
                # シート構造解析
                structure = self.data_handler.load_sheet_from_url(url, sheet_name)
                if not structure:
                    self.root.after(0, lambda: self.add_log_entry("❌ シート構造の解析に失敗しました"))
                    return
                
                self.current_sheet_structure = structure
                
                # タスク行作成
                task_rows = self.data_handler.create_task_rows(structure)
                
                # タスク行を保存
                self.current_task_rows = task_rows
                
                # UI更新
                self.root.after(0, lambda: self._update_preview_display(structure, task_rows))
                self.root.after(0, lambda: self.add_log_entry(f"✅ シート解析完了: {len(task_rows)}件のタスク"))
                
            except Exception as e:
                error_msg = f"シート解析エラー: {e}"
                self.root.after(0, lambda: self.add_log_entry(f"❌ {error_msg}"))
        
        threading.Thread(target=analyze_async, daemon=True).start()
        
    def _update_preview_display(self, structure, task_rows):
        """プレビュー表示更新"""
        # 構造情報更新
        self.header_row_var.set(f"{structure.work_header_row}行目")
        self.copy_columns_var.set(str(len(structure.copy_columns)))
        self.task_rows_var.set(str(len(task_rows)))
        
        # 列AI設定セクションを更新
        self.update_column_ai_section()
        
        # プレビューテーブルクリア
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # タスク行をプレビューに追加
        for i, task in enumerate(task_rows[:20]):  # 最大20件表示
            copy_col_letter = self._number_to_column_letter(task.column_positions.copy_column + 1)
            copy_text = task.copy_text[:50] + "..." if len(task.copy_text) > 50 else task.copy_text
            
            # 列ごとのAI設定を確認
            if copy_col_letter in self.column_ai_config:
                config = self.column_ai_config[copy_col_letter]
                ai_setting = f"{config['ai_service']}/{config['ai_model']}"
            else:
                ai_setting = f"{task.ai_config.ai_service.value}/{task.ai_config.ai_model}"
            
            self.preview_tree.insert("", "end", values=(
                task.row_number,
                copy_col_letter,
                copy_text,
                ai_setting,
                task.status
            ))
        
        # 20件以上ある場合は省略表示
        if len(task_rows) > 20:
            self.preview_tree.insert("", "end", values=(
                "...", "...", f"他 {len(task_rows) - 20} 件", "...", "..."
            ))
            
    def _number_to_column_letter(self, num: int) -> str:
        """列番号をA1形式の文字に変換"""
        result = ""
        while num > 0:
            num -= 1
            result = chr(65 + (num % 26)) + result
            num //= 26
        return result
        
    def on_sheet_selected(self, event=None):
        """シート選択時の処理"""
        self.analyze_selected_sheet()
        
    def on_ai_service_changed(self, event=None):
        """AIサービス変更時の処理"""
        service = self.ai_service_var.get()
        
        # 最新情報があれば使用、なければデフォルト
        try:
            updater = AIModelUpdater()
            cached_info = updater.get_cached_info()
            
            if "ai_services" in cached_info and service in cached_info["ai_services"]:
                service_info = cached_info["ai_services"][service]
                if "models" in service_info and service_info["models"]:
                    models = service_info["models"]
                else:
                    models = self._get_default_models(service)
            else:
                models = self._get_default_models(service)
                
        except Exception:
            models = self._get_default_models(service)
        
        self.ai_model_combo['values'] = models
        if models:
            self.ai_model_var.set(models[0])
            
        # 機能オプションを更新
        self.update_ai_features(service)
        
    def update_ai_features(self, service):
        """AI機能オプション更新"""
        # 既存のウィジェットをクリア
        for widget in self.ai_features_frame.winfo_children():
            widget.destroy()
            
        # 最新情報から機能を取得、なければデフォルト
        try:
            updater = AIModelUpdater()
            cached_info = updater.get_cached_info()
            
            if "ai_services" in cached_info and service in cached_info["ai_services"]:
                service_info = cached_info["ai_services"][service]
                if "features" in service_info:
                    feature_mapping = {
                        "vision": "画像認識",
                        "code_interpreter": "コード実行",
                        "web_search": "Web検索",
                        "dalle": "画像生成",
                        "artifacts": "アーティファクト",
                        "projects": "プロジェクト",
                        "multimodal": "マルチモーダル",
                        "code_execution": "コード実行",
                        "research": "リサーチ",
                        "citations": "引用"
                    }
                    features = [feature_mapping.get(f, f) for f in service_info["features"]]
                else:
                    features = self._get_default_features(service)
            else:
                features = self._get_default_features(service)
                
        except Exception:
            features = self._get_default_features(service)
        
        ttk.Label(self.ai_features_frame, text="機能オプション:").grid(row=0, column=0, sticky=tk.W)
        
        self.feature_vars = {}
        
        for i, feature in enumerate(features):
            var = tk.BooleanVar()
            self.feature_vars[feature] = var
            cb = ttk.Checkbutton(self.ai_features_frame, text=feature, variable=var)
            cb.grid(row=0, column=i+1, padx=5)
            
    def check_login_status(self):
        """ログイン状態確認"""
        def check_async():
            try:
                self.login_status_var.set("確認中...")
                self.login_status_label.configure(foreground="orange")
                
                # 選択されているAIサービスをブラウザで開く
                service = self.ai_service_var.get()
                urls = {
                    "chatgpt": "https://chat.openai.com",
                    "claude": "https://claude.ai",
                    "gemini": "https://gemini.google.com",
                    "genspark": "https://www.genspark.ai",
                    "google_ai_studio": "https://aistudio.google.com"
                }
                
                if service in urls:
                    import webbrowser
                    webbrowser.open(urls[service])
                    self.add_log_entry(f"🌐 {service}のログインページを開きました")
                    
                    # ブラウザが開いたことを示す
                    self.login_status_var.set("ブラウザで確認")
                    self.login_status_label.configure(foreground="blue")
                else:
                    self.login_status_var.set("サービス不明")
                    self.login_status_label.configure(foreground="red")
                    
            except Exception as e:
                self.login_status_var.set("エラー")
                self.login_status_label.configure(foreground="red")
                self.add_log_entry(f"❌ ログイン確認エラー: {e}")
                
        threading.Thread(target=check_async, daemon=True).start()
        
    def start_automation(self):
        """自動化開始"""
        if self.is_running:
            return
            
        # バリデーション
        if not self.sheet_url_var.get().strip():
            messagebox.showwarning("警告", "スプレッドシートURLを入力してください")
            return
            
        if not self.sheet_name_var.get():
            messagebox.showwarning("警告", "シート名を選択してください")
            return
            
        if not self.current_sheet_structure:
            messagebox.showwarning("警告", "シート情報を読み込んでください")
            return
            
        # UI状態更新
        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_text.set("実行中")
        
        # 自動化開始
        self.automation_thread = threading.Thread(target=self.run_automation, daemon=True)
        self.automation_thread.start()
        
        self.add_log_entry("🚀 AI自動化を開始しました")
        
    def run_automation(self):
        """自動化実行（別スレッド）"""
        try:
            # タスク行を取得
            task_rows = self.data_handler.create_task_rows(self.current_sheet_structure)
            total_tasks = len(task_rows)
            
            if total_tasks == 0:
                self.add_log_entry("⚠️ 処理対象のタスクがありません")
                return
            
            self.add_log_entry(f"📋 処理対象タスク: {total_tasks}件")
            
            # AutomationControllerの初期化
            if not self.automation_controller:
                self.automation_controller = AutomationController()
                
            # 各タスクを処理
            for i, task_row in enumerate(task_rows):
                if not self.is_running:
                    break
                    
                try:
                    # 列ごとのAI設定を適用
                    copy_col_letter = self._number_to_column_letter(task_row.column_positions.copy_column + 1)
                    if copy_col_letter in self.column_ai_config:
                        config = self.column_ai_config[copy_col_letter]
                        # AI設定を更新
                        task_row.ai_config.ai_service = AIService(config['ai_service'])
                        task_row.ai_config.ai_model = config['ai_model']
                    
                    # 進捗更新
                    progress = (i / total_tasks) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    
                    self.add_log_entry(f"🔄 タスク{i+1}/{total_tasks}: 行{task_row.row_number}")
                    self.add_log_entry(f"📝 コピーテキスト: {task_row.copy_text[:100]}...")
                    self.add_log_entry(f"🤖 使用AI: {task_row.ai_config.ai_service.value}/{task_row.ai_config.ai_model}")
                    
                    # AI処理（実際の処理）
                    result_text = None
                    try:
                        # ChromeAIExtension方式でAI処理を試行
                        result_text = self._process_with_chrome_extension(
                            task_row.copy_text,
                            task_row.ai_config.ai_service.value,
                            task_row.ai_config.ai_model
                        )
                    except Exception as chrome_error:
                        self.add_log_entry(f"Chrome拡張エラー: {chrome_error}")
                        result_text = f"エラー: Chrome拡張での処理に失敗しました"
                    
                    # Playwright AI処理（実装版）
                    if result_text.startswith("エラー:") or result_text.startswith("Chrome拡張エラー:"):
                        try:
                            from src.automation.playwright_handler import PlaywrightAIHandler
                            
                            # Playwright処理用のタスクデータを作成
                            playwright_task = {
                                'text': task_row.copy_text,
                                'ai_service': task_row.ai_config.ai_service.value,
                                'model': task_row.ai_config.ai_model,
                                'task_id': f"task_{task_row.row_number}"
                            }
                            
                            # Playwrightで処理
                            async def playwright_process():
                                async with PlaywrightAIHandler() as handler:
                                    results = await handler.process_batch_parallel([playwright_task])
                                    return results[0] if results else None
                            
                            import asyncio
                            result = asyncio.run(playwright_process())
                            
                            if result and result.get('success'):
                                result_text = result.get('result', 'Playwrightで処理完了')
                                self.add_log_entry(f"✅ Playwright処理成功")
                            else:
                                result_text = f"Playwrightエラー: {result.get('error', '不明なエラー')}"
                                self.add_log_entry(f"❌ Playwright処理失敗: {result.get('error')}")
                                
                        except Exception as playwright_error:
                            self.add_log_entry(f"❌ Playwright処理エラー: {playwright_error}")
                            result_text = f"処理エラー: Chrome拡張とPlaywright両方で失敗しました"
                    
                    demo_result = result_text
                    
                    # 結果をシートに書き戻し
                    success = self.data_handler.update_task_result(task_row, demo_result)
                    
                    if success:
                        self.add_log_entry(f"✅ タスク{i+1}完了: 結果をシートに書き戻しました")
                        
                        # プレビュー表示を更新
                        self.root.after(0, lambda: self._refresh_preview_after_update(task_row.row_number, "処理済み"))
                    else:
                        self.add_log_entry(f"❌ タスク{i+1}エラー: シート書き戻しに失敗")
                        
                except Exception as task_error:
                    self.add_log_entry(f"❌ タスク{i+1}エラー: {task_error}")
                    
            # 最終進捗更新
            self.root.after(0, lambda: self.progress_var.set(100))
            
            if self.is_running:
                self.add_log_entry("🎉 全ての自動化処理が完了しました！")
            else:
                self.add_log_entry("⏹️ 自動化処理が停止されました")
                
        except Exception as e:
            self.add_log_entry(f"❌ 自動化実行エラー: {e}")
            
        finally:
            # UI状態リセット
            self.root.after(0, self.reset_ui_state)
            
    def _refresh_preview_after_update(self, row_number, new_status):
        """プレビュー表示を部分更新"""
        try:
            # プレビューテーブルの該当行を更新
            for item in self.preview_tree.get_children():
                values = self.preview_tree.item(item, 'values')
                if values and str(values[0]) == str(row_number):
                    # 状態列を更新
                    new_values = list(values)
                    new_values[4] = new_status  # 状態列
                    self.preview_tree.item(item, values=new_values)
                    break
        except Exception as e:
            logger.warning(f"プレビュー更新エラー: {e}")
            
    def stop_automation(self):
        """自動化停止"""
        self.is_running = False
        self.add_log_entry("🛑 自動化停止要求を送信しました")
        
    def reset_ui_state(self):
        """UI状態リセット"""
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_text.set("待機中")
        self.progress_var.set(0)
        
    def save_config(self):
        """設定保存"""
        try:
            filename = filedialog.asksaveasfilename(
                title="設定保存",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                # TODO: 設定保存処理
                self.add_log_entry(f"💾 設定を保存しました: {filename}")
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存に失敗しました: {e}")
            
    def load_config(self):
        """設定読込"""
        try:
            filename = filedialog.askopenfilename(
                title="設定読込",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                # TODO: 設定読込処理
                self.add_log_entry(f"📁 設定を読み込みました: {filename}")
        except Exception as e:
            messagebox.showerror("エラー", f"設定読込に失敗しました: {e}")
            
    def clear_log(self):
        """ログクリア"""
        self.log_text.delete(1.0, tk.END)
        self.add_log_entry("🗑️ ログをクリアしました")
        
    def create_column_ai_section(self, parent, row):
        """列ごとのAI設定セクション"""
        # フレーム
        frame = ttk.LabelFrame(parent, text="🤖 列ごとのAI設定", padding="5")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        frame.columnconfigure(0, weight=1)
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(frame, height=120)
        scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)
        
        # 列AI設定ウィジェットを保存
        self.column_ai_widgets = {}
        
        # ヘッダー
        ttk.Label(scrollable_frame, text="列", font=("", 9, "bold")).grid(row=0, column=0, padx=5, pady=2)
        
        # 初期メッセージ
        self.no_columns_label = ttk.Label(scrollable_frame, text="シートを読み込むと列が表示されます", foreground="gray")
        self.no_columns_label.grid(row=1, column=0, columnspan=5, padx=20, pady=20)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E))
        scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.column_ai_canvas = canvas
        self.column_ai_scrollable_frame = scrollable_frame
        
    def update_column_ai_section(self):
        """列AI設定セクションを更新"""
        # 既存のウィジェットをクリア
        for widget in self.column_ai_scrollable_frame.winfo_children():
            widget.destroy()
            
        if not self.current_sheet_structure or not self.current_sheet_structure.copy_columns:
            # 列がない場合のメッセージ
            ttk.Label(self.column_ai_scrollable_frame, text="コピー列が見つかりません", foreground="gray").grid(
                row=0, column=0, padx=20, pady=20
            )
            return
            
        # ヘッダー行
        ttk.Label(self.column_ai_scrollable_frame, text="列", font=("", 9, "bold")).grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(self.column_ai_scrollable_frame, text="AIサービス", font=("", 9, "bold")).grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(self.column_ai_scrollable_frame, text="モデル", font=("", 9, "bold")).grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(self.column_ai_scrollable_frame, text="詳細設定", font=("", 9, "bold")).grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(self.column_ai_scrollable_frame, text="状態", font=("", 9, "bold")).grid(row=4, column=0, padx=5, pady=2, sticky=tk.W)
        
        # 各列の設定
        self.column_ai_widgets = {}
        col_idx = 1
        
        for col_info in self.current_sheet_structure.copy_columns:
            col_letter = col_info.column_letter
            
            # 列名
            ttk.Label(self.column_ai_scrollable_frame, text=col_letter, font=("", 10, "bold")).grid(
                row=0, column=col_idx, padx=5, pady=2
            )
            
            # AIサービス選択
            service_var = tk.StringVar(value=self.column_ai_config.get(col_letter, {}).get("ai_service", "chatgpt"))
            service_combo = ttk.Combobox(
                self.column_ai_scrollable_frame,
                textvariable=service_var,
                values=["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"],
                state="readonly",
                width=15
            )
            service_combo.grid(row=1, column=col_idx, padx=5, pady=2)
            
            # モデル選択
            model_var = tk.StringVar(value=self.column_ai_config.get(col_letter, {}).get("ai_model", ""))
            model_combo = ttk.Combobox(
                self.column_ai_scrollable_frame,
                textvariable=model_var,
                state="readonly",
                width=15
            )
            model_combo.grid(row=2, column=col_idx, padx=5, pady=2)
            
            # 詳細設定ボタン
            detail_btn = ttk.Button(
                self.column_ai_scrollable_frame,
                text="設定",
                command=lambda c=col_letter: self._open_column_detail_settings(c),
                width=12
            )
            detail_btn.grid(row=3, column=col_idx, padx=5, pady=2)
            
            # 状態表示
            status_var = tk.StringVar(value="未設定")
            status_label = ttk.Label(
                self.column_ai_scrollable_frame,
                textvariable=status_var,
                foreground="orange",
                font=("", 8)
            )
            status_label.grid(row=4, column=col_idx, padx=5, pady=2)
            
            # ウィジェット保存
            self.column_ai_widgets[col_letter] = {
                "service_var": service_var,
                "model_var": model_var,
                "service_combo": service_combo,
                "model_combo": model_combo,
                "detail_btn": detail_btn,
                "status_var": status_var,
                "status_label": status_label
            }
            
            # サービス変更時のイベント
            service_combo.bind("<<ComboboxSelected>>", 
                             lambda e, c=col_letter: self._on_column_service_changed(c))
            
            # モデル変更時のイベント
            model_combo.bind("<<ComboboxSelected>>",
                           lambda e, c=col_letter: self._on_column_model_changed(c))
            
            # 初期モデルリスト更新
            self._update_column_model_options(col_letter)
            
            col_idx += 1
            
    def _on_column_service_changed(self, column):
        """列のサービス変更時"""
        self._update_column_model_options(column)
        self._save_column_ai_config(column)
        
    def _on_column_model_changed(self, column):
        """列のモデル変更時"""
        self._save_column_ai_config(column)
        
    def _update_column_model_options(self, column):
        """列のモデルオプション更新"""
        widgets = self.column_ai_widgets.get(column)
        if not widgets:
            return
            
        service = widgets["service_var"].get()
        
        # 最新情報があれば使用、なければデフォルト
        try:
            updater = AIModelUpdater()
            cached_info = updater.get_cached_info()
            
            if "ai_services" in cached_info and service in cached_info["ai_services"]:
                service_info = cached_info["ai_services"][service]
                if "models" in service_info and service_info["models"]:
                    models = service_info["models"]
                else:
                    models = self._get_default_models(service)
            else:
                models = self._get_default_models(service)
                
        except Exception:
            models = self._get_default_models(service)
            
        widgets["model_combo"]["values"] = models
        if models and not widgets["model_var"].get():
            widgets["model_var"].set(models[0])
            
    def _save_column_ai_config(self, column):
        """列のAI設定を保存"""
        widgets = self.column_ai_widgets.get(column)
        if widgets:
            self.column_ai_config[column] = {
                "ai_service": widgets["service_var"].get(),
                "ai_model": widgets["model_var"].get()
            }
            # プレビューを更新
            if self.current_sheet_structure and self.current_task_rows:
                self._update_preview_display(self.current_sheet_structure, self.current_task_rows)
        
    def configure_column_ai(self):
        """列ごとのAI設定"""
        if not self.current_sheet_structure:
            messagebox.showwarning("警告", "まずシートをロードしてください")
            return
            
        # コピー列のリストを取得
        copy_columns = []
        for col_info in self.current_sheet_structure.copy_columns:
            copy_columns.append(col_info.column_letter)
            
        if not copy_columns:
            messagebox.showinfo("情報", "コピー列が見つかりません")
            return
            
        # ダイアログ表示
        dialog = ColumnAIConfigDialog(self.root, copy_columns, self.column_ai_config)
        result = dialog.show()
        
        if result:
            self.column_ai_config = result
            self.add_log_entry("✅ 列ごとのAI設定を更新しました")
            # プレビューを更新
            if self.current_sheet_structure and self.current_task_rows:
                self._update_preview_display(self.current_sheet_structure, self.current_task_rows)
                
    def update_ai_models(self):
        """最新のAIモデル情報を更新"""
        def update_async():
            try:
                self.add_log_entry("🔄 AIモデル情報を読み込んでいます...")
                self.update_models_btn.configure(state="disabled")
                
                # 検証済みJSONファイルからモデル情報を取得
                results = update_models_sync()
                
                # 結果を表示
                success_count = 0
                for service, info in results.items():
                    if "error" not in info:
                        success_count += 1
                        models = info.get("models", [])
                        self.add_log_entry(f"✅ {service}: {len(models)}個のモデルを読み込み")
                        if models:
                            self.add_log_entry(f"   モデル: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}")
                    else:
                        self.add_log_entry(f"⚠️ {service}: 読み込み失敗")
                        
                self.add_log_entry(f"🎯 読み込み完了: {success_count}/5 サービス")
                
                # モデル選択肢を更新
                self._update_model_options_from_latest()
                
            except Exception as e:
                self.add_log_entry(f"❌ 最新情報更新エラー: {e}")
            finally:
                self.update_models_btn.configure(state="normal")
                
        threading.Thread(target=update_async, daemon=True).start()
        
    def _update_model_options_from_browser_session(self, results: Dict):
        """ブラウザセッション方式の結果からモデル選択肢を更新"""
        try:
            # 結果をファイルに保存（永続化）
            import json
            with open("config/ai_models_browser_session.json", 'w', encoding='utf-8') as f:
                json.dump({
                    "method": "browser_session",
                    "last_updated": datetime.now().isoformat(),
                    "results": results
                }, f, indent=2, ensure_ascii=False)
            
            # 現在のサービスのモデルリストを更新
            current_service = self.ai_service_var.get()
            if current_service in results and "models" in results[current_service]:
                models = results[current_service]["models"]
                if models:
                    self.ai_model_combo["values"] = models
                    # 現在の選択が無効な場合は最初のモデルを選択
                    if self.ai_model_var.get() not in models:
                        self.ai_model_var.set(models[0])
                        
        except Exception as e:
            logger.error(f"ブラウザセッション結果の更新エラー: {e}")
        
    def _update_model_options_from_latest(self):
        """最新情報からモデル選択肢を更新"""
        try:
            updater = AIModelUpdater()
            cached_info = updater.get_cached_info()
            
            if "ai_services" in cached_info:
                # モデル選択肢を更新
                for service, info in cached_info["ai_services"].items():
                    if "models" in info and info["models"]:
                        # 現在のサービスと一致する場合、モデルリストを更新
                        if self.ai_service_var.get() == service:
                            self.ai_model_combo["values"] = info["models"]
                            # 現在の選択が無効な場合は最初のモデルを選択
                            if self.ai_model_var.get() not in info["models"]:
                                self.ai_model_var.set(info["models"][0])
                                
        except Exception as e:
            logger.error(f"モデル選択肢更新エラー: {e}")
            
    def _get_default_models(self, service: str) -> List[str]:
        """デフォルトのモデルリストを取得"""
        default_models = {
            "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "claude": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "gemini-pro-vision"],
            "genspark": ["default", "advanced"],
            "google_ai_studio": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
        }
        return default_models.get(service, ["default"])
        
    def _get_default_features(self, service: str) -> List[str]:
        """デフォルトの機能リストを取得"""
        default_features = {
            "chatgpt": ["画像認識", "コード実行", "Web検索", "画像生成"],
            "claude": ["画像認識", "アーティファクト", "プロジェクト"],
            "gemini": ["画像認識", "マルチモーダル", "コード実行"],
            "genspark": ["リサーチ", "引用"],
            "google_ai_studio": ["画像認識", "マルチモーダル", "コード実行"]
        }
        return default_features.get(service, [])
        
    def edit_model_json(self):
        """モデルJSONを編集"""
        try:
            from src.gui.model_json_editor import ModelJsonEditor
            
            self.add_log_entry("📝 モデル編集ダイアログを開きます...")
            
            # 編集ダイアログを表示
            editor = ModelJsonEditor(self.root)
            result = editor.show()
            
            if result:
                self.add_log_entry("✅ モデル設定を保存しました")
                
                # モデルリストを再読み込み
                self.update_ai_models()
            else:
                self.add_log_entry("❌ モデル編集をキャンセルしました")
                
        except Exception as e:
            self.add_log_entry(f"❌ モデル編集エラー: {e}")
            messagebox.showerror("エラー", f"モデル編集エラー: {e}")
        
    def run(self):
        """GUIアプリケーション実行"""
        self.add_log_entry("🎉 AI自動化システムを起動しました")
        self.add_log_entry("📋 スプレッドシートURLとシート名を設定してください")
        self.add_log_entry("🤖 使用するAIサービスとモデルを選択してください")
        
        # 初期AI設定
        self.on_ai_service_changed()
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.add_log_entry("🛑 アプリケーションが終了されました")
        finally:
            if self.automation_controller:
                # TODO: クリーンアップ処理
                pass


def main():
    """メイン関数"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()