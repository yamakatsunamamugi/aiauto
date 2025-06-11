#!/usr/bin/env python3
"""
AI自動化システム GUIアプリケーション起動スクリプト

使用方法:
1. ターミナルで以下のコマンドを実行:
   python3 gui_app.py

2. または、以下をコピーしてターミナルで実行:
   cd /Users/roudousha/Dropbox/5.AI-auto && python3 gui_app.py
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.gui.main_window import main
    
    if __name__ == "__main__":
        print("🚀 AI自動化システム GUI起動中...")
        print("📍 プロジェクトパス:", project_root)
        main()
        
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("📁 現在のディレクトリ:", os.getcwd())
    print("🔍 Pythonパス:", sys.path[:3])
    sys.exit(1)
except Exception as e:
    print(f"❌ 起動エラー: {e}")
    sys.exit(1)