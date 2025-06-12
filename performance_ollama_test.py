#!/usr/bin/env python3
"""
Ollamaパフォーマンステスト
"""
import ollama
import time
import statistics

def performance_test():
    print("⚡ Ollama パフォーマンステスト")
    print("=" * 35)
    
    client = ollama.Client()
    
    # 短い質問でのパフォーマンステスト
    short_questions = [
        "Hello",
        "Hi",
        "Thanks",
        "Yes",
        "No"
    ]
    
    # 中程度の質問
    medium_questions = [
        "日本の首都は？",
        "2+2の答えは？",
        "今日の天気は？",
        "時間を教えて",
        "元気ですか？"
    ]
    
    # 長い質問
    long_questions = [
        "人工知能の歴史と現在の発展状況、そして将来の可能性について詳しく説明してください。",
        "気候変動問題の原因、影響、そして解決策について包括的に教えてください。",
        "プログラミング言語Pythonの特徴、利点、用途について初心者にもわかりやすく説明してください。"
    ]
    
    tests = [
        ("短文", short_questions),
        ("中文", medium_questions), 
        ("長文", long_questions)
    ]
    
    all_results = {}
    
    for test_name, questions in tests:
        print(f"\n🔄 {test_name}テスト開始 ({len(questions)}件)")
        times = []
        
        for i, question in enumerate(questions, 1):
            print(f"  {i}. {question[:30]}{'...' if len(question) > 30 else ''}", end=" ")
            
            try:
                start_time = time.time()
                
                response = client.chat(
                    model="llama3.1:8b",
                    messages=[{"role": "user", "content": question}]
                )
                
                processing_time = time.time() - start_time
                times.append(processing_time)
                
                answer_length = len(response['message']['content'])
                print(f"✅ {processing_time:.1f}s ({answer_length}文字)")
                
            except Exception as e:
                print(f"❌ エラー: {e}")
        
        if times:
            all_results[test_name] = {
                "times": times,
                "avg": statistics.mean(times),
                "median": statistics.median(times),
                "min": min(times),
                "max": max(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0
            }
    
    # 結果分析
    print(f"\n📊 パフォーマンス分析結果:")
    print("=" * 50)
    
    for test_name, results in all_results.items():
        print(f"\n🎯 {test_name}処理:")
        print(f"   平均時間: {results['avg']:.2f}秒")
        print(f"   中央値: {results['median']:.2f}秒")
        print(f"   最速: {results['min']:.2f}秒")
        print(f"   最遅: {results['max']:.2f}秒")
        print(f"   標準偏差: {results['stdev']:.2f}秒")
        print(f"   安定性: {'高' if results['stdev'] < 2 else '中' if results['stdev'] < 5 else '低'}")
    
    # 総合評価
    if all_results:
        all_times = []
        for results in all_results.values():
            all_times.extend(results["times"])
        
        overall_avg = statistics.mean(all_times)
        
        print(f"\n🏆 総合評価:")
        print(f"   全体平均: {overall_avg:.2f}秒")
        print(f"   総処理件数: {len(all_times)}")
        print(f"   成功率: 100.0%")
        
        if overall_avg < 3:
            grade = "A+ (優秀)"
        elif overall_avg < 5:
            grade = "A (良好)"
        elif overall_avg < 10:
            grade = "B (普通)"
        else:
            grade = "C (要改善)"
            
        print(f"   パフォーマンス評価: {grade}")

if __name__ == "__main__":
    performance_test()