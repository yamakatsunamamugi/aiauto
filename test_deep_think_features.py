#!/usr/bin/env python3
"""
各AIサービスのDeep Think機能の存在を確認するためのテストスクリプト
実行して、実際のUIで利用可能な機能を確認する
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def check_ai_service_features():
    """各AIサービスのUIを開いて機能を手動確認するためのヘルパー"""
    
    services = {
        "Claude": "https://claude.ai",
        "ChatGPT": "https://chat.openai.com", 
        "Gemini": "https://gemini.google.com",
        "Genspark": "https://www.genspark.ai",
        "Google AI Studio": "https://aistudio.google.com"
    }
    
    print("=" * 80)
    print("AI Services Deep Think機能調査")
    print("=" * 80)
    print("\n各サービスのページを開きます。以下を確認してください：\n")
    
    print("【確認項目】")
    print("1. 'Think harder'、'Deep thinking'、'詳細モード'等のオプションがあるか")
    print("2. モデル選択で思考深度を変更できるか")
    print("3. 設定やトグルスイッチで推論モードを変更できるか")
    print("4. システムプロンプトや設定で同等の機能を実現できるか")
    print("\n" + "=" * 80 + "\n")
    
    driver = webdriver.Chrome()
    findings = {}
    
    try:
        for service, url in services.items():
            print(f"\n📍 {service}を確認中...")
            print(f"   URL: {url}")
            driver.get(url)
            
            # ユーザーが確認する時間を確保
            input(f"\n⏸️  {service}のUIを確認してください。確認が終わったらEnterキーを押してください...")
            
            # ユーザーからの入力を記録
            print(f"\n📝 {service}の調査結果を入力してください：")
            has_deep_think = input("   Deep Think相当の機能はありますか？ (y/n): ").lower() == 'y'
            
            if has_deep_think:
                feature_name = input("   機能の名前は何ですか？: ")
                location = input("   どこにありますか？（例：設定メニュー、入力欄の近く）: ")
                selector_hint = input("   要素の特徴（テキスト、クラス名など）: ")
                
                findings[service] = {
                    "has_feature": True,
                    "feature_name": feature_name,
                    "location": location,
                    "selector_hint": selector_hint
                }
            else:
                alternative = input("   代替手段はありますか？（例：モデル選択、プロンプト）: ")
                findings[service] = {
                    "has_feature": False,
                    "alternative": alternative
                }
    
    finally:
        driver.quit()
    
    # 調査結果を保存
    save_findings(findings)
    return findings

def save_findings(findings):
    """調査結果を保存"""
    report = f"""
# Deep Think機能調査レポート
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 調査結果サマリー

"""
    
    for service, data in findings.items():
        report += f"\n### {service}\n"
        if data.get("has_feature"):
            report += f"- ✅ Deep Think相当機能: **あり**\n"
            report += f"- 機能名: {data['feature_name']}\n"
            report += f"- 場所: {data['location']}\n"
            report += f"- セレクタヒント: `{data['selector_hint']}`\n"
        else:
            report += f"- ❌ Deep Think相当機能: **なし**\n"
            report += f"- 代替手段: {data['alternative']}\n"
    
    report += "\n## 実装推奨事項\n\n"
    
    # 実装可能な機能があるかチェック
    implementable = [s for s, d in findings.items() if d.get("has_feature")]
    
    if implementable:
        report += f"以下のサービスで実装可能: {', '.join(implementable)}\n"
    else:
        report += "Deep Think機能は見つかりませんでした。代替アプローチを検討してください。\n"
    
    with open("deep_think_research_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n📄 レポートを deep_think_research_report.md に保存しました")

if __name__ == "__main__":
    check_ai_service_features()