#!/usr/bin/env python3
"""
ブラウザ自動化のテストスクリプト
API不要でWeb版AIサービスを操作するテスト
"""

import sys
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.automation.browser_automation_handler import BrowserAutomationHandler

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_basic_functionality():
    """基本機能のテスト"""
    print("=" * 60)
    print("🧪 ブラウザ自動化基本機能テスト")
    print("=" * 60)
    
    try:
        # ブラウザハンドラーを初期化
        with BrowserAutomationHandler() as handler:
            print("\n✅ ブラウザハンドラーの初期化成功")
            
            # ChatGPTでテスト
            print("\n📝 ChatGPTでテスト実行中...")
            result = handler.process_text(
                service="chatgpt",
                text="Hello! Please respond with a simple greeting.",
                model="gpt-4o"
            )
            
            if result["success"]:
                print(f"✅ ChatGPT応答成功:")
                print(f"   応答: {result['result'][:100]}...")
                print(f"   処理時間: {result['processing_time']:.2f}秒")
            else:
                print(f"❌ ChatGPTエラー: {result['error']}")
            
            # Claudeでテスト（対応している場合）
            print("\n📝 Claudeでテスト実行中...")
            result = handler.process_text(
                service="claude",
                text="Hello! Please respond with a simple greeting.",
                model="claude-3.5-sonnet"
            )
            
            if result["success"]:
                print(f"✅ Claude応答成功:")
                print(f"   応答: {result['result'][:100]}...")
                print(f"   処理時間: {result['processing_time']:.2f}秒")
            else:
                print(f"❌ Claudeエラー: {result['error']}")
    
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


def test_batch_processing():
    """バッチ処理のテスト"""
    print("\n" + "=" * 60)
    print("🧪 バッチ処理テスト")
    print("=" * 60)
    
    try:
        with BrowserAutomationHandler() as handler:
            # 複数のタスクを定義
            tasks = [
                {
                    "service": "chatgpt",
                    "text": "What is 2 + 2?",
                    "model": "gpt-4o"
                },
                {
                    "service": "chatgpt",
                    "text": "Write a haiku about Python programming.",
                    "model": "gpt-4o",
                    "features": ["DeepThink"]
                }
            ]
            
            print(f"\n📋 {len(tasks)}個のタスクを処理中...")
            
            results = handler.process_batch(tasks)
            
            for i, result in enumerate(results):
                print(f"\nタスク{i+1}:")
                if result["success"]:
                    print(f"  ✅ 成功: {result['result'][:100]}...")
                else:
                    print(f"  ❌ 失敗: {result['error']}")
    
    except Exception as e:
        print(f"❌ バッチ処理エラー: {e}")


def test_feature_enablement():
    """特別な機能（DeepThink等）のテスト"""
    print("\n" + "=" * 60)
    print("🧪 特別機能テスト（DeepThink等）")
    print("=" * 60)
    
    try:
        with BrowserAutomationHandler() as handler:
            # DeepThink機能を有効にしてテスト
            print("\n📝 DeepThink機能を有効にしてテスト...")
            result = handler.process_text(
                service="chatgpt",
                text="Please think deeply about: What are the philosophical implications of artificial intelligence?",
                model="gpt-4o",
                features=["DeepThink", "Web検索"]
            )
            
            if result["success"]:
                print(f"✅ DeepThink応答成功:")
                print(f"   応答長: {len(result['result'])}文字")
                print(f"   処理時間: {result['processing_time']:.2f}秒")
                print(f"   応答プレビュー: {result['result'][:200]}...")
            else:
                print(f"❌ DeepThinkエラー: {result['error']}")
    
    except Exception as e:
        print(f"❌ 特別機能テストエラー: {e}")


def interactive_test():
    """対話型テスト"""
    print("\n" + "=" * 60)
    print("🧪 対話型テスト（手動入力）")
    print("=" * 60)
    
    try:
        with BrowserAutomationHandler() as handler:
            while True:
                print("\n使用可能なサービス: chatgpt, claude, gemini")
                service = input("AIサービスを選択 (終了: q): ").strip().lower()
                
                if service == 'q':
                    break
                
                if service not in ['chatgpt', 'claude', 'gemini']:
                    print("❌ 無効なサービスです")
                    continue
                
                text = input("送信するテキスト: ").strip()
                
                if not text:
                    continue
                
                print(f"\n⏳ {service}に送信中...")
                
                result = handler.process_text(
                    service=service,
                    text=text
                )
                
                if result["success"]:
                    print(f"\n✅ 応答:")
                    print("-" * 40)
                    print(result['result'])
                    print("-" * 40)
                    print(f"処理時間: {result['processing_time']:.2f}秒")
                else:
                    print(f"❌ エラー: {result['error']}")
    
    except KeyboardInterrupt:
        print("\n\n👋 テスト終了")
    except Exception as e:
        print(f"❌ 対話型テストエラー: {e}")


def main():
    """メインテスト実行"""
    print("🚀 ブラウザ自動化テスト開始")
    print("API不要でWeb版AIサービスを操作します")
    print()
    print("注意事項:")
    print("1. 事前に各AIサービスにログインしておいてください")
    print("2. Chromeブラウザが必要です")
    print("3. 初回実行時はplaywrightのインストールが必要です:")
    print("   pip install playwright")
    print("   playwright install chromium")
    print()
    
    # Playwrightがインストールされているか確認
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright インストール済み")
    except ImportError:
        print("❌ Playwright が見つかりません")
        print("以下のコマンドでインストールしてください:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return
    
    while True:
        print("\n" + "=" * 60)
        print("テストメニュー:")
        print("1. 基本機能テスト")
        print("2. バッチ処理テスト")
        print("3. 特別機能テスト（DeepThink等）")
        print("4. 対話型テスト")
        print("5. 全テスト実行")
        print("q. 終了")
        print("=" * 60)
        
        choice = input("\n選択してください: ").strip()
        
        if choice == '1':
            test_basic_functionality()
        elif choice == '2':
            test_batch_processing()
        elif choice == '3':
            test_feature_enablement()
        elif choice == '4':
            interactive_test()
        elif choice == '5':
            test_basic_functionality()
            test_batch_processing()
            test_feature_enablement()
        elif choice.lower() == 'q':
            print("\n👋 テスト終了")
            break
        else:
            print("❌ 無効な選択です")


if __name__ == "__main__":
    main()