#!/usr/bin/env python3
"""
シンプルな自動化GUI（拡張機能不要版）
PlaywrightまたはSeleniumで直接ブラウザ操作
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

class SimpleAutomationGUI:
    """シンプルな自動化GUIクラス（拡張機能不要）"""
    
    def __init__(self, root):
        """GUI初期化"""
        self.root = root
        self.root.title("シンプル自動化システム - 拡張機能不要版")
        self.root.geometry("1600x1200")
        
        # データ格納
        self.spreadsheet_url = ""
        self.sheet_name = ""
        self.sheet_data = []
        self.work_row = None
        self.copy_columns = []
        self.column_configs = {}
        
        # APIクライアント
        self.sheets_client = None
        self.browser = None  # Seleniumドライバー
        
        # AI設定データ（最新モデル）
        self.available_ais = {
            "ChatGPT": {
                "models": ["o1-preview", "o1-mini", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "url": "https://chat.openai.com"
            },
            "Claude": {
                "models": ["claude-3.5-sonnet", "claude-3.5-haiku", "claude-3-opus"],
                "url": "https://claude.ai"
            },
            "Gemini": {
                "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
                "url": "https://gemini.google.com"
            }
        }
        
        self.create_widgets()
        self.initialize_clients()
    
    def create_widgets(self):
        """ウィジェット作成"""
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 1. スプレッドシート設定
        setup_frame = ttk.LabelFrame(main_frame, text="📊 スプレッドシート設定", padding="10")
        setup_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(setup_frame, text="URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(setup_frame, width=80)
        self.url_entry.grid(row=0, column=1, padx=5)
        ttk.Button(setup_frame, text="読込", command=self.load_spreadsheet).grid(row=0, column=2)
        
        # 2. AI選択（シンプル版）
        ai_frame = ttk.LabelFrame(main_frame, text="🤖 AI設定", padding="10")
        ai_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(ai_frame, text="使用するAI:").grid(row=0, column=0, sticky=tk.W)
        self.ai_combo = ttk.Combobox(ai_frame, values=list(self.available_ais.keys()), width=20)
        self.ai_combo.set("ChatGPT")
        self.ai_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(ai_frame, text="モデル:").grid(row=0, column=2, sticky=tk.W, padx=(20,5))
        self.model_combo = ttk.Combobox(ai_frame, width=25)
        self.model_combo.grid(row=0, column=3, padx=5)
        
        # AI変更時の処理
        def update_models(event=None):
            ai = self.ai_combo.get()
            if ai in self.available_ais:
                self.model_combo['values'] = self.available_ais[ai]['models']
                self.model_combo.set(self.available_ais[ai]['models'][0])
        
        self.ai_combo.bind('<<ComboboxSelected>>', update_models)
        update_models()
        
        # 3. 実行制御
        control_frame = ttk.LabelFrame(main_frame, text="🚀 実行制御", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(control_frame, text="ブラウザ起動", command=self.start_browser).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="自動化開始", command=self.start_automation).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="停止", command=self.stop_automation).grid(row=0, column=2, padx=5)
        
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.status_label = ttk.Label(control_frame, text="待機中...")
        self.status_label.grid(row=2, column=0, columnspan=3)
        
        # 4. ログ表示（大きめ）
        log_frame = ttk.LabelFrame(main_frame, text="📝 実行ログ", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=30, width=120, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def initialize_clients(self):
        """クライアント初期化"""
        try:
            from src.sheets.sheets_client import SheetsClient
            self.sheets_client = SheetsClient()
            self.log("✅ Google Sheets クライアント初期化成功")
        except Exception as e:
            self.log(f"❌ 初期化エラー: {e}")
    
    def load_spreadsheet(self):
        """スプレッドシート読み込み"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("エラー", "URLを入力してください")
            return
        
        self.log(f"📊 スプレッドシート読み込み開始: {url}")
        # ここにスプレッドシート読み込み処理を実装
        self.log("✅ スプレッドシート読み込み完了（テスト）")
    
    def start_browser(self):
        """ブラウザ起動（Selenium使用）"""
        try:
            self.log("🌐 ブラウザ起動中...")
            
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 既存のプロファイルを使用（ログイン状態維持）
            options.add_argument("user-data-dir=/tmp/chrome_profile")
            
            self.browser = webdriver.Chrome(options=options)
            self.browser.maximize_window()
            
            # 選択されたAIのサイトを開く
            ai = self.ai_combo.get()
            if ai in self.available_ais:
                url = self.available_ais[ai]['url']
                self.browser.get(url)
                self.log(f"✅ {ai}を開きました: {url}")
                self.log("⚠️  必要に応じて手動でログインしてください")
            
        except Exception as e:
            self.log(f"❌ ブラウザ起動エラー: {e}")
            self.log("💡 ChromeDriverが必要です。以下を実行してください:")
            self.log("   pip install selenium webdriver-manager")
    
    def start_automation(self):
        """自動化開始"""
        if not self.browser:
            messagebox.showerror("エラー", "先にブラウザを起動してください")
            return
        
        self.log("🚀 自動化処理開始")
        self.progress.start()
        
        # 別スレッドで実行
        thread = threading.Thread(target=self.run_automation)
        thread.daemon = True
        thread.start()
    
    def run_automation(self):
        """自動化処理実行"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.keys import Keys
            
            ai = self.ai_combo.get()
            self.log(f"🤖 {ai}で処理開始")
            
            # テストメッセージ
            test_text = "こんにちは。今日の天気はどうですか？"
            
            if ai == "ChatGPT":
                # 入力欄を探す
                try:
                    textarea = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.ID, "prompt-textarea"))
                    )
                    textarea.clear()
                    textarea.send_keys(test_text)
                    textarea.send_keys(Keys.RETURN)
                    
                    self.log("✅ メッセージ送信成功")
                    
                    # 応答を待つ
                    time.sleep(5)
                    self.log("✅ 処理完了")
                    
                except Exception as e:
                    self.log(f"❌ 処理エラー: {e}")
                    self.log("💡 ChatGPTにログインしているか確認してください")
            
            elif ai == "Claude":
                self.log("⚠️  Claude自動化は開発中です")
            
            elif ai == "Gemini":
                self.log("⚠️  Gemini自動化は開発中です")
            
        except Exception as e:
            self.log(f"❌ 自動化エラー: {e}")
            import traceback
            self.log(f"詳細:\n{traceback.format_exc()}")
        
        finally:
            self.progress.stop()
            self.update_status("処理完了")
    
    def stop_automation(self):
        """自動化停止"""
        self.progress.stop()
        self.update_status("停止しました")
        self.log("⏹️ 自動化を停止しました")
        
        if self.browser:
            self.browser.quit()
            self.browser = None
            self.log("🌐 ブラウザを閉じました")
    
    def update_status(self, message):
        """ステータス更新"""
        self.status_label.config(text=message)
    
    def log(self, message):
        """ログ出力"""
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_msg)
        self.log_text.see(tk.END)
        
        # エラーは赤色
        if "❌" in message or "エラー" in message:
            self.log_text.tag_add("error", f"end-2l", "end-1l")
            self.log_text.tag_config("error", foreground="red")
        
        # 成功は緑色
        elif "✅" in message:
            self.log_text.tag_add("success", f"end-2l", "end-1l")
            self.log_text.tag_config("success", foreground="green")
        
        # 警告は黄色
        elif "⚠️" in message:
            self.log_text.tag_add("warning", f"end-2l", "end-1l")
            self.log_text.tag_config("warning", foreground="orange")

def main():
    """メイン実行"""
    print("🎯 シンプル自動化GUI（拡張機能不要版）")
    print("="*60)
    print("ブランチ: feature/browser-automation-api-free")
    print("特徴: Chrome拡張機能を使わずSeleniumで直接操作")
    print()
    
    root = tk.Tk()
    app = SimpleAutomationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()