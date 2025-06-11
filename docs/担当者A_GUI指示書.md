# 担当者A: GUI・設定管理 専用指示書

## 🎯 あなたの役割
**GUIアプリケーション全体の設計・実装**
- ユーザーが直感的に操作できるインターフェース作成
- 設定管理システムの構築
- 進捗表示・ログ表示の実装

## 📁 あなたが編集するファイル

### メインファイル
```
src/gui/
├── main_window.py        # 🔥 メインGUIウィンドウ
├── components.py         # 🔥 UI部品（ボタン、リスト等）
├── settings_dialog.py    # 🔥 設定画面ダイアログ
└── progress_window.py    # 🔥 進捗表示画面

main.py                   # 🔥 アプリケーション起動部分のみ
```

### サポートファイル（必要に応じて編集）
```
src/utils/config_manager.py  # 設定管理機能拡張
docs/GUI_DESIGN.md          # UI設計ドキュメント（作成）
```

## 🚀 作業開始手順

### 1日目: 環境セットアップ
```bash
# Git準備
git checkout feature/gui-components
git pull origin develop
git merge develop

# ディレクトリ作成
mkdir -p src/gui
touch src/gui/__init__.py

# 動作確認
python -c "import tkinter; print('tkinter利用可能')"
```

### 2-3日目: メインウィンドウ作成
```python
# src/gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from src.utils.logger import logger
from src.utils.config_manager import config_manager

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_ui()
        self.setup_bindings()
    
    def setup_window(self):
        """ウィンドウ基本設定"""
        self.root.title("AI自動化ツール")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # アイコン設定（オプション）
        # self.root.iconphoto(False, tk.PhotoImage(file="icon.png"))
    
    def setup_ui(self):
        """UI要素配置"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # スプレッドシート設定エリア
        self.create_spreadsheet_section(main_frame)
        
        # AI設定エリア  
        self.create_ai_section(main_frame)
        
        # 制御ボタンエリア
        self.create_control_section(main_frame)
        
        # 進捗・ログエリア
        self.create_progress_section(main_frame)
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
    
    def create_spreadsheet_section(self, parent):
        """スプレッドシート設定セクション"""
        # ラベルフレーム
        sheet_frame = ttk.LabelFrame(parent, text="スプレッドシート設定", padding="5")
        sheet_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # URL入力
        ttk.Label(sheet_frame, text="スプレッドシートURL:").grid(row=0, column=0, sticky=tk.W)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(sheet_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # シート選択
        ttk.Label(sheet_frame, text="シート名:").grid(row=1, column=0, sticky=tk.W)
        self.sheet_var = tk.StringVar()
        self.sheet_combo = ttk.Combobox(sheet_frame, textvariable=self.sheet_var)
        self.sheet_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 更新ボタン
        ttk.Button(sheet_frame, text="シート一覧更新", 
                  command=self.update_sheet_list).grid(row=1, column=2, padx=5)
        
        sheet_frame.columnconfigure(1, weight=1)
    
    def create_ai_section(self, parent):
        """AI設定セクション"""
        ai_frame = ttk.LabelFrame(parent, text="AI設定", padding="5")
        ai_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # AI選択（複数選択可能）
        ttk.Label(ai_frame, text="使用するAI:").grid(row=0, column=0, sticky=tk.W)
        
        # チェックボックスフレーム
        ai_check_frame = ttk.Frame(ai_frame)
        ai_check_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        self.ai_vars = {}
        ai_list = ["ChatGPT", "Claude", "Gemini", "Genspark", "Google AI Studio"]
        for i, ai in enumerate(ai_list):
            var = tk.BooleanVar()
            self.ai_vars[ai] = var
            ttk.Checkbutton(ai_check_frame, text=ai, variable=var).grid(
                row=i//3, column=i%3, sticky=tk.W, padx=5
            )
        
        # 詳細設定ボタン
        ttk.Button(ai_frame, text="詳細設定", 
                  command=self.open_ai_settings).grid(row=0, column=2, padx=5)
    
    def create_control_section(self, parent):
        """制御ボタンセクション"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        # 開始ボタン
        self.start_button = ttk.Button(control_frame, text="処理開始", 
                                      command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 停止ボタン
        self.stop_button = ttk.Button(control_frame, text="処理停止", 
                                     command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 設定保存ボタン
        ttk.Button(control_frame, text="設定保存", 
                  command=self.save_settings).pack(side=tk.LEFT, padx=5)
    
    def create_progress_section(self, parent):
        """進捗・ログセクション"""
        progress_frame = ttk.LabelFrame(parent, text="処理状況", padding="5")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 進捗バー
        ttk.Label(progress_frame, text="進捗:").grid(row=0, column=0, sticky=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var)
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # 進捗ラベル
        self.progress_label = ttk.Label(progress_frame, text="待機中")
        self.progress_label.grid(row=0, column=2)
        
        # ログエリア
        ttk.Label(progress_frame, text="ログ:").grid(row=1, column=0, sticky=(tk.W, tk.N), pady=(10,0))
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=15, width=80)
        self.log_text.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        progress_frame.columnconfigure(1, weight=1)
        progress_frame.rowconfigure(2, weight=1)
    
    # イベントハンドラー（実装必要）
    def update_sheet_list(self):
        """シート一覧更新"""
        # TODO: 担当者Bのsheets_clientを呼び出し
        pass
    
    def open_ai_settings(self):
        """AI詳細設定ダイアログ表示"""
        # TODO: settings_dialog.py を実装
        pass
    
    def start_processing(self):
        """処理開始"""
        # TODO: 担当者Cのautomationを呼び出し
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.add_log("INFO", "処理を開始しました")
    
    def stop_processing(self):
        """処理停止"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.add_log("INFO", "処理を停止しました")
    
    def save_settings(self):
        """設定保存"""
        config = {
            "spreadsheet_url": self.url_var.get(),
            "sheet_name": self.sheet_var.get(),
            "selected_ais": {k: v.get() for k, v in self.ai_vars.items()}
        }
        config_manager.set("gui_settings", config)
        config_manager.save_config()
        self.add_log("INFO", "設定を保存しました")
    
    def add_log(self, level, message):
        """ログ追加"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # ログファイルにも出力
        logger.info(f"GUI: {message}")
    
    def update_progress(self, current, total, message=""):
        """進捗更新"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{current}/{total} - {message}")
    
    def setup_bindings(self):
        """キーバインド設定"""
        self.root.bind('<Control-s>', lambda e: self.save_settings())
        self.root.bind('<F5>', lambda e: self.update_sheet_list())
    
    def run(self):
        """アプリケーション実行"""
        # 設定読み込み
        self.load_settings()
        # メインループ開始
        self.root.mainloop()
    
    def load_settings(self):
        """設定読み込み"""
        gui_settings = config_manager.get("gui_settings", {})
        if gui_settings:
            self.url_var.set(gui_settings.get("spreadsheet_url", ""))
            self.sheet_var.set(gui_settings.get("sheet_name", ""))
            selected_ais = gui_settings.get("selected_ais", {})
            for ai, var in self.ai_vars.items():
                var.set(selected_ais.get(ai, False))

if __name__ == "__main__":
    app = MainWindow()
    app.run()
```

## 📅 開発スケジュール

### 第1週: 基盤構築
- [x] メインウィンドウ基本レイアウト
- [ ] スプレッドシート設定UI
- [ ] AI選択UI  
- [ ] 基本ボタン・イベント

### 第2週: 高度な機能
- [ ] 設定ダイアログ（settings_dialog.py）
- [ ] 進捗表示システム（progress_window.py）
- [ ] ログ表示・フィルター機能

### 第3週: 統合・調整
- [ ] 担当者B・Cとの連携
- [ ] エラーハンドリング強化
- [ ] UI/UXの最適化

## 🔗 他担当との連携

### 担当者Bに提供する機能
```python
def get_spreadsheet_url(self) -> str:
    return self.url_var.get()

def get_selected_sheet(self) -> str:
    return self.sheet_var.get()

def update_sheet_dropdown(self, sheet_names: List[str]):
    self.sheet_combo['values'] = sheet_names
```

### 担当者Cに提供する機能
```python
def get_selected_ais(self) -> List[str]:
    return [ai for ai, var in self.ai_vars.items() if var.get()]

def update_progress_callback(self, current: int, total: int, message: str):
    self.update_progress(current, total, message)

def log_callback(self, level: str, message: str):
    self.add_log(level, message)
```

## ⚠️ 注意点

### セキュリティ
- 設定ファイルに機密情報を保存しない
- ログに個人情報を出力しない

### パフォーマンス
- 長時間処理はThreadingで分離
- GUIフリーズを避ける
- メモリリークに注意

### ユーザビリティ
- エラー時は分かりやすいメッセージ
- 操作の取り消し・やり直し機能
- キーボードショートカット対応

## 🧪 テスト方法

### 基本動作テスト
```bash
# GUI起動テスト
python -c "
from src.gui.main_window import MainWindow
app = MainWindow()
print('GUI初期化成功')
"

# 設定保存テスト
python main.py
# 設定入力後「設定保存」ボタンクリック
# config/settings.json 確認
```

### 毎日のテストチェックリスト
- [ ] アプリケーションが正常起動する
- [ ] 全UI要素が表示される
- [ ] ボタンがクリックできる
- [ ] 設定保存・読み込みが機能する
- [ ] ログが正常に表示される

## 📝 日次報告テンプレート

```
【担当者A - GUI】日次報告
日付: 2024/XX/XX

完了した作業:
- メインウィンドウレイアウト作成
- スプレッドシート設定UI実装

明日の予定:
- AI選択チェックボックス実装
- 進捗バー表示機能追加

困っている点:
- tkinterのレスポンシブレイアウトについて

他担当への依頼:
- 担当者B: get_sheet_names() の戻り値形式確認
```

**頑張ってください！何か質問があれば遠慮なく聞いてください。**