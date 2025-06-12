#!/usr/bin/env python3
"""
CLAUDE.md要件完全対応 - スプレッドシート自動化GUIアプリケーション
Claude専用版（ブラウザ自動化機能統合）

このファイルは gui_automation_app_browser.py のClaude専用コピーです。
他の方が使用している gui_automation_app_fixed.py に影響を与えません。
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading
import time
from pathlib import Path
import logging

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# 動的インポート
def import_modules():
    """必要なモジュールを動的にインポート"""
    global SheetsClient, ExtensionBridge, BrowserAutomationHandler
    
    try:
        from src.sheets.sheets_client import SheetsClient
    except ImportError:
        logging.warning("SheetsClient not found")
        SheetsClient = None
    
    try:
        from src.automation.extension_bridge import ExtensionBridge
    except ImportError:
        logging.warning("ExtensionBridge not found")
        ExtensionBridge = None
    
    try:
        from src.automation.browser_automation_handler import BrowserAutomationHandler
    except ImportError:
        logging.warning("BrowserAutomationHandler not found")
        BrowserAutomationHandler = None

import_modules()

class SpreadsheetAutomationGUI:
    """CLAUDE.md要件完全対応GUIクラス - Claude専用版"""
    
    def __init__(self, root):
        """GUI初期化"""
        self.root = root
        self.root.title("スプレッドシート自動化システム - Claude専用版 (API不要ブラウザ自動化対応)")
        self.root.geometry("1500x1100")
        
        # データ格納
        self.spreadsheet_url = ""
        self.sheet_name = ""
        self.sheet_data = []
        self.work_row = None
        self.copy_columns = []
        self.column_configs = {}
        
        # 自動化モード
        self.automation_mode = tk.StringVar(value="browser")  # デフォルトでブラウザモード
        
        # デバッグモード
        self.debug_mode = True
        
        # APIクライアント
        self.sheets_client = None
        self.extension_bridge = None
        self.browser_handler = None
        
        # AI設定データ（ブラウザ自動化対応）
        self.available_ais = {
            "ChatGPT": {
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "settings": ["DeepThink", "Web検索", "画像認識", "コード実行", "画像生成"],
                "browser_supported": True
            },
            "Claude": {
                "models": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-haiku"],
                "settings": ["DeepThink", "画像認識", "アーティファクト", "プロジェクト"],
                "browser_supported": True
            },
            "Gemini": {
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
                "settings": ["DeepThink", "画像認識", "マルチモーダル", "コード実行"],
                "browser_supported": True
            },
            "Genspark": {
                "models": ["default"],
                "settings": ["リサーチ", "引用", "最新情報"],
                "browser_supported": False
            },
            "Google AI Studio": {
                "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
                "settings": ["DeepThink", "画像認識", "マルチモーダル", "コード実行"],
                "browser_supported": False
            }
        }
        
        # ブラウザセッション状態
        self.browser_sessions = {}
        
        # ブラウザ設定のデフォルト値
        self.browser_profile_path = None
        self.browser_headless = False
        
        self.create_widgets()
        self.initialize_clients()
    
    def create_widgets(self):
        """ウィジェット作成"""
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 0. 自動化モード選択セクション
        mode_frame = ttk.LabelFrame(main_frame, text="🔧 自動化モード選択", padding="10")
        mode_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Radiobutton(mode_frame, text="Chrome拡張機能モード（高速）", 
                       variable=self.automation_mode, value="extension",
                       command=self.on_mode_change).grid(row=0, column=0, padx=10)
        
        ttk.Radiobutton(mode_frame, text="ブラウザ自動化モード（API不要）", 
                       variable=self.automation_mode, value="browser",
                       command=self.on_mode_change).grid(row=0, column=1, padx=10)
        
        # モード説明
        self.mode_info_label = ttk.Label(mode_frame, text="", foreground="blue")
        self.mode_info_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # ブラウザ設定ボタン
        self.browser_settings_btn = ttk.Button(mode_frame, text="ブラウザ設定", 
                                             command=self.open_browser_settings)
        self.browser_settings_btn.grid(row=0, column=2, padx=10)
        
        # 1. スプレッドシート設定セクション
        setup_frame = ttk.LabelFrame(main_frame, text="📊 スプレッドシート設定", padding="10")
        setup_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # スプレッドシートURL
        ttk.Label(setup_frame, text="スプレッドシートURL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(setup_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5)
        ttk.Button(setup_frame, text="URLから読込", command=self.load_from_url).grid(row=0, column=2, padx=5)
        
        # シート名
        ttk.Label(setup_frame, text="シート名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.sheet_combo = ttk.Combobox(setup_frame, width=30, state="readonly")
        self.sheet_combo.grid(row=1, column=1, padx=5, sticky=tk.W)
        ttk.Button(setup_frame, text="シート情報読込", command=self.load_sheet_info).grid(row=1, column=2, padx=5)
        
        # 2. 作業指示行情報
        info_frame = ttk.LabelFrame(main_frame, text="📋 作業指示行情報", padding="10")
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.info_text = tk.Text(info_frame, height=4, width=80)
        self.info_text.grid(row=0, column=0, columnspan=2)
        
        # 3. コピー列設定セクション
        columns_frame = ttk.LabelFrame(main_frame, text="🤖 各コピー列のAI設定", padding="10")
        columns_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(columns_frame, height=300, bg='white')
        scrollbar = ttk.Scrollbar(columns_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(self.canvas_window, width=canvas.winfo_width())
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        # マウスホイールでスクロール
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        import platform
        if platform.system() == 'Darwin':
            canvas.bind("<MouseWheel>", on_mousewheel)
        else:
            canvas.bind("<MouseWheel>", on_mousewheel)
            canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        columns_frame.columnconfigure(0, weight=1)
        columns_frame.rowconfigure(0, weight=1)
        
        # 4. 実行制御セクション
        control_frame = ttk.LabelFrame(main_frame, text="🚀 実行制御", padding="10")
        control_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(control_frame, text="設定保存", command=self.save_config).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="設定読込", command=self.load_config).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="自動化開始", command=self.start_automation).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="停止", command=self.stop_automation).grid(row=0, column=3, padx=5)
        
        # ブラウザセッション管理ボタン
        self.session_btn = ttk.Button(control_frame, text="セッション管理", 
                                    command=self.manage_browser_sessions)
        self.session_btn.grid(row=0, column=4, padx=5)
        
        # 進捗表示
        self.progress = ttk.Progressbar(control_frame, mode='determinate')
        self.progress.grid(row=1, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(control_frame, text="待機中...")
        self.status_label.grid(row=2, column=0, columnspan=5)
        
        # 5. ログセクション
        log_frame = ttk.LabelFrame(main_frame, text="📝 実行ログ", padding="10")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=15, width=100)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 初期モード設定
        self.on_mode_change()
    
    def on_mode_change(self):
        """自動化モード変更時の処理"""
        mode = self.automation_mode.get()
        
        if mode == "extension":
            self.mode_info_label.config(text="Chrome拡張機能を使用した高速処理モード")
            self.browser_settings_btn.grid_remove()
            self.session_btn.grid_remove()
        else:
            self.mode_info_label.config(text="API不要！既存のログインセッションを使用するモード")
            self.browser_settings_btn.grid()
            self.session_btn.grid()
        
        self.log(f"🔄 自動化モードを「{mode}」に変更しました")
    
    def open_browser_settings(self):
        """ブラウザ設定ダイアログ"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("ブラウザ自動化設定")
        settings_window.geometry("500x400")
        
        # プロファイルパス設定
        ttk.Label(settings_window, text="Chromeプロファイルパス:").pack(pady=5)
        profile_entry = ttk.Entry(settings_window, width=50)
        profile_entry.pack(padx=20, pady=5)
        
        # デフォルトパスを設定
        import platform
        if platform.system() == "Darwin":
            default_path = str(Path.home() / "Library/Application Support/Google/Chrome/Default")
        elif platform.system() == "Windows":
            default_path = str(Path.home() / "AppData/Local/Google/Chrome/User Data/Default")
        else:
            default_path = str(Path.home() / ".config/google-chrome/Default")
        
        profile_entry.insert(0, default_path)
        
        # ヘッドレスモード
        headless_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_window, text="ヘッドレスモード（画面非表示）", 
                       variable=headless_var).pack(pady=10)
        
        # 説明
        info_text = tk.Text(settings_window, height=10, width=60, wrap=tk.WORD)
        info_text.pack(padx=20, pady=10)
        info_text.insert(1.0, """ブラウザ自動化の設定：

1. Chromeプロファイルパス：
   既にログイン済みのChromeプロファイルを指定することで、
   APIキーなしで有料プランを利用できます。

2. ヘッドレスモード：
   チェックすると画面が表示されずにバックグラウンドで
   処理されます（デバッグ時はOFFを推奨）。

注意：初回実行時は各AIサービスにログインした状態で
Chromeを一度閉じてから実行してください。""")
        info_text.config(state=tk.DISABLED)
        
        # 保存ボタン
        def save_browser_settings():
            self.browser_profile_path = profile_entry.get()
            self.browser_headless = headless_var.get()
            settings_window.destroy()
            self.log(f"✅ ブラウザ設定を保存しました")
        
        ttk.Button(settings_window, text="保存", command=save_browser_settings).pack(pady=10)
    
    def manage_browser_sessions(self):
        """ブラウザセッション管理ダイアログ"""
        session_window = tk.Toplevel(self.root)
        session_window.title("ブラウザセッション管理")
        session_window.geometry("600x400")
        
        # 現在のセッション一覧
        ttk.Label(session_window, text="アクティブなセッション:").pack(pady=5)
        
        session_frame = ttk.Frame(session_window)
        session_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # セッションリスト
        columns = ("サービス", "状態", "処理数", "開始時刻")
        tree = ttk.Treeview(session_frame, columns=columns, show="tree headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # サンプルデータ
        if hasattr(self, 'browser_handler') and self.browser_handler:
            for service, page in self.browser_handler.pages.items():
                tree.insert("", "end", values=(
                    service.upper(),
                    "アクティブ" if page else "非アクティブ",
                    "0",
                    time.strftime("%H:%M:%S")
                ))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # ボタンフレーム
        btn_frame = ttk.Frame(session_window)
        btn_frame.pack(pady=10)
        
        def open_all_sessions():
            """全AIサービスのセッションを開く"""
            if self.browser_handler:
                for service in ['chatgpt', 'claude', 'gemini']:
                    self.browser_handler.open_ai_service(service)
                self.log("✅ 全AIサービスのセッションを開きました")
                session_window.destroy()
        
        def close_all_sessions():
            """全セッションを閉じる"""
            if self.browser_handler:
                self.browser_handler.close()
                self.browser_handler = None
                self.log("✅ 全セッションを閉じました")
                session_window.destroy()
        
        ttk.Button(btn_frame, text="全セッションを開く", 
                  command=open_all_sessions).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="全セッションを閉じる", 
                  command=close_all_sessions).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="閉じる", 
                  command=session_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def initialize_clients(self):
        """APIクライアント初期化"""
        try:
            # SheetsClient初期化
            if SheetsClient:
                self.sheets_client = SheetsClient()
            else:
                self.log("⚠️ SheetsClientが利用できません")
            
            # ExtensionBridge初期化
            if ExtensionBridge:
                self.extension_bridge = ExtensionBridge()
            else:
                self.log("⚠️ ExtensionBridgeが利用できません")
            
            # BrowserAutomationHandler初期化（必要時に初期化）
            self.browser_handler = None
            
            self.log("✅ クライアント初期化完了")
            
        except Exception as e:
            self.log(f"❌ クライアント初期化失敗: {e}")
    
    def load_from_url(self):
        """URLからスプレッドシート読み込み"""
        url = self.url_entry.get().strip()
        url = url.replace('\n', '').replace('\r', '').replace(' ', '')
        
        if not url:
            messagebox.showerror("エラー", "スプレッドシートURLを入力してください")
            return
        
        self.log(f"🔗 URL解析開始: {url}")
        
        try:
            # URLからスプレッドシートID抽出
            if '/spreadsheets/d/' in url:
                sheet_id = url.split('/spreadsheets/d/')[1].split('/')[0]
                sheet_id = sheet_id.strip().replace('\n', '').replace('\r', '').replace(' ', '')
                self.log(f"📊 抽出されたスプレッドシートID: {sheet_id}")
            else:
                error_msg = "無効なスプレッドシートURLです"
                self.log(f"❌ {error_msg}")
                messagebox.showerror("エラー", error_msg)
                return
            
            self.spreadsheet_url = url
            
            # Google Sheets API認証確認
            self.log("🔐 Google Sheets API認証確認中...")
            if not self.sheets_client or not self.sheets_client.authenticate():
                error_msg = "Google Sheets API認証に失敗しました"
                self.log(f"❌ {error_msg}")
                messagebox.showerror("エラー", f"{error_msg}\n\nconfig/credentials.json を確認してください")
                return
            
            self.log("✅ 認証成功")
            
            # スプレッドシート情報取得
            self.log("📋 スプレッドシート情報取得中...")
            spreadsheet_info = self.sheets_client.get_spreadsheet_info(sheet_id)
            
            if not spreadsheet_info:
                error_msg = "スプレッドシート情報を取得できませんでした"
                self.log(f"❌ {error_msg}")
                self.log("💡 考えられる原因:")
                self.log("  1. スプレッドシートの共有設定を確認してください")
                self.log("  2. サービスアカウントのメールアドレスに編集権限を付与してください")
                messagebox.showerror("エラー", error_msg)
                return
            
            self.log(f"✅ スプレッドシート情報取得成功: {spreadsheet_info['title']}")
            
            # シート名一覧取得
            sheet_names = [sheet['title'] for sheet in spreadsheet_info['sheets']]
            self.sheet_combo['values'] = sheet_names
            if sheet_names:
                self.sheet_combo.set(sheet_names[0])
            
            self.log(f"📄 利用可能なシート: {len(sheet_names)}個")
            
        except Exception as e:
            error_msg = f"スプレッドシート読み込み失敗: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("エラー", error_msg)
    
    def load_sheet_info(self):
        """シート情報読み込みと作業指示行解析"""
        if not self.spreadsheet_url or not self.sheet_combo.get():
            messagebox.showerror("エラー", "スプレッドシートとシート名を設定してください")
            return
        
        try:
            self.sheet_name = self.sheet_combo.get()
            sheet_id = self.spreadsheet_url.split('/spreadsheets/d/')[1].split('/')[0]
            
            # シートデータ読み取り
            range_name = f"{self.sheet_name}!A1:Z100"
            self.sheet_data = self.sheets_client.read_range(sheet_id, range_name)
            
            if not self.sheet_data:
                messagebox.showerror("エラー", "シートデータが見つかりません")
                return
            
            # 作業指示行を検索
            self.work_row = None
            for i in range(3, min(10, len(self.sheet_data))):
                if (len(self.sheet_data[i]) > 0 and 
                    '作業指示行' in str(self.sheet_data[i][0])):
                    self.work_row = i
                    break
            
            if self.work_row is None:
                messagebox.showerror("エラー", "作業指示行が見つかりません")
                return
            
            # コピー列を検索
            self.copy_columns = []
            work_row_data = self.sheet_data[self.work_row]
            
            for j, cell in enumerate(work_row_data):
                if str(cell).strip() == 'コピー':
                    process_col = j - 2
                    error_col = j - 1
                    paste_col = j + 1
                    
                    if process_col >= 0:
                        column_info = {
                            'copy_col': j,
                            'copy_letter': chr(65 + j),
                            'process_col': process_col,
                            'process_letter': chr(65 + process_col),
                            'error_col': error_col,
                            'error_letter': chr(65 + error_col),
                            'paste_col': paste_col,
                            'paste_letter': chr(65 + paste_col)
                        }
                        self.copy_columns.append(column_info)
            
            if not self.copy_columns:
                messagebox.showerror("エラー", "コピー列が見つかりません")
                return
            
            # 情報表示
            info_text = f"作業指示行: {self.work_row + 1}行目\n"
            info_text += f"検出されたコピー列: {len(self.copy_columns)}個\n"
            
            for i, col_info in enumerate(self.copy_columns):
                info_text += f"  列{i+1}: {col_info['copy_letter']}列\n"
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            
            # コピー列設定UIを作成
            self.create_column_config_ui()
            
            self.log(f"✅ シート解析完了: {len(self.copy_columns)}個のコピー列を検出")
            
        except Exception as e:
            self.log(f"❌ シート解析失敗: {e}")
            messagebox.showerror("エラー", str(e))
    
    def create_column_config_ui(self):
        """各コピー列の設定UI作成"""
        # 既存のウィジェットをクリア
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.column_configs = {}
        
        for i, col_info in enumerate(self.copy_columns):
            # 列フレーム
            col_frame = ttk.LabelFrame(
                self.scrollable_frame, 
                text=f"📝 列{i+1}: {col_info['copy_letter']}列", 
                padding="15"
            )
            col_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=10, padx=20)
            
            col_frame.columnconfigure(1, weight=1)
            col_frame.columnconfigure(3, weight=2)
            
            # AI選択
            ttk.Label(col_frame, text="AI:").grid(row=0, column=0, sticky=tk.W)
            ai_combo = ttk.Combobox(col_frame, values=list(self.available_ais.keys()), 
                                   width=18, state="readonly")
            ai_combo.set("ChatGPT")
            ai_combo.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
            
            # モデル選択
            ttk.Label(col_frame, text="モデル:").grid(row=0, column=2, sticky=tk.W, padx=(15,5))
            model_combo = ttk.Combobox(col_frame, width=25, state="readonly")
            model_combo.grid(row=0, column=3, padx=5, sticky=(tk.W, tk.E))
            
            # ブラウザ自動化対応表示
            browser_support_label = ttk.Label(col_frame, text="", foreground="green")
            browser_support_label.grid(row=0, column=4, padx=10)
            
            # 設定選択
            ttk.Label(col_frame, text="設定:").grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
            settings_frame = ttk.Frame(col_frame)
            settings_frame.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5, pady=(10, 5))
            
            settings_vars = {}
            
            # AI変更時の処理
            def update_options(event, ai_combo=ai_combo, model_combo=model_combo, 
                             settings_frame=settings_frame, settings_vars=settings_vars,
                             browser_support_label=browser_support_label):
                selected_ai = ai_combo.get()
                if selected_ai in self.available_ais:
                    # モデル更新
                    model_combo['values'] = self.available_ais[selected_ai]['models']
                    model_combo.set(self.available_ais[selected_ai]['models'][0])
                    
                    # ブラウザ対応状況表示
                    if self.available_ais[selected_ai].get('browser_supported', False):
                        browser_support_label.config(text="✅ ブラウザ自動化対応", 
                                                   foreground="green")
                    else:
                        browser_support_label.config(text="❌ 拡張機能のみ", 
                                                   foreground="red")
                    
                    # 設定チェックボックス更新
                    for widget in settings_frame.winfo_children():
                        widget.destroy()
                    settings_vars.clear()
                    
                    for j, setting in enumerate(self.available_ais[selected_ai]['settings']):
                        var = tk.BooleanVar()
                        if setting == "DeepThink":
                            var.set(True)
                        cb = ttk.Checkbutton(settings_frame, text=setting, variable=var)
                        cb.grid(row=j//3, column=j%3, sticky=tk.W, padx=5)
                        settings_vars[setting] = var
            
            ai_combo.bind('<<ComboboxSelected>>', update_options)
            
            # 初期設定
            update_options(None, ai_combo, model_combo, settings_frame, settings_vars, 
                         browser_support_label)
            
            # 設定を保存
            self.column_configs[i] = {
                'column_info': col_info,
                'ai_combo': ai_combo,
                'model_combo': model_combo,
                'settings_vars': settings_vars,
                'browser_support_label': browser_support_label
            }
    
    def start_automation(self):
        """自動化処理開始"""
        self.log("🚀 自動化開始")
        
        # 必要な情報の確認
        if not self.copy_columns:
            messagebox.showerror("エラー", "コピー列が検出されていません")
            return
        
        # ブラウザモードの場合、ハンドラーを初期化
        if self.automation_mode.get() == "browser":
            if not BrowserAutomationHandler:
                messagebox.showerror("エラー", 
                    "ブラウザ自動化モジュールが利用できません。\n" +
                    "pip install playwright を実行してください")
                return
            
            if not self.browser_handler:
                try:
                    profile_path = getattr(self, 'browser_profile_path', None)
                    self.browser_handler = BrowserAutomationHandler(profile_path)
                    self.browser_handler.start(headless=getattr(self, 'browser_headless', False))
                    self.log("✅ ブラウザ自動化ハンドラーを起動しました")
                except Exception as e:
                    self.log(f"❌ ブラウザ起動エラー: {e}")
                    messagebox.showerror("エラー", f"ブラウザ起動に失敗しました: {e}")
                    return
        
        # 別スレッドで実行
        self.automation_thread = threading.Thread(target=self.run_automation)
        self.automation_thread.daemon = True
        self.automation_thread.start()
    
    def run_automation(self):
        """自動化処理実行"""
        try:
            self.update_status("自動化処理開始...")
            
            sheet_id = self.spreadsheet_url.split('/spreadsheets/d/')[1].split('/')[0]
            total_tasks = 0
            completed_tasks = 0
            
            # 各コピー列を処理
            for col_idx, col_config in self.column_configs.items():
                col_info = col_config['column_info']
                
                self.log(f"\n📝 列{col_idx + 1} ({col_info['copy_letter']}列) を処理中...")
                
                # AI設定取得
                ai_service = col_config['ai_combo'].get()
                model = col_config['model_combo'].get()
                
                # 設定取得
                settings = {}
                features = []
                for setting, var in col_config['settings_vars'].items():
                    if var.get():
                        settings[setting] = True
                        features.append(setting)
                
                self.log(f"  AI: {ai_service}, モデル: {model}")
                self.log(f"  有効な機能: {features}")
                
                # 処理対象行を検索
                row_idx = self.work_row + 1
                while row_idx < len(self.sheet_data):
                    # A列チェック
                    if (len(self.sheet_data[row_idx]) == 0 or 
                        not str(self.sheet_data[row_idx][0]).strip()):
                        break
                    
                    a_value = str(self.sheet_data[row_idx][0]).strip()
                    if not a_value.isdigit():
                        row_idx += 1
                        continue
                    
                    # 処理済みチェック
                    if (len(self.sheet_data[row_idx]) > col_info['process_col'] and 
                        str(self.sheet_data[row_idx][col_info['process_col']]).strip() == '処理済み'):
                        row_idx += 1
                        continue
                    
                    # コピーテキスト取得
                    if len(self.sheet_data[row_idx]) <= col_info['copy_col']:
                        row_idx += 1
                        continue
                    
                    copy_text = str(self.sheet_data[row_idx][col_info['copy_col']]).strip()
                    if not copy_text:
                        row_idx += 1
                        continue
                    
                    total_tasks += 1
                    
                    self.log(f"    行{row_idx + 1}: {copy_text[:50]}...")
                    
                    try:
                        # AI処理実行
                        if self.automation_mode.get() == "extension":
                            # Chrome拡張機能モード
                            result = self.extension_bridge.process_with_extension(
                                text=copy_text,
                                ai_service=ai_service.lower().replace(' ', '_'),
                                model=model
                            )
                        else:
                            # ブラウザ自動化モード
                            result = self.browser_handler.process_text(
                                service=ai_service.lower().replace(' ', '_'),
                                text=copy_text,
                                model=model,
                                features=features
                            )
                        
                        if result['success']:
                            response_text = result['result']
                            
                            # 結果書き込み
                            paste_range = f"{self.sheet_name}!{col_info['paste_letter']}{row_idx + 1}"
                            self.sheets_client.write_range(sheet_id, paste_range, [[response_text]])
                            
                            # 処理完了マーク
                            process_range = f"{self.sheet_name}!{col_info['process_letter']}{row_idx + 1}"
                            self.sheets_client.write_range(sheet_id, process_range, [["処理済み"]])
                            
                            completed_tasks += 1
                            self.log(f"      ✅ 成功")
                        else:
                            # エラー記録
                            error_range = f"{self.sheet_name}!{col_info['error_letter']}{row_idx + 1}"
                            self.sheets_client.write_range(sheet_id, error_range, [[result['error']]])
                            self.log(f"      ❌ 失敗: {result['error']}")
                    
                    except Exception as e:
                        # エラー記録
                        error_range = f"{self.sheet_name}!{col_info['error_letter']}{row_idx + 1}"
                        self.sheets_client.write_range(sheet_id, error_range, [[str(e)]])
                        self.log(f"      ❌ エラー: {e}")
                    
                    # 進捗更新
                    if total_tasks > 0:
                        progress = (completed_tasks / total_tasks) * 100
                        self.progress['value'] = progress
                        self.update_status(f"処理中... {completed_tasks}/{total_tasks} 完了")
                    
                    row_idx += 1
                    time.sleep(2)  # レート制限対策
            
            # 完了
            self.update_status(f"自動化完了: {completed_tasks}/{total_tasks} 成功")
            self.log(f"\n🎉 自動化処理完了: {completed_tasks}/{total_tasks} 成功")
            
        except Exception as e:
            self.log(f"❌ 自動化処理エラー: {e}")
            self.update_status(f"エラー: {e}")
    
    def stop_automation(self):
        """自動化処理停止"""
        self.update_status("停止中...")
        self.log("⏹️ 自動化処理を停止しました")
        
        # ブラウザセッションのクリーンアップ
        if self.browser_handler:
            self.browser_handler.close()
            self.browser_handler = None
    
    def save_config(self):
        """設定保存"""
        try:
            config_data = {
                'spreadsheet_url': self.spreadsheet_url,
                'sheet_name': self.sheet_name,
                'work_row': self.work_row,
                'copy_columns': self.copy_columns,
                'automation_mode': self.automation_mode.get(),
                'column_settings': {}
            }
            
            for idx, config in self.column_configs.items():
                settings = {}
                for setting, var in config['settings_vars'].items():
                    settings[setting] = var.get()
                
                config_data['column_settings'][idx] = {
                    'ai': config['ai_combo'].get(),
                    'model': config['model_combo'].get(),
                    'settings': settings
                }
            
            # ブラウザ設定も保存
            if hasattr(self, 'browser_profile_path'):
                config_data['browser_profile_path'] = self.browser_profile_path
            if hasattr(self, 'browser_headless'):
                config_data['browser_headless'] = self.browser_headless
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="設定を保存"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                self.log(f"✅ 設定を保存しました: {filename}")
                messagebox.showinfo("成功", "設定を保存しました")
        
        except Exception as e:
            self.log(f"❌ 設定保存失敗: {e}")
            messagebox.showerror("エラー", str(e))
    
    def load_config(self):
        """設定読込"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json")],
                title="設定を読み込み"
            )
            
            if not filename:
                return
            
            with open(filename, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 基本設定を復元
            if config_data.get('spreadsheet_url'):
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, config_data['spreadsheet_url'])
                self.load_from_url()
            
            if config_data.get('sheet_name'):
                self.sheet_combo.set(config_data['sheet_name'])
                self.load_sheet_info()
            
            # 自動化モード復元
            if config_data.get('automation_mode'):
                self.automation_mode.set(config_data['automation_mode'])
                self.on_mode_change()
            
            # ブラウザ設定復元
            if config_data.get('browser_profile_path'):
                self.browser_profile_path = config_data['browser_profile_path']
            if config_data.get('browser_headless'):
                self.browser_headless = config_data['browser_headless']
            
            # 列設定を復元
            if config_data.get('column_settings'):
                for idx_str, settings in config_data['column_settings'].items():
                    idx = int(idx_str)
                    if idx in self.column_configs:
                        config = self.column_configs[idx]
                        config['ai_combo'].set(settings.get('ai', 'ChatGPT'))
                        config['model_combo'].set(settings.get('model', ''))
                        
                        for setting, value in settings.get('settings', {}).items():
                            if setting in config['settings_vars']:
                                config['settings_vars'][setting].set(value)
            
            self.log(f"✅ 設定を読み込みました: {filename}")
            messagebox.showinfo("成功", "設定を読み込みました")
        
        except Exception as e:
            self.log(f"❌ 設定読み込み失敗: {e}")
            messagebox.showerror("エラー", str(e))
    
    def update_status(self, message):
        """ステータス更新"""
        self.root.after(0, lambda: self.status_label.config(text=message))
    
    def log(self, message):
        """ログ出力"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
            
            # エラーは赤色で表示
            if "❌" in message or "エラー" in message:
                self.log_text.tag_add("error", f"end-2l", "end-1l")
                self.log_text.tag_config("error", foreground="red")
        
        self.root.after(0, update_log)


def main():
    """メイン実行関数"""
    print("🎯 スプレッドシート自動化GUIアプリ - Claude専用版")
    print("="*60)
    print("📋 主要機能:")
    print("  ✅ Chrome拡張機能モード（高速処理）")
    print("  ✅ ブラウザ自動化モード（API不要）")
    print("  ✅ 既存のログインセッションを活用")
    print("  ✅ 有料プランの無制限利用")
    print("  ✅ DeepThink等の高度な機能対応")
    print()
    print("⚠️  このファイルはClaude専用です")
    print("📱 GUI起動中...")
    
    root = tk.Tk()
    app = SpreadsheetAutomationGUI(root)
    
    # 初回起動時のヘルプメッセージ
    help_message = """
🔰 Claude専用版 - API不要ブラウザ自動化

【準備】
1. 各AIサービス（ChatGPT、Claude等）に
   通常のブラウザでログインしておく
2. ログイン後、一度ブラウザを閉じる

【使用手順】
1. 自動化モードで「ブラウザ自動化モード」を選択
2. スプレッドシートURLを入力して読み込み
3. 各コピー列のAI設定を行う
4. 「自動化開始」をクリック

【メリット】
• APIキー不要
• 従量課金なし
• 有料プランの全機能が使用可能
• DeepThink等の高度な機能も利用可能

💡 初回は「ブラウザ設定」から
   Chromeプロファイルパスを確認してください
    """
    
    app.log(help_message)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n⏹️ アプリケーション終了")
        if hasattr(app, 'browser_handler') and app.browser_handler:
            app.browser_handler.close()


if __name__ == "__main__":
    main()