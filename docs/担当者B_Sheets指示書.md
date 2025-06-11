# 担当者B: Google Sheets連携 専用指示書

## 🎯 あなたの役割
**Google Sheets APIを使用したデータ連携システム構築**
- Google Sheets認証・アクセス管理
- スプレッドシートデータの読み書き
- データ構造の設計・管理
- エラーハンドリング・例外処理

## 📁 あなたが編集するファイル

### メインファイル
```
src/sheets/
├── sheets_client.py      # 🔥 Google Sheets API操作
├── data_handler.py       # 🔥 データ処理・変換
├── auth_manager.py       # 🔥 認証管理
└── models.py             # 🔥 データ構造定義

config/
├── credentials.json      # 🔥 Google API認証情報（作成）
└── sheets_config.json    # 🔥 Sheets固有設定（作成）
```

### サポートファイル（必要に応じて編集）
```
tests/test_sheets.py      # テストファイル（作成）
docs/SHEETS_API_GUIDE.md  # API使用方法ドキュメント（作成）
```

## 🚀 作業開始手順

### 1日目: Google API設定
```bash
# Git準備
git checkout feature/sheets-integration
git pull origin develop
git merge develop

# ディレクトリ作成
mkdir -p src/sheets config tests
touch src/sheets/__init__.py
```

### Google Cloud Console設定（重要）
1. **プロジェクト作成**
   - https://console.cloud.google.com/ にアクセス
   - 「新しいプロジェクト」作成
   - プロジェクト名: "ai-automation-tool"

2. **Google Sheets API有効化**
   - 「APIとサービス」→「ライブラリ」
   - "Google Sheets API" を検索
   - 「有効にする」をクリック

3. **サービスアカウント作成**
   - 「APIとサービス」→「認証情報」
   - 「認証情報を作成」→「サービスアカウント」
   - サービスアカウント名: "sheets-automation"
   - 役割: "編集者"

4. **認証JSONダウンロード**
   - 作成されたサービスアカウントをクリック
   - 「キー」タブ→「キーを追加」→「JSON」
   - ダウンロードしたファイルを `config/credentials.json` として保存

### 2-3日目: 認証システム実装
```python
# src/sheets/auth_manager.py
import os
import json
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from src.utils.logger import logger

class AuthManager:
    """Google Sheets API認証管理"""
    
    def __init__(self, credentials_path: str = "config/credentials.json"):
        self.credentials_path = credentials_path
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        self.credentials: Optional[Credentials] = None
        self.service = None
    
    def authenticate(self) -> bool:
        """
        Google Sheets API認証を実行
        
        Returns:
            bool: 認証成功の可否
        """
        try:
            if not os.path.exists(self.credentials_path):
                logger.error(f"認証ファイルが見つかりません: {self.credentials_path}")
                return False
            
            # サービスアカウント認証
            self.credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.scopes
            )
            
            # Google Sheets APIサービス構築
            self.service = build('sheets', 'v4', credentials=self.credentials)
            
            logger.info("Google Sheets API認証成功")
            return True
            
        except Exception as e:
            logger.error(f"認証エラー: {str(e)}")
            return False
    
    def check_permissions(self, spreadsheet_url: str) -> bool:
        """
        スプレッドシートへのアクセス権限確認
        
        Args:
            spreadsheet_url (str): スプレッドシートURL
            
        Returns:
            bool: アクセス可能か
        """
        try:
            spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_url)
            if not spreadsheet_id:
                return False
            
            # スプレッドシートの基本情報取得を試行
            self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            logger.info(f"スプレッドシートアクセス確認: {spreadsheet_id}")
            return True
            
        except Exception as e:
            logger.error(f"アクセス権限エラー: {str(e)}")
            return False
    
    def extract_spreadsheet_id(self, url: str) -> Optional[str]:
        """
        URLからスプレッドシートIDを抽出
        
        Args:
            url (str): GoogleスプレッドシートURL
            
        Returns:
            Optional[str]: スプレッドシートID
        """
        try:
            # URL形式: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
            if '/spreadsheets/d/' in url:
                start = url.find('/spreadsheets/d/') + len('/spreadsheets/d/')
                end = url.find('/', start)
                if end == -1:
                    end = url.find('#', start)
                if end == -1:
                    end = len(url)
                
                spreadsheet_id = url[start:end]
                logger.debug(f"抽出されたスプレッドシートID: {spreadsheet_id}")
                return spreadsheet_id
                
        except Exception as e:
            logger.error(f"スプレッドシートID抽出エラー: {str(e)}")
        
        return None
    
    def get_service(self):
        """Google Sheets APIサービスを取得"""
        if not self.service:
            if not self.authenticate():
                raise Exception("Google Sheets API認証に失敗しました")
        return self.service
```

### 4-5日目: データ構造定義
```python
# src/sheets/models.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class TaskStatus(Enum):
    """タスク状態"""
    PENDING = "未処理"
    IN_PROGRESS = "処理中"
    COMPLETED = "処理済み"
    ERROR = "エラー"

@dataclass
class TaskRow:
    """処理対象行のデータ構造"""
    row_number: int                    # 行番号
    copy_text: str                     # コピー対象のテキスト
    ai_service: str                    # 使用するAIサービス
    ai_model: str                      # 使用するAIモデル
    copy_column: int                   # コピー列の番号
    process_column: int                # 処理列の番号（コピー列-2）
    error_column: int                  # エラー列の番号（コピー列-1）
    result_column: int                 # 結果列の番号（コピー列+1）
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class SheetConfig:
    """シート設定情報"""
    spreadsheet_url: str
    sheet_name: str
    spreadsheet_id: str
    header_row: int = 5                # 作業指示行（デフォルト5行目）
    work_column: str = 'A'             # 作業列（デフォルトA列）
    copy_columns: List[int] = field(default_factory=list)  # コピー列一覧

@dataclass
class ProcessingResult:
    """処理結果データ"""
    total_tasks: int
    completed_tasks: int
    error_tasks: int
    processing_time: float
    errors: List[Dict[str, Any]] = field(default_factory=list)
```

### 6-7日目: Sheets API操作実装
```python
# src/sheets/sheets_client.py
from typing import List, Dict, Any, Optional, Tuple
from googleapiclient.errors import HttpError
from src.sheets.auth_manager import AuthManager
from src.sheets.models import SheetConfig, TaskRow, TaskStatus
from src.utils.logger import logger

class SheetsClient:
    """Google Sheets API操作クラス"""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth = auth_manager
        self.service = None
    
    def _get_service(self):
        """Google Sheets APIサービス取得"""
        if not self.service:
            self.service = self.auth.get_service()
        return self.service
    
    def get_sheet_names(self, spreadsheet_url: str) -> List[str]:
        """
        スプレッドシートのシート名一覧を取得
        
        Args:
            spreadsheet_url (str): スプレッドシートURL
            
        Returns:
            List[str]: シート名一覧
        """
        try:
            spreadsheet_id = self.auth.extract_spreadsheet_id(spreadsheet_url)
            if not spreadsheet_id:
                raise ValueError("無効なスプレッドシートURL")
            
            service = self._get_service()
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            
            sheet_names = []
            for sheet in spreadsheet.get('sheets', []):
                sheet_name = sheet['properties']['title']
                sheet_names.append(sheet_name)
            
            logger.info(f"シート名一覧取得完了: {sheet_names}")
            return sheet_names
            
        except HttpError as e:
            logger.error(f"Sheets API エラー: {e}")
            raise Exception(f"スプレッドシートアクセスエラー: {e}")
        except Exception as e:
            logger.error(f"シート名取得エラー: {e}")
            raise
    
    def read_range(self, spreadsheet_url: str, range_name: str) -> List[List[str]]:
        """
        指定範囲のデータを読み取り
        
        Args:
            spreadsheet_url (str): スプレッドシートURL
            range_name (str): 範囲指定（例: "Sheet1!A1:Z100"）
            
        Returns:
            List[List[str]]: セルデータ（2次元配列）
        """
        try:
            spreadsheet_id = self.auth.extract_spreadsheet_id(spreadsheet_url)
            service = self._get_service()
            
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueRenderOption='UNFORMATTED_VALUE'
            ).execute()
            
            values = result.get('values', [])
            logger.debug(f"データ読み取り完了: {range_name}, 行数: {len(values)}")
            return values
            
        except Exception as e:
            logger.error(f"データ読み取りエラー: {e}")
            raise
    
    def write_range(self, spreadsheet_url: str, range_name: str, 
                   data: List[List[Any]], value_input_option: str = 'RAW'):
        """
        指定範囲にデータを書き込み
        
        Args:
            spreadsheet_url (str): スプレッドシートURL
            range_name (str): 範囲指定
            data (List[List[Any]]): 書き込みデータ
            value_input_option (str): 入力オプション（RAW/USER_ENTERED）
        """
        try:
            spreadsheet_id = self.auth.extract_spreadsheet_id(spreadsheet_url)
            service = self._get_service()
            
            body = {
                'values': data
            }
            
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            logger.info(f"データ書き込み完了: {range_name}, 更新セル数: {updated_cells}")
            
        except Exception as e:
            logger.error(f"データ書き込みエラー: {e}")
            raise
    
    def write_cell(self, spreadsheet_url: str, cell_address: str, value: Any):
        """
        単一セルに値を書き込み
        
        Args:
            spreadsheet_url (str): スプレッドシートURL
            cell_address (str): セルアドレス（例: "A1"）
            value (Any): 書き込み値
        """
        self.write_range(spreadsheet_url, cell_address, [[value]])
    
    def batch_update(self, spreadsheet_url: str, updates: List[Dict[str, Any]]):
        """
        一括更新処理
        
        Args:
            spreadsheet_url (str): スプレッドシートURL
            updates (List[Dict]): 更新データ一覧
        """
        try:
            spreadsheet_id = self.auth.extract_spreadsheet_id(spreadsheet_url)
            service = self._get_service()
            
            body = {
                'valueInputOption': 'RAW',
                'data': updates
            }
            
            result = service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            total_updated = result.get('totalUpdatedCells', 0)
            logger.info(f"一括更新完了: 更新セル数: {total_updated}")
            
        except Exception as e:
            logger.error(f"一括更新エラー: {e}")
            raise
```

### 8-10日目: データ処理ロジック実装
```python
# src/sheets/data_handler.py
import re
from typing import List, Tuple, Optional
from datetime import datetime
from src.sheets.sheets_client import SheetsClient
from src.sheets.models import SheetConfig, TaskRow, TaskStatus
from src.utils.logger import logger

class DataHandler:
    """スプレッドシートデータ処理クラス"""
    
    def __init__(self, sheets_client: SheetsClient):
        self.client = sheets_client
    
    def find_work_header_row(self, spreadsheet_url: str, sheet_name: str) -> int:
        """
        「作業」列を含む行を特定
        
        Args:
            spreadsheet_url (str): スプレッドシートURL
            sheet_name (str): シート名
            
        Returns:
            int: ヘッダー行番号（1ベース）
        """
        try:
            # A列を1行目から20行目まで検索
            range_name = f"{sheet_name}!A1:A20"
            values = self.client.read_range(spreadsheet_url, range_name)
            
            for row_num, row_data in enumerate(values, 1):
                if row_data and len(row_data) > 0:
                    cell_value = str(row_data[0]).strip()
                    if cell_value == "作業":
                        logger.info(f"作業ヘッダー行を発見: {row_num}行目")
                        return row_num
            
            # デフォルトは5行目
            logger.warning("作業ヘッダー行が見つからないため、5行目を使用")
            return 5
            
        except Exception as e:
            logger.error(f"ヘッダー行検索エラー: {e}")
            return 5
    
    def find_copy_columns(self, spreadsheet_url: str, sheet_name: str, 
                         header_row: int) -> List[int]:
        """
        「コピー」列を全て特定
        
        Args:
            spreadsheet_url (str): スプレッドシートURL
            sheet_name (str): シート名
            header_row (int): ヘッダー行番号
            
        Returns:
            List[int]: コピー列番号一覧（1ベース）
        """
        try:
            # ヘッダー行を全列読み取り（A-Z, AA-AZ）
            range_name = f"{sheet_name}!{header_row}:{header_row}"
            values = self.client.read_range(spreadsheet_url, range_name)
            
            copy_columns = []
            if values and len(values) > 0:
                row_data = values[0]
                for col_num, cell_value in enumerate(row_data, 1):
                    if str(cell_value).strip() == "コピー":
                        copy_columns.append(col_num)
                        logger.info(f"コピー列発見: {col_num}列目")
            
            if not copy_columns:
                logger.warning("コピー列が見つかりませんでした")
            
            return copy_columns
            
        except Exception as e:
            logger.error(f"コピー列検索エラー: {e}")
            return []
    
    def get_task_rows(self, config: SheetConfig) -> List[TaskRow]:
        """
        処理対象行を全て取得
        
        Args:
            config (SheetConfig): シート設定
            
        Returns:
            List[TaskRow]: タスク行一覧
        """
        try:
            tasks = []
            
            # A列の連番を確認（1から開始）
            range_name = f"{config.sheet_name}!A:A"
            a_column_values = self.client.read_range(config.spreadsheet_url, range_name)
            
            # 処理対象行を特定
            target_rows = []
            for row_num, row_data in enumerate(a_column_values, 1):
                if row_data and len(row_data) > 0:
                    cell_value = str(row_data[0]).strip()
                    if cell_value.isdigit():
                        target_rows.append(row_num)
                    elif target_rows:  # 連番が途切れたら終了
                        break
            
            logger.info(f"処理対象行: {len(target_rows)}行")
            
            # 各コピー列について TaskRow を作成
            for copy_col in config.copy_columns:
                process_col = copy_col - 2  # 処理列
                error_col = copy_col - 1    # エラー列
                result_col = copy_col + 1   # 結果列
                
                # 境界チェック
                if process_col < 1:
                    logger.warning(f"処理列が範囲外: コピー列{copy_col}")
                    continue
                
                for row_num in target_rows:
                    # コピー列のテキスト取得
                    copy_cell = self._number_to_column(copy_col) + str(row_num)
                    copy_range = f"{config.sheet_name}!{copy_cell}"
                    copy_data = self.client.read_range(config.spreadsheet_url, copy_range)
                    
                    copy_text = ""
                    if copy_data and len(copy_data) > 0 and len(copy_data[0]) > 0:
                        copy_text = str(copy_data[0][0]).strip()
                    
                    if copy_text:  # コピーテキストがある場合のみタスク作成
                        # 処理状態確認
                        process_cell = self._number_to_column(process_col) + str(row_num)
                        process_range = f"{config.sheet_name}!{process_cell}"
                        process_data = self.client.read_range(config.spreadsheet_url, process_range)
                        
                        status = TaskStatus.PENDING
                        if process_data and len(process_data) > 0 and len(process_data[0]) > 0:
                            status_value = str(process_data[0][0]).strip()
                            if status_value == "処理済み":
                                status = TaskStatus.COMPLETED
                            elif status_value == "処理中":
                                status = TaskStatus.IN_PROGRESS
                            elif status_value == "エラー":
                                status = TaskStatus.ERROR
                        
                        task = TaskRow(
                            row_number=row_num,
                            copy_text=copy_text,
                            ai_service="",  # GUIで設定される
                            ai_model="",    # GUIで設定される
                            copy_column=copy_col,
                            process_column=process_col,
                            error_column=error_col,
                            result_column=result_col,
                            status=status,
                            created_at=datetime.now().isoformat()
                        )
                        tasks.append(task)
            
            logger.info(f"タスク生成完了: {len(tasks)}件")
            return tasks
            
        except Exception as e:
            logger.error(f"タスク行取得エラー: {e}")
            return []
    
    def update_task_status(self, config: SheetConfig, task: TaskRow, 
                          status: TaskStatus, result: str = None, error: str = None):
        """
        タスク状態をスプレッドシートに更新
        
        Args:
            config (SheetConfig): シート設定
            task (TaskRow): 対象タスク
            status (TaskStatus): 新しい状態
            result (str): 処理結果（任意）
            error (str): エラーメッセージ（任意）
        """
        try:
            updates = []
            
            # 処理列更新
            process_cell = f"{config.sheet_name}!" + \
                          self._number_to_column(task.process_column) + str(task.row_number)
            updates.append({
                'range': process_cell,
                'values': [[status.value]]
            })
            
            # エラー列更新
            if error:
                error_cell = f"{config.sheet_name}!" + \
                           self._number_to_column(task.error_column) + str(task.row_number)
                updates.append({
                    'range': error_cell,
                    'values': [[error]]
                })
            
            # 結果列更新
            if result:
                result_cell = f"{config.sheet_name}!" + \
                            self._number_to_column(task.result_column) + str(task.row_number)
                updates.append({
                    'range': result_cell,
                    'values': [[result]]
                })
            
            # 一括更新実行
            if updates:
                self.client.batch_update(config.spreadsheet_url, updates)
                task.status = status
                task.result = result
                task.error_message = error
                task.updated_at = datetime.now().isoformat()
                logger.info(f"タスク状態更新完了: 行{task.row_number}, 状態:{status.value}")
            
        except Exception as e:
            logger.error(f"タスク状態更新エラー: {e}")
            raise
    
    def _number_to_column(self, num: int) -> str:
        """
        列番号をExcel列名に変換（1=A, 2=B, ..., 27=AA）
        
        Args:
            num (int): 列番号（1ベース）
            
        Returns:
            str: Excel列名
        """
        result = ""
        while num > 0:
            num -= 1
            result = chr(ord('A') + num % 26) + result
            num //= 26
        return result
    
    def create_sheet_config(self, spreadsheet_url: str, sheet_name: str) -> SheetConfig:
        """
        シート設定を作成
        
        Args:
            spreadsheet_url (str): スプレッドシートURL
            sheet_name (str): シート名
            
        Returns:
            SheetConfig: シート設定オブジェクト
        """
        try:
            spreadsheet_id = self.client.auth.extract_spreadsheet_id(spreadsheet_url)
            header_row = self.find_work_header_row(spreadsheet_url, sheet_name)
            copy_columns = self.find_copy_columns(spreadsheet_url, sheet_name, header_row)
            
            config = SheetConfig(
                spreadsheet_url=spreadsheet_url,
                sheet_name=sheet_name,
                spreadsheet_id=spreadsheet_id,
                header_row=header_row,
                copy_columns=copy_columns
            )
            
            logger.info(f"シート設定作成完了: {sheet_name}")
            return config
            
        except Exception as e:
            logger.error(f"シート設定作成エラー: {e}")
            raise
```

## 🔗 他担当との連携

### 担当者Aに提供するインターフェース
```python
# 担当者A（GUI）が呼び出す関数
def get_sheet_names(self, url: str) -> List[str]:
    """GUIのシート選択コンボボックス用"""
    return self.sheets_client.get_sheet_names(url)

def get_column_headers(self, url: str, sheet: str) -> List[str]:
    """GUI設定画面用"""
    config = self.data_handler.create_sheet_config(url, sheet)
    return self.sheets_client.read_range(url, f"{sheet}!{config.header_row}:{config.header_row}")[0]

def validate_spreadsheet_access(self, url: str) -> bool:
    """アクセス権限確認"""
    return self.auth_manager.check_permissions(url)
```

### 担当者Cに提供するインターフェース
```python
# 担当者C（自動化）が呼び出す関数
def get_pending_tasks(self, config: SheetConfig) -> List[TaskRow]:
    """未処理タスク一覧を提供"""
    all_tasks = self.data_handler.get_task_rows(config)
    return [task for task in all_tasks if task.status == TaskStatus.PENDING]

def update_task_result(self, config: SheetConfig, task: TaskRow, result: str):
    """処理結果を受け取って更新"""
    self.data_handler.update_task_status(config, task, TaskStatus.COMPLETED, result=result)

def mark_task_error(self, config: SheetConfig, task: TaskRow, error_message: str):
    """エラー状態を更新"""
    self.data_handler.update_task_status(config, task, TaskStatus.ERROR, error=error_message)

def mark_task_in_progress(self, config: SheetConfig, task: TaskRow):
    """処理中状態を更新"""
    self.data_handler.update_task_status(config, task, TaskStatus.IN_PROGRESS)
```

## 🧪 テスト方法

### 認証テスト
```python
# tests/test_auth.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sheets.auth_manager import AuthManager

def test_authentication():
    auth = AuthManager()
    result = auth.authenticate()
    print(f"認証テスト: {'成功' if result else '失敗'}")
    return result

def test_spreadsheet_access():
    auth = AuthManager()
    auth.authenticate()
    
    # テスト用スプレッドシートURL
    test_url = "https://docs.google.com/spreadsheets/d/YOUR_TEST_SPREADSHEET_ID/edit"
    result = auth.check_permissions(test_url)
    print(f"アクセステスト: {'成功' if result else '失敗'}")
    return result

if __name__ == "__main__":
    test_authentication()
    test_spreadsheet_access()
```

### データ処理テスト
```python
# tests/test_data_handler.py
from src.sheets.auth_manager import AuthManager
from src.sheets.sheets_client import SheetsClient
from src.sheets.data_handler import DataHandler

def test_sheet_config_creation():
    auth = AuthManager()
    auth.authenticate()
    
    client = SheetsClient(auth)
    handler = DataHandler(client)
    
    # テスト用URL・シート名
    test_url = "YOUR_TEST_SPREADSHEET_URL"
    test_sheet = "Sheet1"
    
    config = handler.create_sheet_config(test_url, test_sheet)
    print(f"シート設定: {config}")
    
    tasks = handler.get_task_rows(config)
    print(f"タスク数: {len(tasks)}")
    
    for task in tasks[:3]:  # 最初の3件表示
        print(f"タスク: 行{task.row_number}, テキスト: {task.copy_text[:50]}...")

if __name__ == "__main__":
    test_sheet_config_creation()
```

## 📅 開発スケジュール

### 第1週: API基盤構築
- [x] Google Cloud Console設定
- [ ] 認証システム実装（auth_manager.py）
- [ ] 基本API操作実装（sheets_client.py）
- [ ] データモデル定義（models.py）

### 第2週: データ処理システム
- [ ] データ処理ロジック実装（data_handler.py）
- [ ] 「作業」行・「コピー」列検索機能
- [ ] タスク生成・状態管理機能
- [ ] エラーハンドリング強化

### 第3週: 統合・テスト
- [ ] 担当者A・Cとの連携確認
- [ ] パフォーマンス最適化
- [ ] エッジケース対応

## ⚠️ 重要な注意点

### セキュリティ
- **credentials.jsonをGitにコミットしない**
- **テスト用スプレッドシートのみ使用**
- **本番データに誤ってアクセスしない**

### パフォーマンス
- **API呼び出し回数の最小化**
- **一括更新の活用**
- **適切なキャッシュ戦略**

### エラーハンドリング
- **Google API制限への対応**
- **ネットワークエラーの処理**
- **データ形式の検証**

## 📝 日次報告テンプレート

```
【担当者B - Sheets】日次報告
日付: 2024/XX/XX

完了した作業:
- Google Sheets API認証システム実装
- 基本的なデータ読み書き機能実装

明日の予定:
- データ処理ロジック実装
- 「コピー」列検索機能の完成

困っている点:
- Google API制限の詳細仕様について

他担当への依頼:
- 担当者A: シート選択UIでの戻り値形式確認
- 担当者C: TaskRowデータ形式の要件確認
```

## 🔧 テスト用スプレッドシート作成

### サンプルデータ形式
```
A     B      C      D      E      F      G
1
2
3
4
5   作業   処理1   エラー1  コピー1  結果1   処理2
6    1     未処理          サンプル1        未処理
7    2     未処理          サンプル2        未処理
8    3     処理済み        サンプル3  結果3  未処理
```

### スプレッドシート共有設定
1. 作成したテスト用スプレッドシートを開く
2. 「共有」ボタンをクリック
3. サービスアカウントのメールアドレスを追加
4. 権限を「編集者」に設定

**頑張ってください！Google Sheets APIは複雑ですが、しっかりとしたドキュメントがあるので、困った時は遠慮なく質問してください。**