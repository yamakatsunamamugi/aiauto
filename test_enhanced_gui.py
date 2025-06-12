#!/usr/bin/env python3
"""
強化されたGUIアプリケーションのテスト実行スクリプト
CLAUDE.md要件に従って強化されたUI機能をテスト
"""

import sys
import os
import logging

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_enhanced_gui():
    """強化されたGUIアプリケーションをテスト実行"""
    
    print("🚀 強化されたGUIアプリケーションを起動します...")
    print("📋 CLAUDE.md要件対応版:")
    print("   ✅ 複数コピー列対応")
    print("   ✅ 列毎のAI個別設定")
    print("   ✅ DeepThink等詳細機能設定")
    print("   ✅ 処理列(コピー-2)、エラー列(コピー-1)、貼り付け列(コピー+1)自動計算")
    print("   ✅ A列連番行の自動処理")
    print("   ✅ Chrome拡張機能統合")
    print()
    
    try:
        # ログレベルを設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # メインGUIアプリケーションを起動
        from src.gui.main_window import MainWindow
        
        app = MainWindow()
        print("✅ GUIアプリケーション初期化完了")
        print("🖥️ ウィンドウを表示中...")
        print()
        print("💡 使用方法:")
        print("1. スプレッドシートURLを入力")
        print("2. 「シート情報読込」ボタンをクリック")
        print("3. 各コピー列の「設定」ボタンでAI詳細設定")
        print("4. 「自動化開始」ボタンで処理実行")
        print()
        
        app.run()
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("必要なモジュールがインストールされていません。")
        print("requirements.txtを確認してください。")
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_enhanced_gui()