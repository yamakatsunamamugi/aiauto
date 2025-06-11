"""
データ処理ハンドラー

スプレッドシートデータの解析、タスク生成、処理状態管理を行う
CLAUDE.mdの仕様に完全準拠した処理ロジックを実装
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from .models import (
    SheetConfig, TaskRow, TaskStatus, AIService, ColumnPosition,
    SpreadsheetData, ProcessingResult, ValidationError, ColumnAIConfig, ColumnMapping
)
from .sheets_client import SheetsClient, SheetsAPIError


class DataProcessingError(Exception):
    """データ処理関連のエラー"""
    pass


class DataHandler:
    """
    スプレッドシートデータの処理と管理を行うメインクラス
    
    CLAUDE.mdの仕様に従って以下の処理を行う：
    1. 5行目のA列で「作業」文字列を検索
    2. 「コピー」列を複数特定
    3. A列の連番（1,2,3...）を処理対象行として特定
    4. 各「コピー」列に対してタスクを生成
    """
    
    def __init__(self, sheets_client: SheetsClient):
        """
        初期化
        
        Args:
            sheets_client: Sheets APIクライアント
        """
        self.logger = logging.getLogger(__name__)
        self.sheets_client = sheets_client
        self.current_sheet_config = None  # 現在のシート設定を保持
        self.logger.info("DataHandlerが初期化されました")
    
    def load_and_validate_sheet(self, config: SheetConfig) -> SpreadsheetData:
        """
        スプレッドシートを読み込み、データ構造を検証
        
        Args:
            config: シート設定
        
        Returns:
            SpreadsheetData: 検証済みスプレッドシートデータ
        
        Raises:
            DataProcessingError: データ読み込みまたは検証に失敗した場合
        """
        try:
            self.logger.info(f"スプレッドシートを読み込み中: {config.sheet_name}")
            
            # 現在のシート設定を保存
            self.current_sheet_config = config
            
            # データ読み込み
            raw_data = self.sheets_client.read_sheet_data(
                config.spreadsheet_id, 
                config.sheet_name
            )
            
            # SpreadsheetDataオブジェクトを作成
            sheet_data = SpreadsheetData(config)
            sheet_data.set_raw_data(raw_data)
            
            # 構造検証
            if not sheet_data.is_valid():
                error_messages = [error.message for error in sheet_data.validation_errors]
                self.logger.error(f"データ検証エラー: {error_messages}")
                raise DataProcessingError(f"データ検証に失敗しました: {'; '.join(error_messages)}")
            
            self.logger.info(f"データ検証成功: {sheet_data.get_validation_summary()}")
            return sheet_data
            
        except SheetsAPIError as e:
            self.logger.error(f"スプレッドシート読み込みエラー: {e}")
            raise DataProcessingError(f"スプレッドシートの読み込みに失敗しました: {e}")
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise DataProcessingError(f"予期しないエラーが発生しました: {e}")
    
    def find_work_header_row(self, sheet_data: SpreadsheetData) -> int:
        """
        「作業」ヘッダー行を特定
        
        CLAUDE.md仕様: 5行目のA列に「作業」という文字列がある行
        
        Args:
            sheet_data: スプレッドシートデータ
        
        Returns:
            int: ヘッダー行番号（1ベース）
        
        Raises:
            DataProcessingError: ヘッダー行が見つからない場合
        """
        try:
            work_header_row = sheet_data.config.work_header_row
            
            if len(sheet_data.raw_data) < work_header_row:
                raise DataProcessingError(f"スプレッドシートの行数が不足しています（必要: {work_header_row}行以上）")
            
            header_row_data = sheet_data.raw_data[work_header_row - 1]  # 0-based indexing
            
            if len(header_row_data) == 0 or header_row_data[0] != "作業":
                raise DataProcessingError(f"{work_header_row}行目のA列に「作業」が見つかりません")
            
            self.logger.info(f"「作業」ヘッダー行を特定: {work_header_row}行目")
            return work_header_row
            
        except Exception as e:
            self.logger.error(f"ヘッダー行特定エラー: {e}")
            raise DataProcessingError(f"「作業」ヘッダー行の特定に失敗しました: {e}")
    
    def find_copy_columns(self, sheet_data: SpreadsheetData) -> List[int]:
        """
        「コピー」列を全て特定
        
        CLAUDE.md仕様: ヘッダー行で「コピー」と完全一致する列を全て検索
        
        Args:
            sheet_data: スプレッドシートデータ
        
        Returns:
            List[int]: 「コピー」列の位置リスト（1ベース）
        
        Raises:
            DataProcessingError: 「コピー」列が見つからない場合
        """
        try:
            # ヘッダー行を取得
            work_header_row = self.find_work_header_row(sheet_data)
            header_row_data = sheet_data.raw_data[work_header_row - 1]
            
            # 「コピー」列を検索
            copy_columns = []
            for i, cell_value in enumerate(header_row_data):
                if cell_value == "コピー":
                    copy_columns.append(i + 1)  # 1-based indexing
            
            if not copy_columns:
                raise DataProcessingError("「コピー」列が見つかりません。ヘッダー行に「コピー」という列を追加してください")
            
            self.logger.info(f"「コピー」列を特定: {len(copy_columns)}個の列 {copy_columns}")
            return copy_columns
            
        except Exception as e:
            self.logger.error(f"コピー列特定エラー: {e}")
            raise DataProcessingError(f"「コピー」列の特定に失敗しました: {e}")
    
    def get_processing_rows(self, sheet_data: SpreadsheetData) -> List[int]:
        """
        処理対象行を特定
        
        CLAUDE.md仕様: A列に「1」「2」「3」...といった連番が入力されている行
        A列が空白になった時点で処理終了
        
        Args:
            sheet_data: スプレッドシートデータ
        
        Returns:
            List[int]: 処理対象行番号のリスト（1ベース）
        """
        try:
            processing_rows = []
            start_row = sheet_data.config.start_row
            
            self.logger.info(f"処理対象行の検索開始: {start_row}行目から")
            
            for i in range(start_row - 1, len(sheet_data.raw_data)):  # 0-based indexing
                row_data = sheet_data.raw_data[i]
                row_number = i + 1  # 1-based row number
                
                # A列が空白なら処理終了
                if len(row_data) == 0 or not row_data[0].strip():
                    self.logger.info(f"A列が空白のため処理終了: {row_number}行目")
                    break
                
                # A列が数字（連番）なら処理対象
                a_cell_value = str(row_data[0]).strip()
                if a_cell_value.isdigit():
                    processing_rows.append(row_number)
                    self.logger.debug(f"処理対象行を追加: {row_number}行目 (A列: {a_cell_value})")
                else:
                    self.logger.debug(f"処理対象外の行をスキップ: {row_number}行目 (A列: {a_cell_value})")
            
            self.logger.info(f"処理対象行を特定: {len(processing_rows)}行")
            return processing_rows
            
        except Exception as e:
            self.logger.error(f"処理対象行特定エラー: {e}")
            raise DataProcessingError(f"処理対象行の特定に失敗しました: {e}")
    
    def create_column_positions(self, copy_column: int) -> ColumnPosition:
        """
        「コピー」列を基準とした関連列の位置を計算
        
        CLAUDE.md仕様:
        - 処理列: コピー列 - 2
        - エラー列: コピー列 - 1  
        - 貼り付け列: コピー列 + 1
        
        Args:
            copy_column: 「コピー」列の位置（1ベース）
        
        Returns:
            ColumnPosition: 列位置情報
        
        Raises:
            DataProcessingError: 列位置が無効な場合
        """
        try:
            process_column = copy_column - 2
            error_column = copy_column - 1
            result_column = copy_column + 1
            
            # 境界チェック（1列目より左にならないか）
            if process_column < 1 or error_column < 1:
                raise DataProcessingError(
                    f"「コピー」列 {copy_column} に対する処理列またはエラー列の位置が無効です "
                    f"(処理列: {process_column}, エラー列: {error_column}). "
                    f"「コピー」列はC列（3列目）以降に配置してください"
                )
            
            column_positions = ColumnPosition(
                copy_column=copy_column,
                process_column=process_column,
                error_column=error_column,
                result_column=result_column
            )
            
            self.logger.debug(f"列位置を計算: コピー={copy_column}, 処理={process_column}, "
                            f"エラー={error_column}, 結果={result_column}")
            
            return column_positions
            
        except Exception as e:
            self.logger.error(f"列位置計算エラー: {e}")
            raise DataProcessingError(f"列位置の計算に失敗しました: {e}")
    
    def get_ai_config_for_column(self, config: SheetConfig, copy_column: int) -> ColumnAIConfig:
        """
        指定された「コピー」列に対応するAI設定を取得
        
        Args:
            config: シート設定
            copy_column: 「コピー」列の位置
        
        Returns:
            ColumnAIConfig: 使用するAI設定
        """
        # 列毎AI設定が有効で設定されている場合はそれを使用
        if config.use_column_ai_settings:
            mapping = config.get_column_mapping(copy_column)
            if mapping:
                self.logger.debug(f"列 {copy_column} の設定を使用: {mapping.ai_config.ai_service.value}")
                return mapping.ai_config
        
        # デフォルト設定を返す
        return config.get_ai_config_for_column(copy_column)
    
    def create_task_rows(self, sheet_data: SpreadsheetData) -> List[TaskRow]:
        """
        処理タスクを生成
        
        各「コピー」列と各処理対象行の組み合わせでタスクを作成
        
        Args:
            sheet_data: スプレッドシートデータ
        
        Returns:
            List[TaskRow]: 生成されたタスクのリスト
        
        Raises:
            DataProcessingError: タスク生成に失敗した場合
        """
        try:
            self.logger.info("タスク生成を開始")
            
            # 必要な情報を取得
            copy_columns = self.find_copy_columns(sheet_data)
            processing_rows = self.get_processing_rows(sheet_data)
            
            if not processing_rows:
                self.logger.warning("処理対象行が見つかりません")
                return []
            
            tasks = []
            
            # 各「コピー」列に対してタスクを生成
            for copy_column in copy_columns:
                self.logger.info(f"「コピー」列 {copy_column} のタスク生成中")
                
                # 列位置を計算
                column_positions = self.create_column_positions(copy_column)
                
                # AI設定を取得
                ai_config = self.get_ai_config_for_column(sheet_data.config, copy_column)
                
                # 各処理対象行でタスクを作成
                for row_number in processing_rows:
                    try:
                        # コピー対象テキストを取得
                        copy_text = self._get_cell_value(sheet_data, row_number, copy_column)
                        
                        # 空のセルはスキップ
                        if not copy_text.strip():
                            self.logger.debug(f"空のセルをスキップ: {row_number}行目, {copy_column}列目")
                            continue
                        
                        # 処理状態を確認（既に処理済みかどうか）
                        process_status = self._get_cell_value(sheet_data, row_number, column_positions.process_column)
                        
                        # 「処理済み」以外の場合のみタスクを作成
                        if process_status != TaskStatus.COMPLETED.value:
                            task = TaskRow(
                                row_number=row_number,
                                copy_text=copy_text,
                                ai_config=ai_config,
                                column_positions=column_positions,
                                status=TaskStatus.PENDING,
                                created_at=datetime.now()
                            )
                            tasks.append(task)
                            
                            self.logger.debug(f"タスクを生成: 行{row_number}, 列{copy_column}, "
                                            f"AI={ai_config.ai_service.value}, テキスト長={len(copy_text)}")
                        else:
                            self.logger.debug(f"既に処理済みのセルをスキップ: {row_number}行目, {copy_column}列目")
                    
                    except Exception as e:
                        self.logger.error(f"タスク生成エラー (行{row_number}, 列{copy_column}): {e}")
                        continue
            
            self.logger.info(f"タスク生成完了: {len(tasks)}個のタスクを作成")
            return tasks
            
        except Exception as e:
            self.logger.error(f"タスク生成エラー: {e}")
            raise DataProcessingError(f"タスクの生成に失敗しました: {e}")
    
    def get_pending_tasks(self, config: SheetConfig) -> List[TaskRow]:
        """
        未処理タスクを取得
        
        Args:
            config: シート設定
        
        Returns:
            List[TaskRow]: 未処理タスクのリスト
        """
        try:
            # データを読み込み・検証
            sheet_data = self.load_and_validate_sheet(config)
            
            # タスクを生成
            tasks = self.create_task_rows(sheet_data)
            
            # 未処理タスクのみをフィルタ
            pending_tasks = [task for task in tasks if task.status == TaskStatus.PENDING]
            
            self.logger.info(f"未処理タスクを取得: {len(pending_tasks)}個")
            return pending_tasks
            
        except Exception as e:
            self.logger.error(f"未処理タスク取得エラー: {e}")
            raise DataProcessingError(f"未処理タスクの取得に失敗しました: {e}")
    
    def update_task_result(self, config: SheetConfig, task: TaskRow, result: str):
        """
        タスクの処理結果を更新
        
        Args:
            config: シート設定
            task: 更新対象タスク
            result: 処理結果
        """
        try:
            self.sheets_client.update_task_status(
                config, task, TaskStatus.COMPLETED, result=result
            )
            self.logger.info(f"タスク結果を更新: 行{task.row_number}, 列{task.column_positions.copy_column}")
            
        except Exception as e:
            self.logger.error(f"タスク結果更新エラー: {e}")
            raise DataProcessingError(f"タスク結果の更新に失敗しました: {e}")
    
    def mark_task_error(self, config: SheetConfig, task: TaskRow, error_message: str):
        """
        タスクをエラー状態に設定
        
        Args:
            config: シート設定
            task: 更新対象タスク
            error_message: エラーメッセージ
        """
        try:
            self.sheets_client.update_task_status(
                config, task, TaskStatus.ERROR, error_message=error_message
            )
            self.logger.info(f"タスクエラーを記録: 行{task.row_number}, 列{task.column_positions.copy_column}")
            
        except Exception as e:
            self.logger.error(f"タスクエラー記録エラー: {e}")
            raise DataProcessingError(f"タスクエラーの記録に失敗しました: {e}")
    
    def mark_task_in_progress(self, config: SheetConfig, task: TaskRow):
        """
        タスクを処理中状態に設定
        
        Args:
            config: シート設定
            task: 更新対象タスク
        """
        try:
            self.sheets_client.update_task_status(config, task, TaskStatus.IN_PROGRESS)
            self.logger.debug(f"タスクを処理中に設定: 行{task.row_number}, 列{task.column_positions.copy_column}")
            
        except Exception as e:
            self.logger.error(f"タスク状態更新エラー: {e}")
            raise DataProcessingError(f"タスク状態の更新に失敗しました: {e}")
    
    def create_processing_summary(self, tasks: List[TaskRow]) -> ProcessingResult:
        """
        処理結果のサマリーを作成
        
        Args:
            tasks: 処理対象タスクのリスト
        
        Returns:
            ProcessingResult: 処理結果サマリー
        """
        try:
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            error_tasks = len([t for t in tasks if t.status == TaskStatus.ERROR])
            skipped_tasks = total_tasks - completed_tasks - error_tasks
            
            # エラー詳細を収集
            error_details = {}
            for task in tasks:
                if task.status == TaskStatus.ERROR and task.error_message:
                    error_details[task.row_number] = task.error_message
            
            result = ProcessingResult(
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                error_tasks=error_tasks,
                skipped_tasks=skipped_tasks,
                start_time=datetime.now(),
                task_results=tasks.copy(),
                error_details=error_details
            )
            
            self.logger.info(f"処理サマリーを作成: 総数{total_tasks}, 完了{completed_tasks}, "
                           f"エラー{error_tasks}, スキップ{skipped_tasks}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"処理サマリー作成エラー: {e}")
            raise DataProcessingError(f"処理サマリーの作成に失敗しました: {e}")
    
    def validate_sheet_configuration(self, config: SheetConfig) -> Tuple[bool, List[str]]:
        """
        シート設定の妥当性を検証
        
        Args:
            config: 検証対象の設定
        
        Returns:
            Tuple[bool, List[str]]: (検証成功フラグ, エラーメッセージリスト)
        """
        try:
            return self.sheets_client.validate_sheet_structure(config)
        except Exception as e:
            self.logger.error(f"設定検証エラー: {e}")
            return False, [f"設定検証中にエラーが発生しました: {e}"]
    
    def _get_cell_value(self, sheet_data: SpreadsheetData, row: int, col: int) -> str:
        """
        指定されたセルの値を取得
        
        Args:
            sheet_data: スプレッドシートデータ
            row: 行番号（1ベース）
            col: 列番号（1ベース）
        
        Returns:
            str: セルの値（空の場合は空文字列）
        """
        try:
            row_idx = row - 1  # 0-based indexing
            col_idx = col - 1  # 0-based indexing
            
            if (row_idx < 0 or row_idx >= len(sheet_data.raw_data) or
                col_idx < 0):
                return ""
            
            row_data = sheet_data.raw_data[row_idx]
            if col_idx >= len(row_data):
                return ""
            
            return str(row_data[col_idx]) if row_data[col_idx] is not None else ""
            
        except Exception:
            return ""
    
    def load_column_ai_settings_from_config(self, config: SheetConfig, config_manager) -> bool:
        """
        設定ファイルから列毎AI設定を読み込み
        
        Args:
            config: シート設定
            config_manager: 設定マネージャー
            
        Returns:
            bool: 読み込み成功フラグ
        """
        try:
            column_ai_settings = config_manager.get("column_ai_settings", {})
            ai_mode = config_manager.get("ai_mode", "simple")
            
            # 列毎設定モードが有効な場合
            if ai_mode == "column" and column_ai_settings:
                config.use_column_ai_settings = True
                
                # 設定ファイルから列設定を読み込み
                for column_key, settings in column_ai_settings.items():
                    try:
                        # 列番号を取得（A=1, B=2, ...）
                        if column_key.isalpha():
                            copy_column = ColumnMapping._letter_to_number(column_key)
                        else:
                            copy_column = int(column_key)
                        
                        # AI設定を作成
                        ai_config = ColumnAIConfig(
                            ai_service=AIService(settings.get("ai_service", "chatgpt")),
                            ai_model=settings.get("model", "default"),
                            ai_mode=settings.get("mode"),
                            ai_features=settings.get("features", []) if isinstance(settings.get("features"), list) else [],
                            ai_settings=settings.get("settings", {})
                        )
                        
                        # 列マッピングを追加
                        config.add_column_mapping(copy_column, ai_config)
                        
                        self.logger.debug(f"列 {column_key} の設定を読み込み: {ai_config.ai_service.value}")
                        
                    except Exception as e:
                        self.logger.warning(f"列 {column_key} の設定読み込みでエラー: {e}")
                        continue
                
                self.logger.info(f"列毎AI設定を読み込み: {len(config.column_mappings)}列設定")
                return True
            else:
                config.use_column_ai_settings = False
                self.logger.info("シンプル選択モードを使用")
                return True
                
        except Exception as e:
            self.logger.error(f"列毎AI設定の読み込みエラー: {e}")
            config.use_column_ai_settings = False
            return False


# ファクトリー関数とユーティリティ
def create_data_handler(sheets_client: SheetsClient) -> DataHandler:
    """
    DataHandlerインスタンスを作成するファクトリー関数
    
    Args:
        sheets_client: Sheets APIクライアント
    
    Returns:
        DataHandler: 初期化済みのDataHandlerインスタンス
    """
    return DataHandler(sheets_client)


def extract_spreadsheet_id_from_url(url: str) -> str:
    """
    スプレッドシートURLからIDを抽出
    
    Args:
        url: スプレッドシートURL
    
    Returns:
        str: スプレッドシートID
    
    Raises:
        ValueError: 無効なURLの場合
    """
    if "/spreadsheets/d/" in url:
        return url.split("/spreadsheets/d/")[1].split("/")[0]
    else:
        raise ValueError("無効なスプレッドシートURLです")


# 使用例とテスト用のメイン関数
if __name__ == "__main__":
    import sys
    from .sheets_client import create_sheets_client
    from .auth_manager import AuthenticationError
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 3:
        print("使用方法: python data_handler.py <spreadsheet_url> <sheet_name>")
        sys.exit(1)
    
    spreadsheet_url = sys.argv[1]
    sheet_name = sys.argv[2]
    
    try:
        # データハンドラーの作成
        sheets_client = create_sheets_client()
        data_handler = create_data_handler(sheets_client)
        
        # 設定作成
        config = SheetConfig(
            spreadsheet_url=spreadsheet_url,
            sheet_name=sheet_name,
            spreadsheet_id=extract_spreadsheet_id_from_url(spreadsheet_url)
        )
        
        print(f"✅ DataHandlerが初期化されました")
        print(f"スプレッドシートID: {config.spreadsheet_id}")
        
        # 設定検証
        is_valid, errors = data_handler.validate_sheet_configuration(config)
        if not is_valid:
            print(f"❌ 設定検証エラー:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        
        print("✅ 設定検証成功")
        
        # 未処理タスクを取得
        pending_tasks = data_handler.get_pending_tasks(config)
        print(f"未処理タスク数: {len(pending_tasks)}")
        
        if pending_tasks:
            print("\n最初の5タスク:")
            for i, task in enumerate(pending_tasks[:5]):
                print(f"  タスク{i+1}: 行{task.row_number}, "
                      f"AI={task.ai_service.value}, "
                      f"テキスト='{task.copy_text[:50]}...'")
        
    except (AuthenticationError, SheetsAPIError, DataProcessingError) as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)