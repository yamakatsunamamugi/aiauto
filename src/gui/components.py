"""
GUI部品モジュール

再利用可能なGUIコンポーネントとユーティリティ関数を提供します。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Any, Optional, Callable
import re


class ValidationMixin:
    """入力検証用のミックスインクラス"""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """URLの妥当性を検証"""
        if not url:
            return False
        
        # Google SheetsのURL形式をチェック
        pattern = r'https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9-_]+'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """メールアドレスの妥当性を検証"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_required(value: str) -> bool:
        """必須項目の検証"""
        return bool(value and value.strip())


class TooltipMixin:
    """ツールチップ機能のミックスインクラス"""
    
    def create_tooltip(self, widget: tk.Widget, text: str):
        """ウィジェットにツールチップを追加"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Arial", "8"))
            label.pack()
            
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


class LabeledEntry(ttk.Frame, ValidationMixin, TooltipMixin):
    """ラベル付きエントリーウィジェット"""
    
    def __init__(self, parent, label_text: str, width: int = 30, 
                 validate_func: Optional[Callable[[str], bool]] = None,
                 tooltip_text: str = ""):
        super().__init__(parent)
        
        self.validate_func = validate_func
        self.var = tk.StringVar()
        
        # ラベル
        self.label = ttk.Label(self, text=label_text)
        self.label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        # エントリー
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # バリデーション設定
        if validate_func:
            self.entry.bind("<FocusOut>", self._validate)
            self.entry.bind("<KeyRelease>", self._validate_on_change)
        
        # ツールチップ設定
        if tooltip_text:
            self.create_tooltip(self.entry, tooltip_text)
            
        self.columnconfigure(1, weight=1)
        
    def get(self) -> str:
        """値を取得"""
        return self.var.get()
        
    def set(self, value: str):
        """値を設定"""
        self.var.set(value)
        
    def _validate(self, event=None):
        """フォーカスアウト時のバリデーション"""
        if self.validate_func and not self.validate_func(self.get()):
            self.entry.configure(style="Invalid.TEntry")
            return False
        else:
            self.entry.configure(style="TEntry")
            return True
            
    def _validate_on_change(self, event=None):
        """入力変更時のバリデーション（エラー表示のクリア）"""
        if self.entry.cget("style") == "Invalid.TEntry":
            if self.validate_func and self.validate_func(self.get()):
                self.entry.configure(style="TEntry")


class LabeledCombobox(ttk.Frame, TooltipMixin):
    """ラベル付きコンボボックスウィジェット"""
    
    def __init__(self, parent, label_text: str, values: List[str] = None,
                 width: int = 30, state: str = "readonly", tooltip_text: str = ""):
        super().__init__(parent)
        
        self.var = tk.StringVar()
        
        # ラベル
        self.label = ttk.Label(self, text=label_text)
        self.label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        # コンボボックス
        self.combobox = ttk.Combobox(self, textvariable=self.var, 
                                   values=values or [], width=width, state=state)
        self.combobox.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # ツールチップ設定
        if tooltip_text:
            self.create_tooltip(self.combobox, tooltip_text)
            
        self.columnconfigure(1, weight=1)
        
    def get(self) -> str:
        """値を取得"""
        return self.var.get()
        
    def set(self, value: str):
        """値を設定"""
        self.var.set(value)
        
    def set_values(self, values: List[str]):
        """選択肢を設定"""
        self.combobox['values'] = values
        
    def current(self, index: int = None):
        """現在の選択インデックスを取得/設定"""
        if index is not None:
            self.combobox.current(index)
        else:
            return self.combobox.current()


class CheckboxGroup(ttk.Frame):
    """チェックボックスグループウィジェット"""
    
    def __init__(self, parent, title: str, options: Dict[str, str], 
                 columns: int = 3, default_selected: List[str] = None):
        super().__init__(parent)
        
        self.options = options
        self.vars = {}
        
        # グループフレーム
        group_frame = ttk.LabelFrame(self, text=title, padding="5")
        group_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # チェックボックス作成
        row_count = 0
        col_count = 0
        
        for key, display_name in options.items():
            var = tk.BooleanVar()
            self.vars[key] = var
            
            # デフォルト選択設定
            if default_selected and key in default_selected:
                var.set(True)
                
            checkbox = ttk.Checkbutton(group_frame, text=display_name, variable=var)
            checkbox.grid(row=row_count, column=col_count, sticky=tk.W, 
                         padx=(0, 20), pady=2)
            
            col_count += 1
            if col_count >= columns:
                col_count = 0
                row_count += 1
        
        # 制御ボタン
        button_frame = ttk.Frame(group_frame)
        button_frame.grid(row=row_count + 1, column=0, columnspan=columns, 
                         sticky=tk.W, pady=(10, 0))
        
        ttk.Button(button_frame, text="全選択", 
                  command=self.select_all, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="全解除", 
                  command=self.deselect_all, width=10).grid(row=0, column=1)
        
        self.columnconfigure(0, weight=1)
        group_frame.columnconfigure(0, weight=1)
        
    def get_selected(self) -> List[str]:
        """選択された項目のリストを取得"""
        return [key for key, var in self.vars.items() if var.get()]
        
    def set_selected(self, selected: List[str]):
        """選択状態を設定"""
        for key, var in self.vars.items():
            var.set(key in selected)
            
    def select_all(self):
        """全て選択"""
        for var in self.vars.values():
            var.set(True)
            
    def deselect_all(self):
        """全て解除"""
        for var in self.vars.values():
            var.set(False)


class ProgressPanel(ttk.Frame):
    """進捗表示パネルウィジェット"""
    
    def __init__(self, parent, title: str = "進捗状況"):
        super().__init__(parent)
        
        # フレーム設定
        panel_frame = ttk.LabelFrame(self, text=title, padding="5")
        panel_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        panel_frame.columnconfigure(0, weight=1)
        
        # 進捗バー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(panel_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 進捗テキスト
        self.progress_text_var = tk.StringVar(value="待機中...")
        self.progress_label = ttk.Label(panel_frame, textvariable=self.progress_text_var)
        self.progress_label.grid(row=1, column=0, sticky=tk.W)
        
        # 詳細情報表示エリア
        detail_frame = ttk.Frame(panel_frame)
        detail_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        detail_frame.columnconfigure(1, weight=1)
        
        ttk.Label(detail_frame, text="処理済み:").grid(row=0, column=0, sticky=tk.W)
        self.completed_var = tk.StringVar(value="0")
        ttk.Label(detail_frame, textvariable=self.completed_var).grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(detail_frame, text="残り:").grid(row=1, column=0, sticky=tk.W)
        self.remaining_var = tk.StringVar(value="0")
        ttk.Label(detail_frame, textvariable=self.remaining_var).grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(detail_frame, text="エラー:").grid(row=2, column=0, sticky=tk.W)
        self.error_var = tk.StringVar(value="0")
        ttk.Label(detail_frame, textvariable=self.error_var, foreground="red").grid(row=2, column=1, sticky=tk.W, padx=(5, 0))
        
        self.columnconfigure(0, weight=1)
        
    def update_progress(self, current: int, total: int, message: str = ""):
        """進捗を更新"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
            
        if message:
            self.progress_text_var.set(message)
            
    def update_details(self, completed: int, remaining: int, errors: int):
        """詳細情報を更新"""
        self.completed_var.set(str(completed))
        self.remaining_var.set(str(remaining))
        self.error_var.set(str(errors))
        
    def reset(self):
        """進捗をリセット"""
        self.progress_var.set(0)
        self.progress_text_var.set("待機中...")
        self.update_details(0, 0, 0)


class LogPanel(ttk.Frame):
    """ログ表示パネルウィジェット"""
    
    def __init__(self, parent, title: str = "ログ", height: int = 10):
        super().__init__(parent)
        
        # フレーム設定
        panel_frame = ttk.LabelFrame(self, text=title, padding="5")
        panel_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        panel_frame.columnconfigure(0, weight=1)
        panel_frame.rowconfigure(0, weight=1)
        
        # ログテキストエリア
        from tkinter import scrolledtext
        self.log_text = scrolledtext.ScrolledText(panel_frame, height=height, 
                                                wrap=tk.WORD, state="disabled")
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ログレベル用のタグ設定
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("DEBUG", foreground="gray")
        
        # 制御ボタン
        button_frame = ttk.Frame(panel_frame)
        button_frame.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(button_frame, text="クリア", 
                  command=self.clear_log, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="保存", 
                  command=self.save_log, width=10).grid(row=0, column=1)
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
    def add_log(self, level: str, message: str, timestamp: bool = True):
        """ログメッセージを追加"""
        import datetime
        
        if timestamp:
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
            log_message = f"[{time_str}] {level}: {message}\n"
        else:
            log_message = f"{level}: {message}\n"
            
        self.log_text.config(state="normal")
        
        # ログレベルに応じた色付けでテキストを挿入
        start_pos = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, log_message)
        end_pos = self.log_text.index(tk.END)
        
        # タグを適用
        self.log_text.tag_add(level, f"{start_pos} linestart", f"{end_pos} linestart")
        
        # 最下部までスクロール
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        
    def clear_log(self):
        """ログをクリア"""
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        
    def save_log(self):
        """ログをファイルに保存"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("テキストファイル", "*.txt"), ("全てのファイル", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    content = self.log_text.get(1.0, tk.END)
                    f.write(content)
                
                messagebox.showinfo("保存完了", f"ログを保存しました: {filename}")
                
        except Exception as e:
            messagebox.showerror("エラー", f"ログ保存に失敗しました: {e}")


class StatusBar(ttk.Frame):
    """ステータスバーウィジェット"""
    
    def __init__(self, parent):
        super().__init__(parent, relief=tk.SUNKEN, borderwidth=1)
        
        # 左側の状態表示
        self.status_var = tk.StringVar(value="準備完了")
        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W, padx=(5, 0))
        
        # 右側の追加情報表示
        self.info_var = tk.StringVar(value="")
        self.info_label = ttk.Label(self, textvariable=self.info_var)
        self.info_label.grid(row=0, column=1, sticky=tk.E, padx=(0, 5))
        
        self.columnconfigure(0, weight=1)
        
    def set_status(self, status: str):
        """ステータスを設定"""
        self.status_var.set(status)
        
    def set_info(self, info: str):
        """追加情報を設定"""
        self.info_var.set(info)


class ButtonPanel(ttk.Frame):
    """ボタンパネルウィジェット"""
    
    def __init__(self, parent, buttons: List[Dict[str, Any]], layout: str = "horizontal"):
        super().__init__(parent)
        
        self.buttons = {}
        
        if layout == "horizontal":
            for i, button_config in enumerate(buttons):
                btn = ttk.Button(self, **button_config)
                btn.grid(row=0, column=i, padx=(0, 10) if i < len(buttons) - 1 else 0)
                self.buttons[button_config.get("text", f"button_{i}")] = btn
        else:  # vertical
            for i, button_config in enumerate(buttons):
                btn = ttk.Button(self, **button_config)
                btn.grid(row=i, column=0, pady=(0, 5) if i < len(buttons) - 1 else 0, sticky=(tk.W, tk.E))
                self.buttons[button_config.get("text", f"button_{i}")] = btn
                self.columnconfigure(0, weight=1)
                
    def get_button(self, name: str) -> Optional[ttk.Button]:
        """ボタンを名前で取得"""
        return self.buttons.get(name)
        
    def enable_button(self, name: str):
        """ボタンを有効化"""
        button = self.get_button(name)
        if button:
            button.config(state="normal")
            
    def disable_button(self, name: str):
        """ボタンを無効化"""
        button = self.get_button(name)
        if button:
            button.config(state="disabled")


def setup_styles():
    """スタイル設定"""
    style = ttk.Style()
    
    # 無効なエントリー用のスタイル
    style.configure("Invalid.TEntry", fieldbackground="lightpink", 
                   foreground="darkred", bordercolor="red")


# モジュール初期化時にスタイルを設定
setup_styles()