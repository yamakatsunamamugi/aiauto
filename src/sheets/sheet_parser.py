#!/usr/bin/env python3
"""
シートデータ解析エンジン
CLAUDE.md仕様に従ったスプレッドシート構造の解析と検証
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import logger
from .models import TaskRow, ColumnAIConfig, AIService, ColumnPositions
from .sheets_client import SheetsClient


class ParseError(Exception):
    """解析エラー"""
    pass


@dataclass
class CopyColumnInfo:
    """コピー列情報"""
    column_index: int  # 0ベースの列インデックス
    column_letter: str  # A, B, C形式
    process_column: int  # 処理列インデックス
    error_column: int  # エラー列インデックス
    result_column: int  # 結果列インデックス
    ai_config: Optional[ColumnAIConfig] = None


@dataclass
class SheetStructure:
    """シート構造情報"""
    spreadsheet_id: str
    sheet_name: str
    work_header_row: int  # 「作業」ヘッダー行（1ベース）
    data_start_row: int  # データ開始行（1ベース）
    copy_columns: List[CopyColumnInfo]  # コピー列情報のリスト
    headers: List[str]  # ヘッダー行のデータ
    total_rows: int  # 総行数
    total_columns: int  # 総列数


class SheetParser:
    """シートデータ解析クラス"""
    
    def __init__(self, sheets_client: SheetsClient):
        """
        初期化
        
        Args:
            sheets_client: Sheets APIクライアント
        """
        self.sheets_client = sheets_client
        self.work_header_text = "作業"  # CLAUDE.md仕様（A列に「作業」という文字列）
        self.copy_header_text = "コピー"  # CLAUDE.md仕様
        self.work_header_row = 4  # 実際のシート構造に合わせて変更（1ベース）
        
    def parse_sheet_structure(self, spreadsheet_id: str, sheet_name: str) -> Optional[SheetStructure]:
        """
        シート構造を解析
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            
        Returns:
            Optional[SheetStructure]: 解析されたシート構造
        """
        try:
            logger.info(f"シート構造解析開始: {sheet_name}")
            
            # シート全体のデータを読み取り（最大100行、50列）
            range_name = f"{sheet_name}!A1:AX100"
            all_data = self.sheets_client.read_range(spreadsheet_id, range_name)
            
            if not all_data:
                raise ParseError("シートデータの読み取りに失敗しました")
            
            # 「作業」ヘッダー行を検索（5行目のA列を想定）
            work_row_index = self._find_work_header_row(all_data)
            if work_row_index is None:
                raise ParseError(f"A列に「{self.work_header_text}」が含まれる行が見つかりません（通常は5行目）")
            
            work_header_row = work_row_index + 1  # 1ベースに変換
            
            # ヘッダー行のデータを取得
            headers = all_data[work_row_index] if work_row_index < len(all_data) else []
            
            # 「コピー」列を検索
            copy_columns = self._find_copy_columns(headers, work_header_row)
            if not copy_columns:
                raise ParseError(f"「{self.copy_header_text}」列が見つかりません")
            
            # データ開始行を計算
            data_start_row = work_header_row + 1
            
            # シート構造を作成
            structure = SheetStructure(
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name,
                work_header_row=work_header_row,
                data_start_row=data_start_row,
                copy_columns=copy_columns,
                headers=headers,
                total_rows=len(all_data),
                total_columns=len(headers) if headers else 0
            )
            
            logger.info(f"✅ シート構造解析成功: 作業ヘッダー行={work_header_row}, データ開始行={data_start_row}, コピー列数={len(copy_columns)}, 総行数={structure.total_rows}")
            
            return structure
            
        except ParseError as e:
            logger.error(f"❌ シート構造解析エラー: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 予期しない解析エラー: {e}")
            return None
    
    def extract_task_rows(self, structure: SheetStructure) -> List[TaskRow]:
        """
        タスク行を抽出
        
        Args:
            structure: シート構造情報
            
        Returns:
            List[TaskRow]: タスク行のリスト
        """
        try:
            logger.info("タスク行抽出開始...")
            
            # データ範囲を読み取り
            range_name = f"{structure.sheet_name}!A{structure.data_start_row}:AX100"
            data_rows = self.sheets_client.read_range(structure.spreadsheet_id, range_name)
            
            if not data_rows:
                logger.warning("データ行が見つかりません")
                return []
            
            task_rows = []
            
            for row_index, row_data in enumerate(data_rows):
                actual_row_number = structure.data_start_row + row_index
                
                # A列（インデックス0）をチェック
                if not row_data or not row_data[0].strip():
                    # 空白行で処理終了（CLAUDE.md仕様）
                    logger.info(f"空白行を検出: 行{actual_row_number}で処理終了")
                    break
                
                # A列が数値（連番）かチェック
                try:
                    row_number = int(row_data[0])
                except (ValueError, IndexError):
                    logger.warning(f"行{actual_row_number}: A列が数値ではありません: '{row_data[0] if row_data else ''}'")
                    continue
                
                # 各コピー列に対してタスクを作成
                for copy_col_info in structure.copy_columns:
                    task_row = self._create_task_row(
                        row_data, actual_row_number, copy_col_info, structure
                    )
                    if task_row:
                        task_rows.append(task_row)
            
            logger.info(f"✅ タスク行抽出完了: {len(task_rows)}件")
            return task_rows
            
        except Exception as e:
            logger.error(f"❌ タスク行抽出エラー: {e}")
            return []
    
    def _find_work_header_row(self, all_data: List[List[str]]) -> Optional[int]:
        """
        「作業指示行」ヘッダー行を検索
        
        Args:
            all_data: 全シートデータ
            
        Returns:
            Optional[int]: 「作業指示行」行のインデックス（0ベース）
        """
        try:
            # CLAUDE.md仕様：5行目のA列に「作業」があることを想定（幅広く4〜10行目を検索）
            start_row = 3  # 4行目から検索開始（0ベース）
            
            for row_index in range(start_row, min(len(all_data), 10)):  # 最大10行目まで検索
                row_data = all_data[row_index]
                
                # A列（インデックス0）に「作業」が含まれるかチェック
                if row_data and len(row_data) > 0:
                    cell_value = str(row_data[0]).strip()
                    if self.work_header_text in cell_value:  # 「作業」が含まれることをチェック
                        logger.info(f"「{self.work_header_text}」を含むヘッダー発見: 行{row_index + 1} (値: '{cell_value}')")
                        return row_index
            
            return None
            
        except Exception as e:
            logger.error(f"作業ヘッダー行検索エラー: {e}")
            return None
    
    def _find_copy_columns(self, headers: List[str], work_header_row: int) -> List[CopyColumnInfo]:
        """
        「コピー」列を検索
        
        Args:
            headers: ヘッダー行のデータ
            work_header_row: 作業ヘッダー行番号（1ベース）
            
        Returns:
            List[CopyColumnInfo]: コピー列情報のリスト
        """
        try:
            copy_columns = []
            
            for col_index, header_value in enumerate(headers):
                if str(header_value).strip() == self.copy_header_text:
                    # 関連列の位置を計算
                    process_col = col_index - 2  # コピー列-2
                    error_col = col_index - 1    # コピー列-1
                    result_col = col_index + 1   # コピー列+1
                    
                    # 境界チェック
                    if process_col < 0:
                        logger.warning(f"コピー列{col_index + 1}: 処理列が範囲外です（列{process_col + 1}）")
                        continue
                    
                    if error_col < 0:
                        logger.warning(f"コピー列{col_index + 1}: エラー列が範囲外です（列{error_col + 1}）")
                        continue
                    
                    # 最大列数チェック（スプレッドシートの列数制限を考慮）
                    max_columns = len(headers)
                    if result_col >= max_columns:
                        logger.warning(f"コピー列{col_index + 1}: 結果列が範囲外です（列{result_col + 1} > 最大列数{max_columns}）")
                        logger.warning(f"  解決策: スプレッドシートに列を追加するか、コピー列の位置を左に移動してください")
                        continue
                    
                    # 列文字を生成
                    col_letter = self._number_to_column_letter(col_index + 1)
                    
                    copy_col_info = CopyColumnInfo(
                        column_index=col_index,
                        column_letter=col_letter,
                        process_column=process_col,
                        error_column=error_col,
                        result_column=result_col
                    )
                    
                    copy_columns.append(copy_col_info)
                    
                    logger.debug(f"「{self.copy_header_text}」列発見: {col_letter}列（インデックス{col_index}）")
                    logger.debug(f"  - 処理列: {self._number_to_column_letter(process_col + 1)}")
                    logger.debug(f"  - エラー列: {self._number_to_column_letter(error_col + 1)}")
                    logger.debug(f"  - 結果列: {self._number_to_column_letter(result_col + 1)}")
            
            return copy_columns
            
        except Exception as e:
            logger.error(f"コピー列検索エラー: {e}")
            return []
    
    def _create_task_row(self, row_data: List[str], row_number: int, 
                        copy_col_info: CopyColumnInfo, structure: SheetStructure) -> Optional[TaskRow]:
        """
        タスク行を作成
        
        Args:
            row_data: 行データ
            row_number: 行番号（1ベース）
            copy_col_info: コピー列情報
            structure: シート構造
            
        Returns:
            Optional[TaskRow]: 作成されたタスク行
        """
        try:
            # コピー列のテキストを取得
            copy_text = ""
            if len(row_data) > copy_col_info.column_index:
                copy_text = str(row_data[copy_col_info.column_index]).strip()
            
            # 処理列の状態をチェック
            process_status = ""
            if len(row_data) > copy_col_info.process_column:
                process_status = str(row_data[copy_col_info.process_column]).strip()
            
            # 処理済みの場合はスキップ
            if process_status and process_status != "未処理":
                logger.debug(f"行{row_number}: 処理済みのためスキップ（状態: {process_status}）")
                return None
            
            # コピーテキストが空の場合もスキップ
            if not copy_text:
                logger.debug(f"行{row_number}: コピーテキストが空のためスキップ")
                return None
            
            # AI設定を取得（デフォルトはChatGPT）
            ai_config = copy_col_info.ai_config or ColumnAIConfig(
                ai_service=AIService.CHATGPT,
                ai_model="gpt-4"
            )
            
            # 列位置情報を作成
            positions = ColumnPositions(
                copy_column=copy_col_info.column_index,
                process_column=copy_col_info.process_column,
                error_column=copy_col_info.error_column,
                result_column=copy_col_info.result_column
            )
            
            # タスク行を作成
            task_row = TaskRow(
                row_number=row_number,
                copy_text=copy_text,
                ai_config=ai_config,
                column_positions=positions
            )
            
            logger.debug(f"タスク行作成: 行{row_number}, コピー列{copy_col_info.column_letter}")
            return task_row
            
        except Exception as e:
            logger.error(f"タスク行作成エラー（行{row_number}）: {e}")
            return None
    
    def validate_sheet_structure(self, structure: SheetStructure) -> List[str]:
        """
        シート構造を検証
        
        Args:
            structure: シート構造
            
        Returns:
            List[str]: 検証エラーのリスト
        """
        errors = []
        
        try:
            # 基本構造チェック
            if structure.work_header_row < 1:
                errors.append("作業ヘッダー行が無効です")
            
            if structure.data_start_row <= structure.work_header_row:
                errors.append("データ開始行が作業ヘッダー行より前にあります")
            
            if not structure.copy_columns:
                errors.append("コピー列が見つかりません")
            
            # コピー列の検証
            for i, copy_col in enumerate(structure.copy_columns):
                if copy_col.process_column < 0:
                    errors.append(f"コピー列{i+1}: 処理列が範囲外です")
                
                if copy_col.error_column < 0:
                    errors.append(f"コピー列{i+1}: エラー列が範囲外です")
                
                if copy_col.result_column >= structure.total_columns:
                    errors.append(f"コピー列{i+1}: 結果列が範囲外です")
            
            # データ量チェック
            if structure.total_rows < structure.data_start_row:
                errors.append("データ行が存在しません")
            
            logger.info(f"シート構造検証完了: {len(errors)}件のエラー")
            
        except Exception as e:
            errors.append(f"検証中にエラーが発生しました: {e}")
        
        return errors
    
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
    
    def get_parser_status(self) -> Dict[str, Any]:
        """
        パーサーの状態を取得
        
        Returns:
            Dict[str, Any]: パーサー状態情報
        """
        return {
            "work_header_text": self.work_header_text,
            "copy_header_text": self.copy_header_text,
            "work_header_row": self.work_header_row,
            "sheets_client_status": self.sheets_client.get_connection_status()
        }