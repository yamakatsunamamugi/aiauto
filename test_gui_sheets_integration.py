#!/usr/bin/env python3
"""
GUI-Sheets統合機能テストスクリプト
実際のGUIアプリケーションでシート機能をテスト
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.gui.main_window import MainWindow


def create_test_instructions():
    """テスト手順を表示"""
    instructions = """
🧪 GUI-Sheets統合機能テスト手順

【事前準備】
1. Google Cloud Consoleでプロジェクト作成
2. Google Sheets APIを有効化
3. 認証情報作成（OAuth2またはサービスアカウント）
4. 認証ファイルを config/credentials.json に保存

【テスト手順】
1. ✅ GUIアプリケーション起動
2. ✅ スプレッドシートURL入力
3. ✅ 「📋 シート情報読込」ボタンクリック
4. ✅ 認証画面での許可（初回のみ）
5. ✅ シート一覧の表示確認
6. ✅ シート選択での自動解析
7. ✅ データプレビューの表示確認
8. ✅ 自動化実行テスト

【テスト用スプレッドシート例】
- Googleスプレッドシートで新規作成
- A5セルに「作業」と入力
- D5セルに「コピー」と入力
- A6セルから「1」「2」「3」...と連番入力
- D列にテスト用メッセージを入力

【確認ポイント】
- 認証が正常に完了するか
- シート構造が正しく解析されるか
- データプレビューが表示されるか
- 自動化処理が動作するか
- エラーハンドリングが適切か
"""
    
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを隠す
    
    result = messagebox.askquestion(
        "テスト開始",
        instructions + "\n\nGUIアプリケーションを起動しますか？",
        icon='question'
    )
    
    root.destroy()
    
    return result == 'yes'


def run_gui_test():
    """GUI統合テストを実行"""
    print("🚀 GUI-Sheets統合機能テスト開始")
    
    try:
        # テスト手順の表示
        if not create_test_instructions():
            print("⏹️ テストがキャンセルされました")
            return False
        
        print("📱 GUIアプリケーションを起動中...")
        
        # メインGUIアプリケーション起動
        app = MainWindow()
        
        # 初期ログメッセージ
        app.add_log_entry("🧪 GUI-Sheets統合機能テスト開始")
        app.add_log_entry("📋 スプレッドシートURLを入力してテストを開始してください")
        app.add_log_entry("🔗 Google Sheets APIの認証が必要です")
        
        # アプリケーション実行
        app.run()
        
        print("✅ GUIアプリケーションが終了しました")
        return True
        
    except Exception as e:
        print(f"❌ GUI統合テストエラー: {e}")
        return False


if __name__ == "__main__":
    try:
        success = run_gui_test()
        
        if success:
            print("\n🎉 GUI-Sheets統合機能テストが完了しました")
            print("📊 実際の機能確認:")
            print("  - Google Sheets API認証")
            print("  - シート構造解析")
            print("  - データプレビュー表示")
            print("  - 自動化処理実行")
        else:
            print("\n⚠️ テストが中断されました")
        
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 テストが中断されました")
        exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        exit(1)