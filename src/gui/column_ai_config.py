"""
列ごとのAI設定ダイアログ
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional

class ColumnAIConfigDialog:
    """列ごとのAI設定ダイアログ"""
    
    def __init__(self, parent, copy_columns: List[str], current_config: Optional[Dict[str, Dict]] = None):
        """
        初期化
        
        Args:
            parent: 親ウィンドウ
            copy_columns: コピー列のリスト
            current_config: 現在の設定 {column: {"ai_service": str, "ai_model": str}}
        """
        self.result = None
        self.copy_columns = copy_columns
        self.current_config = current_config or {}
        
        # ダイアログ作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🤖 列ごとのAI設定")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 変数
        self.column_configs = {}
        
        self._create_widgets()
        self._load_current_config()
        
        # センタリング
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
    def _create_widgets(self):
        """ウィジェット作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 説明ラベル
        ttk.Label(main_frame, text="各コピー列で使用するAIサービスとモデルを設定してください。").grid(
            row=0, column=0, columnspan=3, pady=(0, 10), sticky=tk.W
        )
        
        # ヘッダー
        ttk.Label(main_frame, text="コピー列", font=("", 10, "bold")).grid(row=1, column=0, padx=5, pady=5)
        ttk.Label(main_frame, text="AIサービス", font=("", 10, "bold")).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(main_frame, text="モデル", font=("", 10, "bold")).grid(row=1, column=2, padx=5, pady=5)
        
        # 列設定
        row = 2
        for col in self.copy_columns:
            # 列名
            ttk.Label(main_frame, text=col).grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
            
            # AIサービス選択
            service_var = tk.StringVar(value="chatgpt")
            service_combo = ttk.Combobox(
                main_frame, 
                textvariable=service_var,
                values=["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"],
                state="readonly",
                width=20
            )
            service_combo.grid(row=row, column=1, padx=5, pady=2)
            
            # モデル選択
            model_var = tk.StringVar()
            model_combo = ttk.Combobox(main_frame, textvariable=model_var, state="readonly", width=20)
            model_combo.grid(row=row, column=2, padx=5, pady=2)
            
            # 設定保存
            self.column_configs[col] = {
                "service_var": service_var,
                "model_var": model_var,
                "service_combo": service_combo,
                "model_combo": model_combo
            }
            
            # サービス変更時のイベント
            service_combo.bind("<<ComboboxSelected>>", 
                             lambda e, c=col: self._on_service_changed(c))
            
            row += 1
        
        # ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self._on_cancel).pack(side=tk.LEFT, padx=5)
        
        # ダイアログの重み設定
        self.dialog.rowconfigure(0, weight=1)
        self.dialog.columnconfigure(0, weight=1)
        main_frame.rowconfigure(row-1, weight=1)
        
    def _load_current_config(self):
        """現在の設定を読み込み"""
        # モデルオプション
        self.model_options = {
            "chatgpt": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            "claude": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "gemini": ["gemini-pro", "gemini-pro-vision"],
            "genspark": ["default"],
            "google_ai_studio": ["gemini-pro", "gemini-pro-vision"]
        }
        
        # 各列の設定
        for col in self.copy_columns:
            config = self.column_configs[col]
            
            # 既存設定があれば適用
            if col in self.current_config:
                service = self.current_config[col].get("ai_service", "chatgpt")
                model = self.current_config[col].get("ai_model", "")
                config["service_var"].set(service)
                config["model_var"].set(model)
            
            # モデルオプション更新
            self._update_model_options(col)
            
    def _on_service_changed(self, column):
        """サービス変更時の処理"""
        self._update_model_options(column)
        
    def _update_model_options(self, column):
        """モデルオプション更新"""
        config = self.column_configs[column]
        service = config["service_var"].get()
        models = self.model_options.get(service, [])
        
        config["model_combo"]["values"] = models
        if models and not config["model_var"].get():
            config["model_var"].set(models[0])
            
    def _on_ok(self):
        """OK押下時"""
        self.result = {}
        for col in self.copy_columns:
            config = self.column_configs[col]
            self.result[col] = {
                "ai_service": config["service_var"].get(),
                "ai_model": config["model_var"].get()
            }
        self.dialog.destroy()
        
    def _on_cancel(self):
        """キャンセル押下時"""
        self.result = None
        self.dialog.destroy()
        
    def show(self) -> Optional[Dict[str, Dict]]:
        """
        ダイアログ表示
        
        Returns:
            設定結果 or None（キャンセル時）
        """
        self.dialog.wait_window()
        return self.result