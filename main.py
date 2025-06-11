#!/usr/bin/env python3
"""
AI自動化ツール - メインエントリーポイント

このツールは、Googleスプレッドシートのデータを読み取り、
複数のAIサービス（ChatGPT、Claude、Gemini等）を自動操作して、
結果をスプレッドシートに書き戻す自動化システムです。

実行方法:
    python main.py

必要な環境:
    - Python 3.8以上
    - Google Sheets API認証情報
    - 各AIサービスへのアクセス権限
"""

import sys
import os
import logging
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ログディレクトリ作成
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

def setup_logging():
    """ログ設定の初期化"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("AI自動化ツールを開始します")
    return logger

def main():
    """メイン処理"""
    logger = setup_logging()
    
    try:
        # GUI起動（担当者A実装予定）
        from src.gui.main_window import MainWindow
        
        logger.info("GUIアプリケーションを起動します")
        app = MainWindow()
        app.run()
        
    except ImportError as e:
        logger.error(f"モジュールのインポートに失敗しました: {e}")
        logger.info("実装が完了していないモジュールがあります")
        print("開発中のため、一部機能が利用できません")
        
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    main()