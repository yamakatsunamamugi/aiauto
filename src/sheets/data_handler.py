"""
Sheetsデータハンドラー
Google Sheets APIとの統合データ管理
"""

from typing import List, Dict, Any, Optional
from .models import TaskRow, ColumnAIConfig, AIService
from .sheets_client import SheetsClient
from .sheet_parser import SheetParser, SheetStructure
from src.utils.logger import logger


class DataHandler:
    """データハンドリングクラス"""
    
    def __init__(self, sheets_client: Optional[SheetsClient] = None):
        """
        初期化
        
        Args:
            sheets_client: Google Sheets APIクライアント
        """
        self.sheets_client = sheets_client or SheetsClient()
        self.sheet_parser = SheetParser(self.sheets_client)
        self.column_ai_settings: Dict[int, ColumnAIConfig] = {}
        self.current_structure: Optional[SheetStructure] = None
        
    def authenticate(self) -> bool:
        """
        Google Sheets API認証
        
        Returns:
            bool: 認証成功の場合True
        """
        return self.sheets_client.authenticate()
    
    def load_sheet_from_url(self, sheet_url: str, sheet_name: Optional[str] = None) -> Optional[SheetStructure]:
        """
        スプレッドシートURLからシート構造をロード
        
        Args:
            sheet_url: スプレッドシートURL
            sheet_name: シート名（指定しない場合は最初のシート）
            
        Returns:
            Optional[SheetStructure]: 解析されたシート構造
        """
        try:
            logger.info(f"シートロード開始: {sheet_url}")
            
            # URLからスプレッドシートIDを抽出
            spreadsheet_id = self.sheets_client.extract_spreadsheet_id(sheet_url)
            if not spreadsheet_id:
                logger.error("スプレッドシートIDの抽出に失敗しました")
                return None
            
            # スプレッドシート情報を取得
            spreadsheet_info = self.sheets_client.get_spreadsheet_info(spreadsheet_id)
            if not spreadsheet_info:
                logger.error("スプレッドシート情報の取得に失敗しました")
                return None
            
            # シート名を決定
            if not sheet_name:
                if spreadsheet_info['sheets']:
                    sheet_name = spreadsheet_info['sheets'][0]['title']
                    logger.info(f"最初のシートを使用: {sheet_name}")
                else:
                    logger.error("利用可能なシートがありません")
                    return None
            
            # シート構造を解析
            structure = self.sheet_parser.parse_sheet_structure(spreadsheet_id, sheet_name)
            if structure:
                self.current_structure = structure
                logger.info(f"✅ シート構造ロード成功: {sheet_name}")
                
                # 構造の検証
                errors = self.sheet_parser.validate_sheet_structure(structure)
                if errors:
                    logger.warning(f"シート構造に警告があります:")
                    for error in errors:
                        logger.warning(f"  - {error}")
            
            return structure
            
        except Exception as e:
            logger.error(f"❌ シートロードエラー: {e}")
            return None
    
    def get_available_sheets(self, sheet_url: str) -> Optional[List[Dict[str, Any]]]:
        """
        利用可能なシート一覧を取得
        
        Args:
            sheet_url: スプレッドシートURL
            
        Returns:
            Optional[List[Dict[str, Any]]]: シート情報のリスト
        """
        try:
            spreadsheet_id = self.sheets_client.extract_spreadsheet_id(sheet_url)
            if not spreadsheet_id:
                return None
                
            spreadsheet_info = self.sheets_client.get_spreadsheet_info(spreadsheet_id)
            if not spreadsheet_info:
                return None
            
            return spreadsheet_info['sheets']
            
        except Exception as e:
            logger.error(f"シート一覧取得エラー: {e}")
            return None
    
    def load_column_ai_settings(self, config_data: Dict[str, Any]):
        """
        列毎AI設定をロード
        
        Args:
            config_data: AI設定データ
        """
        try:
            logger.info("列毎AI設定をロード中...")
            
            # 設定データから列毎AI設定を構築
            self.column_ai_settings = {}
            
            for col_key, ai_setting in config_data.items():
                try:
                    col_index = int(col_key)
                    ai_config = ColumnAIConfig(
                        ai_service=AIService(ai_setting.get('ai_service', 'chatgpt')),
                        ai_model=ai_setting.get('ai_model', 'gpt-4'),
                        ai_mode=ai_setting.get('ai_mode', 'default'),
                        ai_features=ai_setting.get('ai_features', []),
                        ai_settings=ai_setting.get('ai_settings', {})
                    )
                    self.column_ai_settings[col_index] = ai_config
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"AI設定の解析に失敗（列{col_key}）: {e}")
                    continue
            
            logger.info(f"✅ AI設定ロード完了: {len(self.column_ai_settings)}列")
            
        except Exception as e:
            logger.error(f"❌ AI設定ロードエラー: {e}")
    
    def create_task_rows(self, structure: Optional[SheetStructure] = None) -> List[TaskRow]:
        """
        タスク行を作成
        
        Args:
            structure: シート構造（指定しない場合は現在の構造を使用）
            
        Returns:
            List[TaskRow]: タスク行のリスト
        """
        try:
            if not structure:
                structure = self.current_structure
                
            if not structure:
                logger.error("シート構造が設定されていません")
                return []
            
            # シート構造からタスク行を抽出
            task_rows = self.sheet_parser.extract_task_rows(structure)
            
            # AI設定を適用
            for task_row in task_rows:
                copy_col_index = task_row.column_positions.copy_column
                if copy_col_index in self.column_ai_settings:
                    task_row.ai_config = self.column_ai_settings[copy_col_index]
            
            logger.info(f"✅ タスク行作成完了: {len(task_rows)}件")
            return task_rows
            
        except Exception as e:
            logger.error(f"❌ タスク行作成エラー: {e}")
            return []
    
    def update_task_result(self, task_row: TaskRow, result: str, error: Optional[str] = None) -> bool:
        """
        タスク結果をシートに書き戻し
        
        Args:
            task_row: タスク行
            result: 処理結果
            error: エラーメッセージ（任意）
            
        Returns:
            bool: 書き込み成功の場合True
        """
        try:
            if not self.current_structure:
                logger.error("シート構造が設定されていません")
                return False
            
            updates = []
            
            # 処理ステータスを更新
            process_range = f"{self.current_structure.sheet_name}!{self._get_cell_reference(task_row.row_number, task_row.column_positions.process_column + 1)}"
            updates.append({
                'range': process_range,
                'values': [['処理済み']]
            })
            
            # 結果を書き込み
            result_range = f"{self.current_structure.sheet_name}!{self._get_cell_reference(task_row.row_number, task_row.column_positions.result_column + 1)}"
            updates.append({
                'range': result_range,
                'values': [[result]]
            })
            
            # エラーがある場合はエラー列に書き込み
            if error:
                error_range = f"{self.current_structure.sheet_name}!{self._get_cell_reference(task_row.row_number, task_row.column_positions.error_column + 1)}"
                updates.append({
                    'range': error_range,
                    'values': [[error]]
                })
            
            # 一括更新
            success = self.sheets_client.batch_write(self.current_structure.spreadsheet_id, updates)
            
            if success:
                logger.info(f"✅ タスク結果更新成功: 行{task_row.row_number}")
            else:
                logger.error(f"❌ タスク結果更新失敗: 行{task_row.row_number}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ タスク結果更新エラー: {e}")
            return False
    
    def _get_cell_reference(self, row: int, col: int) -> str:
        """
        セル参照を取得（A1形式）
        
        Args:
            row: 行番号（1ベース）
            col: 列番号（1ベース）
            
        Returns:
            str: セル参照（例: "A1", "B5"）
        """
        col_letter = self._number_to_column_letter(col)
        return f"{col_letter}{row}"
    
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
    
    def get_data_handler_status(self) -> Dict[str, Any]:
        """
        データハンドラーの状態を取得
        
        Returns:
            Dict[str, Any]: 状態情報
        """
        return {
            "sheets_client_status": self.sheets_client.get_connection_status(),
            "parser_status": self.sheet_parser.get_parser_status(),
            "current_structure_loaded": self.current_structure is not None,
            "ai_settings_count": len(self.column_ai_settings)
        }