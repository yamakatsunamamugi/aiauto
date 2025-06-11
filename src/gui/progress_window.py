"""
進捗表示画面モジュール

自動化処理の詳細進捗を表示する専用ウィンドウを提供します。
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, List, Any, Optional, Callable
import threading
import time
from datetime import datetime
from enum import Enum

from src.gui.components import ProgressPanel, LogPanel, StatusBar


class TaskStatus(Enum):
    """タスクステータス列挙型"""
    PENDING = "待機中"
    PROCESSING = "処理中"
    COMPLETED = "完了"
    ERROR = "エラー"
    SKIPPED = "スキップ"


class TaskInfo:
    """タスク情報クラス"""
    
    def __init__(self, task_id: str, row_number: int, ai_service: str, 
                 text_preview: str, status: TaskStatus = TaskStatus.PENDING):
        self.task_id = task_id
        self.row_number = row_number
        self.ai_service = ai_service
        self.text_preview = text_preview[:50] + "..." if len(text_preview) > 50 else text_preview
        self.status = status
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.result_preview: Optional[str] = None
        
    @property
    def duration(self) -> Optional[float]:
        """処理時間を秒で取得"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
        
    @property
    def display_duration(self) -> str:
        """表示用の処理時間"""
        duration = self.duration
        if duration is None:
            return "-"
        
        if duration < 60:
            return f"{duration:.1f}秒"
        else:
            minutes = int(duration // 60)
            seconds = duration % 60
            return f"{minutes}分{seconds:.1f}秒"


class ProgressWindow:
    """進捗表示ウィンドウクラス"""
    
    def __init__(self, parent, title: str = "処理進捗"):
        self.parent = parent
        self.title = title
        self.tasks: Dict[str, TaskInfo] = {}
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # コールバック
        self.on_cancel_callback: Optional[Callable] = None
        
        # ウィンドウ作成
        self.window = tk.Toplevel(parent)
        self.setup_window()
        self.setup_ui()
        
        # 更新タイマー
        self.update_timer_active = False
        self.start_update_timer()
        
    def setup_window(self):
        """ウィンドウの基本設定"""
        self.window.title(self.title)
        self.window.geometry("900x700")
        self.window.minsize(600, 500)
        self.window.transient(self.parent)
        
        # 親ウィンドウの中央に配置
        self.center_window()
        
        # 閉じるボタンの処理をオーバーライド
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
    def center_window(self):
        """ウィンドウを親ウィンドウの中央に配置"""
        self.window.update_idletasks()
        
        # 親ウィンドウの位置とサイズを取得
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # ウィンドウのサイズを取得
        window_width = self.window.winfo_reqwidth()
        window_height = self.window.winfo_reqheight()
        
        # 中央位置を計算
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.window.geometry(f"900x700+{x}+{y}")
        
    def setup_ui(self):
        """UI構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ウィンドウのリサイズ設定
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 全体進捗表示
        self.create_overall_progress_section(main_frame, 0)
        
        # 制御ボタン
        self.create_control_section(main_frame, 1)
        
        # タスク詳細表示
        self.create_task_detail_section(main_frame, 2)
        
        # ステータスバー
        self.status_bar = StatusBar(main_frame)
        self.status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def create_overall_progress_section(self, parent: ttk.Frame, row: int):
        """全体進捗セクション"""
        # セクションフレーム
        section_frame = ttk.LabelFrame(parent, text="全体進捗", padding="5")
        section_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        section_frame.columnconfigure(0, weight=1)
        
        # 進捗パネル
        self.progress_panel = ProgressPanel(section_frame, "処理状況")
        self.progress_panel.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 統計情報フレーム
        stats_frame = ttk.Frame(section_frame)
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        stats_frame.columnconfigure(1, weight=1)
        
        # 開始時刻
        ttk.Label(stats_frame, text="開始時刻:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.start_time_var = tk.StringVar(value="未開始")
        ttk.Label(stats_frame, textvariable=self.start_time_var).grid(row=0, column=1, sticky=tk.W)
        
        # 経過時間
        ttk.Label(stats_frame, text="経過時間:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.elapsed_time_var = tk.StringVar(value="00:00:00")
        ttk.Label(stats_frame, textvariable=self.elapsed_time_var).grid(row=0, column=3, sticky=tk.W)
        
        # 予想残り時間
        ttk.Label(stats_frame, text="予想残り時間:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.remaining_time_var = tk.StringVar(value="計算中...")
        ttk.Label(stats_frame, textvariable=self.remaining_time_var).grid(row=1, column=1, sticky=tk.W)
        
        # 平均処理時間
        ttk.Label(stats_frame, text="平均処理時間:").grid(row=1, column=2, sticky=tk.W, padx=(20, 5))
        self.avg_time_var = tk.StringVar(value="-")
        ttk.Label(stats_frame, textvariable=self.avg_time_var).grid(row=1, column=3, sticky=tk.W)
        
    def create_control_section(self, parent: ttk.Frame, row: int):
        """制御ボタンセクション"""
        # ボタンフレーム
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, pady=(0, 10))
        
        # 一時停止/再開ボタン
        self.pause_button = ttk.Button(button_frame, text="一時停止", 
                                     command=self.toggle_pause, width=12)
        self.pause_button.grid(row=0, column=0, padx=(0, 5))
        
        # キャンセルボタン
        self.cancel_button = ttk.Button(button_frame, text="キャンセル", 
                                      command=self.cancel_processing, width=12)
        self.cancel_button.grid(row=0, column=1, padx=(0, 5))
        
        # 詳細表示切り替え
        self.detail_button = ttk.Button(button_frame, text="詳細非表示", 
                                      command=self.toggle_detail_view, width=12)
        self.detail_button.grid(row=0, column=2, padx=(0, 5))
        
        # エクスポートボタン
        self.export_button = ttk.Button(button_frame, text="結果エクスポート", 
                                      command=self.export_results, width=15)
        self.export_button.grid(row=0, column=3)
        
    def create_task_detail_section(self, parent: ttk.Frame, row: int):
        """タスク詳細セクション"""
        # セクションフレーム
        section_frame = ttk.LabelFrame(parent, text="タスク詳細", padding="5")
        section_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        section_frame.columnconfigure(0, weight=1)
        section_frame.rowconfigure(0, weight=1)
        
        # ノートブック（タブ）
        self.notebook = ttk.Notebook(section_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タスクリストタブ
        self.create_task_list_tab()
        
        # ログタブ
        self.create_log_tab()
        
    def create_task_list_tab(self):
        """タスクリストタブ"""
        # タブフレーム
        task_tab = ttk.Frame(self.notebook)
        self.notebook.add(task_tab, text="タスクリスト")
        
        # ツリービュー用フレーム
        tree_frame = ttk.Frame(task_tab)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padding="5")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        task_tab.columnconfigure(0, weight=1)
        task_tab.rowconfigure(0, weight=1)
        
        # ツリービュー
        columns = ("row", "ai", "status", "duration", "preview")
        self.task_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # 列の設定
        self.task_tree.heading("row", text="行")
        self.task_tree.heading("ai", text="AI")
        self.task_tree.heading("status", text="ステータス")
        self.task_tree.heading("duration", text="処理時間")
        self.task_tree.heading("preview", text="テキストプレビュー")
        
        self.task_tree.column("row", width=60, anchor="center")
        self.task_tree.column("ai", width=100, anchor="center")
        self.task_tree.column("status", width=80, anchor="center")
        self.task_tree.column("duration", width=80, anchor="center")
        self.task_tree.column("preview", width=300, anchor="w")
        
        # スクロールバー
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.task_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.task_tree.xview)
        
        self.task_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 配置
        self.task_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # ダブルクリックでタスク詳細表示
        self.task_tree.bind("<Double-1>", self.show_task_detail)
        
        # ステータスごとの色分け設定
        self.task_tree.tag_configure("pending", background="lightgray")
        self.task_tree.tag_configure("processing", background="lightyellow")
        self.task_tree.tag_configure("completed", background="lightgreen")
        self.task_tree.tag_configure("error", background="lightcoral")
        self.task_tree.tag_configure("skipped", background="lightblue")
        
    def create_log_tab(self):
        """ログタブ"""
        # タブフレーム
        log_tab = ttk.Frame(self.notebook)
        self.notebook.add(log_tab, text="ログ")
        
        # ログパネル
        self.log_panel = LogPanel(log_tab, "処理ログ", height=20)
        self.log_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padding="5")
        
        log_tab.columnconfigure(0, weight=1)
        log_tab.rowconfigure(0, weight=1)
        
    def add_task(self, task_info: TaskInfo):
        """タスクを追加"""
        self.tasks[task_info.task_id] = task_info
        self.update_task_tree()
        
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          result_preview: str = None, error_message: str = None):
        """タスクステータスを更新"""
        if task_id not in self.tasks:
            return
            
        task = self.tasks[task_id]
        old_status = task.status
        task.status = status
        
        # 開始時刻記録
        if old_status == TaskStatus.PENDING and status == TaskStatus.PROCESSING:
            task.start_time = datetime.now()
            
        # 終了時刻記録
        elif status in [TaskStatus.COMPLETED, TaskStatus.ERROR, TaskStatus.SKIPPED]:
            task.end_time = datetime.now()
            
        # 結果・エラー情報設定
        if result_preview:
            task.result_preview = result_preview
        if error_message:
            task.error_message = error_message
            
        # ログ出力
        self.log_task_status_change(task, old_status, status)
        
        # UI更新
        self.update_task_tree()
        self.update_statistics()
        
    def log_task_status_change(self, task: TaskInfo, old_status: TaskStatus, new_status: TaskStatus):
        """タスクステータス変更をログ出力"""
        if new_status == TaskStatus.PROCESSING:
            self.log_panel.add_log("INFO", f"行{task.row_number} ({task.ai_service}): 処理開始")
        elif new_status == TaskStatus.COMPLETED:
            duration_str = task.display_duration
            self.log_panel.add_log("INFO", f"行{task.row_number} ({task.ai_service}): 処理完了 ({duration_str})")
        elif new_status == TaskStatus.ERROR:
            error_msg = task.error_message or "不明なエラー"
            self.log_panel.add_log("ERROR", f"行{task.row_number} ({task.ai_service}): エラー - {error_msg}")
        elif new_status == TaskStatus.SKIPPED:
            self.log_panel.add_log("WARNING", f"行{task.row_number} ({task.ai_service}): スキップ")
            
    def update_task_tree(self):
        """タスクツリーを更新"""
        # 既存項目をクリア
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
            
        # タスクを追加
        for task in self.tasks.values():
            status_text = task.status.value
            duration_text = task.display_duration
            
            # タグ（色分け用）
            tag = task.status.name.lower()
            
            # ツリーに挿入
            item = self.task_tree.insert("", "end", values=(
                task.row_number,
                task.ai_service,
                status_text,
                duration_text,
                task.text_preview
            ), tags=(tag,))
            
    def update_statistics(self):
        """統計情報を更新"""
        if not self.tasks:
            return
            
        # 各ステータスの数を計算
        status_counts = {status: 0 for status in TaskStatus}
        for task in self.tasks.values():
            status_counts[task.status] += 1
            
        total_tasks = len(self.tasks)
        completed = status_counts[TaskStatus.COMPLETED]
        errors = status_counts[TaskStatus.ERROR]
        remaining = total_tasks - completed - errors - status_counts[TaskStatus.SKIPPED]
        
        # 進捗パネル更新
        self.progress_panel.update_progress(completed, total_tasks)
        self.progress_panel.update_details(completed, remaining, errors)
        
        # 平均処理時間計算
        completed_tasks = [t for t in self.tasks.values() 
                          if t.status == TaskStatus.COMPLETED and t.duration is not None]
        if completed_tasks:
            avg_duration = sum(t.duration for t in completed_tasks) / len(completed_tasks)
            self.avg_time_var.set(f"{avg_duration:.1f}秒")
            
            # 予想残り時間計算
            if remaining > 0:
                estimated_remaining = remaining * avg_duration
                if estimated_remaining < 3600:  # 1時間未満
                    minutes = int(estimated_remaining // 60)
                    seconds = int(estimated_remaining % 60)
                    self.remaining_time_var.set(f"{minutes:02d}:{seconds:02d}")
                else:
                    hours = int(estimated_remaining // 3600)
                    minutes = int((estimated_remaining % 3600) // 60)
                    self.remaining_time_var.set(f"{hours}時間{minutes:02d}分")
            else:
                self.remaining_time_var.set("完了")
        else:
            self.avg_time_var.set("-")
            self.remaining_time_var.set("計算中...")
            
        # ステータスバー更新
        if self.is_running:
            self.status_bar.set_status(f"処理中... ({completed}/{total_tasks})")
        else:
            self.status_bar.set_status(f"停止中 ({completed}/{total_tasks})")
            
    def start_processing(self):
        """処理開始"""
        self.is_running = True
        self.start_time = datetime.now()
        self.start_time_var.set(self.start_time.strftime("%H:%M:%S"))
        
        # ボタン状態更新
        self.pause_button.config(text="一時停止", state="normal")
        self.cancel_button.config(state="normal")
        
        self.log_panel.add_log("INFO", "自動化処理を開始しました")
        
    def stop_processing(self):
        """処理停止"""
        self.is_running = False
        self.end_time = datetime.now()
        
        # ボタン状態更新
        self.pause_button.config(text="一時停止", state="disabled")
        self.cancel_button.config(state="disabled")
        
        self.log_panel.add_log("INFO", "自動化処理が完了しました")
        
    def toggle_pause(self):
        """一時停止/再開切り替え"""
        # 実装は呼び出し元で制御
        pass
        
    def cancel_processing(self):
        """処理キャンセル"""
        if self.on_cancel_callback:
            self.on_cancel_callback()
            
    def toggle_detail_view(self):
        """詳細表示切り替え"""
        current_text = self.detail_button.cget("text")
        if current_text == "詳細非表示":
            self.notebook.grid_remove()
            self.detail_button.config(text="詳細表示")
            self.window.geometry("900x400")
        else:
            self.notebook.grid()
            self.detail_button.config(text="詳細非表示")
            self.window.geometry("900x700")
            
    def export_results(self):
        """結果をエクスポート"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            title="結果をエクスポート",
            defaultextension=".csv",
            filetypes=[("CSVファイル", "*.csv"), ("全てのファイル", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # ヘッダー
                    writer.writerow(["行番号", "AIサービス", "ステータス", "処理時間", 
                                   "テキストプレビュー", "結果プレビュー", "エラーメッセージ"])
                    
                    # データ
                    for task in self.tasks.values():
                        writer.writerow([
                            task.row_number,
                            task.ai_service,
                            task.status.value,
                            task.display_duration,
                            task.text_preview,
                            task.result_preview or "",
                            task.error_message or ""
                        ])
                        
                self.log_panel.add_log("INFO", f"結果をエクスポートしました: {filename}")
                
            except Exception as e:
                self.log_panel.add_log("ERROR", f"エクスポートエラー: {e}")
                
    def show_task_detail(self, event):
        """タスク詳細を表示（ダブルクリック時）"""
        selection = self.task_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.task_tree.item(item, "values")
        row_number = int(values[0])
        
        # 該当タスクを検索
        task = None
        for t in self.tasks.values():
            if t.row_number == row_number:
                task = t
                break
                
        if task:
            self.show_task_detail_dialog(task)
            
    def show_task_detail_dialog(self, task: TaskInfo):
        """タスク詳細ダイアログを表示"""
        dialog = tk.Toplevel(self.window)
        dialog.title(f"タスク詳細 - 行{task.row_number}")
        dialog.geometry("500x400")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # コンテンツフレーム
        content_frame = ttk.Frame(dialog, padding="10")
        content_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        
        # 基本情報
        ttk.Label(content_frame, text="行番号:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(content_frame, text=str(task.row_number)).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(content_frame, text="AIサービス:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(content_frame, text=task.ai_service).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(content_frame, text="ステータス:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(content_frame, text=task.status.value).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(content_frame, text="処理時間:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(content_frame, text=task.display_duration).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # 入力テキスト
        ttk.Label(content_frame, text="入力テキスト:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=(10, 2))
        input_text = scrolledtext.ScrolledText(content_frame, height=5, width=50, wrap=tk.WORD, state="disabled")
        input_text.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=(10, 2))
        
        # エラーメッセージまたは結果
        if task.error_message:
            ttk.Label(content_frame, text="エラーメッセージ:").grid(row=5, column=0, sticky=(tk.W, tk.N), pady=(5, 2))
            error_text = scrolledtext.ScrolledText(content_frame, height=5, width=50, wrap=tk.WORD, state="disabled")
            error_text.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=(5, 2))
            
            error_text.config(state="normal")
            error_text.insert(tk.END, task.error_message)
            error_text.config(state="disabled")
            
        elif task.result_preview:
            ttk.Label(content_frame, text="結果:").grid(row=5, column=0, sticky=(tk.W, tk.N), pady=(5, 2))
            result_text = scrolledtext.ScrolledText(content_frame, height=5, width=50, wrap=tk.WORD, state="disabled")
            result_text.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=(5, 2))
            
            result_text.config(state="normal")
            result_text.insert(tk.END, task.result_preview)
            result_text.config(state="disabled")
            
        # 閉じるボタン
        ttk.Button(content_frame, text="閉じる", command=dialog.destroy).grid(row=6, column=1, pady=(10, 0), sticky=tk.E)
        
        content_frame.rowconfigure(4, weight=1)
        content_frame.rowconfigure(5, weight=1)
        
    def start_update_timer(self):
        """更新タイマー開始"""
        self.update_timer_active = True
        self.update_timer()
        
    def stop_update_timer(self):
        """更新タイマー停止"""
        self.update_timer_active = False
        
    def update_timer(self):
        """定期更新処理"""
        if not self.update_timer_active:
            return
            
        # 経過時間更新
        if self.start_time and self.is_running:
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(elapsed.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.elapsed_time_var.set(f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
            
        # 次回更新をスケジュール
        self.window.after(1000, self.update_timer)
        
    def on_window_close(self):
        """ウィンドウ閉じる時の処理"""
        if self.is_running:
            from tkinter import messagebox
            if messagebox.askokcancel("確認", "処理中です。ウィンドウを閉じますか？"):
                self.stop_update_timer()
                self.window.destroy()
        else:
            self.stop_update_timer()
            self.window.destroy()
            
    def set_cancel_callback(self, callback: Callable):
        """キャンセルコールバックを設定"""
        self.on_cancel_callback = callback


if __name__ == "__main__":
    # テスト実行
    root = tk.Tk()
    root.withdraw()
    
    # サンプルデータで進捗ウィンドウを表示
    progress_window = ProgressWindow(root, "テスト進捗")
    
    # サンプルタスクを追加
    for i in range(10):
        task = TaskInfo(
            task_id=f"task_{i}",
            row_number=i + 1,
            ai_service="ChatGPT",
            text_preview=f"これはテスト用のサンプルテキストです。行番号{i+1}のデータです。"
        )
        progress_window.add_task(task)
        
    # テスト用のステータス更新
    def update_test_status():
        import random
        for i, task_id in enumerate(list(progress_window.tasks.keys())[:3]):
            status = random.choice([TaskStatus.PROCESSING, TaskStatus.COMPLETED, TaskStatus.ERROR])
            progress_window.update_task_status(task_id, status)
            
    root.after(2000, update_test_status)
    progress_window.start_processing()
    
    root.mainloop()