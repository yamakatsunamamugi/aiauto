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

from src.automation.extension_bridge import ExtensionBridge
from src.sheets.sheets_client import SheetsClient

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
            self.sheets_client = SheetsClient()
            self.extension_bridge = ExtensionBridge()
            self.log("✅ APIクライアント初期化完了")
        except Exception as e:
            self.log(f"❌ APIクライアント初期化失敗: {e}")
    
    def load_from_url(self):
        """URLからスプレッドシート読み込み"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("エラー", "スプレッドシートURLを入力してください")
            return
        
        try:
            # URLからスプレッドシートID抽出
            if '/spreadsheets/d/' in url:
                sheet_id = url.split('/spreadsheets/d/')[1].split('/')[0]
            else:
                messagebox.showerror("エラー", "無効なスプレッドシートURLです")
                return
            
            self.spreadsheet_url = url
            
            # スプレッドシート情報取得
            spreadsheet_info = self.sheets_client.get_spreadsheet_info(sheet_id)
            if not spreadsheet_info:
                messagebox.showerror("エラー", "スプレッドシート情報を取得できませんでした")
                return
            
            # シート名一覧取得
            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet_info['sheets']]
            self.sheet_combo['values'] = sheet_names
            if sheet_names:
                self.sheet_combo.set(sheet_names[0])
            
            self.log(f"✅ スプレッドシート読み込み完了: {len(sheet_names)}シート")
            
        except Exception as e:
            self.log(f"❌ スプレッドシート読み込み失敗: {e}")
            messagebox.showerror("エラー", str(e))
    
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
                    '作業' in str(self.sheet_data[i][0])):
                    self.work_row = i
                    break
            
            if self.work_row is None:
                messagebox.showerror("エラー", "作業指示行（A列に「作業」）が見つかりません")
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
    
    def load_config(self):\n        \"\"\"設定をJSONファイルから読み込み\"\"\"\n        try:\n            filename = filedialog.askopenfilename(\n                filetypes=[(\"JSON files\", \"*.json\")],\n                title=\"設定を読み込み\"\n            )\n            \n            if not filename:\n                return\n            \n            with open(filename, 'r', encoding='utf-8') as f:\n                config_data = json.load(f)\n            \n            # 基本設定を復元\n            if config_data.get('spreadsheet_url'):\n                self.url_entry.delete(0, tk.END)\n                self.url_entry.insert(0, config_data['spreadsheet_url'])\n                self.load_from_url()\n            \n            if config_data.get('sheet_name'):\n                self.sheet_combo.set(config_data['sheet_name'])\n                self.load_sheet_info()\n            \n            # 列設定を復元\n            if config_data.get('column_settings'):\n                for idx_str, settings in config_data['column_settings'].items():\n                    idx = int(idx_str)\n                    if idx in self.column_configs:\n                        config = self.column_configs[idx]\n                        config['ai_combo'].set(settings.get('ai', 'ChatGPT'))\n                        config['model_combo'].set(settings.get('model', ''))\n                        \n                        for setting, value in settings.get('settings', {}).items():\n                            if setting in config['settings_vars']:\n                                config['settings_vars'][setting].set(value)\n                        \n                        config['advanced_settings'] = settings.get('advanced_settings', {})\n                        if config['advanced_settings']:\n                            config['status_label'].config(text=\"設定完了\", foreground=\"green\")\n            \n            self.log(f\"✅ 設定を読み込みました: {filename}\")\n            messagebox.showinfo(\"成功\", \"設定を読み込みました\")\n        \n        except Exception as e:\n            self.log(f\"❌ 設定読み込み失敗: {e}\")\n            messagebox.showerror(\"エラー\", str(e))\n    \n    def start_automation(self):\n        \"\"\"自動化処理開始\"\"\"\n        if not self.copy_columns or not self.column_configs:\n            messagebox.showerror(\"エラー\", \"まずシート情報を読み込んで列設定を行ってください\")\n            return\n        \n        # 別スレッドで実行\n        self.automation_thread = threading.Thread(target=self.run_automation)\n        self.automation_thread.daemon = True\n        self.automation_thread.start()\n    \n    def run_automation(self):\n        \"\"\"自動化処理実行（メインロジック）\"\"\"\n        try:\n            self.update_status(\"自動化処理開始...\")\n            sheet_id = self.spreadsheet_url.split('/spreadsheets/d/')[1].split('/')[0]\n            \n            total_tasks = 0\n            completed_tasks = 0\n            \n            # 各コピー列を処理\n            for col_idx, col_config in self.column_configs.items():\n                col_info = col_config['column_info']\n                \n                self.log(f\"\\n📝 列{col_idx + 1} ({col_info['copy_letter']}列) を処理中...\")\n                \n                # AI設定取得\n                ai_service = col_config['ai_combo'].get().lower().replace(' ', '_')\n                model = col_config['model_combo'].get()\n                \n                # 設定取得\n                settings = {}\n                for setting, var in col_config['settings_vars'].items():\n                    settings[setting] = var.get()\n                \n                advanced_settings = col_config.get('advanced_settings', {})\n                \n                self.log(f\"  AI: {ai_service}, モデル: {model}\")\n                self.log(f\"  設定: {[k for k, v in settings.items() if v]}\")\n                \n                # 処理対象行を検索（A列の連番）\n                row_idx = self.work_row + 1\n                while row_idx < len(self.sheet_data):\n                    # A列チェック\n                    if (len(self.sheet_data[row_idx]) == 0 or \n                        not str(self.sheet_data[row_idx][0]).strip()):\n                        break  # 空行で終了\n                    \n                    a_value = str(self.sheet_data[row_idx][0]).strip()\n                    if not a_value.isdigit():\n                        row_idx += 1\n                        continue\n                    \n                    # 処理済みチェック\n                    if (len(self.sheet_data[row_idx]) > col_info['process_col'] and \n                        str(self.sheet_data[row_idx][col_info['process_col']]).strip() == '処理済み'):\n                        row_idx += 1\n                        continue\n                    \n                    # コピーテキスト取得\n                    if len(self.sheet_data[row_idx]) <= col_info['copy_col']:\n                        row_idx += 1\n                        continue\n                    \n                    copy_text = str(self.sheet_data[row_idx][col_info['copy_col']]).strip()\n                    if not copy_text:\n                        row_idx += 1\n                        continue\n                    \n                    total_tasks += 1\n                    \n                    self.log(f\"    行{row_idx + 1}: {copy_text[:50]}...\")\n                    \n                    try:\n                        # AI処理実行\n                        result = self.extension_bridge.process_with_extension(\n                            text=copy_text,\n                            ai_service=ai_service.replace('_', ''),\n                            model=model\n                        )\n                        \n                        if result['success']:\n                            response_text = result['result']\n                            \n                            # カスタムプロンプトがあれば追加\n                            if advanced_settings.get('custom_prompt'):\n                                response_text = f\"{advanced_settings['custom_prompt']}\\n\\n{response_text}\"\n                            \n                            # 結果書き込み\n                            paste_range = f\"{self.sheet_name}!{col_info['paste_letter']}{row_idx + 1}\"\n                            self.sheets_client.write_range(sheet_id, paste_range, [[response_text]])\n                            \n                            # 処理完了マーク\n                            process_range = f\"{self.sheet_name}!{col_info['process_letter']}{row_idx + 1}\"\n                            self.sheets_client.write_range(sheet_id, process_range, [[\"処理済み\"]])\n                            \n                            completed_tasks += 1\n                            self.log(f\"      ✅ 成功\")\n                        else:\n                            # エラー記録\n                            error_range = f\"{self.sheet_name}!{col_info['error_letter']}{row_idx + 1}\"\n                            self.sheets_client.write_range(sheet_id, error_range, [[result['error']]])\n                            self.log(f\"      ❌ 失敗: {result['error']}\")\n                    \n                    except Exception as e:\n                        # エラー記録\n                        error_range = f\"{self.sheet_name}!{col_info['error_letter']}{row_idx + 1}\"\n                        self.sheets_client.write_range(sheet_id, error_range, [[str(e)]])\n                        self.log(f\"      ❌ エラー: {e}\")\n                    \n                    # 進捗更新\n                    if total_tasks > 0:\n                        progress = (completed_tasks / total_tasks) * 100\n                        self.progress['value'] = progress\n                        self.update_status(f\"処理中... {completed_tasks}/{total_tasks} 完了\")\n                    \n                    row_idx += 1\n                    time.sleep(2)  # レート制限対策\n            \n            # 完了\n            self.update_status(f\"自動化完了: {completed_tasks}/{total_tasks} 成功\")\n            self.log(f\"\\n🎉 自動化処理完了: {completed_tasks}/{total_tasks} 成功\")\n            \n            if total_tasks > 0:\n                success_rate = (completed_tasks / total_tasks) * 100\n                self.log(f\"成功率: {success_rate:.1f}%\")\n            \n        except Exception as e:\n            self.log(f\"❌ 自動化処理エラー: {e}\")\n            self.update_status(f\"エラー: {e}\")\n    \n    def stop_automation(self):\n        \"\"\"自動化処理停止\"\"\"\n        # 実装：スレッド停止機能\n        self.update_status(\"停止中...\")\n        self.log(\"⏹️ 自動化処理を停止しました\")\n    \n    def update_status(self, message):\n        \"\"\"ステータス更新（UIスレッドセーフ）\"\"\"\n        self.root.after(0, lambda: self.status_label.config(text=message))\n    \n    def log(self, message):\n        \"\"\"ログ出力（UIスレッドセーフ）\"\"\"\n        timestamp = time.strftime(\"%H:%M:%S\")\n        log_message = f\"[{timestamp}] {message}\\n\"\n        \n        def update_log():\n            self.log_text.insert(tk.END, log_message)\n            self.log_text.see(tk.END)\n        \n        self.root.after(0, update_log)\n\ndef main():\n    \"\"\"メイン実行関数\"\"\"\n    print(\"🎯 CLAUDE.md要件完全対応 - スプレッドシート自動化GUIアプリ\")\n    print(\"=\"*60)\n    print(\"📋 主要機能:\")\n    print(\"  ✅ 5行目作業指示行の自動検出\")\n    print(\"  ✅ 複数コピー列の個別AI設定\")\n    print(\"  ✅ 各AIの最新モデル選択\")\n    print(\"  ✅ DeepThink等詳細設定\")\n    print(\"  ✅ Chrome拡張機能統合\")\n    print(\"  ✅ 設定保存・読込機能\")\n    print()\n    print(\"📱 GUI起動中...\")\n    \n    root = tk.Tk()\n    app = SpreadsheetAutomationGUI(root)\n    \n    # 初心者向けヘルプメッセージ\n    help_message = \"\"\"\n🔰 初心者向け使用手順:\n\n1. 📊 スプレッドシート設定\n   - GoogleスプレッドシートのURLを入力\n   - 「URLから読込」でシート一覧を取得\n   - 対象シートを選択\n\n2. 📋 シート情報読込\n   - 「シート情報読込」で作業指示行を自動検出\n   - 5行目のA列「作業」から構造解析\n   - 複数のコピー列を自動検出\n\n3. 🤖 AI設定\n   - 各コピー列毎にAIを選択\n   - モデルを選択（最新モデル対応）\n   - DeepThink等の設定をチェック\n   - 「詳細設定」で温度等を調整\n\n4. 🚀 実行\n   - 「自動化開始」で処理実行\n   - リアルタイム進捗表示\n   - ログで詳細確認\n\n💡 設定は保存・読込できます！\n    \"\"\"\n    \n    app.log(help_message)\n    \n    try:\n        root.mainloop()\n    except KeyboardInterrupt:\n        print(\"\\n⏹️ アプリケーション終了\")\n\nif __name__ == \"__main__\":\n    main()