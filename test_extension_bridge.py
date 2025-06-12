#!/usr/bin/env python3
"""
ExtensionBridge修正版テスト
"""

import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge import ExtensionBridge

def test_extension_bridge():
    """ExtensionBridge修正版をテスト"""
    
    print("🔍 ExtensionBridge修正版テスト開始")
    print("=" * 60)
    
    try:
        # ExtensionBridge初期化
        bridge = ExtensionBridge()
        print("✅ ExtensionBridge初期化成功")
        
        # 拡張機能状態確認
        status = bridge.check_extension_status()
        print(f"📊 拡張機能状態: {status['status']} - {status['message']}")
        
        # テスト用短文でAI処理実行
        test_text = "Hello, World! これはテストメッセージです。"
        test_services = ["chatgpt", "claude", "gemini"]
        
        for service in test_services:
            print(f"\n🤖 {service}でのテスト実行:")
            
            result = bridge.process_with_extension(
                text=test_text,
                ai_service=service,
                model="default"
            )
            
            if result['success']:
                print(f"  ✅ 成功: {result['result']}")
                if result.get('mock', False):
                    print(f"  ⚠️ モック応答使用")
                print(f"  ⏱️ 処理時間: {result.get('processing_time', 'N/A')}秒")
            else:
                print(f"  ❌ 失敗: {result['error']}")
        
        # 統計情報表示
        stats = bridge.get_statistics()
        print(f"\n📊 処理統計:")
        print(f"  リクエスト総数: {stats['total_requests']}")
        print(f"  成功: {stats['successful_requests']}")
        print(f"  失敗: {stats['failed_requests']}")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_extension_bridge()
    
    if success:
        print("\n✅ ExtensionBridge修正版テスト成功")
        print("🚀 GUIアプリでモック機能が利用可能")
    else:
        print("\n❌ ExtensionBridge修正版テスト失敗")