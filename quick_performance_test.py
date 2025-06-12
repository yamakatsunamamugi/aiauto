#!/usr/bin/env python3
"""
クイックパフォーマンステスト
"""
import ollama
import time

def quick_performance_test():
    print("⚡ クイック パフォーマンステスト")
    print("=" * 35)
    
    client = ollama.Client()
    
    # 短い質問のみでテスト
    questions = [
        "Hello",
        "こんにちは", 
        "1+1は？",
        "東京",
        "ありがとう"
    ]
    
    print(f"🔄 {len(questions)}件の短文処理テスト開始")
    
    times = []
    successful = 0
    
    for i, question in enumerate(questions, 1):
        print(f"{i}. '{question}'", end=" ")
        
        try:
            start_time = time.time()
            
            response = client.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": question}],
                options={"num_predict": 50}  # 短い回答に制限
            )
            
            processing_time = time.time() - start_time
            times.append(processing_time)
            successful += 1
            
            answer = response['message']['content']
            print(f"✅ {processing_time:.1f}s")
            print(f"   → {answer[:40]}{'...' if len(answer) > 40 else ''}")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    # 結果分析
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 パフォーマンス結果:")
        print(f"   成功率: {successful}/{len(questions)} ({successful/len(questions)*100:.1f}%)")
        print(f"   平均時間: {avg_time:.2f}秒")
        print(f"   最速: {min_time:.2f}秒")
        print(f"   最遅: {max_time:.2f}秒")
        print(f"   時間範囲: {max_time - min_time:.2f}秒")
        
        # 評価
        if avg_time < 2:
            grade = "🚀 優秀"
        elif avg_time < 5:
            grade = "✅ 良好"
        elif avg_time < 10:
            grade = "⚠️ 普通"
        else:
            grade = "❌ 要改善"
            
        print(f"   評価: {grade}")
        
    else:
        print("❌ 全てのテストが失敗しました")

if __name__ == "__main__":
    quick_performance_test()