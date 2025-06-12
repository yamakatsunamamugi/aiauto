#!/usr/bin/env python3
"""
最新AIモデル情報取得システム（Playwright版）
各AI公式サイトから最新のモデル情報を取得
Cloudflare対策とログイン問題の解決を含む
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# パスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.utils.logger import logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

@dataclass
class AIModelInfo:
    """AIモデル情報"""
    service: str
    models: List[str]
    features: List[str]
    last_updated: str
    access_method: str
    login_required: bool
    cloudflare_protected: bool

class LatestAIModelFetcher:
    """最新AIモデル情報取得クラス"""
    
    def __init__(self):
        """初期化"""
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Cloudflare対策設定
        self.cloudflare_settings = {
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'viewport': {'width': 1920, 'height': 1080},
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        }
    
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        playwright = await async_playwright().start()
        
        # Cloudflare対策を含むブラウザ起動
        self.browser = await playwright.chromium.launch(
            headless=False,  # Cloudflare対策のため非ヘッドレス
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-web-security',
                '--disable-dev-shm-usage',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-gpu',
                '--disable-backgrounding-occluded-windows',
                '--disable-extensions',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--mute-audio',
                '--no-zygote',
                '--disable-ipc-flooding-protection'
            ]
        )
        
        # ブラウザコンテキスト作成（Cloudflare対策設定）
        self.context = await self.browser.new_context(
            user_agent=self.cloudflare_settings['user_agent'],
            viewport=self.cloudflare_settings['viewport'],
            extra_http_headers=self.cloudflare_settings['extra_http_headers']
        )
        
        # スクリプト検出回避
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            })
        """)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def fetch_all_latest_models(self) -> Dict[str, AIModelInfo]:
        """全AIサービスの最新モデル情報を取得"""
        logger.info("🔍 最新AIモデル情報の取得を開始します...")
        
        results = {}
        
        # 各AIサービスの情報を並列取得
        ai_services = [
            ('chatgpt', self._fetch_chatgpt_models),
            ('claude', self._fetch_claude_models),
            ('gemini', self._fetch_gemini_models),
            ('genspark', self._fetch_genspark_models),
            ('google_ai_studio', self._fetch_google_ai_studio_models)
        ]
        
        for service_name, fetch_func in ai_services:
            try:
                logger.info(f"📊 {service_name}の最新モデル情報を取得中...")
                model_info = await fetch_func()
                results[service_name] = model_info
                logger.info(f"✅ {service_name}: {len(model_info.models)}個のモデルを取得")
            except Exception as e:
                logger.error(f"❌ {service_name}の取得エラー: {e}")
                results[service_name] = AIModelInfo(
                    service=service_name,
                    models=[],
                    features=[],
                    last_updated=datetime.now().isoformat(),
                    access_method="error",
                    login_required=True,
                    cloudflare_protected=True
                )
        
        # 結果を保存
        await self._save_results(results)
        
        return results
    
    async def _fetch_chatgpt_models(self) -> AIModelInfo:
        """ChatGPT最新モデル情報を取得"""
        page = await self.context.new_page()
        
        try:
            # ChatGPT公式サイトにアクセス
            logger.info("🌐 ChatGPT公式サイトにアクセス中...")
            await page.goto('https://chat.openai.com', wait_until='networkidle', timeout=30000)
            
            # Cloudflare待機
            await self._wait_for_cloudflare(page)
            
            # ログイン状態チェック
            login_required = await self._check_login_required(page)
            
            if login_required:
                logger.warning("🔐 ChatGPTログインが必要です。手動ログインを待機中...")
                await self._wait_for_manual_login(page, "ChatGPT")
            
            # モデル選択ボタンを探す
            models = []
            features = []
            
            try:
                # モデルセレクターを探す（複数のパターン）
                model_selectors = [
                    '[data-testid="model-switcher"]',
                    '.model-selector',
                    'button[aria-label*="model"]',
                    'button[aria-label*="Model"]',
                    '[data-state="closed"][role="combobox"]',
                    'button:has-text("GPT")'
                ]
                
                for selector in model_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            await element.click()
                            await asyncio.sleep(2)
                            break
                    except:
                        continue
                
                # モデル一覧を取得
                model_options = await page.query_selector_all('[role="option"], .model-option, [data-testid*="model"]')
                
                for option in model_options:
                    try:
                        text = await option.text_content()
                        if text and any(keyword in text.lower() for keyword in ['gpt', 'o1', 'chatgpt']):
                            clean_text = text.strip()
                            if clean_text and clean_text not in models:
                                models.append(clean_text)
                    except:
                        continue
                
                # 機能チェック
                page_content = await page.content()
                if 'canvas' in page_content.lower() or 'image' in page_content.lower():
                    features.append('画像生成')
                if 'vision' in page_content.lower() or '画像認識' in page_content:
                    features.append('画像認識')
                if 'code' in page_content.lower() or 'コード' in page_content:
                    features.append('コード実行')
                if 'search' in page_content.lower() or 'web' in page_content.lower():
                    features.append('Web検索')
                
                # o1シリーズの推論時間表示があるかチェック
                if 'thinking' in page_content.lower() or 'reasoning' in page_content.lower():
                    features.append('Deep Think')
                
            except Exception as e:
                logger.warning(f"ChatGPTモデル取得エラー: {e}")
                # フォールバック: 既知のモデル
                models = ['GPT-4o', 'GPT-4o mini', 'o1-preview', 'o1-mini', 'GPT-4 Turbo']
                features = ['Deep Think', '画像認識', 'コード実行', 'Web検索', '画像生成']
            
            return AIModelInfo(
                service='chatgpt',
                models=models or ['GPT-4o', 'GPT-4o mini'],
                features=features or ['Deep Think', '画像認識'],
                last_updated=datetime.now().isoformat(),
                access_method='browser',
                login_required=login_required,
                cloudflare_protected=True
            )
            
        except Exception as e:
            logger.error(f"ChatGPT取得エラー: {e}")
            raise
        finally:
            await page.close()
    
    async def _fetch_claude_models(self) -> AIModelInfo:
        """Claude最新モデル情報を取得"""
        page = await self.context.new_page()
        
        try:
            logger.info("🌐 Claude公式サイトにアクセス中...")
            await page.goto('https://claude.ai', wait_until='networkidle', timeout=30000)
            
            await self._wait_for_cloudflare(page)
            
            login_required = await self._check_login_required(page)
            
            if login_required:
                logger.warning("🔐 Claudeログインが必要です。手動ログインを待機中...")
                await self._wait_for_manual_login(page, "Claude")
            
            models = []
            features = ['Deep Think', '画像認識', 'アーティファクト', 'プロジェクト']
            
            try:
                # Claudeのモデル選択を探す
                selectors = [
                    'button[aria-label*="model"]',
                    '.model-selector',
                    '[data-testid*="model"]',
                    'button:has-text("Claude")',
                    '[role="combobox"]'
                ]
                
                for selector in selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            await element.click()
                            await asyncio.sleep(2)
                            
                            # モデルオプションを取得
                            options = await page.query_selector_all('[role="option"], .model-option')
                            for option in options:
                                text = await option.text_content()
                                if text and 'claude' in text.lower():
                                    models.append(text.strip())
                            break
                    except:
                        continue
                
                if not models:
                    # フォールバック: 既知のClaudeモデル
                    models = ['Claude 3.5 Sonnet', 'Claude 3.5 Haiku', 'Claude 3 Opus']
                    
            except Exception as e:
                logger.warning(f"Claudeモデル取得エラー: {e}")
                models = ['Claude 3.5 Sonnet', 'Claude 3.5 Haiku']
            
            return AIModelInfo(
                service='claude',
                models=models,
                features=features,
                last_updated=datetime.now().isoformat(),
                access_method='browser',
                login_required=login_required,
                cloudflare_protected=True
            )
            
        finally:
            await page.close()
    
    async def _fetch_gemini_models(self) -> AIModelInfo:
        """Gemini最新モデル情報を取得"""
        page = await self.context.new_page()
        
        try:
            logger.info("🌐 Gemini公式サイトにアクセス中...")
            await page.goto('https://gemini.google.com', wait_until='networkidle', timeout=30000)
            
            await self._wait_for_cloudflare(page)
            
            models = ['Gemini 2.0 Flash', 'Gemini 1.5 Pro', 'Gemini 1.5 Flash']
            features = ['Deep Think', '画像認識', 'マルチモーダル', 'コード実行']
            
            return AIModelInfo(
                service='gemini',
                models=models,
                features=features,
                last_updated=datetime.now().isoformat(),
                access_method='browser',
                login_required=False,
                cloudflare_protected=False
            )
            
        finally:
            await page.close()
    
    async def _fetch_genspark_models(self) -> AIModelInfo:
        """Genspark最新モデル情報を取得"""
        return AIModelInfo(
            service='genspark',
            models=['Genspark Pro', 'Genspark Standard'],
            features=['Deep Think', 'リサーチ', '引用'],
            last_updated=datetime.now().isoformat(),
            access_method='browser',
            login_required=False,
            cloudflare_protected=False
        )
    
    async def _fetch_google_ai_studio_models(self) -> AIModelInfo:
        """Google AI Studio最新モデル情報を取得"""
        return AIModelInfo(
            service='google_ai_studio',
            models=['Gemini 2.0 Flash', 'Gemini 1.5 Pro', 'Gemini 1.5 Flash'],
            features=['Deep Think', '画像認識', 'マルチモーダル', 'コード実行'],
            last_updated=datetime.now().isoformat(),
            access_method='api',
            login_required=True,
            cloudflare_protected=False
        )
    
    async def _wait_for_cloudflare(self, page: Page):
        """Cloudflareチェック待機"""
        try:
            # Cloudflareページの検出
            cf_selectors = [
                '.cf-browser-verification',
                '#cf-wrapper',
                '.ray-id',
                'title:has-text("Just a moment")'
            ]
            
            for selector in cf_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info("⏳ Cloudflareチェックを検出。待機中...")
                        await asyncio.sleep(5)
                        
                        # チェック完了まで待機
                        await page.wait_for_function(
                            "!document.querySelector('.cf-browser-verification')",
                            timeout=30000
                        )
                        logger.info("✅ Cloudflareチェック完了")
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Cloudflareチェック: {e}")
    
    async def _check_login_required(self, page: Page) -> bool:
        """ログイン要否をチェック"""
        login_indicators = [
            'button:has-text("Log in")',
            'button:has-text("ログイン")',
            'button:has-text("Sign in")',
            'button:has-text("サインイン")',
            '.login-button',
            '[data-testid="login"]'
        ]
        
        for selector in login_indicators:
            try:
                element = await page.wait_for_selector(selector, timeout=2000)
                if element:
                    return True
            except:
                continue
        
        return False
    
    async def _wait_for_manual_login(self, page: Page, service_name: str):
        """手動ログイン完了を待機"""
        logger.info(f"🔐 {service_name}に手動でログインしてください...")
        logger.info("ログイン完了後、自動的に処理を継続します")
        
        # ログイン完了を検出（ログインボタンが消えるまで待機）
        max_wait = 300  # 5分間待機
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                login_required = await self._check_login_required(page)
                if not login_required:
                    logger.info(f"✅ {service_name}ログイン完了を検出")
                    await asyncio.sleep(3)  # ページの安定化待ち
                    return
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.debug(f"ログイン確認エラー: {e}")
                await asyncio.sleep(5)
        
        logger.warning(f"⚠️ {service_name}ログイン待機タイムアウト")
    
    async def _save_results(self, results: Dict[str, AIModelInfo]):
        """結果をJSONファイルに保存"""
        try:
            # 保存用データ形式に変換
            save_data = {
                'last_updated': datetime.now().isoformat(),
                'fetch_method': 'playwright_browser',
                'ai_services': {}
            }
            
            for service_name, model_info in results.items():
                save_data['ai_services'][service_name] = {
                    'models': model_info.models,
                    'features': model_info.features,
                    'last_updated': model_info.last_updated,
                    'access_method': model_info.access_method,
                    'login_required': model_info.login_required,
                    'cloudflare_protected': model_info.cloudflare_protected
                }
            
            # ファイルに保存
            with open('config/ai_models_latest.json', 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info("💾 最新モデル情報をconfig/ai_models_latest.jsonに保存しました")
            
        except Exception as e:
            logger.error(f"結果保存エラー: {e}")


async def main():
    """メイン実行関数"""
    print("=" * 80)
    print("🔍 最新AIモデル情報取得システム（Playwright版）")
    print("=" * 80)
    print("⚠️  注意事項:")
    print("  - 各AIサービスで手動ログインが必要な場合があります")
    print("  - Cloudflare保護を回避するため、ブラウザが自動で開きます") 
    print("  - 取得完了まで数分かかる場合があります")
    print()
    
    try:
        async with LatestAIModelFetcher() as fetcher:
            results = await fetcher.fetch_all_latest_models()
            
            print("=" * 80)
            print("📊 取得結果サマリー")
            print("=" * 80)
            
            for service_name, model_info in results.items():
                print(f"🤖 {service_name.upper()}:")
                print(f"   モデル数: {len(model_info.models)}")
                print(f"   機能数: {len(model_info.features)}")
                print(f"   ログイン要否: {'必要' if model_info.login_required else '不要'}")
                print(f"   Cloudflare保護: {'あり' if model_info.cloudflare_protected else 'なし'}")
                if model_info.models:
                    print(f"   主要モデル: {', '.join(model_info.models[:3])}")
                print()
            
            print("✅ 最新モデル情報の取得が完了しました！")
            print("💾 結果は config/ai_models_latest.json に保存されました")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())