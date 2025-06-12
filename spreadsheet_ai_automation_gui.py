#!/usr/bin/env python3
"""
スプレッドシート×AI統合自動化GUIアプリケーション
APIを使わずにブラウザ自動化でAIサービスと連携
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import json
import time
import re
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Any

# Playwright関連のインポート
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwrightがインストールされていません。pip install playwrightを実行してください。")

# Google Sheets関連のインポート
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("gspreadがインストールされていません。pip install gspread google-auth google-auth-oauthlib google-auth-httpauthを実行してください。")

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_gui.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AIServiceConfig:
    """AIサービス設定クラス"""
    
    # AIサービスのURL
    SERVICES = {
        'ChatGPT': 'https://chatgpt.com',
        'Claude': 'https://claude.ai',
        'Gemini': 'https://gemini.google.com',
        'Genspark': 'https://genspark.ai',
        'Google AI Studio': 'https://aistudio.google.com'
    }
    
    # 各AIサービスのセレクタ情報（実際の値は動的に更新される可能性があります）
    SELECTORS = {
        'ChatGPT': {
            'input': 'textarea[placeholder*="Message"]',
            'send': 'button[data-testid="send-button"]',
            'response': 'div[data-message-author-role="assistant"]',
            'model_button': 'button[aria-haspopup="menu"]',
            'settings': {
                'deep_think': 'input[type="checkbox"][name="deep-think"]'
            }
        },
        'Claude': {
            'input': 'div[contenteditable="true"]',
            'send': 'button[aria-label="Send message"]',
            'response': 'div[data-test-id="assistant-message"]',
            'model_button': 'button[data-test-id="model-selector"]'
        },
        'Gemini': {
            'input': 'textarea[placeholder*="Enter a prompt"]',
            'send': 'button[aria-label="Send message"]',
            'response': 'div.response-container'
        }
    }


class SpreadsheetAIAutomationGUI:
    """メインGUIアプリケーションクラス"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("スプレッドシート×AI自動化ツール")
        self.root.geometry("1200x800")
        
        # キューとスレッド管理
        self.log_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.processing = False
        self.browser_context = None
        self.playwright = None
        
        # データ保存用
        self.sheet_data = []
        self.ai_configs = {}  # 各コピー列のAI設定
        
        # GUI構築
        self.setup_gui()
        
        # ログ更新タイマー
        self.update_logs()
        
    def setup_gui(self):
        """GUI要素の構築"""
        
        # メインコンテナ
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タブ構造
        notebook = ttk.Notebook(main_container)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 1. 基本設定タブ
        self.setup_basic_tab(notebook)
        
        # 2. AI設定タブ
        self.setup_ai_config_tab(notebook)
        
        # 3. 処理状況タブ
        self.setup_process_tab(notebook)
        
        # 4. ログタブ
        self.setup_log_tab(notebook)
        
        # ウィンドウのリサイズ設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(0, weight=1)
        
    def setup_basic_tab(self, notebook):
        """基本設定タブの構築"""
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="基本設定")
        
        # スプレッドシートURL入力
        ttk.Label(basic_frame, text="スプレッドシートURL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sheet_url_var = tk.StringVar()
        sheet_url_entry = ttk.Entry(basic_frame, textvariable=self.sheet_url_var, width=60)
        sheet_url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # シート選択
        ttk.Label(basic_frame, text="シート名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.sheet_name_var = tk.StringVar()
        self.sheet_combo = ttk.Combobox(basic_frame, textvariable=self.sheet_name_var, width=30)
        self.sheet_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # シート取得ボタン
        ttk.Button(basic_frame, text="シート一覧取得", 
                  command=self.fetch_sheet_names).grid(row=1, column=2, padx=5)
        
        # 認証ファイル選択
        ttk.Label(basic_frame, text="認証ファイル:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cred_file_var = tk.StringVar(value="config/credentials.json")
        ttk.Entry(basic_frame, textvariable=self.cred_file_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Button(basic_frame, text="参照", command=self.browse_cred_file).grid(row=2, column=2, padx=5)
        
        # Chrome プロファイルパス
        ttk.Label(basic_frame, text="Chromeプロファイル:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.chrome_profile_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.chrome_profile_var, width=50).grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 処理開始ボタン
        self.start_button = ttk.Button(basic_frame, text="処理開始", 
                                      command=self.start_processing, 
                                      style="Accent.TButton")
        self.start_button.grid(row=4, column=0, columnspan=3, pady=20)
        
        # 停止ボタン
        self.stop_button = ttk.Button(basic_frame, text="停止", 
                                     command=self.stop_processing,
                                     state=tk.DISABLED)
        self.stop_button.grid(row=5, column=0, columnspan=3)
        
        basic_frame.columnconfigure(1, weight=1)
        
    def setup_ai_config_tab(self, notebook):
        """AI設定タブの構築"""
        ai_frame = ttk.Frame(notebook, padding="10")
        notebook.add(ai_frame, text="AI設定")
        
        # 説明ラベル
        ttk.Label(ai_frame, text="各コピー列で使用するAIサービスを設定してください。").grid(row=0, column=0, columnspan=3, pady=10)
        
        # AI設定テーブル
        columns = ('コピー列', 'AIサービス', 'モデル', '設定')
        self.ai_config_tree = ttk.Treeview(ai_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.ai_config_tree.heading(col, text=col)
            self.ai_config_tree.column(col, width=150)
        
        self.ai_config_tree.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(ai_frame, orient=tk.VERTICAL, command=self.ai_config_tree.yview)
        scrollbar.grid(row=1, column=3, sticky=(tk.N, tk.S))
        self.ai_config_tree.configure(yscrollcommand=scrollbar.set)
        
        # 設定ボタン
        button_frame = ttk.Frame(ai_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="列を追加", command=self.add_ai_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="編集", command=self.edit_ai_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="削除", command=self.delete_ai_config).pack(side=tk.LEFT, padx=5)
        
        # AIサービスログイン状態
        login_frame = ttk.LabelFrame(ai_frame, text="AIサービスログイン状態", padding="10")
        login_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        self.login_status_labels = {}
        for i, service in enumerate(AIServiceConfig.SERVICES.keys()):
            ttk.Label(login_frame, text=f"{service}:").grid(row=i//2, column=(i%2)*2, sticky=tk.W, padx=5)
            status_label = ttk.Label(login_frame, text="未確認", foreground="gray")
            status_label.grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5)
            self.login_status_labels[service] = status_label
        
        ttk.Button(login_frame, text="ログイン状態確認", command=self.check_login_status).grid(row=3, column=0, columnspan=4, pady=10)
        
        ai_frame.rowconfigure(1, weight=1)
        ai_frame.columnconfigure(0, weight=1)
        
    def setup_process_tab(self, notebook):
        """処理状況タブの構築"""
        process_frame = ttk.Frame(notebook, padding="10")
        notebook.add(process_frame, text="処理状況")
        
        # 進捗バー
        ttk.Label(process_frame, text="全体進捗:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(process_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_label = ttk.Label(process_frame, text="0%")
        self.progress_label.grid(row=0, column=2, padx=5)
        
        # 処理状況テーブル
        ttk.Label(process_frame, text="処理詳細:").grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        columns = ('行番号', 'コピー列', '状態', 'AIサービス', 'エラー')
        self.process_tree = ttk.Treeview(process_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=120)
        
        self.process_tree.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        scrollbar.grid(row=2, column=3, sticky=(tk.N, tk.S))
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        process_frame.columnconfigure(1, weight=1)
        process_frame.rowconfigure(2, weight=1)
        
    def setup_log_tab(self, notebook):
        """ログタブの構築"""
        log_frame = ttk.Frame(notebook, padding="10")
        notebook.add(log_frame, text="ログ")
        
        # ログテキストエリア
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ログレベル選択
        level_frame = ttk.Frame(log_frame)
        level_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(level_frame, text="ログレベル:").pack(side=tk.LEFT, padx=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(level_frame, textvariable=self.log_level_var, 
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                                      width=10, state="readonly")
        log_level_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(level_frame, text="ログクリア", command=self.clear_logs).pack(side=tk.RIGHT, padx=5)
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def fetch_sheet_names(self):
        """スプレッドシートのシート名一覧を取得"""
        if not GSPREAD_AVAILABLE:
            messagebox.showerror("エラー", "gspreadがインストールされていません。")
            return
            
        url = self.sheet_url_var.get()
        if not url:
            messagebox.showwarning("警告", "スプレッドシートURLを入力してください。")
            return
            
        try:
            # 認証とクライアント作成
            creds = Credentials.from_service_account_file(
                self.cred_file_var.get(),
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            client = gspread.authorize(creds)
            
            # スプレッドシートを開く
            spreadsheet = client.open_by_url(url)
            sheet_names = [sheet.title for sheet in spreadsheet.worksheets()]
            
            # コンボボックスに設定
            self.sheet_combo['values'] = sheet_names
            if sheet_names:
                self.sheet_combo.current(0)
                
            self.log_message("INFO", f"シート一覧を取得しました: {sheet_names}")
            
        except Exception as e:
            self.log_message("ERROR", f"シート取得エラー: {str(e)}")
            messagebox.showerror("エラー", f"シート取得に失敗しました: {str(e)}")
            
    def browse_cred_file(self):
        """認証ファイルを選択"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="認証ファイルを選択",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.cred_file_var.set(filename)
            
    def add_ai_config(self):
        """AI設定を追加"""
        dialog = AIConfigDialog(self.root, "AI設定追加")
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.ai_configs[dialog.result['column']] = dialog.result
            self.update_ai_config_tree()
            
    def edit_ai_config(self):
        """AI設定を編集"""
        selection = self.ai_config_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "編集する項目を選択してください。")
            return
            
        item = self.ai_config_tree.item(selection[0])
        values = item['values']
        
        dialog = AIConfigDialog(self.root, "AI設定編集", {
            'column': values[0],
            'service': values[1],
            'model': values[2],
            'settings': values[3]
        })
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.ai_configs[dialog.result['column']] = dialog.result
            self.update_ai_config_tree()
            
    def delete_ai_config(self):
        """AI設定を削除"""
        selection = self.ai_config_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "削除する項目を選択してください。")
            return
            
        item = self.ai_config_tree.item(selection[0])
        column = item['values'][0]
        
        if messagebox.askyesno("確認", f"列 {column} の設定を削除しますか？"):
            del self.ai_configs[column]
            self.update_ai_config_tree()
            
    def update_ai_config_tree(self):
        """AI設定テーブルを更新"""
        # 既存の項目をクリア
        for item in self.ai_config_tree.get_children():
            self.ai_config_tree.delete(item)
            
        # 設定を追加
        for column, config in self.ai_configs.items():
            self.ai_config_tree.insert('', 'end', values=(
                config['column'],
                config['service'],
                config.get('model', '-'),
                config.get('settings', '-')
            ))
            
    def check_login_status(self):
        """AIサービスのログイン状態を確認"""
        if not PLAYWRIGHT_AVAILABLE:
            messagebox.showerror("エラー", "Playwrightがインストールされていません。")
            return
            
        def check_in_thread():
            try:
                with sync_playwright() as p:
                    browser = self._get_browser(p)
                    
                    for service, url in AIServiceConfig.SERVICES.items():
                        try:
                            page = browser.new_page()
                            page.goto(url, wait_until='networkidle', timeout=30000)
                            
                            # ログイン状態の簡易チェック（サービスごとに異なる）
                            logged_in = False
                            if service == 'ChatGPT':
                                logged_in = page.query_selector('textarea[placeholder*="Message"]') is not None
                            elif service == 'Claude':
                                logged_in = page.query_selector('div[contenteditable="true"]') is not None
                            # 他のサービスも同様に実装
                            
                            status = "ログイン済み" if logged_in else "未ログイン"
                            color = "green" if logged_in else "red"
                            
                            self.root.after(0, lambda s=service, st=status, c=color: 
                                          self.update_login_status(s, st, c))
                            
                            page.close()
                            
                        except Exception as e:
                            self.root.after(0, lambda s=service: 
                                          self.update_login_status(s, "エラー", "red"))
                            
                    browser.close()
                    
            except Exception as e:
                self.log_message("ERROR", f"ログイン状態確認エラー: {str(e)}")
                
        thread = threading.Thread(target=check_in_thread)
        thread.daemon = True
        thread.start()
        
    def update_login_status(self, service, status, color):
        """ログイン状態表示を更新"""
        if service in self.login_status_labels:
            self.login_status_labels[service].config(text=status, foreground=color)
            
    def start_processing(self):
        """処理開始"""
        if self.processing:
            messagebox.showwarning("警告", "既に処理が実行中です。")
            return
            
        # 入力チェック
        if not self.sheet_url_var.get():
            messagebox.showwarning("警告", "スプレッドシートURLを入力してください。")
            return
            
        if not self.sheet_name_var.get():
            messagebox.showwarning("警告", "シート名を選択してください。")
            return
            
        if not self.ai_configs:
            messagebox.showwarning("警告", "AI設定を追加してください。")
            return
            
        # UIの状態変更
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 処理スレッド開始
        thread = threading.Thread(target=self.process_automation)
        thread.daemon = True
        thread.start()
        
    def stop_processing(self):
        """処理停止"""
        self.processing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_message("INFO", "処理を停止しました。")
        
    def process_automation(self):
        """自動化処理のメインロジック"""
        try:
            self.log_message("INFO", "自動化処理を開始します。")
            
            # スプレッドシート接続
            sheet = self.connect_to_sheet()
            if not sheet:
                return
                
            # 作業指示行の検索
            work_row = self.find_work_instruction_row(sheet)
            if work_row == -1:
                self.log_message("ERROR", "作業指示行が見つかりません。")
                return
                
            self.log_message("INFO", f"作業指示行: {work_row}行目")
            
            # コピー列の検索
            copy_columns = self.find_copy_columns(sheet, work_row)
            if not copy_columns:
                self.log_message("ERROR", "コピー列が見つかりません。")
                return
                
            self.log_message("INFO", f"コピー列: {copy_columns}")
            
            # ブラウザ起動
            with sync_playwright() as p:
                browser = self._get_browser(p)
                
                # 各コピー列を処理
                for copy_col in copy_columns:
                    if not self.processing:
                        break
                        
                    self.process_copy_column(sheet, browser, work_row, copy_col)
                    
                browser.close()
                
            self.log_message("INFO", "自動化処理が完了しました。")
            
        except Exception as e:
            self.log_message("ERROR", f"処理エラー: {str(e)}")
            logger.exception("処理エラー")
            
        finally:
            self.processing = False
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            
    def connect_to_sheet(self):
        """スプレッドシートに接続"""
        try:
            creds = Credentials.from_service_account_file(
                self.cred_file_var.get(),
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_url(self.sheet_url_var.get())
            sheet = spreadsheet.worksheet(self.sheet_name_var.get())
            
            self.log_message("INFO", "スプレッドシートに接続しました。")
            return sheet
            
        except Exception as e:
            self.log_message("ERROR", f"スプレッドシート接続エラー: {str(e)}")
            return None
            
    def find_work_instruction_row(self, sheet):
        """作業指示行を検索"""
        try:
            # A列の値を取得
            col_a_values = sheet.col_values(1)
            
            # "作業指示行"を含む行を検索
            for i, value in enumerate(col_a_values):
                if value and "作業指示行" in str(value):
                    return i + 1  # 1ベースのインデックス
                    
            return -1
            
        except Exception as e:
            self.log_message("ERROR", f"作業指示行検索エラー: {str(e)}")
            return -1
            
    def find_copy_columns(self, sheet, work_row):
        """コピー列を検索"""
        try:
            # 作業指示行の値を取得
            row_values = sheet.row_values(work_row)
            
            copy_columns = []
            for i, value in enumerate(row_values):
                if value == "コピー":
                    copy_columns.append(i + 1)  # 1ベースのインデックス
                    
            return copy_columns
            
        except Exception as e:
            self.log_message("ERROR", f"コピー列検索エラー: {str(e)}")
            return []
            
    def process_copy_column(self, sheet, browser, work_row, copy_col):
        """特定のコピー列を処理"""
        try:
            # 列のインデックス計算
            process_col = copy_col - 2  # 処理列
            error_col = copy_col - 1    # エラー列
            paste_col = copy_col + 1    # 貼り付け列
            
            # 境界チェック
            if process_col < 1:
                self.log_message("WARNING", f"コピー列 {copy_col} の処理列が範囲外です。")
                return
                
            # AI設定取得
            col_letter = self._col_num_to_letter(copy_col)
            ai_config = self.ai_configs.get(col_letter, {
                'service': 'ChatGPT',
                'model': 'gpt-4',
                'settings': {}
            })
            
            # AIページを開く
            ai_page = browser.new_page()
            ai_service = ai_config['service']
            ai_page.goto(AIServiceConfig.SERVICES[ai_service])
            
            # A列の値を確認して処理
            row = work_row + 1
            while self.processing:
                try:
                    # A列の値を取得
                    a_value = sheet.cell(row, 1).value
                    
                    # A列が空白なら終了
                    if not a_value:
                        break
                        
                    # 数値でない場合はスキップ
                    try:
                        int(a_value)
                    except (ValueError, TypeError):
                        row += 1
                        continue
                        
                    # 処理列の値を確認
                    process_value = sheet.cell(row, process_col).value
                    if process_value and process_value not in ["", "未処理"]:
                        row += 1
                        continue
                        
                    # コピー列のテキストを取得
                    copy_text = sheet.cell(row, copy_col).value
                    if not copy_text:
                        row += 1
                        continue
                        
                    self.log_message("INFO", f"行 {row}: 処理開始")
                    
                    # AIに送信して結果を取得
                    result = self.send_to_ai(ai_page, ai_service, copy_text, ai_config)
                    
                    if result['success']:
                        # 結果を貼り付け列に書き込み
                        sheet.update_cell(row, paste_col, result['response'])
                        
                        # 処理済みマーク
                        sheet.update_cell(row, process_col, "処理済み")
                        
                        self.log_message("INFO", f"行 {row}: 処理完了")
                        
                        # 進捗更新
                        self.update_process_tree(row, col_letter, "完了", ai_service, "")
                        
                    else:
                        # エラーを記録
                        sheet.update_cell(row, error_col, result['error'])
                        self.log_message("ERROR", f"行 {row}: {result['error']}")
                        
                        self.update_process_tree(row, col_letter, "エラー", ai_service, result['error'])
                        
                    # レート制限対策
                    time.sleep(3)
                    
                except Exception as e:
                    error_msg = f"行処理エラー: {str(e)}"
                    self.log_message("ERROR", error_msg)
                    try:
                        sheet.update_cell(row, error_col, error_msg)
                    except:
                        pass
                        
                row += 1
                
            ai_page.close()
            
        except Exception as e:
            self.log_message("ERROR", f"列処理エラー: {str(e)}")
            
    def send_to_ai(self, page, service, prompt, config):
        """AIサービスにプロンプトを送信して結果を取得"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # セレクタ取得
                selectors = AIServiceConfig.SELECTORS.get(service, {})
                
                # 入力欄にテキストを入力
                input_selector = selectors.get('input')
                if input_selector:
                    page.fill(input_selector, prompt)
                else:
                    return {'success': False, 'error': f'{service}の入力セレクタが見つかりません'}
                    
                # 送信ボタンをクリック
                send_selector = selectors.get('send')
                if send_selector:
                    page.click(send_selector)
                else:
                    # Enterキーで送信
                    page.keyboard.press('Enter')
                    
                # レスポンスを待つ
                response_selector = selectors.get('response')
                if response_selector:
                    # 新しいレスポンスが表示されるまで待つ
                    page.wait_for_selector(response_selector, state='visible', timeout=60000)
                    
                    # 最新のレスポンスを取得
                    time.sleep(2)  # レスポンスが完全に表示されるまで待つ
                    responses = page.query_selector_all(response_selector)
                    if responses:
                        latest_response = responses[-1].inner_text()
                        return {'success': True, 'response': latest_response}
                        
                return {'success': False, 'error': 'レスポンスが取得できませんでした'}
                
            except Exception as e:
                retry_count += 1
                error_msg = f"AI送信エラー (リトライ {retry_count}/{max_retries}): {str(e)}"
                self.log_message("WARNING", error_msg)
                
                if retry_count >= max_retries:
                    return {'success': False, 'error': f"最大リトライ回数を超過: {str(e)}"}
                    
                time.sleep(10)  # リトライ前に待機
                
        return {'success': False, 'error': '不明なエラー'}
        
    def _get_browser(self, playwright):
        """ブラウザインスタンスを取得"""
        chrome_profile = self.chrome_profile_var.get()
        
        if chrome_profile:
            # 既存のChromeプロファイルを使用
            return playwright.chromium.launch_persistent_context(
                user_data_dir=chrome_profile,
                headless=False,
                slow_mo=500  # デバッグ用に動作を遅くする
            )
        else:
            # 新規ブラウザインスタンス
            browser = playwright.chromium.launch(headless=False, slow_mo=500)
            return browser.new_context()
            
    def _col_num_to_letter(self, col_num):
        """列番号をアルファベットに変換"""
        letter = ''
        while col_num > 0:
            col_num -= 1
            letter = chr(col_num % 26 + 65) + letter
            col_num //= 26
        return letter
        
    def update_process_tree(self, row, column, status, ai_service, error):
        """処理状況テーブルを更新"""
        self.root.after(0, lambda: self.process_tree.insert('', 'end', values=(
            row, column, status, ai_service, error
        )))
        
    def log_message(self, level, message):
        """ログメッセージを追加"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        self.log_queue.put(log_entry)
        
        # ロガーにも出力
        if level == "DEBUG":
            logger.debug(message)
        elif level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
            
    def update_logs(self):
        """ログ表示を更新"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, log_entry)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
            
        # 100ms後に再度実行
        self.root.after(100, self.update_logs)
        
    def clear_logs(self):
        """ログをクリア"""
        self.log_text.delete(1.0, tk.END)
        
    def run(self):
        """アプリケーションを実行"""
        self.root.mainloop()


class AIConfigDialog:
    """AI設定ダイアログ"""
    
    def __init__(self, parent, title, initial_values=None):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # フレーム
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # コピー列
        ttk.Label(frame, text="コピー列:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.column_var = tk.StringVar(value=initial_values.get('column', '') if initial_values else '')
        ttk.Entry(frame, textvariable=self.column_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # AIサービス
        ttk.Label(frame, text="AIサービス:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.service_var = tk.StringVar(value=initial_values.get('service', 'ChatGPT') if initial_values else 'ChatGPT')
        service_combo = ttk.Combobox(frame, textvariable=self.service_var, 
                                    values=list(AIServiceConfig.SERVICES.keys()),
                                    state="readonly", width=20)
        service_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # モデル
        ttk.Label(frame, text="モデル:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value=initial_values.get('model', '') if initial_values else '')
        self.model_combo = ttk.Combobox(frame, textvariable=self.model_var, width=20)
        self.model_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # サービス変更時にモデル一覧を更新
        service_combo.bind('<<ComboboxSelected>>', self.update_models)
        
        # 設定（チェックボックス）
        settings_frame = ttk.LabelFrame(frame, text="設定", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.deep_think_var = tk.BooleanVar()
        ttk.Checkbutton(settings_frame, text="Deep Think", variable=self.deep_think_var).pack(anchor=tk.W)
        
        # ボタン
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # 初期モデル更新
        self.update_models()
        
    def update_models(self, event=None):
        """選択されたサービスに応じてモデル一覧を更新"""
        service = self.service_var.get()
        
        # サービスごとのモデル一覧（実際の値は動的に取得する必要があります）
        models = {
            'ChatGPT': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            'Claude': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
            'Gemini': ['gemini-pro', 'gemini-pro-vision'],
            'Genspark': ['genspark-default'],
            'Google AI Studio': ['gemini-1.5-pro', 'gemini-1.5-flash']
        }
        
        self.model_combo['values'] = models.get(service, [])
        if models.get(service):
            self.model_combo.current(0)
            
    def ok_clicked(self):
        """OKボタンクリック時の処理"""
        if not self.column_var.get():
            messagebox.showwarning("警告", "コピー列を入力してください。", parent=self.dialog)
            return
            
        self.result = {
            'column': self.column_var.get(),
            'service': self.service_var.get(),
            'model': self.model_var.get(),
            'settings': {
                'deep_think': self.deep_think_var.get()
            }
        }
        
        self.dialog.destroy()


def main():
    """メイン関数"""
    # 必要なライブラリの確認
    if not PLAYWRIGHT_AVAILABLE:
        print("\n=== セットアップが必要です ===")
        print("以下のコマンドを実行してください：")
        print("pip install playwright")
        print("playwright install chromium")
        print("========================\n")
        
    if not GSPREAD_AVAILABLE:
        print("\n=== セットアップが必要です ===")
        print("以下のコマンドを実行してください：")
        print("pip install gspread google-auth google-auth-oauthlib google-auth-httpauth2")
        print("========================\n")
        
    # アプリケーション起動
    app = SpreadsheetAIAutomationGUI()
    app.run()


if __name__ == "__main__":
    main()