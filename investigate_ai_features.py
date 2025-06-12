#!/usr/bin/env python3
"""
AIサービスの機能調査スクリプト（モデル選択とDeep Think機能）
プロのアプローチ：まず事実を収集する
"""

import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class AIFeatureInvestigator:
    """AIサービスの機能を調査するクラス"""
    
    def __init__(self):
        self.driver = None
        self.findings = {}
        
    def investigate_all_services(self):
        """全サービスを調査"""
        services = {
            "claude": {
                "url": "https://claude.ai", 
                "name": "Claude",
                "expected_models": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-haiku"]
            },
            "chatgpt": {
                "url": "https://chat.openai.com",
                "name": "ChatGPT", 
                "expected_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
            },
            "gemini": {
                "url": "https://gemini.google.com",
                "name": "Gemini",
                "expected_models": ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
            },
            "genspark": {
                "url": "https://www.genspark.ai",
                "name": "Genspark",
                "expected_models": ["default", "advanced"]
            },
            "google_ai_studio": {
                "url": "https://aistudio.google.com",
                "name": "Google AI Studio",
                "expected_models": ["gemini-1.5-pro", "gemini-1.5-flash"]
            }
        }
        
        self.driver = webdriver.Chrome()
        
        try:
            for service_id, service_info in services.items():
                print(f"\n{'='*60}")
                print(f"🔍 {service_info['name']} の調査開始")
                print(f"{'='*60}")
                
                self.driver.get(service_info['url'])
                time.sleep(3)  # ページ読み込み待機
                
                # 自動調査を試みる
                findings = self.auto_investigate(service_id, service_info)
                
                # 手動確認も促す
                print(f"\n📋 {service_info['name']} の手動確認")
                print("以下の項目を確認してください：")
                print("1. モデル選択ドロップダウンの存在と位置")
                print("2. 'Think harder'等の思考モードオプション")
                print("3. その他の高度な設定オプション")
                
                manual_findings = self.manual_investigation(service_info['name'])
                
                # 結果をマージ
                self.findings[service_id] = {
                    **findings,
                    **manual_findings,
                    "timestamp": datetime.now().isoformat()
                }
                
        finally:
            if self.driver:
                self.driver.quit()
        
        # 結果を保存
        self.save_findings()
        self.generate_implementation_plan()
        
    def auto_investigate(self, service_id, service_info):
        """自動で要素を探索"""
        findings = {
            "service_name": service_info['name'],
            "url": service_info['url'],
            "model_selector": None,
            "deep_think_features": [],
            "other_features": []
        }
        
        # モデルセレクタを探す
        model_selectors = [
            # 一般的なパターン
            "button[aria-label*='model' i]",
            "button[data-testid*='model' i]",
            "select[name*='model' i]",
            "div[class*='model-selector' i]",
            "div[class*='model-picker' i]",
            # サービス固有
            f"button:contains('{service_info['expected_models'][0]}')" if service_info['expected_models'] else None
        ]
        
        for selector in filter(None, model_selectors):
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                findings["model_selector"] = {
                    "found": True,
                    "selector": selector,
                    "text": element.text[:50] if element.text else "No text"
                }
                print(f"✅ モデルセレクタ発見: {selector}")
                break
            except:
                continue
        
        # Deep Think機能を探す
        think_patterns = [
            # テキストベース
            "//*[contains(text(), 'think harder')]",
            "//*[contains(text(), 'Think harder')]",
            "//*[contains(text(), 'deep think')]",
            "//*[contains(text(), 'reasoning')]",
            "//*[contains(text(), '詳細')]",
            # 属性ベース
            "//*[contains(@aria-label, 'think')]",
            "//button[contains(@class, 'think')]",
            "//input[@type='checkbox'][contains(@name, 'think')]"
        ]
        
        for pattern in think_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for element in elements[:3]:  # 最初の3つまで
                    findings["deep_think_features"].append({
                        "xpath": pattern,
                        "text": element.text[:50] if element.text else "No text",
                        "tag": element.tag_name
                    })
            except:
                continue
        
        return findings
        
    def manual_investigation(self, service_name):
        """手動調査の結果を収集"""
        manual_findings = {}
        
        input(f"\n⏸️  {service_name}のページを確認してください。準備ができたらEnterを押してください...")
        
        # モデル選択について
        has_model_selector = input("モデル選択機能はありますか？ (y/n): ").lower() == 'y'
        if has_model_selector:
            manual_findings["manual_model_selector"] = {
                "exists": True,
                "location": input("  場所の説明（例：右上のドロップダウン）: "),
                "interaction": input("  操作方法（クリック、ホバー等）: "),
                "visible_models": input("  表示されているモデル名（カンマ区切り）: ")
            }
        
        # Deep Think機能について
        has_deep_think = input("Deep Think/Think harder機能はありますか？ (y/n): ").lower() == 'y'
        if has_deep_think:
            manual_findings["manual_deep_think"] = {
                "exists": True,
                "name": input("  正確な機能名: "),
                "location": input("  場所の説明: "),
                "type": input("  UIタイプ（チェックボックス、トグル、ボタン等）: ")
            }
        
        return manual_findings
        
    def save_findings(self):
        """調査結果を保存"""
        output_file = "ai_features_investigation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.findings, f, indent=2, ensure_ascii=False)
        print(f"\n💾 調査結果を {output_file} に保存しました")
        
    def generate_implementation_plan(self):
        """実装計画を生成"""
        plan = f"""# AI機能実装計画

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 調査結果サマリー

"""
        
        # モデル選択機能
        model_selector_services = []
        deep_think_services = []
        
        for service_id, data in self.findings.items():
            service_name = data.get('service_name', service_id)
            
            # モデルセレクタ
            if data.get('model_selector', {}).get('found') or data.get('manual_model_selector', {}).get('exists'):
                model_selector_services.append(service_name)
                
            # Deep Think
            if data.get('deep_think_features') or data.get('manual_deep_think', {}).get('exists'):
                deep_think_services.append(service_name)
        
        plan += f"### モデル選択機能\n"
        plan += f"- 実装可能なサービス: {', '.join(model_selector_services) if model_selector_services else 'なし'}\n\n"
        
        plan += f"### Deep Think機能\n"
        plan += f"- 実装可能なサービス: {', '.join(deep_think_services) if deep_think_services else 'なし'}\n\n"
        
        # 実装推奨事項
        plan += "## 実装推奨事項\n\n"
        
        if model_selector_services:
            plan += "### 1. モデル選択機能の実装\n"
            plan += "- ai_service_selectors.jsonに各サービスのモデルセレクタを追加\n"
            plan += "- 各AIハンドラーにselect_model()メソッドを実装\n"
            plan += "- GUIでモデル選択をサポート\n\n"
        
        if deep_think_services:
            plan += "### 2. Deep Think機能の実装\n"
            plan += "- 機能トグルのセレクタを追加\n"
            plan += "- 各AIハンドラーにenable_deep_think()メソッドを実装\n\n"
        
        if not model_selector_services and not deep_think_services:
            plan += "### 代替アプローチ\n"
            plan += "- プロンプトエンジニアリングでの実現を検討\n"
            plan += "- システムプロンプトの活用\n"
            plan += "- 高性能モデルの固定選択\n"
        
        with open("implementation_plan.md", 'w', encoding='utf-8') as f:
            f.write(plan)
        print(f"📋 実装計画を implementation_plan.md に保存しました")

if __name__ == "__main__":
    investigator = AIFeatureInvestigator()
    investigator.investigate_all_services()