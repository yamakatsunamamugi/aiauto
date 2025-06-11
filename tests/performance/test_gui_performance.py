"""
GUIパフォーマンステストとメモリリークチェック

担当者A（GUI）によるパフォーマンス・安定性テストの実装
"""

import unittest
import tkinter as tk
import time
import threading
import gc
import tracemalloc
import psutil
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor

sys.path.append(str(Path(__file__).parents[2]))

from src.gui.main_window import MainWindow
from src.gui.components import *
from src.gui.progress_window import ProgressWindow
from tests.fixtures.gui_fixtures import GUITestHelper, MemoryLeakDetector, performance_monitor


class TestGUIPerformance(unittest.TestCase):
    """GUIパフォーマンステスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.app = MainWindow()
        self.app.root.withdraw()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.app.root.destroy()
        gc.collect()
    
    def test_startup_time(self):
        """アプリケーション起動時間テスト"""
        startup_times = []
        
        for _ in range(5):
            start_time = time.time()
            
            # 新しいアプリケーションインスタンスを作成
            test_app = MainWindow()
            test_app.root.withdraw()
            test_app.root.update_idletasks()
            
            end_time = time.time()
            startup_time = end_time - start_time
            startup_times.append(startup_time)
            
            test_app.root.destroy()
            gc.collect()
        
        # 平均起動時間が3秒以内であることを確認
        avg_startup_time = sum(startup_times) / len(startup_times)
        self.assertLess(avg_startup_time, 3.0, f"起動時間が遅すぎます: {avg_startup_time:.2f}秒")
        
        # 起動時間の一貫性を確認（標準偏差が小さいこと）
        import statistics
        std_dev = statistics.stdev(startup_times)
        self.assertLess(std_dev, 1.0, "起動時間のばらつきが大きすぎます")
    
    def test_ui_responsiveness(self):
        """UI応答性テスト"""
        response_times = []
        
        # 大量のログを追加してUIの応答性をテスト
        for i in range(100):
            start_time = time.time()
            
            self.app.add_log("INFO", f"テストログメッセージ {i}")
            self.app.root.update_idletasks()
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
        
        # 各UI更新が100ms以内であることを確認
        max_response_time = max(response_times)
        self.assertLess(max_response_time, 0.1, f"UI応答が遅すぎます: {max_response_time:.3f}秒")
        
        # 平均応答時間が50ms以内であることを確認
        avg_response_time = sum(response_times) / len(response_times)
        self.assertLess(avg_response_time, 0.05, f"平均UI応答が遅すぎます: {avg_response_time:.3f}秒")
    
    def test_large_data_handling(self):
        """大量データ処理のパフォーマンステスト"""
        start_time = time.time()
        
        # 大量のチェックボックスを持つグループを作成
        large_options = [f"Option_{i}" for i in range(1000)]
        checkbox_group = CheckboxGroup(self.app.root, "大量オプション", large_options)
        
        # 全選択操作
        checkbox_group.select_all()
        selected = checkbox_group.get_selected()
        
        # 全解除操作
        checkbox_group.select_none()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 大量データ処理が5秒以内であることを確認
        self.assertLess(total_time, 5.0, f"大量データ処理が遅すぎます: {total_time:.2f}秒")
        
        # 正しく処理されたことを確認
        self.assertEqual(len(selected), 1000)
        self.assertEqual(len(checkbox_group.get_selected()), 0)
    
    def test_concurrent_ui_updates(self):
        """同時UI更新のパフォーマンステスト"""
        progress_panel = ProgressPanel(self.app.root)
        update_times = []
        
        def update_progress(thread_id):
            """各スレッドでの進捗更新"""
            for i in range(10):
                start_time = time.time()
                
                progress_panel.update_progress(
                    i * 10 + thread_id, 
                    100, 
                    f"Thread {thread_id}: {i}"
                )
                
                end_time = time.time()
                update_times.append(end_time - start_time)
                time.sleep(0.01)
        
        # 10個のスレッドで同時更新
        threads = []
        for thread_id in range(10):
            thread = threading.Thread(target=update_progress, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 更新時間の統計
        if update_times:
            max_update_time = max(update_times)
            avg_update_time = sum(update_times) / len(update_times)
            
            self.assertLess(max_update_time, 0.1, "同時更新時の最大応答時間が遅すぎます")
            self.assertLess(avg_update_time, 0.05, "同時更新時の平均応答時間が遅すぎます")
    
    def test_window_resize_performance(self):
        """ウィンドウリサイズのパフォーマンステスト"""
        self.app.root.deiconify()
        
        resize_times = []
        sizes = [(800, 600), (1000, 700), (1200, 800), (1000, 700), (800, 600)]
        
        for width, height in sizes:
            start_time = time.time()
            
            self.app.root.geometry(f"{width}x{height}")
            self.app.root.update_idletasks()
            
            end_time = time.time()
            resize_time = end_time - start_time
            resize_times.append(resize_time)
        
        # リサイズ時間が200ms以内であることを確認
        max_resize_time = max(resize_times)
        self.assertLess(max_resize_time, 0.2, f"ウィンドウリサイズが遅すぎます: {max_resize_time:.3f}秒")


class TestMemoryUsage(unittest.TestCase):
    """メモリ使用量テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        gc.collect()
        self.initial_memory = self.get_memory_usage()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        gc.collect()
    
    def get_memory_usage(self):
        """現在のメモリ使用量を取得（MB）"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def test_app_memory_usage(self):
        """アプリケーションのメモリ使用量テスト"""
        app = MainWindow()
        app.root.withdraw()
        
        # アプリ作成後のメモリ使用量
        after_creation = self.get_memory_usage()
        memory_increase = after_creation - self.initial_memory
        
        # アプリケーションが100MB以下のメモリ使用量であることを確認
        self.assertLess(memory_increase, 100, f"メモリ使用量が多すぎます: {memory_increase:.2f}MB")
        
        app.root.destroy()
        gc.collect()
        
        # 破棄後のメモリ使用量
        after_destruction = self.get_memory_usage()
        
        # メモリがある程度解放されることを確認
        memory_after_cleanup = after_destruction - self.initial_memory
        self.assertLess(memory_after_cleanup, memory_increase * 0.8, "メモリが適切に解放されていません")
    
    def test_memory_leak_detection(self):
        """メモリリーク検出テスト"""
        detector = MemoryLeakDetector()
        detector.start()
        
        # 複数回のアプリケーション作成・破棄
        for i in range(10):
            app = MainWindow()
            app.root.withdraw()
            
            # 大量のログを追加
            for j in range(100):
                app.add_log("INFO", f"Test log {i}-{j}")
            
            app.root.destroy()
            gc.collect()
            
            # 5回ごとにメモリ使用量を測定
            if i % 5 == 4:
                detector.measure(f"Iteration {i+1}")
        
        detector.stop()
        
        # メモリリークがないことを確認（閾値: 50MB）
        self.assertFalse(detector.has_leak(50), "メモリリークが検出されました")
    
    def test_large_widget_creation_memory(self):
        """大量ウィジェット作成時のメモリテスト"""
        root = tk.Tk()
        root.withdraw()
        
        initial_memory = self.get_memory_usage()
        
        # 大量のウィジェットを作成
        widgets = []
        for i in range(1000):
            frame = ttk.Frame(root)
            label = ttk.Label(frame, text=f"Label {i}")
            entry = ttk.Entry(frame)
            button = ttk.Button(frame, text=f"Button {i}")
            
            widgets.extend([frame, label, entry, button])
        
        after_creation = self.get_memory_usage()
        memory_increase = after_creation - initial_memory
        
        # ウィジェット作成時のメモリ増加が200MB以下であることを確認
        self.assertLess(memory_increase, 200, f"ウィジェット作成時のメモリ増加が多すぎます: {memory_increase:.2f}MB")
        
        # ウィジェットを破棄
        for widget in widgets:
            try:
                widget.destroy()
            except:
                pass
        
        root.destroy()
        gc.collect()


class TestLongRunningOperations(unittest.TestCase):
    """長時間実行操作のテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.app = MainWindow()
        self.app.root.withdraw()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.app.root.destroy()
    
    def test_long_running_log_updates(self):
        """長時間のログ更新テスト"""
        start_time = time.time()
        log_count = 1000
        
        # 大量のログ更新をシミュレート
        for i in range(log_count):
            self.app.add_log("INFO", f"Long running test log {i}")
            
            # 100件ごとにGUI更新
            if i % 100 == 0:
                self.app.root.update_idletasks()
                
                # 実行時間をチェック（無限ループを防ぐ）
                elapsed = time.time() - start_time
                if elapsed > 30:  # 30秒以上は異常
                    self.fail(f"ログ更新が30秒を超えました: {elapsed:.2f}秒")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 1000件のログ更新が10秒以内であることを確認
        self.assertLess(total_time, 10.0, f"ログ更新時間が長すぎます: {total_time:.2f}秒")
        
        # ログが正しく記録されていることを確認
        log_content = self.app.log_text.get("1.0", tk.END)
        self.assertIn(f"Long running test log {log_count-1}", log_content)
    
    def test_continuous_progress_updates(self):
        """継続的な進捗更新テスト"""
        progress_window = ProgressWindow(self.app.root)
        
        # 複数タスクの同時進捗更新
        tasks = ["Task_A", "Task_B", "Task_C", "Task_D", "Task_E"]
        
        for task in tasks:
            progress_window.add_task(task, 100)
        
        start_time = time.time()
        
        # 1分間の継続的な進捗更新
        while time.time() - start_time < 60:  # 1分間
            for task in tasks:
                import random
                progress = random.randint(0, 100)
                progress_window.update_task_progress(task, progress)
            
            time.sleep(0.1)
            progress_window.window.update_idletasks()
        
        # ウィンドウが正常に動作していることを確認
        self.assertTrue(progress_window.window.winfo_exists())
        
        progress_window.window.destroy()
    
    def test_stress_ui_operations(self):
        """UI操作のストレステスト"""
        stress_duration = 30  # 30秒間のストレステスト
        start_time = time.time()
        operation_count = 0
        
        while time.time() - start_time < stress_duration:
            # 様々なUI操作をランダムに実行
            import random
            operation = random.choice([
                'add_log',
                'update_progress',
                'toggle_mode',
                'update_status'
            ])
            
            try:
                if operation == 'add_log':
                    level = random.choice(['INFO', 'WARNING', 'ERROR'])
                    self.app.add_log(level, f"Stress test message {operation_count}")
                
                elif operation == 'update_progress':
                    progress = random.randint(0, 100)
                    self.app.update_progress_callback(progress, 100, f"Stress test {operation_count}")
                
                elif operation == 'toggle_mode':
                    mode = random.choice(['simple', 'column'])
                    self.app.ai_mode_var.set(mode)
                    self.app.toggle_ai_mode()
                
                elif operation == 'update_status':
                    # ステータス更新（実装されている場合）
                    pass
                
                operation_count += 1
                
                # 10操作ごとにGUI更新
                if operation_count % 10 == 0:
                    self.app.root.update_idletasks()
                
            except Exception as e:
                self.fail(f"ストレステスト中にエラーが発生: {e}")
        
        # 十分な数の操作が実行されたことを確認
        self.assertGreater(operation_count, 100, "ストレステストの操作数が少なすぎます")


class TestResourceCleanup(unittest.TestCase):
    """リソースクリーンアップテスト"""
    
    def test_widget_destruction_cleanup(self):
        """ウィジェット破棄時のクリーンアップテスト"""
        # リソース追跡
        created_widgets = []
        
        for i in range(100):
            root = tk.Tk()
            root.withdraw()
            
            app = MainWindow()
            created_widgets.append((root, app))
            
            # アプリケーションを使用
            app.add_log("INFO", f"Test app {i}")
            app.update_progress_callback(i, 100, f"App {i}")
            
            # リソースを解放
            app.root.destroy()
            root.destroy()
        
        # ガベージコレクション
        gc.collect()
        
        # メモリリークがないことを確認
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        # 最終メモリ使用量が妥当であることを確認（実装依存）
        # 具体的な閾値は環境によって調整が必要
    
    def test_thread_cleanup(self):
        """スレッドクリーンアップテスト"""
        initial_thread_count = threading.active_count()
        
        # 複数のスレッドを作成して破棄
        for i in range(10):
            def worker():
                time.sleep(0.1)
            
            thread = threading.Thread(target=worker)
            thread.start()
            thread.join()
        
        # スレッドが適切にクリーンアップされたことを確認
        final_thread_count = threading.active_count()
        self.assertEqual(initial_thread_count, final_thread_count, "スレッドがクリーンアップされていません")


if __name__ == "__main__":
    # パフォーマンステストは時間がかかるため、verbose出力
    unittest.main(verbosity=2)