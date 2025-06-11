"""
セッション管理モジュール

ブラウザセッション・認証状態の管理と永続化
手動ログイン状態の維持とセッション復旧機能を提供
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from playwright.async_api import BrowserContext, Page

from src.utils.logger import logger
from src.utils.config_manager import config_manager


class SessionManager:
    """セッション・認証管理クラス"""
    
    def __init__(self, base_session_dir: Optional[str] = None):
        """
        セッション管理の初期化
        
        Args:
            base_session_dir: セッションデータの基本ディレクトリ
        """
        self.base_session_dir = Path(base_session_dir or "sessions")
        self.base_session_dir.mkdir(parents=True, exist_ok=True)
        
        # セッション情報を保存するファイル
        self.session_info_file = self.base_session_dir / "session_info.json"
        
        # 各サービスのセッション情報
        self.session_info: Dict[str, Dict[str, Any]] = {}
        
        # セッション有効期限（デフォルト7日）
        self.session_validity_days = config_manager.get('automation.session_validity_days', 7)
        
        self._load_session_info()
        logger.info(f"SessionManagerを初期化しました (ディレクトリ: {self.base_session_dir})")

    def _load_session_info(self):
        """セッション情報をファイルから読み込み"""
        try:
            if self.session_info_file.exists():
                with open(self.session_info_file, 'r', encoding='utf-8') as f:
                    self.session_info = json.load(f)
                logger.info("既存のセッション情報を読み込みました")
            else:
                self.session_info = {}
                logger.info("新規セッション情報を作成します")
        except Exception as e:
            logger.error(f"セッション情報の読み込みに失敗: {e}")
            self.session_info = {}

    def _save_session_info(self):
        """セッション情報をファイルに保存"""
        try:
            with open(self.session_info_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_info, f, ensure_ascii=False, indent=2, default=str)
            logger.debug("セッション情報を保存しました")
        except Exception as e:
            logger.error(f"セッション情報の保存に失敗: {e}")

    def get_session_dir(self, service_name: str) -> Path:
        """
        サービス別のセッションディレクトリを取得
        
        Args:
            service_name: サービス名
            
        Returns:
            Path: セッションディレクトリパス
        """
        session_dir = self.base_session_dir / service_name.lower()
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    async def save_session(self, service_name: str, context: BrowserContext) -> bool:
        """
        ブラウザコンテキストのセッションを保存
        
        Args:
            service_name: サービス名
            context: ブラウザコンテキスト
            
        Returns:
            bool: 保存成功の可否
        """
        try:
            logger.info(f"{service_name}: セッション保存開始")
            
            session_dir = self.get_session_dir(service_name)
            
            # Cookieを保存
            cookies = await context.cookies()
            cookies_file = session_dir / "cookies.json"
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            # LocalStorageを保存（可能な場合）
            try:
                pages = context.pages
                if pages:
                    page = pages[0]
                    local_storage = await page.evaluate("() => JSON.stringify(localStorage)")
                    
                    storage_file = session_dir / "local_storage.json"
                    with open(storage_file, 'w', encoding='utf-8') as f:
                        f.write(local_storage)
                    
                    # SessionStorageを保存
                    session_storage = await page.evaluate("() => JSON.stringify(sessionStorage)")
                    session_storage_file = session_dir / "session_storage.json"
                    with open(session_storage_file, 'w', encoding='utf-8') as f:
                        f.write(session_storage)
                        
            except Exception as storage_error:
                logger.warning(f"{service_name}: ストレージ保存でエラー: {storage_error}")
            
            # セッション情報を更新
            self.session_info[service_name] = {
                "last_saved": datetime.now().isoformat(),
                "cookies_count": len(cookies),
                "session_dir": str(session_dir)
            }
            
            self._save_session_info()
            logger.info(f"{service_name}: セッション保存完了 (クッキー数: {len(cookies)})")
            return True
            
        except Exception as e:
            logger.error(f"{service_name}: セッション保存でエラー: {e}")
            return False

    async def restore_session(self, service_name: str, context: BrowserContext) -> bool:
        """
        保存されたセッションを復元
        
        Args:
            service_name: サービス名
            context: ブラウザコンテキスト
            
        Returns:
            bool: 復元成功の可否
        """
        try:
            logger.info(f"{service_name}: セッション復元開始")
            
            session_dir = self.get_session_dir(service_name)
            
            # セッション有効性チェック
            if not self._is_session_valid(service_name):
                logger.warning(f"{service_name}: セッションが無効または期限切れです")
                return False
            
            # Cookieを復元
            cookies_file = session_dir / "cookies.json"
            if cookies_file.exists():
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                
                if cookies:
                    await context.add_cookies(cookies)
                    logger.info(f"{service_name}: クッキー復元完了 (数: {len(cookies)})")
            
            # LocalStorage/SessionStorageの復元は、ページアクセス時に実行
            logger.info(f"{service_name}: セッション復元完了")
            return True
            
        except Exception as e:
            logger.error(f"{service_name}: セッション復元でエラー: {e}")
            return False

    async def restore_page_storage(self, service_name: str, page: Page) -> bool:
        """
        ページのLocalStorage/SessionStorageを復元
        
        Args:
            service_name: サービス名
            page: Playwrightページ
            
        Returns:
            bool: 復元成功の可否
        """
        try:
            session_dir = self.get_session_dir(service_name)
            
            # LocalStorage復元
            local_storage_file = session_dir / "local_storage.json"
            if local_storage_file.exists():
                with open(local_storage_file, 'r', encoding='utf-8') as f:
                    local_storage_data = f.read()
                
                if local_storage_data and local_storage_data.strip():
                    await page.evaluate(f"""
                        () => {{
                            const data = {local_storage_data};
                            for (const [key, value] of Object.entries(data)) {{
                                localStorage.setItem(key, value);
                            }}
                        }}
                    """)
                    logger.debug(f"{service_name}: LocalStorage復元完了")
            
            # SessionStorage復元
            session_storage_file = session_dir / "session_storage.json"
            if session_storage_file.exists():
                with open(session_storage_file, 'r', encoding='utf-8') as f:
                    session_storage_data = f.read()
                
                if session_storage_data and session_storage_data.strip():
                    await page.evaluate(f"""
                        () => {{
                            const data = {session_storage_data};
                            for (const [key, value] of Object.entries(data)) {{
                                sessionStorage.setItem(key, value);
                            }}
                        }}
                    """)
                    logger.debug(f"{service_name}: SessionStorage復元完了")
            
            return True
            
        except Exception as e:
            logger.error(f"{service_name}: ページストレージ復元でエラー: {e}")
            return False

    def _is_session_valid(self, service_name: str) -> bool:
        """
        セッションの有効性をチェック
        
        Args:
            service_name: サービス名
            
        Returns:
            bool: セッションが有効かどうか
        """
        if service_name not in self.session_info:
            return False
        
        session_data = self.session_info[service_name]
        last_saved_str = session_data.get('last_saved')
        
        if not last_saved_str:
            return False
        
        try:
            last_saved = datetime.fromisoformat(last_saved_str)
            expiry_date = last_saved + timedelta(days=self.session_validity_days)
            
            is_valid = datetime.now() < expiry_date
            
            if not is_valid:
                logger.info(f"{service_name}: セッションが期限切れです "
                           f"(保存日時: {last_saved}, 期限: {expiry_date})")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"{service_name}: セッション有効性チェックでエラー: {e}")
            return False

    async def check_login_status(self, service_name: str, page: Page) -> bool:
        """
        サービスのログイン状態を確認
        
        Args:
            service_name: サービス名
            page: Playwrightページ
            
        Returns:
            bool: ログイン状態
        """
        try:
            # サービス固有のログイン確認ロジックは、
            # 各AIHandlerで実装されているlogin_check()メソッドを使用
            logger.info(f"{service_name}: ログイン状態確認")
            
            # ここでは基本的なチェックのみ実装
            # 実際のログイン確認は各AIHandlerで行う
            current_url = page.url
            
            service_domains = {
                'chatgpt': 'chat.openai.com',
                'claude': 'claude.ai',
                'gemini': 'gemini.google.com',
                'genspark': 'genspark.ai',
                'google_ai_studio': 'aistudio.google.com'
            }
            
            expected_domain = service_domains.get(service_name.lower())
            if expected_domain and expected_domain in current_url:
                logger.debug(f"{service_name}: 正しいドメインにアクセス中")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"{service_name}: ログイン状態確認でエラー: {e}")
            return False

    async def clear_session(self, service_name: str) -> bool:
        """
        特定サービスのセッションをクリア
        
        Args:
            service_name: サービス名
            
        Returns:
            bool: クリア成功の可否
        """
        try:
            logger.info(f"{service_name}: セッションクリア開始")
            
            session_dir = self.get_session_dir(service_name)
            
            # セッションファイルを削除
            for file_path in session_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            
            # セッション情報から削除
            if service_name in self.session_info:
                del self.session_info[service_name]
                self._save_session_info()
            
            logger.info(f"{service_name}: セッションクリア完了")
            return True
            
        except Exception as e:
            logger.error(f"{service_name}: セッションクリアでエラー: {e}")
            return False

    def get_session_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        全セッションの概要を取得
        
        Returns:
            Dict[str, Dict[str, Any]]: セッション概要
        """
        summary = {}
        
        for service_name, session_data in self.session_info.items():
            is_valid = self._is_session_valid(service_name)
            
            summary[service_name] = {
                "valid": is_valid,
                "last_saved": session_data.get('last_saved'),
                "cookies_count": session_data.get('cookies_count', 0),
                "session_dir": session_data.get('session_dir')
            }
        
        return summary

    async def cleanup_expired_sessions(self) -> int:
        """
        期限切れセッションをクリーンアップ
        
        Returns:
            int: クリーンアップしたセッション数
        """
        cleaned_count = 0
        
        for service_name in list(self.session_info.keys()):
            if not self._is_session_valid(service_name):
                await self.clear_session(service_name)
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"期限切れセッション {cleaned_count}件をクリーンアップしました")
        
        return cleaned_count

    def update_session_validity_days(self, days: int):
        """
        セッション有効期限を更新
        
        Args:
            days: 有効期限（日数）
        """
        self.session_validity_days = days
        config_manager.set('automation.session_validity_days', days)
        config_manager.save_config()
        logger.info(f"セッション有効期限を {days}日に更新しました")