#!/usr/bin/env python3
"""
AI Service DOM Selector Analysis Script

This script analyzes the DOM structure of various AI services to identify
automation-friendly selectors for text input, submission, and response areas.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Install with: pip install playwright")
    exit(1)


class AISelectorAnalyzer:
    """AI service DOM selector analyzer"""
    
    def __init__(self, headless: bool = False, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
    async def analyze_all_services(self):
        """すべてのAIサービスを分析"""
        services = {
            "Claude.ai": "https://claude.ai",
            "Gemini": "https://gemini.google.com", 
            "Genspark": "https://www.genspark.ai",
            "Google AI Studio": "https://aistudio.google.com",
            "ChatGPT": "https://chat.openai.com"
        }
        
        results = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 720}
            )
            
            for service_name, url in services.items():
                print(f"\n🔍 Analyzing {service_name}...")
                try:
                    result = await self.analyze_service(context, service_name, url)
                    results[service_name] = result
                    print(f"✅ {service_name} analysis completed")
                    
                    # 各サービス間で2秒待機
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Error analyzing {service_name}: {e}")
                    results[service_name] = {"error": str(e)}
            
            await browser.close()
            
        return results
    
    async def analyze_service(self, context, service_name: str, url: str):
        """個別サービスを分析"""
        page = await context.new_page()
        
        try:
            # ページに移動
            print(f"  → Navigating to {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
            await page.wait_for_timeout(3000)  # ページ読み込み待機
            
            # 基本情報取得
            title = await page.title()
            print(f"  → Page title: {title}")
            
            # セレクター分析
            analysis = {
                "service_name": service_name,
                "url": url,
                "title": title,
                "analyzed_at": datetime.now().isoformat(),
                "selectors": await self.find_ui_selectors(page),
                "login_indicators": await self.find_login_indicators(page),
                "dom_structure": await self.analyze_dom_structure(page)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing {service_name}: {e}")
            raise
            
        finally:
            await page.close()
    
    async def find_ui_selectors(self, page):
        """UI要素のセレクターを特定"""
        selectors = {
            "text_input": [],
            "submit_button": [],
            "response_area": [],
            "model_selector": [],
            "settings_button": []
        }
        
        # テキスト入力エリア候補
        input_candidates = [
            'textarea[placeholder*="message"]',
            'textarea[placeholder*="prompt"]',
            'textarea[placeholder*="ask"]',
            'textarea[placeholder*="type"]',
            'textarea[data-testid*="input"]',
            'textarea[aria-label*="input"]',
            'textarea[aria-label*="message"]',
            '[contenteditable="true"]',
            'input[type="text"][placeholder*="message"]',
            'div[role="textbox"]'
        ]
        
        for candidate in input_candidates:
            try:
                elements = await page.query_selector_all(candidate)
                if elements:
                    for i, element in enumerate(elements):
                        attrs = await self.get_element_attributes(element)
                        selectors["text_input"].append({
                            "selector": candidate,
                            "index": i,
                            "attributes": attrs
                        })
            except Exception:
                pass
        
        # 送信ボタン候補
        submit_candidates = [
            'button[data-testid*="send"]',
            'button[aria-label*="send"]',
            'button[aria-label*="submit"]',
            'button[type="submit"]',
            'button:has-text("Send")',
            'button:has-text("Submit")',
            '[role="button"]:has-text("Send")',
            'button svg[data-icon*="send"]',
            'button svg[data-icon*="arrow"]'
        ]
        
        for candidate in submit_candidates:
            try:
                elements = await page.query_selector_all(candidate)
                if elements:
                    for i, element in enumerate(elements):
                        attrs = await self.get_element_attributes(element)
                        selectors["submit_button"].append({
                            "selector": candidate,
                            "index": i,
                            "attributes": attrs
                        })
            except Exception:
                pass
        
        # レスポンスエリア候補
        response_candidates = [
            '[data-testid*="message"]',
            '[data-testid*="response"]',
            '[role="log"]',
            '[role="main"] > div',
            '.message-content',
            '.response-content',
            '[aria-live="polite"]',
            '[aria-live="assertive"]'
        ]
        
        for candidate in response_candidates:
            try:
                elements = await page.query_selector_all(candidate)
                if elements:
                    for i, element in enumerate(elements):
                        attrs = await self.get_element_attributes(element)
                        selectors["response_area"].append({
                            "selector": candidate,
                            "index": i,
                            "attributes": attrs
                        })
            except Exception:
                pass
        
        # モデル選択候補
        model_candidates = [
            'select[data-testid*="model"]',
            'button[data-testid*="model"]',
            '[aria-label*="model"]',
            '[aria-label*="Model"]',
            '.model-selector',
            '[role="combobox"]'
        ]
        
        for candidate in model_candidates:
            try:
                elements = await page.query_selector_all(candidate)
                if elements:
                    for i, element in enumerate(elements):
                        attrs = await self.get_element_attributes(element)
                        selectors["model_selector"].append({
                            "selector": candidate,
                            "index": i,
                            "attributes": attrs
                        })
            except Exception:
                pass
        
        return selectors
    
    async def find_login_indicators(self, page):
        """ログイン状態インジケーターを特定"""
        indicators = {
            "login_required": [],
            "logged_in": [],
            "user_menu": []
        }
        
        # ログイン必要インジケーター
        login_required_candidates = [
            'button:has-text("Sign in")',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'a:has-text("Sign in")',
            'a:has-text("Log in")',
            '[data-testid*="login"]',
            '[data-testid*="signin"]'
        ]
        
        for candidate in login_required_candidates:
            try:
                elements = await page.query_selector_all(candidate)
                if elements:
                    for element in elements:
                        attrs = await self.get_element_attributes(element)
                        indicators["login_required"].append({
                            "selector": candidate,
                            "attributes": attrs
                        })
            except Exception:
                pass
        
        # ログイン済みインジケーター
        logged_in_candidates = [
            '[data-testid*="user"]',
            '[data-testid*="avatar"]',
            '[aria-label*="user"]',
            '[aria-label*="profile"]',
            '.user-avatar',
            '.profile-button',
            'button[aria-haspopup="menu"]'
        ]
        
        for candidate in logged_in_candidates:
            try:
                elements = await page.query_selector_all(candidate)
                if elements:
                    for element in elements:
                        attrs = await self.get_element_attributes(element)
                        indicators["logged_in"].append({
                            "selector": candidate,
                            "attributes": attrs
                        })
            except Exception:
                pass
        
        return indicators
    
    async def analyze_dom_structure(self, page):
        """DOM構造を分析"""
        structure = {}
        
        try:
            # data-testid属性を持つ要素
            testid_elements = await page.query_selector_all('[data-testid]')
            structure["testid_elements"] = []
            
            for element in testid_elements[:20]:  # 最大20要素
                tag = await element.evaluate('el => el.tagName.toLowerCase()')
                testid = await element.get_attribute('data-testid')
                structure["testid_elements"].append({
                    "tag": tag,
                    "data-testid": testid
                })
            
            # aria-label属性を持つ要素
            aria_elements = await page.query_selector_all('[aria-label]')
            structure["aria_elements"] = []
            
            for element in aria_elements[:20]:
                tag = await element.evaluate('el => el.tagName.toLowerCase()')
                aria_label = await element.get_attribute('aria-label')
                structure["aria_elements"].append({
                    "tag": tag,
                    "aria-label": aria_label
                })
            
            # role属性を持つ要素
            role_elements = await page.query_selector_all('[role]')
            structure["role_elements"] = []
            
            for element in role_elements[:20]:
                tag = await element.evaluate('el => el.tagName.toLowerCase()')
                role = await element.get_attribute('role')
                structure["role_elements"].append({
                    "tag": tag,
                    "role": role
                })
                
        except Exception as e:
            structure["error"] = str(e)
        
        return structure
    
    async def get_element_attributes(self, element):
        """要素の属性を取得"""
        try:
            attrs = await element.evaluate('''
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            ''')
            
            # テキスト内容も取得
            text = await element.text_content()
            if text and len(text.strip()) > 0:
                attrs['text_content'] = text.strip()[:100]  # 最大100文字
            
            # プレースホルダーも取得
            placeholder = await element.get_attribute('placeholder')
            if placeholder:
                attrs['placeholder'] = placeholder
                
            return attrs
            
        except Exception:
            return {}


async def main():
    """メイン実行関数"""
    print("🚀 Starting AI Service DOM Selector Analysis...")
    
    analyzer = AISelectorAnalyzer(headless=True)  # ヘッドレスモードで実行
    results = await analyzer.analyze_all_services()
    
    # 結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/roudousha/Dropbox/5.AI-auto/ai_selectors_analysis_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 Analysis complete! Results saved to: {output_file}")
    
    # 結果サマリーを表示
    print("\n📊 Analysis Summary:")
    for service_name, data in results.items():
        if "error" in data:
            print(f"  ❌ {service_name}: {data['error']}")
        else:
            selectors = data.get('selectors', {})
            text_inputs = len(selectors.get('text_input', []))
            submit_buttons = len(selectors.get('submit_button', []))
            response_areas = len(selectors.get('response_area', []))
            
            print(f"  ✅ {service_name}:")
            print(f"    - Text inputs found: {text_inputs}")
            print(f"    - Submit buttons found: {submit_buttons}")
            print(f"    - Response areas found: {response_areas}")


if __name__ == "__main__":
    asyncio.run(main())