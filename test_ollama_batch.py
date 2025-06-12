#!/usr/bin/env python3
"""
Ollama統合システム バッチ処理テスト
複数のテキストを一度に処理します
"""

from src.automation.ollama_handler import OllamaAIHandler
import time

def main():
    print("📋 Ollama AI統合システム バッチ処理テスト")
    print("=" * 50)
    
    # テストデータ
    test_texts = [
        "日本の首都について教えてください。",
        "プログラミング言語Pythonの特徴は？",
        "AIの未来について簡潔に説明してください。",
        "環境問題の解決策を提案してください。",
        "健康的な生活習慣について教えてください。"
    ]
    
    try:
        # ハンドラー初期化
        print("🔄 Ollamaハンドラーを初期化中...")
        handler = OllamaAIHandler()
        print("✅ 初期化完了！")
        
        print(f"\n📝 {len(test_texts)}件のテキストを処理します...")
        print("=" * 50)
        
        start_time = time.time()
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n🔄 処理 {i}/{len(test_texts)}: {text[:30]}...")
            
            result = handler.process_text(
                text=text,
                model="llama3.1:8b",
                system_prompt="簡潔で分かりやすい日本語で回答してください。"
            )
            
            if result["success"]:
                print(f"✅ 成功 ({result['processing_time']:.2f}秒)")
                print(f"   回答: {result['result'][:100]}...")
            else:
                print(f"❌ 失敗: {result['error']}")
        
        total_time = time.time() - start_time
        
        # 統計情報
        stats = handler.get_statistics()
        print(f"\n📊 バッチ処理統計:")
        print(f"   - 総処理時間: {total_time:.2f}秒")
        print(f"   - 成功: {stats['successful_requests']}/{stats['total_requests']}")
        print(f"   - 平均処理時間: {stats['average_response_time']:.2f}秒")
        print(f"   - 成功率: {(stats['successful_requests'] / stats['total_requests'] * 100):.1f}%")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()