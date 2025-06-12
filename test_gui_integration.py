#!/usr/bin/env python3
"""
手動モデル管理機能統合テスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.gui.main_window import MainWindow

def test_gui_integration():
    """GUIテスト - 手動モデル管理ボタンが正しく表示されるか確認"""
    print("🚀 GUI統合テスト開始...")
    print("📝 手動モデル管理ボタン（📝 手動管理）が表示されることを確認してください")
    print("✅ ボタンをクリックしてダイアログが開くことを確認してください")
    
    # GUIアプリケーション起動
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    test_gui_integration()