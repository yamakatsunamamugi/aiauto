#!/usr/bin/env python3
"""
Chrome拡張機能ライブテスト
実際のブラウザ操作でChrome拡張機能をテストします

実行方法:
python3 test_chrome_extension_live.py
"""

import sys
import time
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge import ExtensionBridge

def test_extension_live():
    """Chrome拡張機能ライブテスト"""
    
    print("🚀 Chrome拡張機能ライブテスト開始")
    print("=" * 60)
    
    # ExtensionBridge初期化
    print("\n🔧 ExtensionBridge初期化中...")
    bridge = ExtensionBridge()
    print("✅ 初期化完了")
    
    # 拡張機能状態確認
    print("\n🔌 拡張機能状態確認...")
    status = bridge.check_extension_status()
    print(f"📍 状態: {status['status']}")
    print(f"📝 詳細: {status['message']}")
    
    if status['status'] == 'missing':
        print("\n❌ Chrome拡張機能がインストールされていません")
        print("📋 インストール手順:")
        print("1. chrome://extensions/ を開く")
        print("2. 開発者モードをON")
        print("3. '読み込み'で以下フォルダを選択:")
        print(f"   {project_root}/chrome-extension")
        return False
    
    # 対応AIサービス一覧
    print("\n🤖 対応AIサービス:")
    services = bridge.get_supported_ai_services()
    for i, service in enumerate(services, 1):
        url = bridge.supported_sites[service]
        print(f"  {i}. {service.upper()}: {url}")
    
    # 統計情報表示
    print("\n📊 現在の統計情報:")
    stats = bridge.get_statistics()
    print(f"  総リクエスト数: {stats['total_requests']}")
    print(f"  成功数: {stats['successful_requests']}")
    print(f"  失敗数: {stats['failed_requests']}")
    print(f"  成功率: {stats['success_rate']:.1f}%")
    
    print("\n" + "=" * 60)
    print("🎯 次のステップ:")
    print("1. ブラウザで対応AIサイトの1つを開く")
    print("2. ログインする")
    print("3. Chrome右上の拡張機能アイコンをクリック")
    print("4. '接続テスト'ボタンを押す")
    print("5. 応答を確認する")
    
    # インタラクティブテスト
    print("\n🧪 実際のAI処理テストを実行しますか？")
    print("注意: ChromeでAIサイトにログインしてから実行してください")
    
    while True:
        choice = input("\nテストを実行する？ (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            return run_ai_processing_test(bridge)
        elif choice in ['n', 'no']:
            print("✅ テスト完了。後で手動で確認してください。")
            return True
        else:
            print("❓ 'y' または 'n' を入力してください")

def run_ai_processing_test(bridge):
    """実際のAI処理テスト"""
    
    print("\n🎯 AI処理テスト開始")
    print("-" * 40)
    
    # AIサービス選択
    services = bridge.get_supported_ai_services()
    print("使用するAIサービスを選択してください:")
    for i, service in enumerate(services, 1):
        print(f"  {i}. {service.upper()}")
    
    while True:
        try:
            choice = int(input(f"\n番号を選択 (1-{len(services)}): "))
            if 1 <= choice <= len(services):
                selected_service = services[choice - 1]
                break
            else:
                print(f"❓ 1から{len(services)}の番号を入力してください")
        except ValueError:
            print("❓ 数字を入力してください")
    
    # テストプロンプト
    test_prompt = input("\nテスト用プロンプトを入力 (空白でデフォルト): ").strip()
    if not test_prompt:
        test_prompt = "こんにちは！これはChrome拡張機能のテストです。簡単に挨拶してください。"
    
    print(f"\n🚀 {selected_service.upper()}で処理開始...")
    print(f"📝 プロンプト: {test_prompt}")
    print("⏳ 処理中... (最大2分待機)")
    
    # 実際のAI処理実行
    try:
        start_time = time.time()
        result = bridge.process_with_extension(
            text=test_prompt,
            ai_service=selected_service,
            model=None  # デフォルトモデル使用
        )
        processing_time = time.time() - start_time
        
        print(f"\n⏱️ 処理時間: {processing_time:.2f}秒")
        
        if result['success']:
            print("🎉 AI処理成功！")
            print(f"🤖 使用AI: {result['ai_service']}")
            if 'model' in result:
                print(f"🧠 モデル: {result['model']}")
            print(f"📝 応答:")
            print(f"   {result['result'][:200]}{'...' if len(result['result']) > 200 else ''}")
            
            # 統計更新
            updated_stats = bridge.get_statistics()
            print(f"\n📊 更新された統計:")
            print(f"  総リクエスト数: {updated_stats['total_requests']}")
            print(f"  成功数: {updated_stats['successful_requests']}")
            print(f"  成功率: {updated_stats['success_rate']:.1f}%")
            print(f"  平均処理時間: {updated_stats['average_response_time']:.2f}秒")
            
            return True
        else:
            print("❌ AI処理失敗")
            print(f"🚨 エラー: {result['error']}")
            print("\n💡 トラブルシューティング:")
            print("- Chromeで対応AIサイトにログインしているか確認")
            print("- 拡張機能が正しくインストールされているか確認")
            print("- ネットワーク接続を確認")
            return False
            
    except Exception as e:
        print(f"❌ 処理中にエラーが発生: {e}")
        return False

def main():
    """メイン関数"""
    print("🎮 Chrome拡張機能統合システム ライブテスト")
    print("このスクリプトで実際にChrome拡張機能を動作確認できます")
    
    try:
        success = test_extension_live()
        if success:
            print("\n🎉 テスト完了！Chrome拡張機能は正常に動作しています。")
        else:
            print("\n⚠️ テストで問題が発生しました。セットアップを確認してください。")
    except KeyboardInterrupt:
        print("\n\n⏹️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")

if __name__ == "__main__":
    main()