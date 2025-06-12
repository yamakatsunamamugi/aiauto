#!/usr/bin/env python3
"""
バッチ処理Ollamaテスト
"""
import ollama
import time

def batch_test():
    print("📋 Ollama バッチ処理テスト")
    print("=" * 35)
    
    # 大量テストデータ
    test_data = [
        {"question": "こんにちは", "expected_type": "挨拶"},
        {"question": "日本の首都は？", "expected_type": "地理"},
        {"question": "2+2は？", "expected_type": "計算"},
        {"question": "プログラミングとは？", "expected_type": "技術"},
        {"question": "AIの未来は？", "expected_type": "予測"},
        {"question": "おすすめの本は？", "expected_type": "推薦"},
        {"question": "健康的な食事とは？", "expected_type": "健康"},
        {"question": "環境問題について", "expected_type": "社会"},
    ]
    
    client = ollama.Client()
    
    print(f"🔄 {len(test_data)}件のバッチ処理開始...")
    
    results = []
    start_time = time.time()
    
    for i, item in enumerate(test_data, 1):
        question = item["question"]
        category = item["expected_type"]
        
        print(f"{i:2d}. [{category:>4}] {question}", end=" ")
        
        try:
            item_start = time.time()
            
            response = client.chat(
                model="llama3.1:8b",
                messages=[
                    {"role": "system", "content": "簡潔で的確に回答してください。"},
                    {"role": "user", "content": question}
                ]
            )
            
            item_time = time.time() - item_start
            answer = response['message']['content']
            
            results.append({
                "question": question,
                "answer": answer,
                "time": item_time,
                "success": True,
                "category": category
            })
            
            print(f"✅ ({item_time:.1f}s)")
            print(f"      → {answer[:60]}{'...' if len(answer) > 60 else ''}")
            
        except Exception as e:
            item_time = time.time() - item_start
            results.append({
                "question": question,
                "error": str(e),
                "time": item_time,
                "success": False,
                "category": category
            })
            
            print(f"❌ ({item_time:.1f}s) {e}")
    
    total_time = time.time() - start_time
    
    # 統計分析
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"\n📊 バッチ処理結果分析:")
    print(f"   総処理時間: {total_time:.1f}秒")
    print(f"   成功: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"   失敗: {len(failed)}")
    
    if successful:
        avg_time = sum(r["time"] for r in successful) / len(successful)
        max_time = max(r["time"] for r in successful)
        min_time = min(r["time"] for r in successful)
        
        print(f"   平均処理時間: {avg_time:.1f}秒")
        print(f"   最速: {min_time:.1f}秒, 最遅: {max_time:.1f}秒")
        print(f"   スループット: {len(successful)/total_time:.1f}件/秒")
        
        # カテゴリー別分析
        categories = {}
        for r in successful:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r["time"])
        
        print(f"\n📈 カテゴリー別パフォーマンス:")
        for cat, times in categories.items():
            avg_cat_time = sum(times) / len(times)
            print(f"   {cat:>6}: {avg_cat_time:.1f}秒 (件数: {len(times)})")

if __name__ == "__main__":
    batch_test()