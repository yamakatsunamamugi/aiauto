#!/usr/bin/env python3
"""
GUI アプリケーション起動スクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.main_window import MainWindow

if __name__ == "__main__":
    print("🚀 AI自動化システムGUIを起動中...")
    app = MainWindow()
    app.run()