#!/usr/bin/env python3
"""
Chrome拡張機能 クイックテスト
"""

import sys
import time
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge import ExtensionBridge

def quick_test():
    """クイックテスト実行"""
    
    print("🚀 Chrome拡張機能クイックテスト")
    print("=" * 40)
    
    # ExtensionBridge初期化
    print("\n🔧 ExtensionBridge初期化...")
    bridge = ExtensionBridge()
    
    # 状態確認
    print("\n🔌 拡張機能状態確認...")
    status = bridge.check_extension_status()
    print(f"📍 状態: {status['status']}")
    print(f"📝 詳細: {status['message']}")
    
    if status['status'] != 'active':
        print("❌ Chrome拡張機能が利用できません")
        return False
    
    # 簡単なAI処理テスト
    print("\n🧪 AI処理テスト...")
    test_text = "こんにちは、テストです。OKと返答してください。"
    
    try:
        print("⏳ 処理中...")
        start_time = time.time()
        
        result = bridge.process_with_extension(
            text=test_text,
            ai_service="chatgpt",
            model=None
        )
        
        processing_time = time.time() - start_time
        
        if result['success']:
            print(f"✅ 成功! ({processing_time:.2f}秒)")
            print(f"🤖 応答: {result['result']}")
            return True
        else:
            print(f"❌ 失敗: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    print(f"\n{'🎉 テスト成功!' if success else '❌ テスト失敗'}")