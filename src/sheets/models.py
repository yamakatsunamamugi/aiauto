"""
データ構造定義モジュール

Google Sheetsからの処理タスクとAI操作に関連するデータ構造を定義
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from typing import ForwardRef


class TaskStatus(Enum):
    """タスクの処理状態を表す列挙型"""
    PENDING = "未処理"          # 処理待ち
    IN_PROGRESS = "処理中"      # 処理実行中
    COMPLETED = "処理済み"      # 処理完了
    ERROR = "エラー"           # エラー発生


class AIService(Enum):
    """サポートするAIサービスの種類"""
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    GENSPARK = "genspark"
    GOOGLE_AI_STUDIO = "google_ai_studio"
    PERPLEXITY = "perplexity"


@dataclass
class ColumnPosition:
    """
    スプレッドシートの列位置情報
    
    「コピー」列を基準として、関連する列の位置を管理
    """
    copy_column: int         # 「コピー」列の位置（A=1, B=2...）
    process_column: int      # 処理列の位置（コピー列-2）
    error_column: int        # エラー列の位置（コピー列-1）
    result_column: int       # 結果列の位置（コピー列+1）
    
    def __post_init__(self):
        """データ検証: 列番号が1以上であることを確認"""
        if any(col < 1 for col in [self.copy_column, self.process_column, 
                                  self.error_column, self.result_column]):
            raise ValueError("列番号は1以上である必要があります")


@dataclass
class ColumnAIConfig:
    """
    列毎のAI設定情報
    
    個別の列に対して指定されるAIサービスとその設定
    """
    ai_service: AIService               # 使用するAIサービス
    ai_model: str                       # 使用するAIモデル名
    ai_mode: Optional[str] = None       # AIモード（creative、balanced、precise等）
    ai_features: Optional[List[str]] = None  # 使用する機能のリスト
    ai_settings: Optional[Dict[str, Any]] = None  # 追加設定
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.ai_features is None:
            self.ai_features = []
        if self.ai_settings is None:
            self.ai_settings = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "ai_service": self.ai_service.value,
            "ai_model": self.ai_model,
            "ai_mode": self.ai_mode,
            "ai_features": self.ai_features,
            "ai_settings": self.ai_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColumnAIConfig':
        """辞書から作成"""
        return cls(
            ai_service=AIService(data["ai_service"]),
            ai_model=data["ai_model"],
            ai_mode=data.get("ai_mode"),
            ai_features=data.get("ai_features", []),
            ai_settings=data.get("ai_settings", {})
        )


@dataclass
class TaskRow:
    """
    処理対象となる1行分のタスク情報
    
    スプレッドシートの1行から抽出された処理タスクの詳細情報
    """
    # 基本情報
    row_number: int                    # スプレッドシートの行番号
    copy_text: str                     # コピー対象のテキスト
    ai_config: ColumnAIConfig          # 使用するAI設定（新しい統合された設定）
    
    # 列位置情報
    column_positions: ColumnPosition   # 関連列の位置情報
    
    # 処理状態
    status: TaskStatus = TaskStatus.PENDING  # 処理状態
    result: Optional[str] = None             # AI処理結果
    error_message: Optional[str] = None      # エラーメッセージ
    
    # メタデータ
    created_at: datetime = None              # タスク作成日時
    processed_at: Optional[datetime] = None  # 処理完了日時
    retry_count: int = 0                     # リトライ回数
    
    # 後方互換性のためのプロパティ
    @property
    def ai_service(self) -> AIService:
        """後方互換性のためのai_service プロパティ"""
        return self.ai_config.ai_service
    
    @property 
    def ai_model(self) -> str:
        """後方互換性のためのai_model プロパティ"""
        return self.ai_config.ai_model
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def mark_in_progress(self):
        """処理中状態に変更"""
        self.status = TaskStatus.IN_PROGRESS
        self.processed_at = datetime.now()
    
    def mark_completed(self, result: str):
        """処理完了状態に変更"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.processed_at = datetime.now()
    
    def mark_error(self, error_message: str):
        """エラー状態に変更"""
        self.status = TaskStatus.ERROR
        self.error_message = error_message
        self.processed_at = datetime.now()
    
    def increment_retry(self):
        """リトライ回数を増加"""
        self.retry_count += 1


@dataclass 
class ColumnMapping:
    """
    列の位置とAI設定のマッピング情報
    
    スプレッドシートの列番号とその列で使用するAI設定の組み合わせ
    """
    column_letter: str                  # 列記号（A, B, C...）
    column_number: int                  # 列番号（1, 2, 3...）
    column_positions: ColumnPosition    # 関連列の位置情報
    ai_config: ColumnAIConfig          # この列で使用するAI設定
    is_active: bool = True             # この列が処理対象かどうか
    
    def __post_init__(self):
        """初期化後の検証"""
        # 列番号と列記号の整合性チェック
        expected_letter = self._number_to_letter(self.column_number)
        if self.column_letter.upper() != expected_letter:
            raise ValueError(f"列番号 {self.column_number} に対応する列記号は {expected_letter} ですが、{self.column_letter} が指定されました")
    
    @staticmethod
    def _number_to_letter(column_number: int) -> str:
        """列番号を列記号に変換（A=1, B=2, ...）"""
        result = ""
        while column_number > 0:
            column_number -= 1
            result = chr(column_number % 26 + ord('A')) + result
            column_number //= 26
        return result
    
    @staticmethod
    def _letter_to_number(column_letter: str) -> int:
        """列記号を列番号に変換（A=1, B=2, ...）"""
        result = 0
        for char in column_letter.upper():
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result
    
    @classmethod
    def create_from_copy_column(cls, copy_column_number: int, ai_config: ColumnAIConfig) -> 'ColumnMapping':
        """コピー列番号からColumnMappingを作成"""
        column_letter = cls._number_to_letter(copy_column_number)
        column_positions = ColumnPosition(
            copy_column=copy_column_number,
            process_column=copy_column_number - 2,
            error_column=copy_column_number - 1,
            result_column=copy_column_number + 1
        )
        
        return cls(
            column_letter=column_letter,
            column_number=copy_column_number,
            column_positions=column_positions,
            ai_config=ai_config
        )


@dataclass
class SheetConfig:
    """
    スプレッドシート設定情報
    
    処理対象のスプレッドシートの設定と動作パラメータ
    """
    # スプレッドシート情報
    spreadsheet_url: str               # スプレッドシートのURL
    spreadsheet_id: str                # スプレッドシートID（URLから抽出）
    sheet_name: str                    # 対象シート名
    
    # 処理設定
    work_header_row: int = 5           # 「作業」ヘッダーが含まれる行番号
    start_row: int = 6                 # データ処理開始行（通常はヘッダー行+1）
    
    # AI設定
    default_ai_service: AIService = AIService.CHATGPT  # デフォルトAI
    ai_configs: Dict[str, Dict[str, Any]] = None       # AIごとの設定
    column_mappings: List[ColumnMapping] = None        # 列毎のAI設定マッピング
    use_column_ai_settings: bool = False               # 列毎AI設定を使用するかどうか
    
    def __post_init__(self):
        """初期化後の処理"""
        # スプレッドシートIDをURLから抽出
        if "/spreadsheets/d/" in self.spreadsheet_url:
            self.spreadsheet_id = self.spreadsheet_url.split("/spreadsheets/d/")[1].split("/")[0]
        else:
            raise ValueError("無効なスプレッドシートURLです")
        
        # AI設定の初期化
        if self.ai_configs is None:
            self.ai_configs = {}
        if self.column_mappings is None:
            self.column_mappings = []
    
    def add_column_mapping(self, copy_column_number: int, ai_config: ColumnAIConfig):
        """列マッピングを追加"""
        mapping = ColumnMapping.create_from_copy_column(copy_column_number, ai_config)
        
        # 既存のマッピングを削除（同じ列番号の場合）
        self.column_mappings = [m for m in self.column_mappings if m.column_number != copy_column_number]
        
        # 新しいマッピングを追加
        self.column_mappings.append(mapping)
    
    def get_column_mapping(self, copy_column_number: int) -> Optional[ColumnMapping]:
        """指定した列番号のマッピングを取得"""
        for mapping in self.column_mappings:
            if mapping.column_number == copy_column_number:
                return mapping
        return None
    
    def get_ai_config_for_column(self, copy_column_number: int) -> ColumnAIConfig:
        """指定した列のAI設定を取得（なければデフォルト設定）"""
        mapping = self.get_column_mapping(copy_column_number)
        if mapping and self.use_column_ai_settings:
            return mapping.ai_config
        
        # デフォルト設定を返す
        return ColumnAIConfig(
            ai_service=self.default_ai_service,
            ai_model=self._get_default_model(self.default_ai_service)
        )
    
    def _get_default_model(self, ai_service: AIService) -> str:
        """AIサービスのデフォルトモデルを取得"""
        defaults = {
            AIService.CHATGPT: "gpt-4",
            AIService.CLAUDE: "claude-3-sonnet",
            AIService.GEMINI: "gemini-pro",
            AIService.GENSPARK: "default",
            AIService.GOOGLE_AI_STUDIO: "gemini-pro",
            AIService.PERPLEXITY: "claude-sonnet-4"
        }
        return defaults.get(ai_service, "default")


@dataclass
class ProcessingResult:
    """
    処理結果の統計情報
    
    一連の処理が完了した後の結果サマリー
    """
    total_tasks: int                   # 総タスク数
    completed_tasks: int               # 完了タスク数
    error_tasks: int                   # エラータスク数
    skipped_tasks: int                 # スキップされたタスク数
    
    # 処理時間
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # 詳細結果
    task_results: List[TaskRow] = None  # 個別タスクの結果
    error_details: Dict[int, str] = None  # エラー詳細（行番号: エラーメッセージ）
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.task_results is None:
            self.task_results = []
        if self.error_details is None:
            self.error_details = {}
    
    @property
    def success_rate(self) -> float:
        """成功率を計算"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def processing_time(self) -> Optional[float]:
        """処理時間を秒単位で計算"""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()
    
    def mark_completed(self):
        """処理完了をマーク"""
        self.end_time = datetime.now()


@dataclass
class ValidationError:
    """データ検証エラー情報"""
    row_number: int
    column: str
    error_type: str
    message: str
    suggestion: Optional[str] = None


class SpreadsheetData:
    """
    スプレッドシートの全データを管理するクラス
    
    読み込んだスプレッドシートデータの構造化と検証を行う
    """
    
    def __init__(self, sheet_config: SheetConfig):
        self.config = sheet_config
        self.raw_data: List[List[str]] = []  # 生データ
        self.header_row: List[str] = []      # ヘッダー行
        self.copy_columns: List[int] = []    # 「コピー」列の位置リスト
        self.task_rows: List[TaskRow] = []   # 処理対象タスク
        self.validation_errors: List[ValidationError] = []  # 検証エラー
    
    def set_raw_data(self, data: List[List[str]]):
        """生データを設定"""
        self.raw_data = data
        self._validate_structure()
    
    def _validate_structure(self):
        """データ構造の検証"""
        self.validation_errors.clear()
        
        # 最小行数の確認
        if len(self.raw_data) < self.config.work_header_row:
            self.validation_errors.append(
                ValidationError(
                    row_number=0,
                    column="全体",
                    error_type="INSUFFICIENT_ROWS",
                    message=f"スプレッドシートの行数が不足しています（必要: {self.config.work_header_row}行以上）"
                )
            )
            return
        
        # ヘッダー行の取得
        if len(self.raw_data) >= self.config.work_header_row:
            self.header_row = self.raw_data[self.config.work_header_row - 1]
        
        # 「作業」セルの確認
        if len(self.header_row) == 0 or self.header_row[0] != "作業":
            self.validation_errors.append(
                ValidationError(
                    row_number=self.config.work_header_row,
                    column="A",
                    error_type="MISSING_WORK_HEADER",
                    message=f"{self.config.work_header_row}行目のA列に「作業」が見つかりません",
                    suggestion="A列に「作業」という文字列を入力してください"
                )
            )
    
    def find_copy_columns(self) -> List[int]:
        """「コピー」列を全て特定"""
        self.copy_columns = []
        
        for i, cell_value in enumerate(self.header_row):
            if cell_value == "コピー":
                self.copy_columns.append(i + 1)  # 1-based indexing
        
        if not self.copy_columns:
            self.validation_errors.append(
                ValidationError(
                    row_number=self.config.work_header_row,
                    column="全体",
                    error_type="NO_COPY_COLUMNS",
                    message="「コピー」列が見つかりません",
                    suggestion="ヘッダー行に「コピー」という列を追加してください"
                )
            )
        
        return self.copy_columns
    
    def get_processing_rows(self) -> List[int]:
        """処理対象行番号のリストを取得"""
        processing_rows = []
        
        start_idx = self.config.start_row - 1  # 0-based indexing
        
        for i in range(start_idx, len(self.raw_data)):
            row = self.raw_data[i]
            
            # A列が空白なら処理終了
            if len(row) == 0 or not row[0].strip():
                break
            
            # A列が数字（連番）なら処理対象
            if row[0].strip().isdigit():
                processing_rows.append(i + 1)  # 1-based row number
        
        return processing_rows
    
    def is_valid(self) -> bool:
        """データが有効かどうかを判定"""
        return len(self.validation_errors) == 0
    
    def get_validation_summary(self) -> str:
        """検証結果のサマリーを取得"""
        if self.is_valid():
            return f"✅ データ検証成功: {len(self.copy_columns)}個のコピー列、{len(self.get_processing_rows())}行の処理対象"
        else:
            error_count = len(self.validation_errors)
            return f"❌ データ検証エラー: {error_count}個のエラーが見つかりました"