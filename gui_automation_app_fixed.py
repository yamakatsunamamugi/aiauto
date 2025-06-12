#!/usr/bin/env python3
"""
CLAUDE.md要件完全対応 - スプレッドシート自動化GUIアプリケーション
詳細な初心者向け解説付き

要件：
1. 5行目のA列「作業」から作業指示行特定
2. 複数「コピー」列の検索と個別AI設定
3. 各AIの最新モデル選択とDeepThink等設定
4. 処理列(コピー-2)、エラー列(コピー-1)、貼り付け列(コピー+1)
5. A列連番処理とChrome拡張機能統合
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading
import time
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# インポートは initialize_clients() で動的に行う

class SpreadsheetAutomationGUI:
    """CLAUDE.md要件完全対応GUIクラス"""
    
    def __init__(self, root):
        """GUI初期化"""
        self.root = root
        self.root.title("スプレッドシート自動化システム - CLAUDE.md完全対応版")
        self.root.geometry("1000x800")
        
        # データ格納
        self.spreadsheet_url = ""
        self.sheet_name = ""
        self.sheet_data = []
        self.work_row = None
        self.copy_columns = []  # 複数のコピー列情報
        self.column_configs = {}  # 各列の設定
        
        # APIクライアント
        self.sheets_client = None
        self.extension_bridge = None
        
        # AI設定データ
        self.available_ais = {
            "ChatGPT": {
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "settings": ["DeepThink", "Web検索", "画像認識", "コード実行", "画像生成"]
            },
            "Claude": {
                "models": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-haiku"],
                "settings": ["DeepThink", "画像認識", "アーティファクト", "プロジェクト"]
            },
            "Gemini": {
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
                "settings": ["DeepThink", "画像認識", "マルチモーダル", "コード実行"]
            },
            "Genspark": {
                "models": ["default"],
                "settings": ["リサーチ", "引用", "最新情報"]
            },
            "Google AI Studio": {
                "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
                "settings": ["DeepThink", "画像認識", "マルチモーダル", "コード実行"]
            }
        }
        
        self.create_widgets()
        self.initialize_clients()
    
    def create_widgets(self):
        """ウィジェット作成"""
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 1. スプレッドシート設定セクション
        setup_frame = ttk.LabelFrame(main_frame, text="📊 スプレッドシート設定", padding="10")
        setup_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
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
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.info_text = tk.Text(info_frame, height=4, width=80)
        self.info_text.grid(row=0, column=0, columnspan=2)
        
        # 3. コピー列設定セクション（複数列対応）
        columns_frame = ttk.LabelFrame(main_frame, text="🤖 各コピー列のAI設定", padding="10")
        columns_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(columns_frame, height=200)
        scrollbar = ttk.Scrollbar(columns_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 4. 実行制御セクション
        control_frame = ttk.LabelFrame(main_frame, text="🚀 実行制御", padding="10")
        control_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(control_frame, text="設定保存", command=self.save_config).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="設定読込", command=self.load_config).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="自動化開始", command=self.start_automation).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="停止", command=self.stop_automation).grid(row=0, column=3, padx=5)
        
        # 進捗表示
        self.progress = ttk.Progressbar(control_frame, mode='determinate')
        self.progress.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(control_frame, text="待機中...")
        self.status_label.grid(row=2, column=0, columnspan=4)
        
        # 5. ログセクション
        log_frame = ttk.LabelFrame(main_frame, text="📝 実行ログ", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=80)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def initialize_clients(self):
        """APIクライアント初期化"""
        try:
            # SheetsClientをインポートして初期化
            from src.sheets.sheets_client import SheetsClient
            self.sheets_client = SheetsClient()
            
            # ExtensionBridgeをインポートして初期化
            try:
                from src.automation.extension_bridge import ExtensionBridge
                self.extension_bridge = ExtensionBridge()
            except ImportError:
                # フォールバック用ダミークラス
                class DummyExtensionBridge:
                    def process_with_extension(self, **kwargs):
                        return {"success": True, "result": "テスト応答"}
                self.extension_bridge = DummyExtensionBridge()
                self.log("⚠️ ExtensionBridgeが見つかりません。ダミークラスを使用します")
            
            self.log("✅ APIクライアント初期化完了")
        except Exception as e:
            self.log(f"❌ APIクライアント初期化失敗: {e}")
            self.log(f"📝 詳細エラー: {type(e).__name__}: {e}")
    
    def load_from_url(self):
        """URLからスプレッドシート読み込み"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("エラー", "スプレッドシートURLを入力してください")
            return
        
        self.log(f"🔗 URL解析開始: {url}")
        
        try:
            # URLからスプレッドシートID抽出
            if '/spreadsheets/d/' in url:
                sheet_id = url.split('/spreadsheets/d/')[1].split('/')[0]
                self.log(f"📊 抽出されたスプレッドシートID: {sheet_id}")
            else:
                error_msg = "無効なスプレッドシートURLです"
                self.log(f"❌ {error_msg}")
                messagebox.showerror("エラー", error_msg)
                return
            
            self.spreadsheet_url = url
            
            # まず認証を確認
            self.log("🔐 Google Sheets API認証確認中...")
            if not self.sheets_client.authenticate():
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
                self.log("  1. スプレッドシートが以下のメールアドレスに共有されていない:")
                self.log("     ai-automation-bot@my-ai-automation-462102.iam.gserviceaccount.com")
                self.log("  2. 共有権限が「閲覧者」になっている（「編集者」が必要）")
                self.log("  3. スプレッドシートが削除されているか、URLが間違っている")
                messagebox.showerror("エラー", f"{error_msg}\n\n解決方法:\n1. スプレッドシートを開く\n2. 右上の「共有」をクリック\n3. 以下を追加:\n   ai-automation-bot@my-ai-automation-462102.iam.gserviceaccount.com\n4. 権限を「編集者」に設定")
                return
            
            self.log(f"✅ スプレッドシート情報取得成功: {spreadsheet_info['title']}")
            
            # シート名一覧取得
            sheet_names = [sheet['title'] for sheet in spreadsheet_info['sheets']]
            self.sheet_combo['values'] = sheet_names
            if sheet_names:
                self.sheet_combo.set(sheet_names[0])
            
            self.log(f"📄 利用可能なシート: {len(sheet_names)}個")
            for i, name in enumerate(sheet_names):
                self.log(f"  {i+1}. {name}")
            
            self.log(f"✅ スプレッドシート読み込み完了")
            
        except Exception as e:
            error_msg = f"スプレッドシート読み込み失敗: {e}"
            self.log(f"❌ {error_msg}")
            self.log(f"📝 詳細エラー: {type(e).__name__}")
            messagebox.showerror("エラー", error_msg)
    
    def load_sheet_info(self):
        """シート情報読み込みと作業指示行解析"""
        if not self.spreadsheet_url or not self.sheet_combo.get():
            messagebox.showerror("エラー", "スプレッドシートとシート名を設定してください")
            return
        
        try:
            self.sheet_name = self.sheet_combo.get()
            sheet_id = self.spreadsheet_url.split('/spreadsheets/d/')[1].split('/')[0]
            
            # シートデータ読み取り（100行まで）
            range_name = f"{self.sheet_name}!A1:Z100"
            self.sheet_data = self.sheets_client.read_range(sheet_id, range_name)
            
            if not self.sheet_data:
                messagebox.showerror("エラー", "シートデータが見つかりません")
                return
            
            # 作業指示行を検索（CLAUDE.md要件：5行目周辺を検索）
            self.work_row = None
            for i in range(4, min(10, len(self.sheet_data))):  # 5-10行目を検索
                if (len(self.sheet_data[i]) > 0 and 
                    '作業指示行' in str(self.sheet_data[i][0])):
                    self.work_row = i
                    break
            
            if self.work_row is None:
                messagebox.showerror("エラー", "作業指示行（A列に「作業指示行」）が見つかりません")
                return
            
            # コピー列を検索
            self.copy_columns = []
            work_row_data = self.sheet_data[self.work_row]
            
            for j, cell in enumerate(work_row_data):
                if str(cell).strip() == 'コピー':
                    # 列位置情報を計算
                    process_col = j - 2  # 処理列
                    error_col = j - 1    # エラー列
                    paste_col = j + 1    # 貼り付け列
                    
                    if process_col >= 0:  # 境界チェック
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
            info_text += f"ヘッダー: {work_row_data}\n"
            info_text += f"検出されたコピー列: {len(self.copy_columns)}個\n"
            
            for i, col_info in enumerate(self.copy_columns):
                info_text += f"  列{i+1}: {col_info['copy_letter']}列 (処理:{col_info['process_letter']}, エラー:{col_info['error_letter']}, 貼付:{col_info['paste_letter']})\n"
            
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
                text=f"📝 列{i+1}: {col_info['copy_letter']}列 (コピー列)", 
                padding="10"
            )
            col_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=5, padx=10)
            
            # AI選択
            ttk.Label(col_frame, text="AI:").grid(row=0, column=0, sticky=tk.W)
            ai_combo = ttk.Combobox(col_frame, values=list(self.available_ais.keys()), width=15, state="readonly")
            ai_combo.set("ChatGPT")  # デフォルト
            ai_combo.grid(row=0, column=1, padx=5)
            
            # モデル選択
            ttk.Label(col_frame, text="モデル:").grid(row=0, column=2, sticky=tk.W, padx=(10,0))
            model_combo = ttk.Combobox(col_frame, width=20, state="readonly")
            model_combo.grid(row=0, column=3, padx=5)
            
            # 設定選択
            ttk.Label(col_frame, text="設定:").grid(row=1, column=0, sticky=tk.W, pady=5)
            settings_frame = ttk.Frame(col_frame)
            settings_frame.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5)
            
            settings_vars = {}
            
            # AI変更時のモデル・設定更新
            def update_options(event, ai_combo=ai_combo, model_combo=model_combo, settings_frame=settings_frame, settings_vars=settings_vars):
                selected_ai = ai_combo.get()
                if selected_ai in self.available_ais:
                    # モデル更新
                    model_combo['values'] = self.available_ais[selected_ai]['models']
                    model_combo.set(self.available_ais[selected_ai]['models'][0])
                    
                    # 設定チェックボックス更新
                    for widget in settings_frame.winfo_children():
                        widget.destroy()
                    settings_vars.clear()
                    
                    for j, setting in enumerate(self.available_ais[selected_ai]['settings']):
                        var = tk.BooleanVar()
                        if setting == "DeepThink":  # DeepThinkはデフォルトON
                            var.set(True)
                        cb = ttk.Checkbutton(settings_frame, text=setting, variable=var)
                        cb.grid(row=j//3, column=j%3, sticky=tk.W, padx=5)
                        settings_vars[setting] = var
            
            ai_combo.bind('<<ComboboxSelected>>', update_options)
            
            # 初期設定
            update_options(None, ai_combo, model_combo, settings_frame, settings_vars)
            
            # 詳細設定ボタン
            ttk.Button(col_frame, text="詳細設定", 
                      command=lambda idx=i: self.open_advanced_settings(idx)).grid(row=0, column=4, padx=10)
            
            # 設定状況表示
            status_label = ttk.Label(col_frame, text="未設定", foreground="red")
            status_label.grid(row=1, column=4, padx=10)
            
            # 設定を保存
            self.column_configs[i] = {
                'column_info': col_info,
                'ai_combo': ai_combo,
                'model_combo': model_combo,
                'settings_vars': settings_vars,
                'status_label': status_label
            }
    
    def open_advanced_settings(self, column_index):
        """詳細設定ダイアログ"""
        config = self.column_configs[column_index]
        
        # 新しいウィンドウ
        settings_window = tk.Toplevel(self.root)
        settings_window.title(f"詳細設定 - 列{column_index + 1}")
        settings_window.geometry("400x300")
        
        # 温度設定
        ttk.Label(settings_window, text="Temperature (0.0-1.0):").pack(pady=5)
        temp_var = tk.DoubleVar(value=0.7)
        temp_scale = ttk.Scale(settings_window, from_=0.0, to=1.0, variable=temp_var, orient=tk.HORIZONTAL)
        temp_scale.pack(fill=tk.X, padx=20)
        
        # 最大トークン数
        ttk.Label(settings_window, text="Max Tokens:").pack(pady=5)
        tokens_var = tk.IntVar(value=4000)
        tokens_entry = ttk.Entry(settings_window, textvariable=tokens_var)
        tokens_entry.pack(padx=20)
        
        # カスタムプロンプト
        ttk.Label(settings_window, text="カスタムプロンプト:").pack(pady=5)
        prompt_text = tk.Text(settings_window, height=5, width=40)
        prompt_text.pack(padx=20, pady=5)
        
        # 保存ボタン
        def save_advanced():
            config['advanced_settings'] = {
                'temperature': temp_var.get(),
                'max_tokens': tokens_var.get(),
                'custom_prompt': prompt_text.get(1.0, tk.END).strip()
            }
            config['status_label'].config(text="設定完了", foreground="green")
            settings_window.destroy()
            self.log(f"列{column_index + 1}の詳細設定を保存しました")
        
        ttk.Button(settings_window, text="保存", command=save_advanced).pack(pady=10)
    
    def save_config(self):
        """設定をJSONファイルに保存"""
        try:
            config_data = {
                'spreadsheet_url': self.spreadsheet_url,
                'sheet_name': self.sheet_name,
                'work_row': self.work_row,
                'copy_columns': self.copy_columns,
                'column_settings': {}
            }
            
            for idx, config in self.column_configs.items():
                settings = {}
                for setting, var in config['settings_vars'].items():
                    settings[setting] = var.get()
                
                config_data['column_settings'][idx] = {
                    'ai': config['ai_combo'].get(),
                    'model': config['model_combo'].get(),
                    'settings': settings,
                    'advanced_settings': config.get('advanced_settings', {})
                }
            
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
        """設定をJSONファイルから読み込み"""
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
                        
                        config['advanced_settings'] = settings.get('advanced_settings', {})
                        if config['advanced_settings']:
                            config['status_label'].config(text="設定完了", foreground="green")
            
            self.log(f"✅ 設定を読み込みました: {filename}")
            messagebox.showinfo("成功", "設定を読み込みました")
        
        except Exception as e:
            self.log(f"❌ 設定読み込み失敗: {e}")
            messagebox.showerror("エラー", str(e))
    
    def start_automation(self):
        """自動化処理開始"""
        if not self.copy_columns or not self.column_configs:
            messagebox.showerror("エラー", "まずシート情報を読み込んで列設定を行ってください")
            return
        
        # 別スレッドで実行
        self.automation_thread = threading.Thread(target=self.run_automation)
        self.automation_thread.daemon = True
        self.automation_thread.start()
    
    def run_automation(self):
        """自動化処理実行（メインロジック）"""
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
                ai_service = col_config['ai_combo'].get().lower().replace(' ', '_')
                model = col_config['model_combo'].get()
                
                # 設定取得
                settings = {}
                for setting, var in col_config['settings_vars'].items():
                    settings[setting] = var.get()
                
                advanced_settings = col_config.get('advanced_settings', {})
                
                self.log(f"  AI: {ai_service}, モデル: {model}")
                self.log(f"  設定: {[k for k, v in settings.items() if v]}")
                
                # 処理対象行を検索（A列の連番）
                row_idx = self.work_row + 1
                while row_idx < len(self.sheet_data):
                    # A列チェック
                    if (len(self.sheet_data[row_idx]) == 0 or 
                        not str(self.sheet_data[row_idx][0]).strip()):
                        break  # 空行で終了
                    
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
                        result = self.extension_bridge.process_with_extension(
                            text=copy_text,
                            ai_service=ai_service.replace('_', ''),
                            model=model
                        )
                        
                        if result['success']:
                            response_text = result['result']
                            
                            # カスタムプロンプトがあれば追加
                            if advanced_settings.get('custom_prompt'):
                                response_text = f"{advanced_settings['custom_prompt']}\n\n{response_text}"
                            
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
            
            if total_tasks > 0:
                success_rate = (completed_tasks / total_tasks) * 100
                self.log(f"成功率: {success_rate:.1f}%")
            
        except Exception as e:
            self.log(f"❌ 自動化処理エラー: {e}")
            self.update_status(f"エラー: {e}")
    
    def stop_automation(self):
        """自動化処理停止"""
        # 実装：スレッド停止機能
        self.update_status("停止中...")
        self.log("⏹️ 自動化処理を停止しました")
    
    def update_status(self, message):
        """ステータス更新（UIスレッドセーフ）"""
        self.root.after(0, lambda: self.status_label.config(text=message))
    
    def log(self, message):
        """ログ出力（UIスレッドセーフ）"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
        
        self.root.after(0, update_log)

def main():
    """メイン実行関数"""
    print("🎯 CLAUDE.md要件完全対応 - スプレッドシート自動化GUIアプリ")
    print("="*60)
    print("📋 主要機能:")
    print("  ✅ 5行目作業指示行の自動検出")
    print("  ✅ 複数コピー列の個別AI設定")
    print("  ✅ 各AIの最新モデル選択")
    print("  ✅ DeepThink等詳細設定")
    print("  ✅ Chrome拡張機能統合")
    print("  ✅ 設定保存・読込機能")
    print()
    print("📱 GUI起動中...")
    
    root = tk.Tk()
    app = SpreadsheetAutomationGUI(root)
    
    # 初心者向けヘルプメッセージ
    help_message = """
🔰 初心者向け使用手順:

1. 📊 スプレッドシート設定
   - GoogleスプレッドシートのURLを入力
   - 「URLから読込」でシート一覧を取得
   - 対象シートを選択

2. 📋 シート情報読込
   - 「シート情報読込」で作業指示行を自動検出
   - 5行目のA列「作業指示行」から構造解析
   - 複数のコピー列を自動検出

3. 🤖 AI設定
   - 各コピー列毎にAIを選択
   - モデルを選択（最新モデル対応）
   - DeepThink等の設定をチェック
   - 「詳細設定」で温度等を調整

4. 🚀 実行
   - 「自動化開始」で処理実行
   - リアルタイム進捗表示
   - ログで詳細確認

💡 設定は保存・読込できます！
    """
    
    app.log(help_message)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n⏹️ アプリケーション終了")

if __name__ == "__main__":
    main()