"""
Sheetsデータモデル（テスト用モック）
本実装は担当者Bが実装予定
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class AIService(Enum):
    """AIサービス種別"""
    CHATGPT = "chatgpt"
    CLAUDE = "claude" 
    GEMINI = "gemini"
    GENSPARK = "genspark"
    GOOGLE_AI_STUDIO = "google_ai_studio"


@dataclass
class ColumnAIConfig:
    """列毎AI設定"""
    ai_service: AIService
    ai_model: str = "default"
    ai_mode: str = "default"
    ai_features: List[str] = None
    ai_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.ai_features is None:
            self.ai_features = []
        if self.ai_settings is None:
            self.ai_settings = {}


@dataclass
class ColumnPositions:
    """列位置情報"""
    copy_column: int
    process_column: int
    error_column: int
    result_column: int


@dataclass
class TaskRow:
    """タスク行データ"""
    row_number: int
    copy_text: str
    ai_config: ColumnAIConfig
    column_positions: ColumnPositions
    status: str = "未処理"
    result: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SheetConfig:
    """シート設定"""
    spreadsheet_url: str
    sheet_name: str
    spreadsheet_id: str = ""
    
    def __post_init__(self):
        if not self.spreadsheet_id and self.spreadsheet_url:
            # URLからスプレッドシートIDを抽出（簡易版）
            if "/spreadsheets/d/" in self.spreadsheet_url:
                self.spreadsheet_id = self.spreadsheet_url.split("/spreadsheets/d/")[1].split("/")[0]


@dataclass 
class SheetData:
    """シートデータ"""
    config: SheetConfig
    headers: List[str]
    data_rows: List[List[str]]
    copy_columns: List[int]