#!/usr/bin/env python3
"""
ステップバイステップ動作確認スクリプト
各段階を詳細に確認しながら実行
"""

import sys
import time
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge import ExtensionBridge

def test_step_by_step():
    """段階的テスト実行"""
    
    print("🔍 Chrome拡張機能 ステップバイステップテスト")
    print("=" * 50)
    
    # Step 1: 拡張機能確認
    print("\n【Step 1】Chrome拡張機能の確認")
    print("-" * 30)
    
    bridge = ExtensionBridge()
    status = bridge.check_extension_status()
    
    print(f"📍 拡張機能状態: {status['status']}")
    print(f"📝 詳細: {status['message']}")
    
    if status['status'] != 'active':
        print("❌ 拡張機能が利用できません")
        print("💡 解決方法:")
        print("1. chrome://extensions/ を開く")
        print("2. 開発者モードをON")
        print("3. AI Automation Bridgeを再読み込み")
        return False
    
    print("✅ 拡張機能は正常です")
    
    # Step 2: ChatGPTアクセス確認
    print("\n【Step 2】ChatGPTアクセス確認")
    print("-" * 30)
    print("🌐 ChatGPT (https://chatgpt.com) にログインしていますか？")
    print("拡張機能のポップアップで「ChatGPT: ✓ アクティブ」と表示されますか？")
    
    response = input("確認できた場合は 'y' を入力: ").strip().lower()
    if response != 'y':
        print("❌ まずChatGPTにログインしてください")
        print("💡 手順:")
        print("1. https://chatgpt.com を開く")
        print("2. ログインする")
        print("3. 拡張機能アイコンをクリック")
        print("4. 「接続テスト」を実行")
        return False
    
    print("✅ ChatGPTアクセス確認完了")
    
    # Step 3: 実際のAI処理テスト
    print("\n【Step 3】AI処理の実際の動作確認")
    print("-" * 30)
    
    test_text = "こんにちは！これはテストです。「テスト成功」と返答してください。"
    print(f"📝 送信テキスト: {test_text}")
    print("⏳ AIに送信中... (ChatGPTの画面を確認してください)")
    
    try:
        start_time = time.time()
        result = bridge.process_with_extension(
            text=test_text,
            ai_service="chatgpt",
            model=None
        )
        processing_time = time.time() - start_time
        
        print(f"\n⏱️ 処理時間: {processing_time:.2f}秒")
        
        if result['success']:
            print("✅ AI処理成功！")
            print(f"🤖 ChatGPTの回答: {result['result']}")
            print("\n🔍 実際の動作:")
            print("1. Chrome拡張機能がChatGPTのテキスト入力欄を特定")
            print("2. 自動でテキストを入力")
            print("3. 送信ボタンを自動クリック") 
            print("4. AIの応答を自動取得")
            print("5. Pythonに結果を返送")
            
            # Step 4: スプレッドシート連携説明
            print("\n【Step 4】スプレッドシート連携の仕組み")
            print("-" * 30)
            print("✅ AI処理は正常に動作しています")
            print("📊 スプレッドシート連携:")
            print("  - PythonでGoogleスプレッドシートを読み取り")
            print("  - 各行のテキストを上記のAI処理に送信")
            print("  - AI回答をスプレッドシートに自動書き込み")
            print("\n🎯 完全自動化の準備完了！")
            return True
            
        else:
            print(f"❌ AI処理失敗: {result['error']}")
            print("\n🔍 確認事項:")
            print("1. ChatGPTにログインしているか")
            print("2. ChatGPTページが開いているか")
            print("3. ネットワーク接続に問題ないか")
            return False
            
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        print("\n💡 トラブルシューティング:")
        print("1. Chromeを再起動")
        print("2. 拡張機能を再読み込み")
        print("3. ChatGPTに再ログイン")
        return False

def main():
    """メイン実行"""
    
    print("🎮 Chrome拡張機能の動作を段階的に確認します")
    print("各ステップで実際に何が起こっているかを詳しく説明します\n")
    
    try:
        success = test_step_by_step()
        
        if success:
            print("\n🎉 全てのテストが成功しました！")
            print("📋 次のステップ:")
            print("1. Googleスプレッドシートを準備")
            print("2. run_full_automation.py で完全自動化を実行")
            print("\n実行コマンド:")
            print("python3 run_full_automation.py")
        else:
            print("\n⚠️ 問題が発生しました")
            print("📋 SIMPLE_USAGE_GUIDE.md を確認してください")
            
    except KeyboardInterrupt:
        print("\n⏹️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")

if __name__ == "__main__":
    main()