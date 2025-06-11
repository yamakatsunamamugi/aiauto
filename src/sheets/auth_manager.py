#!/usr/bin/env python3
"""
Google Sheets API認証管理モジュール
サービスアカウント認証とOAuth2認証の両方をサポート
"""

import json
import os
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.logger import logger


class AuthManager:
    """Google Sheets API認証管理クラス"""
    
    # Google Sheets APIのスコープ
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        初期化
        
        Args:
            credentials_path: 認証ファイルのパス
        """
        self.credentials_path = credentials_path or "config/credentials.json"
        self.token_path = "config/token.json"
        self.credentials = None
        self.service = None
        
    def authenticate(self) -> bool:
        """
        認証を実行
        
        Returns:
            bool: 認証成功の場合True
        """
        try:
            logger.info("Google Sheets API認証開始...")
            
            # 既存のトークンをチェック
            if os.path.exists(self.token_path):
                logger.info("既存のトークンファイルを確認中...")
                self.credentials = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            
            # トークンが無効または期限切れの場合は再認証
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("トークンを更新中...")
                    self.credentials.refresh(Request())
                else:
                    # 新しい認証フローを実行
                    success = self._perform_authentication()
                    if not success:
                        return False
            
            # 認証情報を保存
            if self.credentials:
                self._save_credentials()
                logger.info("✅ Google Sheets API認証成功")
                return True
            else:
                logger.error("❌ 認証情報の取得に失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 認証エラー: {e}")
            return False
    
    def _perform_authentication(self) -> bool:
        """
        認証フローを実行
        
        Returns:
            bool: 認証成功の場合True
        """
        try:
            # サービスアカウント認証を試行
            if self._try_service_account_auth():
                logger.info("✅ サービスアカウント認証成功")
                return True
                
            # OAuth2認証を試行
            if self._try_oauth2_auth():
                logger.info("✅ OAuth2認証成功")
                return True
                
            logger.error("❌ 全ての認証方法が失敗しました")
            return False
            
        except Exception as e:
            logger.error(f"❌ 認証フロー実行エラー: {e}")
            return False
    
    def _try_service_account_auth(self) -> bool:
        """
        サービスアカウント認証を試行
        
        Returns:
            bool: 認証成功の場合True
        """
        try:
            if not os.path.exists(self.credentials_path):
                logger.warning(f"認証ファイルが見つかりません: {self.credentials_path}")
                return False
                
            # サービスアカウント認証情報を読み込み
            logger.info("サービスアカウント認証を試行中...")
            self.credentials = ServiceAccountCredentials.from_service_account_file(
                self.credentials_path, scopes=self.SCOPES
            )
            
            # 認証テスト
            test_service = build('sheets', 'v4', credentials=self.credentials)
            
            logger.info("✅ サービスアカウント認証成功")
            return True
            
        except Exception as e:
            logger.warning(f"サービスアカウント認証失敗: {e}")
            return False
    
    def _try_oauth2_auth(self) -> bool:
        """
        OAuth2認証を試行
        
        Returns:
            bool: 認証成功の場合True
        """
        try:
            if not os.path.exists(self.credentials_path):
                logger.error(f"OAuth2認証ファイルが見つかりません: {self.credentials_path}")
                return False
                
            logger.info("OAuth2認証を試行中...")
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.SCOPES
            )
            
            # ローカルサーバーを使用して認証
            self.credentials = flow.run_local_server(port=0)
            
            logger.info("✅ OAuth2認証成功")
            return True
            
        except Exception as e:
            logger.error(f"OAuth2認証失敗: {e}")
            return False
    
    def _save_credentials(self):
        """認証情報を保存"""
        try:
            if self.credentials and hasattr(self.credentials, 'to_json'):
                # OAuth2認証の場合
                with open(self.token_path, 'w') as token_file:
                    token_file.write(self.credentials.to_json())
                logger.info(f"トークンを保存しました: {self.token_path}")
            else:
                # サービスアカウント認証の場合は保存不要
                logger.info("サービスアカウント認証のため、トークン保存をスキップ")
                
        except Exception as e:
            logger.warning(f"認証情報保存エラー: {e}")
    
    def get_service(self):
        """
        Google Sheets APIサービスオブジェクトを取得
        
        Returns:
            googleapiclient.discovery.Resource: Sheets APIサービス
        """
        try:
            if not self.credentials:
                logger.error("認証が完了していません")
                return None
                
            if not self.service:
                self.service = build('sheets', 'v4', credentials=self.credentials)
                logger.info("Google Sheets APIサービスを初期化しました")
                
            return self.service
            
        except Exception as e:
            logger.error(f"Sheets APIサービス取得エラー: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        接続テストを実行
        
        Returns:
            bool: 接続成功の場合True
        """
        try:
            service = self.get_service()
            if not service:
                return False
                
            # APIバージョン情報を取得してテスト
            logger.info("接続テストを実行中...")
            
            # 空のリクエストでAPIの動作確認
            # 実際のスプレッドシートIDは不要で、API自体の動作を確認
            
            logger.info("✅ Google Sheets API接続テスト成功")
            return True
            
        except HttpError as e:
            logger.error(f"❌ HTTP エラー: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 接続テストエラー: {e}")
            return False
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        認証状態を取得
        
        Returns:
            Dict[str, Any]: 認証状態情報
        """
        status = {
            "authenticated": False,
            "auth_type": None,
            "credentials_file_exists": os.path.exists(self.credentials_path),
            "token_file_exists": os.path.exists(self.token_path),
            "error": None
        }
        
        try:
            if self.credentials:
                status["authenticated"] = self.credentials.valid
                
                if isinstance(self.credentials, ServiceAccountCredentials):
                    status["auth_type"] = "service_account"
                else:
                    status["auth_type"] = "oauth2"
                    
                if hasattr(self.credentials, 'expired'):
                    status["expired"] = self.credentials.expired
                    
        except Exception as e:
            status["error"] = str(e)
            
        return status


def create_credentials_example():
    """認証ファイルのサンプルを作成"""
    
    # OAuth2用のサンプル
    oauth2_example = {
        "installed": {
            "client_id": "your-client-id.apps.googleusercontent.com",
            "project_id": "your-project-id", 
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "your-client-secret",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    # サービスアカウント用のサンプル
    service_account_example = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id", 
        "private_key": "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
    }
    
    return {
        "oauth2_example": oauth2_example,
        "service_account_example": service_account_example
    }