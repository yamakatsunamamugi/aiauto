#!/usr/bin/env python3
"""
直接的なOllamaテスト（import無し）
"""
import ollama
import time

def test_ollama_direct():
    print("🤖 Ollama直接テスト")
    print("=" * 30)
    
    try:
        # Ollamaクライアント作成
        client = ollama.Client()
        
        # モデル一覧取得
        print("📋 利用可能モデル確認中...")
        try:
            models = client.list()
            model_names = [model['name'] for model in models['models']]
            print(f"✅ モデル: {model_names}")
        except Exception as e:
            print(f"⚠️ モデル一覧取得エラー: {e}")
            model_names = ["llama3.1:8b"]  # デフォルト
            
        if not model_names:
            print("❌ 利用可能なモデルがありません")
            return
            
        model_to_use = model_names[0]
        print(f"🎯 使用モデル: {model_to_use}")
        
        # テスト質問
        questions = [
            "Hello",
            "日本の首都は？",
            "2+2=?"
        ]
        
        print(f"\n📝 {len(questions)}個の質問をテスト...")
        successful = 0
        total_time = 0
        
        for i, question in enumerate(questions, 1):
            print(f"\n{i}. 質問: {question}")
            print("   処理中...", end="", flush=True)
            
            start_time = time.time()
            
            try:
                response = client.chat(
                    model=model_to_use,
                    messages=[
                        {"role": "user", "content": question}
                    ]
                )
                
                processing_time = time.time() - start_time
                total_time += processing_time
                successful += 1
                
                answer = response['message']['content']
                print(f" ✅ ({processing_time:.1f}秒)")
                print(f"   回答: {answer[:100]}{'...' if len(answer) > 100 else ''}")
                
            except Exception as e:
                processing_time = time.time() - start_time
                print(f" ❌ ({processing_time:.1f}秒)")
                print(f"   エラー: {e}")
        
        # 統計表示
        print(f"\n📊 テスト結果:")
        print(f"   成功: {successful}/{len(questions)}")
        print(f"   成功率: {(successful/len(questions)*100):.1f}%")
        if successful > 0:
            print(f"   平均時間: {(total_time/successful):.1f}秒")
        print(f"   総処理時間: {total_time:.1f}秒")
        
    except Exception as e:
        print(f"❌ 全体エラー: {e}")

if __name__ == "__main__":
    test_ollama_direct()