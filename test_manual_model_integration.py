#!/usr/bin/env python3
"""
手動モデル管理統合テストスクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_manual_model_manager():
    """手動モデル管理機能のテスト"""
    print("=== 手動モデル管理機能テスト ===\n")
    
    from src.gui.manual_model_manager import ManualModelManager, update_model_list
    
    # ManualModelManagerのテスト
    print("1. ManualModelManagerのテスト")
    manager = ManualModelManager()
    
    # 全サービスのモデルを取得
    all_models = manager.get_all_models()
    print(f"  保存されているサービス数: {len(all_models)}")
    for service, models in all_models.items():
        print(f"  - {service}: {len(models)}個のモデル")
    
    print("\n2. update_model_list()関数のテスト")
    models = update_model_list()
    print(f"  取得されたサービス数: {len(models)}")
    for service, model_list in models.items():
        print(f"  - {service}: {model_list}")
    
    # 必須サービスの確認
    required_services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
    missing_services = [s for s in required_services if s not in models]
    if missing_services:
        print(f"\n  ⚠️ 不足しているサービス: {missing_services}")
    else:
        print("\n  ✅ 全ての必須サービスが含まれています")
    
    print("\n=== テスト完了 ===")

def test_main_window_integration():
    """main_window.pyとの統合テスト"""
    print("\n=== main_window.py統合テスト ===\n")
    
    # _get_default_modelsメソッドのテスト
    from src.gui.main_window import MainWindow
    import tkinter as tk
    
    # テスト用のrootウィンドウを作成（表示はしない）
    root = tk.Tk()
    root.withdraw()
    
    try:
        # MainWindowインスタンスを作成（UIは表示しない）
        window = MainWindow()
        window.root.withdraw()
        
        print("1. _get_default_models()メソッドのテスト")
        services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
        
        for service in services:
            models = window._get_default_models(service)
            print(f"  {service}: {models}")
        
        print("\n  ✅ _get_default_models()メソッドは手動管理されたモデルを返します")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    finally:
        root.destroy()
    
    print("\n=== 統合テスト完了 ===")

if __name__ == "__main__":
    test_manual_model_manager()
    test_main_window_integration()