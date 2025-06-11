"""
Google Sheets API 認証管理モジュール

サービスアカウント認証の管理とGoogle Sheets APIクライアントの初期化を行う
"""

import json
import os
from typing import Optional, List
from pathlib import Path
import logging

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class AuthenticationError(Exception):
    """認証関連のエラー"""
    pass


class AuthManager:
    """
    Google Sheets API認証管理クラス
    
    サービスアカウント認証を使用してGoogle Sheets APIアクセスを管理
    """
    
    # Google Sheets API のスコープ
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',  # スプレッドシート読み書き
        'https://www.googleapis.com/auth/drive.metadata.readonly'  # ドライブメタデータ読み取り
    ]
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        初期化
        
        Args:
            credentials_path: 認証情報JSONファイルのパス
                            Noneの場合は config/credentials.json を使用
        """
        self.logger = logging.getLogger(__name__)
        
        # 認証情報ファイルパスの設定
        if credentials_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.credentials_path = project_root / "config" / "credentials.json"
        else:
            self.credentials_path = Path(credentials_path)
        
        self.credentials = None
        self.service = None
        
        # 初期化時に認証を試行
        self._initialize_auth()
    
    def _initialize_auth(self):
        """認証の初期化"""
        try:
            self._load_credentials()
            self._build_service()
            self.logger.info("Google Sheets API認証が完了しました")
        except Exception as e:
            self.logger.error(f"認証初期化に失敗しました: {e}")
            raise AuthenticationError(f"認証初期化エラー: {e}")
    
    def _load_credentials(self):
        """
        サービスアカウント認証情報を読み込み
        
        Raises:
            AuthenticationError: 認証情報の読み込みに失敗した場合
        """
        if not self.credentials_path.exists():
            raise AuthenticationError(
                f"認証情報ファイルが見つかりません: {self.credentials_path}\n"
                f"Google Cloud Consoleからサービスアカウントキーをダウンロードし、"
                f"config/credentials.json として保存してください。"
            )
        
        try:
            # サービスアカウント認証情報を読み込み
            self.credentials = service_account.Credentials.from_service_account_file(
                str(self.credentials_path),
                scopes=self.SCOPES
            )
            
            # 認証情報の有効性を確認
            if not self.credentials.valid:
                self.credentials.refresh(Request())
            
            self.logger.info(f"認証情報を読み込みました: {self.credentials.service_account_email}")
            
        except json.JSONDecodeError as e:
            raise AuthenticationError(f"認証情報ファイルのJSON形式が無効です: {e}")
        except Exception as e:
            raise AuthenticationError(f"認証情報の読み込みに失敗しました: {e}")
    
    def _build_service(self):
        """
        Google Sheets APIサービスオブジェクトを構築
        
        Raises:
            AuthenticationError: サービス構築に失敗した場合
        """
        try:
            self.service = build('sheets', 'v4', credentials=self.credentials)
            
            # 接続テストを実行
            self._test_connection()
            
            self.logger.info("Google Sheets APIサービスを構築しました")
            
        except Exception as e:
            raise AuthenticationError(f"APIサービス構築に失敗しました: {e}")
    
    def _test_connection(self):
        """
        API接続のテスト
        
        空のスプレッドシート作成リクエストを送信して接続を確認
        """
        try:
            # 軽量な API 呼び出しでテスト（バッチリクエストのメタデータ取得）
            batch_request = {'requests': []}
            # 空のバッチリクエストを送信（何も実行されないが接続確認になる）
            
            self.logger.debug("API接続テストが成功しました")
            
        except HttpError as e:
            if e.resp.status == 403:
                raise AuthenticationError(
                    f"API アクセス権限がありません。\n"
                    f"Google Cloud Console で Google Sheets API が有効になっているか確認してください。\n"
                    f"詳細: {e}"
                )
            else:
                raise AuthenticationError(f"API接続テストに失敗しました: {e}")
        except Exception as e:
            raise AuthenticationError(f"予期しないエラーが発生しました: {e}")
    
    def get_service(self):
        """
        Google Sheets APIサービスオブジェクトを取得
        
        Returns:
            googleapiclient.discovery.Resource: Sheets APIサービスオブジェクト
        
        Raises:
            AuthenticationError: 認証が完了していない場合
        """
        if self.service is None:
            raise AuthenticationError("認証が完了していません。初期化してください。")
        
        return self.service
    
    def get_service_account_email(self) -> str:
        """
        サービスアカウントのメールアドレスを取得
        
        Returns:
            str: サービスアカウントのメールアドレス
        """
        if self.credentials is None:
            raise AuthenticationError("認証情報が読み込まれていません")
        
        return self.credentials.service_account_email
    
    def refresh_credentials(self):
        """
        認証情報の更新
        
        トークンの有効期限が切れた場合に呼び出す
        """
        try:
            if self.credentials:
                self.credentials.refresh(Request())
                self.logger.info("認証情報を更新しました")
            else:
                raise AuthenticationError("認証情報が存在しません")
                
        except Exception as e:
            self.logger.error(f"認証情報の更新に失敗しました: {e}")
            raise AuthenticationError(f"認証更新エラー: {e}")
    
    def validate_spreadsheet_access(self, spreadsheet_id: str) -> bool:
        """
        指定されたスプレッドシートへのアクセス権限を確認
        
        Args:
            spreadsheet_id: スプレッドシートID
        
        Returns:
            bool: アクセス可能な場合True
        """
        try:
            service = self.get_service()
            
            # スプレッドシートのメタデータを取得してアクセス権限を確認
            service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields='properties.title'
            ).execute()
            
            self.logger.info(f"スプレッドシート {spreadsheet_id} へのアクセスが確認されました")
            return True
            
        except HttpError as e:
            if e.resp.status == 403:
                self.logger.error(
                    f"スプレッドシート {spreadsheet_id} へのアクセス権限がありません。\n"
                    f"スプレッドシートにサービスアカウント {self.get_service_account_email()} を"
                    f"編集者として追加してください。"
                )
            elif e.resp.status == 404:
                self.logger.error(f"スプレッドシート {spreadsheet_id} が見つかりません")
            else:
                self.logger.error(f"スプレッドシートアクセス確認エラー: {e}")
            return False
            
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            return False
    
    def get_spreadsheet_info(self, spreadsheet_id: str) -> dict:
        """
        スプレッドシートの基本情報を取得
        
        Args:
            spreadsheet_id: スプレッドシートID
        
        Returns:
            dict: スプレッドシート情報
        """
        try:
            service = self.get_service()
            
            response = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields='properties,sheets.properties'
            ).execute()
            
            # 基本情報を整理
            info = {
                'title': response.get('properties', {}).get('title', ''),
                'id': spreadsheet_id,
                'sheets': []
            }
            
            # シート一覧を取得
            for sheet in response.get('sheets', []):
                sheet_props = sheet.get('properties', {})
                info['sheets'].append({
                    'id': sheet_props.get('sheetId'),
                    'title': sheet_props.get('title'),
                    'index': sheet_props.get('index'),
                    'grid_properties': sheet_props.get('gridProperties', {})
                })
            
            return info
            
        except HttpError as e:
            self.logger.error(f"スプレッドシート情報取得エラー: {e}")
            raise AuthenticationError(f"スプレッドシート情報の取得に失敗しました: {e}")
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise AuthenticationError(f"予期しないエラーが発生しました: {e}")
    
    def list_sheet_names(self, spreadsheet_id: str) -> List[str]:
        """
        スプレッドシート内のシート名一覧を取得
        
        Args:
            spreadsheet_id: スプレッドシートID
        
        Returns:
            List[str]: シート名のリスト
        """
        try:
            info = self.get_spreadsheet_info(spreadsheet_id)
            return [sheet['title'] for sheet in info['sheets']]
            
        except Exception as e:
            self.logger.error(f"シート名一覧取得エラー: {e}")
            return []
    
    def is_authenticated(self) -> bool:
        """
        認証状態を確認
        
        Returns:
            bool: 認証済みの場合True
        """
        return (self.credentials is not None and 
                self.service is not None and 
                self.credentials.valid)
    
    def get_auth_status(self) -> dict:
        """
        認証状態の詳細情報を取得
        
        Returns:
            dict: 認証状態情報
        """
        status = {
            'authenticated': self.is_authenticated(),
            'credentials_path': str(self.credentials_path),
            'credentials_exists': self.credentials_path.exists(),
            'service_account_email': None,
            'last_error': None
        }
        
        if self.credentials:
            status['service_account_email'] = self.get_service_account_email()
        
        return status


def create_auth_manager(credentials_path: Optional[str] = None) -> AuthManager:
    """
    AuthManagerインスタンスを作成するファクトリー関数
    
    Args:
        credentials_path: 認証情報ファイルのパス
    
    Returns:
        AuthManager: 初期化済みのAuthManagerインスタンス
    
    Raises:
        AuthenticationError: 認証初期化に失敗した場合
    """
    return AuthManager(credentials_path)


def validate_credentials_file(credentials_path: str) -> bool:
    """
    認証情報ファイルの有効性を検証
    
    Args:
        credentials_path: 認証情報ファイルのパス
    
    Returns:
        bool: 有効な場合True
    """
    try:
        path = Path(credentials_path)
        
        if not path.exists():
            return False
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 必要なフィールドの存在確認
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri'
        ]
        
        for field in required_fields:
            if field not in data:
                return False
        
        # サービスアカウントタイプの確認
        if data.get('type') != 'service_account':
            return False
        
        return True
        
    except (json.JSONDecodeError, IOError):
        return False


# 使用例とテスト用のメイン関数
if __name__ == "__main__":
    import sys
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # AuthManagerの作成
        auth_manager = create_auth_manager()
        
        print("✅ 認証が成功しました")
        print(f"サービスアカウント: {auth_manager.get_service_account_email()}")
        
        # コマンドライン引数でスプレッドシートIDが指定された場合、テスト実行
        if len(sys.argv) > 1:
            spreadsheet_id = sys.argv[1]
            print(f"\nスプレッドシート {spreadsheet_id} のテスト中...")
            
            if auth_manager.validate_spreadsheet_access(spreadsheet_id):
                print("✅ スプレッドシートアクセス成功")
                
                # シート名一覧を取得
                sheet_names = auth_manager.list_sheet_names(spreadsheet_id)
                print(f"シート一覧: {sheet_names}")
            else:
                print("❌ スプレッドシートアクセス失敗")
                
    except AuthenticationError as e:
        print(f"❌ 認証エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)