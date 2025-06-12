#!/usr/bin/env python3
"""
Ollama統合システム スタンドアロンテスト
簡単にOllamaでAI処理をテストできます
"""

from src.automation.ollama_handler import OllamaAIHandler
from src.automation.ollama_config import OllamaConfig

def main():
    print("🤖 Ollama AI統合システム スタンドアロンテスト")
    print("=" * 50)
    
    try:
        # ハンドラー初期化
        print("🔄 Ollamaハンドラーを初期化中...")
        handler = OllamaAIHandler()
        print("✅ 初期化完了！")
        
        # 利用可能なモデルを表示
        print(f"\n📋 利用可能なモデル: {handler.available_models}")
        
        # 設定情報を表示
        config = OllamaConfig.get_default_config()
        print(f"\n⚙️ デフォルト設定:")
        print(f"   - デフォルトモデル: {config['default_model']}")
        print(f"   - システムプロンプト: {list(config['system_prompts'].keys())}")
        
        # 推奨設定を表示
        recommendations = OllamaConfig.get_model_recommendations()
        print(f"\n🎯 用途別推奨設定:")
        for purpose, settings in recommendations.items():
            print(f"   - {purpose}: {settings['model']} ({settings['description']})")
        
        print("\n" + "=" * 50)
        print("💬 対話テストを開始します。'quit'で終了")
        print("=" * 50)
        
        while True:
            # ユーザー入力
            user_input = input("\n質問を入力してください: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '終了', 'q']:
                break
                
            if not user_input:
                continue
            
            print("🔄 処理中...")
            
            # AI処理実行
            result = handler.process_text(
                text=user_input,
                model="llama3.1:8b",
                system_prompt="親切で丁寧な日本語のアシスタントとして回答してください。"
            )
            
            if result["success"]:
                print(f"🤖 回答: {result['result']}")
                print(f"⏱️ 処理時間: {result['processing_time']:.2f}秒")
            else:
                print(f"❌ エラー: {result['error']}")
        
        # 最終統計
        stats = handler.get_statistics()
        print(f"\n📊 セッション統計:")
        print(f"   - 総リクエスト数: {stats['total_requests']}")
        print(f"   - 成功: {stats['successful_requests']}")
        print(f"   - 失敗: {stats['failed_requests']}")
        print(f"   - 平均処理時間: {stats['average_response_time']:.2f}秒")
        
        print("\n👋 テストを終了しました。ありがとうございました！")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("\n📋 トラブルシューティング:")
        print("1. Ollamaがインストールされているか確認: ollama --version")
        print("2. Ollamaサービスが起動しているか確認: ollama list")
        print("3. llama3.1:8bモデルがダウンロードされているか確認")

if __name__ == "__main__":
    main()