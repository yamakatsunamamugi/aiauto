#!/usr/bin/env python3
"""
デバッグヘルパー - エラー診断と解決支援
"""

import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DebugHelper:
    """デバッグ支援クラス"""
    
    @staticmethod
    def check_imports():
        """必要なモジュールのインポート確認"""
        modules = {
            'tkinter': 'GUI基本ライブラリ',
            'google.oauth2': 'Google認証',
            'googleapiclient': 'Google API',
            'psutil': 'プロセス管理（オプション）'
        }
        
        results = {}
        for module, description in modules.items():
            try:
                __import__(module)
                results[module] = f"✅ {description}"
                logger.info(f"{module}: OK")
            except ImportError as e:
                results[module] = f"❌ {description} - {e}"
                logger.error(f"{module}: FAILED - {e}")
        
        return results
    
    @staticmethod
    def check_file_structure():
        """プロジェクト構造の確認"""
        required_files = [
            'gui_automation_app_fixed.py',
            'src/sheets/sheets_client.py',
            'src/sheets/auth_manager.py',
            'src/automation/extension_bridge.py',
            'config/credentials.json',
            'chrome-extension/manifest.json'
        ]
        
        project_root = Path(__file__).parent
        results = {}
        
        for file_path in required_files:
            full_path = project_root / file_path
            if full_path.exists():
                results[file_path] = f"✅ 存在"
                logger.info(f"{file_path}: EXISTS")
            else:
                results[file_path] = f"❌ 不在"
                logger.error(f"{file_path}: MISSING")
        
        return results
    
    @staticmethod
    def diagnose_error(error_type, error_message):
        """エラー診断と解決提案"""
        solutions = {
            'ImportError': {
                'psutil': 'pip install psutil',
                'google': 'pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client',
                'tkinter': 'macOS: brew install python-tk, Ubuntu: sudo apt-get install python3-tk'
            },
            'HTTPError': {
                '404': 'スプレッドシートIDが正しいか確認、共有設定を確認',
                '403': '認証情報を確認、APIが有効か確認',
                '401': 'credentials.jsonを更新、再認証が必要'
            },
            'AttributeError': {
                'NoneType': '初期化されていないオブジェクト、Noneチェックを追加',
                'module': 'インポートパスを確認、__init__.pyの存在確認'
            }
        }
        
        if error_type in solutions:
            for key, solution in solutions[error_type].items():
                if key in error_message:
                    return solution
        
        return "一般的な解決策: ログを確認、スタックトレースを分析、最小再現コードを作成"
    
    @staticmethod
    def create_test_environment():
        """テスト環境のセットアップ"""
        logger.info("テスト環境セットアップ開始")
        
        # 必要なディレクトリ作成
        dirs = ['logs', 'temp', 'test_data']
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)
            logger.info(f"ディレクトリ作成: {dir_name}")
        
        # 環境変数設定
        import os
        os.environ['PYTHONPATH'] = str(Path(__file__).parent)
        logger.info(f"PYTHONPATH設定: {os.environ['PYTHONPATH']}")
        
        return True

def main():
    """デバッグヘルパー実行"""
    print("🔍 デバッグヘルパー起動")
    print("=" * 60)
    
    helper = DebugHelper()
    
    # インポート確認
    print("\n📦 モジュールインポート確認:")
    imports = helper.check_imports()
    for module, status in imports.items():
        print(f"  {module}: {status}")
    
    # ファイル構造確認
    print("\n📁 プロジェクト構造確認:")
    files = helper.check_file_structure()
    for file_path, status in files.items():
        print(f"  {file_path}: {status}")
    
    # テスト環境セットアップ
    print("\n🔧 テスト環境セットアップ:")
    if helper.create_test_environment():
        print("  ✅ 完了")
    
    # エラー診断例
    print("\n💡 エラー診断例:")
    test_errors = [
        ('ImportError', "No module named 'psutil'"),
        ('HTTPError', "404 Not Found"),
        ('AttributeError', "'NoneType' object has no attribute 'get'")
    ]
    
    for error_type, error_msg in test_errors:
        solution = helper.diagnose_error(error_type, error_msg)
        print(f"  {error_type}: {error_msg}")
        print(f"    → 解決策: {solution}")

if __name__ == "__main__":
    main()