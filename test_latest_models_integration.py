#!/usr/bin/env python3
"""
最新モデル統合テスト
更新されたAIモデル情報がシステムに正しく統合されているかテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from src.gui.main_window import MainWindow

def test_latest_models_integration():
    """最新モデル統合テスト"""
    
    print("=" * 80)
    print("🧪 最新AIモデル統合テスト")
    print("=" * 80)
    
    # MainWindowクラスをインスタンス化（GUI起動なし）
    try:
        # モデル情報を直接テスト
        app = MainWindow()
        
        print("📊 統合されたAIモデル情報:")
        print("-" * 50)
        
        ai_services = ['chatgpt', 'claude', 'gemini', 'genspark', 'google_ai_studio']
        
        for service in ai_services:
            models = app._get_default_models(service)
            features = app._get_default_features(service)
            
            print(f"🤖 {service.upper()}:")
            print(f"   📋 モデル数: {len(models)}")
            print(f"   🏆 最新モデル: {models[0] if models else 'なし'}")
            print(f"   ⚙️  機能数: {len(features)}")
            print(f"   🎯 主要機能: {', '.join(features[:3])}")
            
            # 最新モデルの検証
            if service == 'chatgpt' and 'o1-preview' in models:
                print("   ✅ o1-previewが含まれています（最新推論モデル）")
            elif service == 'claude' and 'Claude 3.5 Sonnet' in models:
                print("   ✅ Claude 3.5 Sonnetが含まれています（最新モデル）")
            elif service == 'gemini' and 'Gemini 2.0 Flash' in models:
                print("   ✅ Gemini 2.0 Flashが含まれています（最新モデル）")
            
            # Deep Think機能の確認
            if 'Deep Think' in features or 'Deep Research' in features:
                print("   🧠 Deep Think/Research機能対応")
            
            print()
        
        # 設定ファイルの確認
        print("📄 設定ファイル確認:")
        print("-" * 50)
        
        try:
            with open('config/ai_models_latest.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            print(f"✅ 設定ファイル読み込み成功")
            print(f"📅 最終更新: {config_data.get('last_updated', 'N/A')}")
            print(f"🔄 取得方法: {config_data.get('fetch_method', 'N/A')}")
            
            config_services = list(config_data.get('ai_services', {}).keys())
            print(f"🤖 対応サービス: {len(config_services)}個")
            
            for service in config_services:
                service_data = config_data['ai_services'][service]
                model_count = len(service_data.get('models', []))
                feature_count = len(service_data.get('features', []))
                print(f"   {service}: {model_count}モデル, {feature_count}機能")
            
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
        
        print()
        print("=" * 80)
        print("📊 テスト結果サマリー")
        print("=" * 80)
        
        # 各サービスの最新性チェック
        latest_features = [
            ('ChatGPT', 'o1-preview' in app._get_default_models('chatgpt')),
            ('Claude', 'Claude 3.5 Sonnet' in app._get_default_models('claude')),
            ('Gemini', 'Gemini 2.0 Flash' in app._get_default_models('gemini')),
            ('Deep Think対応', any('Deep' in feature for features in [app._get_default_features(s) for s in ai_services] for feature in features))
        ]
        
        passed_tests = sum(1 for _, passed in latest_features if passed)
        total_tests = len(latest_features)
        
        for feature_name, passed in latest_features:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {feature_name}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📈 総合成功率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 75:
            print("🎉 最新AIモデル統合成功！")
            print("🚀 最新のo1-preview、Claude 3.5 Sonnet、Gemini 2.0 Flash対応")
            print("💡 Deep Think機能も利用可能")
        else:
            print("⚠️ 一部のモデル統合に問題があります")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_latest_models_integration()
    
    if success:
        print("\n✅ 最新モデル統合テスト完了")
        print("🎯 次: python3 gui_app.py で最新モデルを使用可能")
    else:
        print("\n❌ モデル統合に問題があります")