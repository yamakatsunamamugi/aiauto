#!/usr/bin/env python3
"""
最新AIモデル情報の手動更新
（2025年6月12日時点の最新情報）
"""

import json
from datetime import datetime

def update_latest_ai_models():
    """最新のAIモデル情報で更新"""
    
    # 2025年6月12日時点の最新モデル情報
    latest_models = {
        "last_updated": datetime.now().isoformat(),
        "fetch_method": "manual_verification_2025_06_12",
        "ai_services": {
            "chatgpt": {
                "models": [
                    "o1-preview",  # 最新の推論モデル
                    "o1-mini",     # 軽量版推論モデル
                    "GPT-4o",      # 最新のマルチモーダルモデル
                    "GPT-4o mini", # 軽量版マルチモーダル
                    "GPT-4 Turbo", # 従来の高性能モデル
                    "GPT-4",       # 標準モデル
                    "GPT-3.5 Turbo" # 高速モデル
                ],
                "features": [
                    "Deep Think",    # o1シリーズの推論機能
                    "画像認識",      # Vision機能
                    "画像生成",      # DALL-E統合
                    "コード実行",    # Code Interpreter
                    "Web検索",       # Browsing機能
                    "ファイル分析",  # Advanced Data Analysis
                    "カスタムGPT",   # GPTs機能
                    "音声対話"       # Voice機能
                ],
                "last_updated": datetime.now().isoformat(),
                "access_method": "browser",
                "login_required": True,
                "cloudflare_protected": True,
                "notes": "o1シリーズは推論時間が表示される。GPT-4oは最新のマルチモーダル対応"
            },
            "claude": {
                "models": [
                    "Claude 3.5 Sonnet",    # 最新・最高性能
                    "Claude 3.5 Haiku",     # 高速版
                    "Claude 3 Opus",        # 従来の最高性能
                    "Claude 3 Sonnet",      # バランス型
                    "Claude 3 Haiku"        # 高速型
                ],
                "features": [
                    "Deep Think",      # 思考プロセス表示
                    "画像認識",        # Vision機能
                    "アーティファクト", # Artifacts機能
                    "プロジェクト",     # Projects機能
                    "200K Context",    # 長文対応
                    "コード実行",      # MCP対応
                    "ファイル分析"     # PDF等の分析
                ],
                "last_updated": datetime.now().isoformat(),
                "access_method": "browser",
                "login_required": True,
                "cloudflare_protected": True,
                "notes": "Claude 3.5 Sonnetが最新で最高性能。Artifactsでコード実行可能"
            },
            "gemini": {
                "models": [
                    "Gemini 2.0 Flash",     # 最新・最高性能
                    "Gemini 1.5 Pro",      # 従来の高性能
                    "Gemini 1.5 Flash",    # 高速版
                    "Gemini 1.0 Pro"       # 標準版
                ],
                "features": [
                    "Deep Think",         # 推論機能
                    "画像認識",           # マルチモーダル
                    "動画分析",           # Video理解
                    "音声認識",           # Audio理解
                    "コード実行",         # Code Execution
                    "リアルタイム検索",   # Search Integration
                    "長文対応",           # 2M tokens
                    "Live API"            # リアルタイムAPI
                ],
                "last_updated": datetime.now().isoformat(),
                "access_method": "browser",
                "login_required": False,
                "cloudflare_protected": False,
                "notes": "Gemini 2.0 Flashは最新。Live APIでリアルタイム対話可能"
            },
            "genspark": {
                "models": [
                    "Genspark Pro",
                    "Genspark Standard"
                ],
                "features": [
                    "Deep Research",   # 詳細リサーチ
                    "引用付き回答",     # Source Citation
                    "リアルタイム検索", # Real-time Search
                    "マルチソース統合"  # Multi-source
                ],
                "last_updated": datetime.now().isoformat(),
                "access_method": "browser",
                "login_required": False,
                "cloudflare_protected": False,
                "notes": "リサーチ特化AI。引用付きで信頼性が高い"
            },
            "google_ai_studio": {
                "models": [
                    "Gemini 2.0 Flash",
                    "Gemini 1.5 Pro",
                    "Gemini 1.5 Flash",
                    "Gemini 1.0 Pro"
                ],
                "features": [
                    "API Access",      # プログラマティックアクセス
                    "Fine-tuning",     # カスタムモデル作成
                    "Prompt Design",   # プロンプト設計支援
                    "Batch Processing", # バッチ処理
                    "マルチモーダル",   # 画像・音声・動画
                    "Function Calling" # 関数呼び出し
                ],
                "last_updated": datetime.now().isoformat(),
                "access_method": "api",
                "login_required": True,
                "cloudflare_protected": False,
                "notes": "Google AI Studioは開発者向け。API経由でアクセス可能"
            }
        }
    }
    
    # ファイルに保存
    with open('config/ai_models_latest.json', 'w', encoding='utf-8') as f:
        json.dump(latest_models, f, indent=2, ensure_ascii=False)
    
    print("✅ 最新AIモデル情報を更新しました")
    print("📊 更新されたモデル:")
    
    for service, info in latest_models["ai_services"].items():
        print(f"  🤖 {service.upper()}: {len(info['models'])}個のモデル")
        print(f"     最新: {info['models'][0] if info['models'] else 'なし'}")
        print(f"     機能: {len(info['features'])}個")
        print()

if __name__ == "__main__":
    update_latest_ai_models()