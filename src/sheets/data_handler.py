"""
Sheetsデータハンドラー（テスト用モック）
本実装は担当者Bが実装予定
"""

from typing import List, Dict, Any, Optional
from .models import TaskRow, SheetConfig, SheetData, ColumnAIConfig, AIService, ColumnPositions


class DataHandler:
    """データハンドリングクラス（モック）"""
    
    def __init__(self, sheets_client=None):
        """初期化"""
        self.sheets_client = sheets_client
        self.column_ai_settings: Dict[int, ColumnAIConfig] = {}
    
    def load_column_ai_settings_from_config(self, sheet_config: SheetConfig, config_manager):
        """列毎AI設定をロード（モック）"""
        # テスト用のダミー設定
        self.column_ai_settings = {
            1: ColumnAIConfig(
                ai_service=AIService.CHATGPT,
                ai_model="gpt-4",
                ai_mode="creative"
            ),
            2: ColumnAIConfig(
                ai_service=AIService.CLAUDE,
                ai_model="claude-3.5-sonnet",
                ai_mode="precise"
            )
        }
    
    def load_and_validate_sheet(self, sheet_config: SheetConfig) -> SheetData:
        """シートデータをロードして検証（モック）"""
        # テスト用のダミーデータ
        return SheetData(
            config=sheet_config,
            headers=["番号", "処理", "エラー", "コピー", "貼り付け"],
            data_rows=[
                ["1", "", "", "テストメッセージ1", ""],
                ["2", "", "", "テストメッセージ2", ""],
            ],
            copy_columns=[3]  # 0ベースインデックス
        )
    
    def create_task_rows(self, sheet_data: SheetData) -> List[TaskRow]:
        """タスク行を作成（モック）"""
        tasks = []
        
        for i, row in enumerate(sheet_data.data_rows):
            if len(row) > 3 and row[0]:  # 番号がある行
                # 列位置を計算
                copy_col = 3  # コピー列
                positions = ColumnPositions(
                    copy_column=copy_col,
                    process_column=copy_col - 2,  # 処理列
                    error_column=copy_col - 1,    # エラー列
                    result_column=copy_col + 1    # 貼り付け列
                )
                
                # AI設定を取得（デフォルトはChatGPT）
                ai_config = self.column_ai_settings.get(
                    copy_col, 
                    ColumnAIConfig(ai_service=AIService.CHATGPT)
                )
                
                task = TaskRow(
                    row_number=i + 1,
                    copy_text=row[copy_col] if len(row) > copy_col else "",
                    ai_config=ai_config,
                    column_positions=positions
                )
                tasks.append(task)
        
        return tasks