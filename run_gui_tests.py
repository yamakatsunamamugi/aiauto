#!/usr/bin/env python3
"""
GUIテスト実行スクリプト

担当者A（GUI）のすべてのテストを実行するためのスクリプト
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# プロジェクトルートを確認
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_command(command, description):
    """コマンドを実行して結果を表示"""
    print(f"\n{'='*60}")
    print(f"実行中: {description}")
    print(f"コマンド: {command}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=project_root
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"実行時間: {duration:.2f}秒")
        
        if result.stdout:
            print("標準出力:")
            print(result.stdout)
        
        if result.stderr:
            print("エラー出力:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
        else:
            print(f"❌ {description} - 失敗 (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ {description} - 実行エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("🎯 GUI テストスイート実行開始")
    print(f"プロジェクトルート: {project_root}")
    
    # 必要なパッケージのインストール確認
    required_packages = [
        "pytest",
        "pytest-cov", 
        "pytest-mock",
        "psutil"
    ]
    
    print("\n📦 必要なパッケージのインストール確認:")
    for package in required_packages:
        if run_command(f"pip show {package}", f"{package}の確認"):
            print(f"✅ {package} はインストール済み")
        else:
            print(f"⚠️ {package} をインストールします...")
            run_command(f"pip install {package}", f"{package}のインストール")
    
    # テスト実行
    test_results = []
    
    # 1. 既存のGUIテスト実行
    test_results.append(
        run_command(
            "python -m pytest tests/test_gui_components.py -v",
            "既存GUIコンポーネントテスト"
        )
    )
    
    # 2. 単体テスト実行
    test_results.append(
        run_command(
            "python -m pytest tests/unit/gui/ -v",
            "GUI単体テスト"
        )
    )
    
    # 3. E2Eテスト実行
    test_results.append(
        run_command(
            "python -m pytest tests/e2e/test_user_workflows.py -v",
            "E2Eワークフローテスト"
        )
    )
    
    # 4. 統合テスト実行
    test_results.append(
        run_command(
            "python -m pytest tests/integration/test_gui_integration.py -v",
            "GUI統合テスト"
        )
    )
    
    # 5. パフォーマンステスト実行（時間がかかる場合は別途実行）
    run_performance = input("\n⏱️ パフォーマンステストを実行しますか？ (y/n): ").lower() == 'y'
    if run_performance:
        test_results.append(
            run_command(
                "python -m pytest tests/performance/test_gui_performance.py -v -s",
                "GUIパフォーマンステスト"
            )
        )
    
    # 6. カバレッジレポート生成
    print("\n📊 カバレッジレポート生成:")
    run_command(
        "python -m pytest tests/unit/gui/ tests/integration/test_gui_integration.py --cov=src/gui --cov-report=html --cov-report=term",
        "カバレッジレポート生成"
    )
    
    # 結果サマリー
    print("\n" + "="*60)
    print("🎯 テスト結果サマリー")
    print("="*60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    for i, result in enumerate(test_results):
        test_names = [
            "既存GUIコンポーネントテスト",
            "GUI単体テスト", 
            "E2Eワークフローテスト",
            "GUI統合テスト",
            "GUIパフォーマンステスト"
        ]
        status = "✅ 成功" if result else "❌ 失敗"
        if i < len(test_names):
            print(f"{test_names[i]}: {status}")
    
    print(f"\n合計: {passed_tests}/{total_tests} のテストが成功")
    
    if passed_tests == total_tests:
        print("🎉 すべてのテストが成功しました！")
        return 0
    else:
        print("⚠️ 一部のテストが失敗しました。詳細を確認してください。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)