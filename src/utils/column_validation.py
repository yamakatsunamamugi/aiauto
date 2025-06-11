"""
列設定検証ユーティリティモジュール

列毎AI設定の検証と エラーハンドリングを提供
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.sheets.models import AIService, ColumnAIConfig
from src.utils.column_utils import column_letter_to_number, column_number_to_letter, get_copy_column_positions


class ValidationLevel(Enum):
    """検証レベル"""
    ERROR = "error"      # 処理を続行できないエラー
    WARNING = "warning"  # 注意が必要だが続行可能
    INFO = "info"        # 情報のみ


@dataclass
class ValidationResult:
    """検証結果"""
    level: ValidationLevel
    message: str
    column: Optional[str] = None
    suggestion: Optional[str] = None
    error_code: Optional[str] = None


class ColumnConfigValidator:
    """列設定検証クラス"""
    
    def __init__(self):
        self.validation_results: List[ValidationResult] = []
    
    def validate_column_ai_settings(self, column_settings: Dict[str, Any]) -> Tuple[bool, List[ValidationResult]]:
        """
        列毎AI設定を検証
        
        Args:
            column_settings: 列毎AI設定辞書
        
        Returns:
            Tuple[bool, List[ValidationResult]]: (検証成功フラグ, 検証結果リスト)
        """
        self.validation_results = []
        
        if not column_settings:
            self.validation_results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="列毎AI設定が空です",
                suggestion="少なくとも1つの列にAI設定を追加してください"
            ))
            return False, self.validation_results
        
        # 各列設定を検証
        has_errors = False
        for column_key, settings in column_settings.items():
            column_errors = self._validate_single_column_config(column_key, settings)
            if any(result.level == ValidationLevel.ERROR for result in column_errors):
                has_errors = True
            self.validation_results.extend(column_errors)
        
        # 列位置の重複チェック
        self._validate_column_positions(column_settings)
        
        # AI設定の整合性チェック
        self._validate_ai_settings_consistency(column_settings)
        
        return not has_errors, self.validation_results
    
    def _validate_single_column_config(self, column_key: str, settings: Dict[str, Any]) -> List[ValidationResult]:
        """単一列設定の検証"""
        results = []
        
        # 列番号の検証
        try:
            if column_key.isalpha():
                column_number = column_letter_to_number(column_key)
            else:
                column_number = int(column_key)
                column_key = column_number_to_letter(column_number)
        except (ValueError, KeyError) as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"無効な列指定: {column_key}",
                column=column_key,
                error_code="INVALID_COLUMN"
            ))
            return results
        
        # 列位置の検証（C列以降かどうか）
        if column_number < 3:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"列 {column_key} はC列（3列目）以降に配置してください",
                column=column_key,
                suggestion="「コピー」列はC列以降に配置する必要があります",
                error_code="INVALID_COLUMN_POSITION"
            ))
        
        # AIサービスの検証
        ai_service = settings.get("ai_service")
        if not ai_service:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"列 {column_key}: AIサービスが指定されていません",
                column=column_key,
                error_code="MISSING_AI_SERVICE"
            ))
        else:
            try:
                AIService(ai_service)
            except ValueError:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"列 {column_key}: 無効なAIサービス '{ai_service}'",
                    column=column_key,
                    suggestion="有効なAIサービス: chatgpt, claude, gemini, perplexity, genspark",
                    error_code="INVALID_AI_SERVICE"
                ))
        
        # AIモデルの検証
        ai_model = settings.get("model")
        if not ai_model:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"列 {column_key}: AIモデルが指定されていません（デフォルトを使用）",
                column=column_key
            ))
        
        # AI設定の検証
        ai_settings = settings.get("settings", {})
        if not isinstance(ai_settings, dict):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"列 {column_key}: AI設定が辞書形式ではありません",
                column=column_key
            ))
        
        return results
    
    def _validate_column_positions(self, column_settings: Dict[str, Any]):
        """列位置の重複チェック"""
        column_numbers = []
        
        for column_key in column_settings.keys():
            try:
                if column_key.isalpha():
                    column_number = column_letter_to_number(column_key)
                else:
                    column_number = int(column_key)
                
                if column_number in column_numbers:
                    self.validation_results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"列番号 {column_number} が重複しています",
                        column=column_number_to_letter(column_number),
                        error_code="DUPLICATE_COLUMN"
                    ))
                else:
                    column_numbers.append(column_number)
                    
            except ValueError:
                continue  # 既に他の検証でエラーが出ているはず
    
    def _validate_ai_settings_consistency(self, column_settings: Dict[str, Any]):
        """AI設定の整合性チェック"""
        ai_service_counts = {}
        
        for column_key, settings in column_settings.items():
            ai_service = settings.get("ai_service")
            if ai_service:
                ai_service_counts[ai_service] = ai_service_counts.get(ai_service, 0) + 1
        
        # 情報として各AIサービスの使用数を報告
        for ai_service, count in ai_service_counts.items():
            self.validation_results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message=f"{ai_service}: {count}列で使用"
            ))
    
    def validate_column_ai_config(self, ai_config: ColumnAIConfig) -> List[ValidationResult]:
        """ColumnAIConfigオブジェクトの検証"""
        results = []
        
        # AIサービスの検証
        if not isinstance(ai_config.ai_service, AIService):
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="無効なAIサービス型",
                error_code="INVALID_AI_SERVICE_TYPE"
            ))
        
        # AIモデルの検証
        if not ai_config.ai_model or not isinstance(ai_config.ai_model, str):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="AIモデルが指定されていないか無効です"
            ))
        
        # AI機能の検証
        if ai_config.ai_features and not isinstance(ai_config.ai_features, list):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="AI機能の設定が無効です（リスト形式である必要があります）"
            ))
        
        # AI設定の検証
        if ai_config.ai_settings and not isinstance(ai_config.ai_settings, dict):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message="AI設定が無効です（辞書形式である必要があります）"
            ))
        
        return results
    
    def validate_sheet_structure_for_columns(self, copy_columns: List[int]) -> List[ValidationResult]:
        """
        スプレッドシート構造と列設定の整合性を検証
        
        Args:
            copy_columns: 検出された「コピー」列のリスト
        
        Returns:
            List[ValidationResult]: 検証結果のリスト
        """
        results = []
        
        if not copy_columns:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="スプレッドシートに「コピー」列が見つかりません",
                suggestion="ヘッダー行に「コピー」という列を追加してください",
                error_code="NO_COPY_COLUMNS"
            ))
            return results
        
        # 各コピー列の位置を検証
        for copy_column in copy_columns:
            try:
                get_copy_column_positions(copy_column)
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    message=f"列 {column_number_to_letter(copy_column)}: 設定可能",
                    column=column_number_to_letter(copy_column)
                ))
            except ValueError as e:
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"列 {column_number_to_letter(copy_column)}: {str(e)}",
                    column=column_number_to_letter(copy_column),
                    error_code="INVALID_COPY_COLUMN_POSITION"
                ))
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """検証結果のサマリーを取得"""
        error_count = len([r for r in self.validation_results if r.level == ValidationLevel.ERROR])
        warning_count = len([r for r in self.validation_results if r.level == ValidationLevel.WARNING])
        info_count = len([r for r in self.validation_results if r.level == ValidationLevel.INFO])
        
        return {
            "total_issues": len(self.validation_results),
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "has_errors": error_count > 0,
            "has_warnings": warning_count > 0,
            "is_valid": error_count == 0
        }
    
    def format_results_for_display(self) -> str:
        """検証結果を表示用にフォーマット"""
        if not self.validation_results:
            return "検証結果: すべて正常です"
        
        lines = ["=== 列設定検証結果 ==="]
        
        # エラーを先に表示
        errors = [r for r in self.validation_results if r.level == ValidationLevel.ERROR]
        if errors:
            lines.append("\n🔴 エラー:")
            for result in errors:
                column_info = f" (列 {result.column})" if result.column else ""
                lines.append(f"  • {result.message}{column_info}")
                if result.suggestion:
                    lines.append(f"    💡 {result.suggestion}")
        
        # 警告を表示
        warnings = [r for r in self.validation_results if r.level == ValidationLevel.WARNING]
        if warnings:
            lines.append("\n🟡 警告:")
            for result in warnings:
                column_info = f" (列 {result.column})" if result.column else ""
                lines.append(f"  • {result.message}{column_info}")
        
        # 情報を表示
        infos = [r for r in self.validation_results if r.level == ValidationLevel.INFO]
        if infos:
            lines.append("\nℹ️ 情報:")
            for result in infos:
                lines.append(f"  • {result.message}")
        
        # サマリー
        summary = self.get_summary()
        lines.append(f"\n📊 サマリー: エラー{summary['error_count']}件、警告{summary['warning_count']}件")
        
        return "\n".join(lines)


# ファクトリー関数
def validate_column_ai_settings(column_settings: Dict[str, Any]) -> Tuple[bool, str]:
    """
    列毎AI設定を検証（簡易版）
    
    Args:
        column_settings: 列毎AI設定辞書
    
    Returns:
        Tuple[bool, str]: (検証成功フラグ, 結果メッセージ)
    """
    validator = ColumnConfigValidator()
    is_valid, results = validator.validate_column_ai_settings(column_settings)
    message = validator.format_results_for_display()
    
    return is_valid, message


def validate_single_column_config(column_key: str, settings: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    単一列設定を検証（簡易版）
    
    Args:
        column_key: 列キー
        settings: 設定辞書
    
    Returns:
        Tuple[bool, List[str]]: (検証成功フラグ, エラーメッセージリスト)
    """
    validator = ColumnConfigValidator()
    results = validator._validate_single_column_config(column_key, settings)
    
    errors = [r.message for r in results if r.level == ValidationLevel.ERROR]
    is_valid = len(errors) == 0
    
    return is_valid, errors


# テスト関数
def _test_column_validation():
    """バリデーション機能のテスト"""
    # テスト用の設定
    test_settings = {
        "C": {
            "ai_service": "chatgpt",
            "model": "gpt-4",
            "mode": "creative",
            "features": ["deep_research"],
            "settings": {}
        },
        "E": {
            "ai_service": "claude",
            "model": "claude-3-sonnet",
            "mode": "balanced",
            "features": [],
            "settings": {}
        },
        "A": {  # 無効な位置
            "ai_service": "gemini",
            "model": "gemini-pro"
        }
    }
    
    validator = ColumnConfigValidator()
    is_valid, results = validator.validate_column_ai_settings(test_settings)
    
    print("=== テスト結果 ===")
    print(f"検証結果: {'成功' if is_valid else '失敗'}")
    print(validator.format_results_for_display())
    
    summary = validator.get_summary()
    print(f"\nサマリー: {summary}")


if __name__ == "__main__":
    _test_column_validation()