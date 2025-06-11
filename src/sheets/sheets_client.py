#!/usr/bin/env python3
"""
Google Sheets APIクライアント
スプレッドシートの読み取り・書き込み・操作を管理
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from googleapiclient.errors import HttpError
import time

from src.utils.logger import logger
from .auth_manager import AuthManager


class SheetsClient:
    """Google Sheets APIクライアントクラス"""
    
    def __init__(self, auth_manager: Optional[AuthManager] = None):
        """
        初期化
        
        Args:
            auth_manager: 認証管理オブジェクト
        """
        self.auth_manager = auth_manager or AuthManager()
        self.service = None
        self._authenticated = False
        
    def authenticate(self) -> bool:
        """
        認証を実行
        
        Returns:
            bool: 認証成功の場合True
        """
        try:
            logger.info("Sheets APIクライアント認証開始...")
            
            success = self.auth_manager.authenticate()
            if success:
                self.service = self.auth_manager.get_service()
                self._authenticated = self.service is not None
                
                if self._authenticated:
                    logger.info("✅ Sheets APIクライアント認証成功")
                else:
                    logger.error("❌ APIサービス取得失敗")
                    
            return self._authenticated
            
        except Exception as e:
            logger.error(f"❌ Sheets APIクライアント認証エラー: {e}")
            return False
    
    def extract_spreadsheet_id(self, url: str) -> Optional[str]:
        """
        スプレッドシートURLからIDを抽出
        
        Args:
            url: スプレッドシートURL
            
        Returns:
            Optional[str]: スプレッドシートID
        """
        try:
            # Google SheetsのURL形式:
            # https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={SHEET_ID}
            pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            
            if match:
                spreadsheet_id = match.group(1)
                logger.info(f"スプレッドシートID抽出成功: {spreadsheet_id}")
                return spreadsheet_id
            else:
                logger.error(f"無効なスプレッドシートURL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"スプレッドシートID抽出エラー: {e}")
            return None
    
    def get_spreadsheet_info(self, spreadsheet_id: str) -> Optional[Dict[str, Any]]:
        """
        スプレッドシート情報を取得
        
        Args:
            spreadsheet_id: スプレッドシートID
            
        Returns:
            Optional[Dict[str, Any]]: スプレッドシート情報
        """
        try:
            if not self._check_authentication():
                return None
                
            logger.info(f"スプレッドシート情報取得中: {spreadsheet_id}")
            
            # スプレッドシートのメタデータを取得
            result = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            # シート一覧を抽出
            sheets = []
            for sheet in result.get('sheets', []):
                sheet_info = {
                    'id': sheet['properties']['sheetId'],
                    'title': sheet['properties']['title'],
                    'index': sheet['properties']['index'],
                    'rowCount': sheet['properties']['gridProperties'].get('rowCount', 0),
                    'columnCount': sheet['properties']['gridProperties'].get('columnCount', 0)
                }
                sheets.append(sheet_info)
            
            info = {
                'id': result['spreadsheetId'],
                'title': result['properties']['title'],
                'locale': result['properties'].get('locale', 'en'),
                'sheets': sheets
            }
            
            logger.info(f"✅ スプレッドシート情報取得成功: {info['title']}")
            logger.info(f"シート数: {len(sheets)}")
            
            return info
            
        except HttpError as e:
            logger.error(f"❌ HTTP エラー: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ スプレッドシート情報取得エラー: {e}")
            return None
    
    def read_range(self, spreadsheet_id: str, range_name: str) -> Optional[List[List[str]]]:
        """
        指定範囲のセルデータを読み取り
        
        Args:
            spreadsheet_id: スプレッドシートID
            range_name: 範囲名（例: "Sheet1!A1:Z100"）
            
        Returns:
            Optional[List[List[str]]]: セルデータの2次元配列
        """
        try:
            if not self._check_authentication():
                return None
                
            logger.info(f"セル範囲読み取り中: {range_name}")
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueRenderOption='UNFORMATTED_VALUE',
                dateTimeRenderOption='FORMATTED_STRING'
            ).execute()
            
            values = result.get('values', [])
            
            # データを文字列に変換（数値も含む）
            normalized_values = []
            for row in values:
                normalized_row = [str(cell) if cell is not None else '' for cell in row]
                normalized_values.append(normalized_row)
            
            logger.info(f"✅ セル範囲読み取り成功: {len(normalized_values)}行")
            return normalized_values
            
        except HttpError as e:
            logger.error(f"❌ HTTP エラー: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ セル範囲読み取りエラー: {e}")
            return None
    
    def write_range(self, spreadsheet_id: str, range_name: str, values: List[List[Any]], 
                   value_input_option: str = 'RAW') -> bool:
        """
        指定範囲にセルデータを書き込み
        
        Args:
            spreadsheet_id: スプレッドシートID
            range_name: 範囲名（例: "Sheet1!A1:B2"）
            values: 書き込むデータの2次元配列
            value_input_option: 'RAW'（そのまま）または'USER_ENTERED'（数式評価）
            
        Returns:
            bool: 書き込み成功の場合True
        """
        try:
            if not self._check_authentication():
                return False
                
            logger.info(f"セル範囲書き込み中: {range_name}")
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            logger.info(f"✅ セル範囲書き込み成功: {updated_cells}セル更新")
            
            return True
            
        except HttpError as e:
            logger.error(f"❌ HTTP エラー: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ セル範囲書き込みエラー: {e}")
            return False
    
    def write_cell(self, spreadsheet_id: str, sheet_name: str, row: int, col: int, value: Any) -> bool:
        """
        単一セルに値を書き込み
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            row: 行番号（1ベース）
            col: 列番号（1ベース）
            value: 書き込む値
            
        Returns:
            bool: 書き込み成功の場合True
        """
        try:
            # 列番号をA1形式に変換
            col_letter = self._number_to_column_letter(col)
            range_name = f"{sheet_name}!{col_letter}{row}"
            
            return self.write_range(spreadsheet_id, range_name, [[value]])
            
        except Exception as e:
            logger.error(f"❌ 単一セル書き込みエラー: {e}")
            return False
    
    def batch_write(self, spreadsheet_id: str, updates: List[Dict[str, Any]]) -> bool:
        """
        複数範囲への一括書き込み
        
        Args:
            spreadsheet_id: スプレッドシートID
            updates: 更新データのリスト
                     [{'range': 'Sheet1!A1', 'values': [['value']]}, ...]
                     
        Returns:
            bool: 書き込み成功の場合True
        """
        try:
            if not self._check_authentication():
                return False
                
            if not updates:
                logger.warning("更新データが空です")
                return True
                
            logger.info(f"一括書き込み実行中: {len(updates)}件")
            
            # バッチ更新リクエストを構築
            value_ranges = []
            for update in updates:
                value_ranges.append({
                    'range': update['range'],
                    'values': update['values']
                })
            
            body = {
                'valueInputOption': 'RAW',
                'data': value_ranges
            }
            
            result = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            total_updated = sum(reply.get('updatedCells', 0) 
                              for reply in result.get('replies', []))
            
            logger.info(f"✅ 一括書き込み成功: {total_updated}セル更新")
            
            return True
            
        except HttpError as e:
            logger.error(f"❌ HTTP エラー: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 一括書き込みエラー: {e}")
            return False
    
    def find_cell_with_value(self, spreadsheet_id: str, sheet_name: str, 
                           search_value: str, search_range: Optional[str] = None) -> Optional[Tuple[int, int]]:
        """
        特定の値を持つセルを検索
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            search_value: 検索する値
            search_range: 検索範囲（例: "A1:Z100"）
            
        Returns:
            Optional[Tuple[int, int]]: (行, 列)の位置（1ベース）、見つからない場合None
        """
        try:
            # 検索範囲を設定
            if search_range:
                range_name = f"{sheet_name}!{search_range}"
            else:
                range_name = f"{sheet_name}"
                
            # データを読み取り
            values = self.read_range(spreadsheet_id, range_name)
            if not values:
                return None
            
            # 値を検索
            for row_idx, row in enumerate(values):
                for col_idx, cell_value in enumerate(row):
                    if str(cell_value).strip() == str(search_value).strip():
                        row_pos = row_idx + 1  # 1ベースに変換
                        col_pos = col_idx + 1  # 1ベースに変換
                        logger.info(f"値'{search_value}'を発見: 行{row_pos}, 列{col_pos}")
                        return (row_pos, col_pos)
            
            logger.warning(f"値'{search_value}'が見つかりませんでした")
            return None
            
        except Exception as e:
            logger.error(f"❌ セル検索エラー: {e}")
            return None
    
    def create_backup(self, spreadsheet_id: str, backup_name: str) -> Optional[str]:
        """
        スプレッドシートのバックアップを作成
        
        Args:
            spreadsheet_id: スプレッドシートID
            backup_name: バックアップ名
            
        Returns:
            Optional[str]: バックアップファイルのID
        """
        try:
            # Drive APIを使用してコピーを作成
            # 注意: Drive APIのスコープが必要
            logger.info(f"バックアップ作成中: {backup_name}")
            
            # TODO: Drive API統合
            # 現在はログのみ
            logger.warning("バックアップ機能は未実装です")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ バックアップ作成エラー: {e}")
            return None
    
    def _check_authentication(self) -> bool:
        """認証状態をチェック"""
        if not self._authenticated or not self.service:
            logger.error("認証が完了していません。先にauthenticate()を実行してください")
            return False
        return True
    
    def _number_to_column_letter(self, num: int) -> str:
        """
        列番号をA1形式の文字に変換
        
        Args:
            num: 列番号（1ベース）
            
        Returns:
            str: 列文字（A, B, C, ..., AA, AB, ...）
        """
        result = ""
        while num > 0:
            num -= 1
            result = chr(65 + (num % 26)) + result
            num //= 26
        return result
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        接続状態を取得
        
        Returns:
            Dict[str, Any]: 接続状態情報
        """
        status = {
            "authenticated": self._authenticated,
            "service_available": self.service is not None,
            "auth_status": self.auth_manager.get_auth_status() if self.auth_manager else {}
        }
        
        return status