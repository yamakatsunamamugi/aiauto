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
        # from src.gui.main_window import MainWindow
        
        # 統合機能を実装する場合のコールバック設定例
        # （他担当者のモジュールが完成後に有効化）
        def setup_integration(app):
            """他モジュールとの統合設定"""
            try:
                # Google Sheets連携（担当者B実装予定）
                # from src.sheets.sheets_client import SheetsClient
                # sheets_client = SheetsClient()
                # app.set_get_sheet_names_callback(sheets_client.get_sheet_names)
                
                # ブラウザ自動化連携
                from src.automation.automation_controller import AutomationController
                automation_controller = AutomationController()
                # app.set_start_automation_callback(automation_controller.start_automation)
                
                logger.info("統合機能の設定が完了しました")
            except ImportError as e:
                logger.warning(f"統合モジュールが未実装です: {e}")
                logger.info("一部機能は開発中のため利用できません")
        
        logger.info("ブラウザ自動化システムをテストします")
        
        # Automation機能のテスト実行
        import asyncio
        from src.automation.automation_controller import AutomationController
        from src.automation.browser_manager import BrowserManager
        
        async def test_automation():
            logger.info("AutomationController初期化テスト")
            controller = AutomationController()
            logger.info("✅ AutomationController初期化成功")
            
            logger.info("BrowserManager初期化テスト")
            browser_manager = BrowserManager()
            logger.info("✅ BrowserManager初期化成功")
            
            logger.info("利用可能なAIサービス一覧取得テスト")
            available_ais = controller.get_available_ais()
            logger.info(f"✅ 利用可能なAI: {list(available_ais.keys())}")
        
        logger.info("非同期テスト実行中...")
        asyncio.run(test_automation())
        logger.info("🎉 ブラウザ自動化システムのテスト完了")
        
    except ImportError as e:
        logger.error(f"モジュールのインポートに失敗しました: {e}")
        logger.info("実装が完了していないモジュールがあります")
        print("開発中のため、一部機能が利用できません")
        
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    main()