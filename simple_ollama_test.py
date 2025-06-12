#!/usr/bin/env python3
"""
シンプルなOllamaテスト
"""
import sys
sys.path.append('/Users/roudousha/Dropbox/5.AI-auto')

from src.automation.ollama_handler import OllamaAIHandler

def main():
    print("🤖 Ollama統合システム シンプルテスト")
    print("=" * 40)
    
    try:
        # ハンドラー初期化
        print("🔄 初期化中...")
        handler = OllamaAIHandler()
        print("✅ 初期化完了")
        
        # テスト質問リスト
        questions = [
            "こんにちは",
            "日本の首都は？",
            "2+2の答えは？"
        ]
        
        print(f"\n📝 {len(questions)}個の質問をテスト中...")
        
        for i, question in enumerate(questions, 1):
            print(f"\n{i}. 質問: {question}")
            print("   処理中...", end="", flush=True)
            
            result = handler.process_text(question)
            
            if result["success"]:
                print(f" ✅ ({result['processing_time']:.1f}秒)")
                print(f"   回答: {result['result']}")
            else:
                print(f" ❌")
                print(f"   エラー: {result['error']}")
        
        # 統計表示
        stats = handler.get_statistics()
        print(f"\n📊 結果統計:")
        print(f"   成功: {stats['successful_requests']}/{stats['total_requests']}")
        print(f"   平均時間: {stats['average_response_time']:.1f}秒")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()