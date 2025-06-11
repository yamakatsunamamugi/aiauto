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
from src.utils.logger import logger


class MainWindow:
    """メインGUIウィンドウクラス"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.automation_controller = None
        self.automation_thread = None
        self.is_running = False
        
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
        
        # === AI設定セクション ===
        self.create_ai_section(main_frame, 1)
        
        # === 制御セクション ===
        self.create_control_section(main_frame, 2)
        
        # === ログセクション ===
        self.create_log_section(main_frame, 3)
        
        # === ステータスバー ===
        self.create_status_bar(main_frame, 4)
        
    def create_spreadsheet_section(self, parent, row):
        """スプレッドシート設定セクション"""
        # フレーム
        frame = ttk.LabelFrame(parent, text="📊 Googleスプレッドシート設定", padding="5")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        frame.columnconfigure(1, weight=1)
        
        # スプレッドシートURL
        ttk.Label(frame, text="スプレッドシートURL:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.sheet_url_var = tk.StringVar()
        url_entry = ttk.Entry(frame, textvariable=self.sheet_url_var, width=60)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # シート名選択
        ttk.Label(frame, text="シート名:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.sheet_name_var = tk.StringVar()
        self.sheet_name_combo = ttk.Combobox(frame, textvariable=self.sheet_name_var, state="readonly")
        self.sheet_name_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
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
        
        # ログイン確認ボタン
        self.check_login_btn = ttk.Button(frame, text="🔐 ログイン確認", command=self.check_login_status)
        self.check_login_btn.grid(row=3, column=2, padx=5, pady=5)
        
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
        
    def load_sheet_info(self):
        """シート情報読込"""
        url = self.sheet_url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "スプレッドシートURLを入力してください")
            return
            
        self.add_log_entry("🔄 シート情報を読み込み中...")
        # TODO: 実際のシート情報読込処理
        self.sheet_name_combo['values'] = ["Sheet1", "データ", "テスト"]
        self.sheet_name_var.set("Sheet1")
        self.add_log_entry("✅ シート情報読み込み完了")
        
    def on_ai_service_changed(self, event=None):
        """AIサービス変更時の処理"""
        service = self.ai_service_var.get()
        
        # モデル選択肢を更新
        models = {
            "chatgpt": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            "claude": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "gemini": ["gemini-pro", "gemini-pro-vision"],
            "genspark": ["default"],
            "google_ai_studio": ["gemini-pro", "gemini-pro-vision"]
        }
        
        self.ai_model_combo['values'] = models.get(service, ["default"])
        if models.get(service):
            self.ai_model_var.set(models[service][0])
            
        # 機能オプションを更新
        self.update_ai_features(service)
        
    def update_ai_features(self, service):
        """AI機能オプション更新"""
        # 既存のウィジェットをクリア
        for widget in self.ai_features_frame.winfo_children():
            widget.destroy()
            
        # サービス毎の機能オプション
        features = {
            "chatgpt": ["DeepThink", "Code Interpreter", "Web Browsing"],
            "claude": ["思考モード", "長文解析"],
            "gemini": ["マルチモーダル", "コード生成"],
            "genspark": ["リサーチモード"],
            "google_ai_studio": ["実験的機能"]
        }
        
        ttk.Label(self.ai_features_frame, text="機能オプション:").grid(row=0, column=0, sticky=tk.W)
        
        self.feature_vars = {}
        service_features = features.get(service, [])
        
        for i, feature in enumerate(service_features):
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
                
                # TODO: 実際のログイン状態確認
                # 仮の結果
                logged_in = False
                
                if logged_in:
                    self.login_status_var.set("ログイン済み")
                    self.login_status_label.configure(foreground="green")
                else:
                    self.login_status_var.set("要ログイン")
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
            # TODO: 実際の自動化処理
            import time
            for i in range(101):
                if not self.is_running:
                    break
                    
                # 進捗更新
                self.root.after(0, lambda: self.progress_var.set(i))
                
                # ログ出力
                if i % 20 == 0:
                    self.add_log_entry(f"📊 処理進捗: {i}%")
                    
                time.sleep(0.1)
                
            if self.is_running:
                self.add_log_entry("✅ 自動化処理が完了しました")
            else:
                self.add_log_entry("⏹️ 自動化処理が停止されました")
                
        except Exception as e:
            self.add_log_entry(f"❌ 自動化エラー: {e}")
            
        finally:
            # UI状態リセット
            self.root.after(0, self.reset_ui_state)
            
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