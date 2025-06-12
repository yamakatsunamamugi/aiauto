#!/usr/bin/env python3
"""
リアルタイム最新AIモデル情報取得
MCP Playwrightを使用して実際の公式サイトから最新情報を取得
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright

class RealTimeModelFetcher:
    """リアルタイムモデル情報取得クラス"""
    
    def __init__(self):
        self.results = {
            'fetch_time': datetime.now().isoformat(),
            'method': 'real_time_playwright_mcp',
            'services': {}
        }
    
    async def fetch_chatgpt_models(self):
        """ChatGPT最新モデル情報をリアルタイム取得"""
        print("🔍 ChatGPT公式サイトから最新モデル情報を取得中...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                print("🌐 https://chat.openai.com にアクセス中...")
                await page.goto('https://chat.openai.com', wait_until='networkidle', timeout=45000)
                
                # 少し待機
                await asyncio.sleep(5)
                
                title = await page.title()
                print(f"📄 ページタイトル: {title}")
                
                # ページの全テキストを取得
                page_text = await page.evaluate('document.body.innerText')
                
                # モデル名を正規表現で検索
                models_found = set()
                
                # より包括的なパターンで検索
                patterns = [
                    r'(?i)o1[\s-]*preview',
                    r'(?i)o1[\s-]*mini',
                    r'(?i)gpt[\s-]*4o[\s-]*mini',
                    r'(?i)gpt[\s-]*4o',
                    r'(?i)gpt[\s-]*4[\s-]*turbo',
                    r'(?i)gpt[\s-]*4',
                    r'(?i)gpt[\s-]*3\.5[\s-]*turbo',
                    r'(?i)claude[\s-]*3\.5[\s-]*sonnet',
                    r'(?i)claude[\s-]*3\.5[\s-]*haiku',
                    r'(?i)gemini[\s-]*2\.0[\s-]*flash',
                    r'(?i)gemini[\s-]*1\.5[\s-]*pro'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        clean_match = re.sub(r'\s+', ' ', match.strip())
                        if clean_match and len(clean_match) > 2:
                            models_found.add(clean_match)
                
                # DOM要素からも検索
                try:
                    # ボタンやリンクのテキストを検索
                    buttons = await page.query_selector_all('button, a, span, div')
                    print(f"🔍 {len(buttons)}個の要素を調査中...")
                    
                    for button in buttons[:100]:  # 最初の100個を確認
                        try:
                            text = await button.text_content()
                            if text and ('gpt' in text.lower() or 'o1' in text.lower() or 'model' in text.lower()):
                                for pattern in patterns:
                                    matches = re.findall(pattern, text)
                                    for match in matches:
                                        clean_match = re.sub(r'\s+', ' ', match.strip())
                                        if clean_match and len(clean_match) > 2:
                                            models_found.add(clean_match)
                        except:
                            continue
                            
                except Exception as e:
                    print(f"DOM検索エラー: {e}")
                
                await browser.close()
                
                # 結果を整理
                models_list = sorted(list(models_found))
                
                self.results['services']['chatgpt'] = {
                    'models': models_list,
                    'found_count': len(models_list),
                    'page_title': title,
                    'access_success': True
                }
                
                print(f"✅ ChatGPT: {len(models_list)}個のモデルを発見")
                for model in models_list:
                    print(f"  - {model}")
                
                return models_list
                
            except Exception as e:
                print(f"❌ ChatGPT取得エラー: {e}")
                await browser.close()
                self.results['services']['chatgpt'] = {
                    'models': [],
                    'error': str(e),
                    'access_success': False
                }
                return []
    
    async def fetch_claude_models(self):
        """Claude最新モデル情報をリアルタイム取得"""
        print("\n🔍 Claude公式サイトから最新モデル情報を取得中...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                print("🌐 https://claude.ai にアクセス中...")
                await page.goto('https://claude.ai', wait_until='networkidle', timeout=45000)
                
                await asyncio.sleep(5)
                
                title = await page.title()
                print(f"📄 ページタイトル: {title}")
                
                # ページの全テキストを取得
                page_text = await page.evaluate('document.body.innerText')
                
                models_found = set()
                
                # Claudeモデルのパターン
                claude_patterns = [
                    r'(?i)claude[\s-]*3\.5[\s-]*sonnet',
                    r'(?i)claude[\s-]*3\.5[\s-]*haiku',
                    r'(?i)claude[\s-]*3[\s-]*opus',
                    r'(?i)claude[\s-]*3[\s-]*sonnet',
                    r'(?i)claude[\s-]*3[\s-]*haiku'
                ]
                
                for pattern in claude_patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        clean_match = re.sub(r'\s+', ' ', match.strip())
                        if clean_match and len(clean_match) > 5:
                            models_found.add(clean_match)
                
                await browser.close()
                
                models_list = sorted(list(models_found))
                
                self.results['services']['claude'] = {
                    'models': models_list,
                    'found_count': len(models_list),
                    'page_title': title,
                    'access_success': True
                }
                
                print(f"✅ Claude: {len(models_list)}個のモデルを発見")
                for model in models_list:
                    print(f"  - {model}")
                
                return models_list
                
            except Exception as e:
                print(f"❌ Claude取得エラー: {e}")
                await browser.close()
                self.results['services']['claude'] = {
                    'models': [],
                    'error': str(e),
                    'access_success': False
                }
                return []
    
    async def fetch_gemini_models(self):
        """Gemini最新モデル情報をリアルタイム取得"""
        print("\n🔍 Gemini公式サイトから最新モデル情報を取得中...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                print("🌐 https://gemini.google.com にアクセス中...")
                await page.goto('https://gemini.google.com', wait_until='networkidle', timeout=45000)
                
                await asyncio.sleep(5)
                
                title = await page.title()
                print(f"📄 ページタイトル: {title}")
                
                # ページの全テキストを取得
                page_text = await page.evaluate('document.body.innerText')
                
                models_found = set()
                
                # Geminiモデルのパターン  
                gemini_patterns = [
                    r'(?i)gemini[\s-]*2\.0[\s-]*flash',
                    r'(?i)gemini[\s-]*1\.5[\s-]*pro',
                    r'(?i)gemini[\s-]*1\.5[\s-]*flash',
                    r'(?i)gemini[\s-]*1\.0[\s-]*pro'
                ]
                
                for pattern in gemini_patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        clean_match = re.sub(r'\s+', ' ', match.strip())
                        if clean_match and len(clean_match) > 5:
                            models_found.add(clean_match)
                
                await browser.close()
                
                models_list = sorted(list(models_found))
                
                self.results['services']['gemini'] = {
                    'models': models_list,
                    'found_count': len(models_list),
                    'page_title': title,
                    'access_success': True
                }
                
                print(f"✅ Gemini: {len(models_list)}個のモデルを発見")
                for model in models_list:
                    print(f"  - {model}")
                
                return models_list
                
            except Exception as e:
                print(f"❌ Gemini取得エラー: {e}")
                await browser.close()
                self.results['services']['gemini'] = {
                    'models': [],
                    'error': str(e),
                    'access_success': False
                }
                return []
    
    async def fetch_all_models(self):
        """全AIサービスの最新モデル情報を取得"""
        print("=" * 80)
        print("🚀 リアルタイム最新AIモデル情報取得開始")
        print("=" * 80)
        
        # 各サービスから情報を取得
        await self.fetch_chatgpt_models()
        await self.fetch_claude_models() 
        await self.fetch_gemini_models()
        
        # 結果を保存
        with open('config/real_time_ai_models.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print("📊 リアルタイム取得結果サマリー")
        print("=" * 80)
        
        total_models = 0
        for service, data in self.results['services'].items():
            model_count = len(data.get('models', []))
            total_models += model_count
            status = "✅ 成功" if data.get('access_success', False) else "❌ 失敗"
            print(f"{status} {service.upper()}: {model_count}個のモデル")
            
            if data.get('models'):
                print(f"    最新: {data['models'][0]}")
        
        print(f"\n📈 総モデル数: {total_models}個")
        print(f"💾 結果保存: config/real_time_ai_models.json")
        
        return self.results

async def main():
    """メイン実行"""
    fetcher = RealTimeModelFetcher()
    results = await fetcher.fetch_all_models()
    
    print("\n🎯 この結果が実際の最新モデル情報です！")
    return results

if __name__ == "__main__":
    results = asyncio.run(main())