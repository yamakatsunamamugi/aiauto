"""
Google Sheets API操作クライアント

スプレッドシートの読み書き操作を提供する高レベルAPIクライアント
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import time
from datetime import datetime

from googleapiclient.errors import HttpError

from .auth_manager import AuthManager, AuthenticationError
from .models import SheetConfig, TaskRow, TaskStatus, SpreadsheetData


class SheetsAPIError(Exception):
    """Sheets API関連のエラー"""
    pass


class SheetsClient:
    """
    Google Sheets API操作クライアント
    
    スプレッドシートの読み書き、データ操作を行うメインクラス
    """
    
    def __init__(self, auth_manager: AuthManager):
        """
        初期化
        
        Args:
            auth_manager: 認証管理インスタンス
        """
        self.logger = logging.getLogger(__name__)
        self.auth_manager = auth_manager
        self.service = auth_manager.get_service()
        
        # API制限対応のための設定
        self.batch_size = 100  # 一度に処理する行数
        self.api_delay = 0.1   # API呼び出し間の待機時間（秒）
        
        self.logger.info("SheetsClientが初期化されました")
    
    def get_sheet_names(self, spreadsheet_id: str) -> List[str]:
        """
        スプレッドシート内のシート名一覧を取得
        
        Args:
            spreadsheet_id: スプレッドシートID
        
        Returns:
            List[str]: シート名のリスト
        """
        try:
            return self.auth_manager.list_sheet_names(spreadsheet_id)
        except Exception as e:
            self.logger.error(f"シート名一覧取得エラー: {e}")
            raise SheetsAPIError(f"シート名一覧の取得に失敗しました: {e}")
    
    def read_sheet_data(self, spreadsheet_id: str, sheet_name: str, 
                       range_name: Optional[str] = None) -> List[List[str]]:
        """
        シートデータを読み取り
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            range_name: 読み取り範囲（例: 'A1:Z100'）。Noneの場合は全体
        
        Returns:
            List[List[str]]: シートデータ（行×列の2次元リスト）
        """
        try:
            # 範囲指定
            if range_name:
                full_range = f"{sheet_name}!{range_name}"
            else:
                full_range = sheet_name
            
            # データ読み取り
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=full_range,
                valueRenderOption='UNFORMATTED_VALUE',
                dateTimeRenderOption='FORMATTED_STRING'
            ).execute()
            
            values = result.get('values', [])
            
            # データを正規化（行の長さを統一）
            if values:
                max_cols = max(len(row) for row in values)
                normalized_values = []
                for row in values:
                    # 不足分を空文字で埋める
                    normalized_row = row + [''] * (max_cols - len(row))
                    # 各セルを文字列に変換
                    normalized_row = [str(cell) if cell is not None else '' for cell in normalized_row]
                    normalized_values.append(normalized_row)
                values = normalized_values
            
            self.logger.info(f"シートデータを読み取りました: {len(values)}行")
            return values
            
        except HttpError as e:
            self.logger.error(f"シートデータ読み取りエラー: {e}")
            if e.resp.status == 400:
                raise SheetsAPIError(f"無効な範囲指定またはシート名です: {range_name}")
            elif e.resp.status == 403:
                raise SheetsAPIError("スプレッドシートへのアクセス権限がありません")
            elif e.resp.status == 404:
                raise SheetsAPIError("指定されたシートが見つかりません")
            else:
                raise SheetsAPIError(f"シートデータの読み取りに失敗しました: {e}")
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise SheetsAPIError(f"予期しないエラーが発生しました: {e}")
    
    def write_cell(self, spreadsheet_id: str, sheet_name: str, 
                   row: int, col: int, value: str):
        """
        単一セルに値を書き込み
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            row: 行番号（1ベース）
            col: 列番号（1ベース、A=1, B=2...）
            value: 書き込む値
        """
        try:
            # 列番号をアルファベットに変換
            col_letter = self._col_num_to_letter(col)
            cell_range = f"{sheet_name}!{col_letter}{row}"
            
            # 値を書き込み
            body = {
                'values': [[str(value)]]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=cell_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            self.logger.debug(f"セル {cell_range} に値を書き込みました: {value}")
            
            # API制限対応の待機
            time.sleep(self.api_delay)
            
        except HttpError as e:
            self.logger.error(f"セル書き込みエラー: {e}")
            raise SheetsAPIError(f"セルへの書き込みに失敗しました: {e}")
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise SheetsAPIError(f"予期しないエラーが発生しました: {e}")
    
    def write_range(self, spreadsheet_id: str, sheet_name: str,
                    start_row: int, start_col: int, values: List[List[str]]):
        """
        範囲指定で複数セルに値を書き込み
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            start_row: 開始行番号（1ベース）
            start_col: 開始列番号（1ベース）
            values: 書き込む値の2次元リスト
        """
        try:
            if not values or not values[0]:
                return
            
            # 範囲を計算
            end_row = start_row + len(values) - 1
            end_col = start_col + len(values[0]) - 1
            
            start_col_letter = self._col_num_to_letter(start_col)
            end_col_letter = self._col_num_to_letter(end_col)
            
            range_name = f"{sheet_name}!{start_col_letter}{start_row}:{end_col_letter}{end_row}"
            
            # 値を書き込み
            body = {
                'values': values
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            self.logger.info(f"範囲 {range_name} に {len(values)}行の値を書き込みました")
            
            # API制限対応の待機
            time.sleep(self.api_delay)
            
        except HttpError as e:
            self.logger.error(f"範囲書き込みエラー: {e}")
            raise SheetsAPIError(f"範囲への書き込みに失敗しました: {e}")
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise SheetsAPIError(f"予期しないエラーが発生しました: {e}")
    
    def batch_update_cells(self, spreadsheet_id: str, sheet_name: str,
                          updates: List[Dict[str, Any]]):
        """
        複数セルを一括更新
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            updates: 更新データのリスト
                    [{'row': 行番号, 'col': 列番号, 'value': 値}, ...]
        """
        try:
            if not updates:
                return
            
            # バッチ更新用のデータを準備
            data = []
            for update in updates:
                row = update['row']
                col = update['col']
                value = update['value']
                
                col_letter = self._col_num_to_letter(col)
                range_name = f"{sheet_name}!{col_letter}{row}"
                
                data.append({
                    'range': range_name,
                    'values': [[str(value)]]
                })
            
            # バッチ更新を実行
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': data
            }
            
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            self.logger.info(f"{len(updates)}個のセルを一括更新しました")
            
            # API制限対応の待機
            time.sleep(self.api_delay * 0.5)
            
        except HttpError as e:
            self.logger.error(f"一括更新エラー: {e}")
            raise SheetsAPIError(f"一括更新に失敗しました: {e}")
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise SheetsAPIError(f"予期しないエラーが発生しました: {e}")
    
    def update_task_status(self, config: SheetConfig, task: TaskRow, 
                          status: TaskStatus, result: Optional[str] = None,
                          error_message: Optional[str] = None):
        """
        タスクの状態を更新
        
        Args:
            config: シート設定
            task: 更新対象タスク
            status: 新しい状態
            result: 処理結果（完了時）
            error_message: エラーメッセージ（エラー時）
        """
        try:
            updates = []
            
            # 処理列の更新
            updates.append({
                'row': task.row_number,
                'col': task.column_positions.process_column,
                'value': status.value
            })
            
            # 結果またはエラーメッセージの更新
            if status == TaskStatus.COMPLETED and result:
                updates.append({
                    'row': task.row_number,
                    'col': task.column_positions.result_column,
                    'value': result
                })
                # エラー列をクリア
                updates.append({
                    'row': task.row_number,
                    'col': task.column_positions.error_column,
                    'value': ''
                })
            elif status == TaskStatus.ERROR and error_message:
                updates.append({
                    'row': task.row_number,
                    'col': task.column_positions.error_column,
                    'value': error_message
                })
            
            # 一括更新
            self.batch_update_cells(config.spreadsheet_id, config.sheet_name, updates)
            
            # タスクオブジェクトの状態も更新
            task.status = status
            if result:
                task.result = result
            if error_message:
                task.error_message = error_message
            
            self.logger.info(f"タスク {task.row_number}行目の状態を更新: {status.value}")
            
        except Exception as e:
            self.logger.error(f"タスク状態更新エラー: {e}")
            raise SheetsAPIError(f"タスク状態の更新に失敗しました: {e}")
    
    def get_sheet_metadata(self, spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
        """
        シートのメタデータを取得
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
        
        Returns:
            Dict[str, Any]: シートメタデータ
        """
        try:
            response = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields='sheets.properties'
            ).execute()
            
            for sheet in response.get('sheets', []):
                props = sheet.get('properties', {})
                if props.get('title') == sheet_name:
                    return {
                        'sheet_id': props.get('sheetId'),
                        'title': props.get('title'),
                        'index': props.get('index'),
                        'row_count': props.get('gridProperties', {}).get('rowCount', 0),
                        'column_count': props.get('gridProperties', {}).get('columnCount', 0)
                    }
            
            raise SheetsAPIError(f"シート '{sheet_name}' が見つかりません")
            
        except HttpError as e:
            self.logger.error(f"シートメタデータ取得エラー: {e}")
            raise SheetsAPIError(f"シートメタデータの取得に失敗しました: {e}")
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise SheetsAPIError(f"予期しないエラーが発生しました: {e}")
    
    def clear_range(self, spreadsheet_id: str, sheet_name: str, range_name: str):
        """
        指定範囲のセルをクリア
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            range_name: クリア範囲（例: 'A1:C10'）
        """
        try:
            full_range = f"{sheet_name}!{range_name}"
            
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=full_range,
                body={}
            ).execute()
            
            self.logger.info(f"範囲 {full_range} をクリアしました")
            
            # API制限対応の待機
            time.sleep(self.api_delay)
            
        except HttpError as e:
            self.logger.error(f"範囲クリアエラー: {e}")
            raise SheetsAPIError(f"範囲のクリアに失敗しました: {e}")
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise SheetsAPIError(f"予期しないエラーが発生しました: {e}")
    
    def validate_sheet_structure(self, config: SheetConfig) -> Tuple[bool, List[str]]:
        """
        シート構造の検証
        
        Args:
            config: シート設定
        
        Returns:
            Tuple[bool, List[str]]: (検証成功フラグ, エラーメッセージリスト)
        """
        errors = []
        
        try:
            # シートの存在確認
            sheet_names = self.get_sheet_names(config.spreadsheet_id)
            if config.sheet_name not in sheet_names:
                errors.append(f"シート '{config.sheet_name}' が見つかりません")
                return False, errors
            
            # データ読み取り
            data = self.read_sheet_data(config.spreadsheet_id, config.sheet_name)
            
            # 最小行数の確認
            if len(data) < config.work_header_row:
                errors.append(f"シートの行数が不足しています（必要: {config.work_header_row}行以上）")
            
            # ヘッダー行の確認
            if len(data) >= config.work_header_row:
                header_row = data[config.work_header_row - 1]
                if len(header_row) == 0 or header_row[0] != "作業":
                    errors.append(f"{config.work_header_row}行目のA列に「作業」が見つかりません")
                
                # 「コピー」列の確認
                copy_columns = [i for i, cell in enumerate(header_row) if cell == "コピー"]
                if not copy_columns:
                    errors.append("「コピー」列が見つかりません")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"シート構造検証エラー: {e}")
            errors.append(f"シート構造の検証中にエラーが発生しました: {e}")
            return False, errors
    
    def _col_num_to_letter(self, col_num: int) -> str:
        """
        列番号をアルファベットに変換
        
        Args:
            col_num: 列番号（1ベース、A=1, B=2...）
        
        Returns:
            str: 列アルファベット（A, B, C, ..., AA, AB, ...）
        """
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(col_num % 26 + ord('A')) + result
            col_num //= 26
        return result
    
    def _letter_to_col_num(self, letter: str) -> int:
        """
        列アルファベットを番号に変換
        
        Args:
            letter: 列アルファベット（A, B, C, ..., AA, AB, ...）
        
        Returns:
            int: 列番号（1ベース）
        """
        col_num = 0
        for char in letter.upper():
            col_num = col_num * 26 + (ord(char) - ord('A') + 1)
        return col_num
    
    def create_backup_sheet(self, spreadsheet_id: str, source_sheet_name: str,
                           backup_suffix: Optional[str] = None) -> str:
        """
        シートのバックアップを作成
        
        Args:
            spreadsheet_id: スプレッドシートID
            source_sheet_name: バックアップ元シート名
            backup_suffix: バックアップシート名のサフィックス
        
        Returns:
            str: 作成されたバックアップシート名
        """
        try:
            if backup_suffix is None:
                backup_suffix = datetime.now().strftime("_%Y%m%d_%H%M%S")
            
            backup_sheet_name = f"{source_sheet_name}_backup{backup_suffix}"
            
            # 元シートの情報を取得
            sheet_metadata = self.get_sheet_metadata(spreadsheet_id, source_sheet_name)
            source_sheet_id = sheet_metadata['sheet_id']
            
            # シートを複製
            body = {
                'destinationSpreadsheetId': spreadsheet_id
            }
            
            response = self.service.spreadsheets().sheets().copyTo(
                spreadsheetId=spreadsheet_id,
                sheetId=source_sheet_id,
                body=body
            ).execute()
            
            new_sheet_id = response['sheetId']
            
            # バックアップシートの名前を変更
            requests = [{
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': new_sheet_id,
                        'title': backup_sheet_name
                    },
                    'fields': 'title'
                }
            }]
            
            body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            self.logger.info(f"バックアップシートを作成しました: {backup_sheet_name}")
            return backup_sheet_name
            
        except Exception as e:
            self.logger.error(f"バックアップシート作成エラー: {e}")
            raise SheetsAPIError(f"バックアップシートの作成に失敗しました: {e}")


def create_sheets_client(credentials_path: Optional[str] = None) -> SheetsClient:
    """
    SheetsClientインスタンスを作成するファクトリー関数
    
    Args:
        credentials_path: 認証情報ファイルのパス
    
    Returns:
        SheetsClient: 初期化済みのSheetsClientインスタンス
    """
    auth_manager = AuthManager(credentials_path)
    return SheetsClient(auth_manager)


# 使用例とテスト用のメイン関数
if __name__ == "__main__":
    import sys
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("使用方法: python sheets_client.py <spreadsheet_id> [sheet_name]")
        sys.exit(1)
    
    spreadsheet_id = sys.argv[1]
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # SheetsClientの作成
        client = create_sheets_client()
        
        print(f"✅ SheetsClientが初期化されました")
        
        # シート名一覧を取得
        sheet_names = client.get_sheet_names(spreadsheet_id)
        print(f"シート一覧: {sheet_names}")
        
        if sheet_name and sheet_name in sheet_names:
            # 指定されたシートのデータを読み取り
            data = client.read_sheet_data(spreadsheet_id, sheet_name)
            print(f"\nシート '{sheet_name}' のデータ:")
            print(f"行数: {len(data)}")
            
            if data:
                print("最初の5行:")
                for i, row in enumerate(data[:5]):
                    print(f"行{i+1}: {row}")
        
    except (AuthenticationError, SheetsAPIError) as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)