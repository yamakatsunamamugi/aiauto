"""
Google Sheets連携パッケージ

Google Sheets APIを使用したスプレッドシートの読み書き、
データ処理、タスク管理機能を提供する。

主要コンポーネント:
- AuthManager: Google API認証管理
- SheetsClient: スプレッドシート操作API
- DataHandler: データ処理とタスク管理
- Models: データ構造定義

使用例:
    from src.sheets import create_sheets_client, create_data_handler, SheetConfig
    
    # クライアント作成
    client = create_sheets_client()
    handler = create_data_handler(client)
    
    # 設定作成
    config = SheetConfig(
        spreadsheet_url="https://docs.google.com/spreadsheets/d/...",
        sheet_name="Sheet1"
    )
    
    # 未処理タスクを取得
    tasks = handler.get_pending_tasks(config)
"""

from .auth_manager import (
    AuthManager,
    AuthenticationError,
    create_auth_manager,
    validate_credentials_file
)

from .sheets_client import (
    SheetsClient,
    SheetsAPIError,
    create_sheets_client
)

from .data_handler import (
    DataHandler,
    DataProcessingError,
    create_data_handler,
    extract_spreadsheet_id_from_url
)

from .models import (
    # データ構造
    TaskRow,
    ColumnPosition,
    SheetConfig,
    ProcessingResult,
    ValidationError,
    SpreadsheetData,
    
    # 列挙型
    TaskStatus,
    AIService
)

# バージョン情報
__version__ = "1.0.0"
__author__ = "AI Automation Team"

# パッケージレベルのエクスポート
__all__ = [
    # クラス
    "AuthManager",
    "SheetsClient", 
    "DataHandler",
    "TaskRow",
    "ColumnPosition",
    "SheetConfig",
    "ProcessingResult",
    "ValidationError",
    "SpreadsheetData",
    
    # 列挙型
    "TaskStatus",
    "AIService",
    
    # 例外
    "AuthenticationError",
    "SheetsAPIError",
    "DataProcessingError",
    
    # ファクトリー関数
    "create_auth_manager",
    "create_sheets_client",
    "create_data_handler",
    
    # ユーティリティ関数
    "validate_credentials_file",
    "extract_spreadsheet_id_from_url"
]


def get_version() -> str:
    """パッケージバージョンを取得"""
    return __version__


def create_complete_handler(credentials_path: str = None):
    """
    完全なハンドラーセットを作成する便利関数
    
    Args:
        credentials_path: 認証情報ファイルのパス
    
    Returns:
        tuple: (sheets_client, data_handler)
    
    Raises:
        AuthenticationError: 認証に失敗した場合
    """
    try:
        # SheetsClientを作成
        sheets_client = create_sheets_client(credentials_path)
        
        # DataHandlerを作成
        data_handler = create_data_handler(sheets_client)
        
        return sheets_client, data_handler
        
    except Exception as e:
        raise AuthenticationError(f"ハンドラーセットの作成に失敗しました: {e}")


def validate_environment() -> tuple[bool, list[str]]:
    """
    環境設定の検証
    
    Returns:
        tuple: (検証成功フラグ, エラーメッセージリスト)
    """
    errors = []
    
    try:
        # 必要なパッケージの確認
        import google.auth
        import google.oauth2.service_account
        import googleapiclient.discovery
    except ImportError as e:
        errors.append(f"必要なGoogle APIパッケージがインストールされていません: {e}")
    
    # 認証情報ファイルの確認
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    credentials_path = project_root / "config" / "credentials.json"
    
    if not credentials_path.exists():
        errors.append(f"認証情報ファイルが見つかりません: {credentials_path}")
    elif not validate_credentials_file(str(credentials_path)):
        errors.append("認証情報ファイルの形式が無効です")
    
    return len(errors) == 0, errors


# パッケージロード時の初期化
def _initialize_package():
    """パッケージの初期化処理"""
    import logging
    
    # ログ設定
    logger = logging.getLogger(__name__)
    logger.info(f"Sheets パッケージ v{__version__} が読み込まれました")
    
    # 環境検証
    is_valid, errors = validate_environment()
    if not is_valid:
        logger.warning("環境検証でエラーが検出されました:")
        for error in errors:
            logger.warning(f"  - {error}")


# パッケージ初期化実行
_initialize_package()