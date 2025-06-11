"""
列操作ユーティリティモジュール

スプレッドシートの列番号と列記号の変換、列関連の操作を提供
"""

import re
from typing import List, Tuple, Optional


def column_letter_to_number(column_letter: str) -> int:
    """
    列記号を列番号に変換（A=1, B=2, ...）
    
    Args:
        column_letter: 列記号（例: A, B, C, AA, AB等）
    
    Returns:
        int: 列番号（1ベース）
    
    Examples:
        >>> column_letter_to_number("A")
        1
        >>> column_letter_to_number("Z")
        26
        >>> column_letter_to_number("AA")
        27
    """
    if not column_letter or not column_letter.isalpha():
        raise ValueError(f"無効な列記号: {column_letter}")
    
    result = 0
    for char in column_letter.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result


def column_number_to_letter(column_number: int) -> str:
    """
    列番号を列記号に変換（1=A, 2=B, ...）
    
    Args:
        column_number: 列番号（1ベース）
    
    Returns:
        str: 列記号
    
    Examples:
        >>> column_number_to_letter(1)
        'A'
        >>> column_number_to_letter(26)
        'Z'
        >>> column_number_to_letter(27)
        'AA'
    """
    if column_number < 1:
        raise ValueError(f"列番号は1以上である必要があります: {column_number}")
    
    result = ""
    while column_number > 0:
        column_number -= 1
        result = chr(column_number % 26 + ord('A')) + result
        column_number //= 26
    return result


def get_copy_column_positions(copy_column: int) -> Tuple[int, int, int, int]:
    """
    「コピー」列を基準とした関連列の位置を計算
    
    Args:
        copy_column: 「コピー」列の位置（1ベース）
    
    Returns:
        Tuple[int, int, int, int]: (処理列, エラー列, コピー列, 結果列)
    
    Raises:
        ValueError: 列位置が無効な場合
    """
    if copy_column < 3:
        raise ValueError(f"「コピー」列はC列（3列目）以降に配置してください。現在: {copy_column}")
    
    process_column = copy_column - 2
    error_column = copy_column - 1
    result_column = copy_column + 1
    
    return process_column, error_column, copy_column, result_column


def parse_column_range(range_spec: str) -> List[str]:
    """
    列範囲指定文字列を解析して列記号のリストを返す
    
    Args:
        range_spec: 列範囲指定（例: "A:E", "C,D,F", "A"）
    
    Returns:
        List[str]: 列記号のリスト
    
    Examples:
        >>> parse_column_range("A:C")
        ['A', 'B', 'C']
        >>> parse_column_range("C,E,G")
        ['C', 'E', 'G']
    """
    if not range_spec:
        return []
    
    # カンマ区切りの場合
    if ',' in range_spec:
        columns = []
        for part in range_spec.split(','):
            part = part.strip().upper()
            if part and part.isalpha():
                columns.append(part)
        return columns
    
    # 範囲指定の場合（例: A:E）
    if ':' in range_spec:
        start_col, end_col = range_spec.split(':', 1)
        start_col = start_col.strip().upper()
        end_col = end_col.strip().upper()
        
        if not (start_col.isalpha() and end_col.isalpha()):
            raise ValueError(f"無効な列範囲指定: {range_spec}")
        
        start_num = column_letter_to_number(start_col)
        end_num = column_letter_to_number(end_col)
        
        if start_num > end_num:
            start_num, end_num = end_num, start_num
        
        return [column_number_to_letter(i) for i in range(start_num, end_num + 1)]
    
    # 単一列の場合
    column = range_spec.strip().upper()
    if column.isalpha():
        return [column]
    
    return []


def find_copy_columns_in_header(header_row: List[str]) -> List[Tuple[int, str]]:
    """
    ヘッダー行から「コピー」列を特定
    
    Args:
        header_row: ヘッダー行のデータ
    
    Returns:
        List[Tuple[int, str]]: (列番号, 列記号)のリスト
    """
    copy_columns = []
    
    for i, cell_value in enumerate(header_row):
        if cell_value and str(cell_value).strip() == "コピー":
            column_number = i + 1  # 1ベース
            column_letter = column_number_to_letter(column_number)
            copy_columns.append((column_number, column_letter))
    
    return copy_columns


def validate_column_positions(copy_columns: List[int]) -> List[str]:
    """
    「コピー」列の位置を検証
    
    Args:
        copy_columns: 「コピー」列の位置リスト
    
    Returns:
        List[str]: 検証エラーメッセージのリスト
    """
    errors = []
    
    for copy_column in copy_columns:
        if copy_column < 3:
            column_letter = column_number_to_letter(copy_column)
            errors.append(f"「コピー」列 {column_letter}({copy_column}) はC列（3列目）以降に配置してください")
    
    return errors


def create_cell_reference(sheet_name: str, column: int, row: int) -> str:
    """
    セル参照文字列を作成
    
    Args:
        sheet_name: シート名
        column: 列番号（1ベース）
        row: 行番号（1ベース）
    
    Returns:
        str: セル参照文字列（例: "Sheet1!A1"）
    """
    column_letter = column_number_to_letter(column)
    return f"{sheet_name}!{column_letter}{row}"


def create_range_reference(sheet_name: str, start_column: int, start_row: int, 
                          end_column: Optional[int] = None, end_row: Optional[int] = None) -> str:
    """
    範囲参照文字列を作成
    
    Args:
        sheet_name: シート名
        start_column: 開始列番号（1ベース）
        start_row: 開始行番号（1ベース）
        end_column: 終了列番号（省略時は開始列と同じ）
        end_row: 終了行番号（省略時は開始行と同じ）
    
    Returns:
        str: 範囲参照文字列（例: "Sheet1!A1:B2"）
    """
    start_col_letter = column_number_to_letter(start_column)
    start_ref = f"{start_col_letter}{start_row}"
    
    if end_column is None and end_row is None:
        return f"{sheet_name}!{start_ref}"
    
    end_col_letter = column_number_to_letter(end_column or start_column)
    end_row = end_row or start_row
    end_ref = f"{end_col_letter}{end_row}"
    
    return f"{sheet_name}!{start_ref}:{end_ref}"


def get_column_info_summary(copy_columns: List[int]) -> str:
    """
    列情報のサマリー文字列を作成
    
    Args:
        copy_columns: 「コピー」列の位置リスト
    
    Returns:
        str: サマリー文字列
    """
    if not copy_columns:
        return "「コピー」列が見つかりません"
    
    column_info = []
    for copy_col in copy_columns:
        try:
            process_col, error_col, _, result_col = get_copy_column_positions(copy_col)
            copy_letter = column_number_to_letter(copy_col)
            process_letter = column_number_to_letter(process_col)
            error_letter = column_number_to_letter(error_col)
            result_letter = column_number_to_letter(result_col)
            
            column_info.append(f"{copy_letter}列(処理:{process_letter}, エラー:{error_letter}, 結果:{result_letter})")
        except ValueError as e:
            column_letter = column_number_to_letter(copy_col)
            column_info.append(f"{column_letter}列(エラー: {e})")
    
    return f"「コピー」列: {', '.join(column_info)}"


# テスト関数
def _test_column_utils():
    """ユーティリティ関数のテスト"""
    # 列番号と列記号の変換テスト
    assert column_letter_to_number("A") == 1
    assert column_letter_to_number("Z") == 26
    assert column_letter_to_number("AA") == 27
    assert column_number_to_letter(1) == "A"
    assert column_number_to_letter(26) == "Z"
    assert column_number_to_letter(27) == "AA"
    
    # 列位置計算テスト
    process, error, copy, result = get_copy_column_positions(3)
    assert (process, error, copy, result) == (1, 2, 3, 4)
    
    # 列範囲解析テスト
    assert parse_column_range("A:C") == ["A", "B", "C"]
    assert parse_column_range("C,E,G") == ["C", "E", "G"]
    assert parse_column_range("A") == ["A"]
    
    print("✅ 列ユーティリティのテストが完了しました")


if __name__ == "__main__":
    _test_column_utils()