#!/usr/bin/env python3
"""
Ollama機能テスト
"""
import ollama
import time

def feature_test():
    print("🔧 Ollama 機能テスト")
    print("=" * 30)
    
    client = ollama.Client()
    
    # テスト1: 基本会話
    print("\n1️⃣ 基本会話テスト")
    try:
        response = client.chat(
            model="llama3.1:8b",
            messages=[{"role": "user", "content": "あなたの名前は？"}]
        )
        print(f"✅ 回答: {response['message']['content'][:50]}...")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    # テスト2: システムプロンプト
    print("\n2️⃣ システムプロンプトテスト")
    try:
        response = client.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": "あなたは関西弁で話すキャラクターです。"},
                {"role": "user", "content": "こんにちは"}
            ]
        )
        print(f"✅ 関西弁回答: {response['message']['content'][:50]}...")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    # テスト3: 連続会話
    print("\n3️⃣ 連続会話テスト")
    try:
        messages = [
            {"role": "user", "content": "私の名前はテストユーザーです"},
            {"role": "assistant", "content": "こんにちは、テストユーザーさん！"},
            {"role": "user", "content": "私の名前を覚えていますか？"}
        ]
        
        response = client.chat(
            model="llama3.1:8b",
            messages=messages
        )
        print(f"✅ 記憶テスト: {response['message']['content'][:50]}...")
        has_name = "テストユーザー" in response['message']['content']
        print(f"   名前記憶: {'✅ 成功' if has_name else '❌ 失敗'}")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    # テスト4: 数学計算
    print("\n4️⃣ 計算能力テスト")
    math_questions = [
        ("10 + 25 =", "35"),
        ("8 × 7 =", "56"),
        ("100 ÷ 4 =", "25")
    ]
    
    for question, expected in math_questions:
        try:
            response = client.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": question}]
            )
            answer = response['message']['content']
            contains_expected = expected in answer
            print(f"   {question} → {'✅' if contains_expected else '❌'} {answer[:20]}...")
        except Exception as e:
            print(f"   {question} → ❌ エラー: {e}")
    
    # テスト5: 日本語理解
    print("\n5️⃣ 日本語理解テスト")
    japanese_tests = [
        "敬語で挨拶してください",
        "「桜」の季節はいつですか？",
        "「おつかれさまでした」の意味は？"
    ]
    
    for test_q in japanese_tests:
        try:
            response = client.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": test_q}]
            )
            answer = response['message']['content']
            print(f"   Q: {test_q[:20]}... → ✅ {answer[:30]}...")
        except Exception as e:
            print(f"   Q: {test_q[:20]}... → ❌ {e}")
    
    # テスト6: モデル情報
    print("\n6️⃣ モデル情報テスト")
    try:
        models = client.list()
        print(f"✅ 利用可能モデル数: {len(models['models'])}")
        for model in models['models']:
            name = model.get('name', 'Unknown')
            size = model.get('size', 0)
            print(f"   - {name}: {size//1000000000:.1f}GB")
    except Exception as e:
        print(f"❌ モデル情報取得エラー: {e}")
    
    print(f"\n🎉 機能テスト完了！")

if __name__ == "__main__":
    feature_test()