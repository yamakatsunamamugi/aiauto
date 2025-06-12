#!/usr/bin/env python3
"""
AIサービスのセレクタを動的に更新するユーティリティ
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    from playwright.sync_api import sync_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)


class AISelectorUpdater:
    """AIサービスのセレクタを動的に検出・更新"""
    
    def __init__(self):
        self.selectors_file = Path("config/ai_selectors_dynamic.json")
        self.selectors = self.load_selectors()
        
    def load_selectors(self) -> Dict[str, Any]:
        """保存されたセレクタを読み込み"""
        if self.selectors_file.exists():
            with open(self.selectors_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
        
    def save_selectors(self):
        """セレクタを保存"""
        self.selectors_file.parent.mkdir(exist_ok=True)
        with open(self.selectors_file, 'w', encoding='utf-8') as f:
            json.dump(self.selectors, f, indent=2, ensure_ascii=False)
            
    def detect_chatgpt_selectors(self, page: Page) -> Dict[str, str]:
        """ChatGPTのセレクタを検出"""
        selectors = {}
        
        try:
            # 入力欄を検出
            input_candidates = [
                'textarea[placeholder*="Message"]',
                'textarea[placeholder*="Send a message"]',
                'textarea[data-id="root"]',
                'textarea.m-0',
                'div[contenteditable="true"] p'
            ]
            
            for selector in input_candidates:
                if page.query_selector(selector):
                    selectors['input'] = selector
                    logger.info(f"ChatGPT入力欄セレクタ検出: {selector}")
                    break
                    
            # 送信ボタンを検出
            send_candidates = [
                'button[data-testid="send-button"]',
                'button[data-testid="fruitjuice-send-button"]',
                'button[aria-label="Send message"]',
                'button svg.icon-sm',  # 送信アイコンを含むボタン
            ]
            
            for selector in send_candidates:
                if page.query_selector(selector):
                    selectors['send'] = selector
                    logger.info(f"ChatGPT送信ボタンセレクタ検出: {selector}")
                    break
                    
            # レスポンスエリアを検出
            response_candidates = [
                'div[data-message-author-role="assistant"]',
                'div.markdown.prose',
                'div.agent-turn',
                'div.min-h-[20px]'
            ]
            
            for selector in response_candidates:
                if page.query_selector(selector):
                    selectors['response'] = selector
                    logger.info(f"ChatGPTレスポンスセレクタ検出: {selector}")
                    break
                    
            # モデル選択ボタンを検出
            model_candidates = [
                'button[aria-haspopup="menu"]',
                'button:has-text("GPT-4")',
                'button:has-text("GPT-3.5")',
                'div[role="button"]:has-text("Model")'
            ]
            
            for selector in model_candidates:
                if page.query_selector(selector):
                    selectors['model_button'] = selector
                    break
                    
        except Exception as e:
            logger.error(f"ChatGPTセレクタ検出エラー: {e}")
            
        return selectors
        
    def detect_claude_selectors(self, page: Page) -> Dict[str, str]:
        """Claudeのセレクタを検出"""
        selectors = {}
        
        try:
            # 入力欄を検出
            input_candidates = [
                'div[contenteditable="true"]',
                'div.ProseMirror',
                'div[role="textbox"]',
                'div[data-placeholder*="Talk to Claude"]'
            ]
            
            for selector in input_candidates:
                if page.query_selector(selector):
                    selectors['input'] = selector
                    logger.info(f"Claude入力欄セレクタ検出: {selector}")
                    break
                    
            # 送信ボタンを検出
            send_candidates = [
                'button[aria-label="Send message"]',
                'button[aria-label="Send Message"]',
                'button:has-text("Send")',
                'button[type="submit"]'
            ]
            
            for selector in send_candidates:
                if page.query_selector(selector):
                    selectors['send'] = selector
                    logger.info(f"Claude送信ボタンセレクタ検出: {selector}")
                    break
                    
            # レスポンスエリアを検出
            response_candidates = [
                'div[data-test-id="assistant-message"]',
                'div.prose',
                'div[data-testid="conversation-turn"]',
                'div.font-claude-message'
            ]
            
            for selector in response_candidates:
                if page.query_selector(selector):
                    selectors['response'] = selector
                    logger.info(f"Claudeレスポンスセレクタ検出: {selector}")
                    break
                    
        except Exception as e:
            logger.error(f"Claudeセレクタ検出エラー: {e}")
            
        return selectors
        
    def detect_gemini_selectors(self, page: Page) -> Dict[str, str]:
        """Geminiのセレクタを検出"""
        selectors = {}
        
        try:
            # 入力欄を検出
            input_candidates = [
                'textarea[placeholder*="Enter a prompt"]',
                'textarea[placeholder*="Ask Gemini"]',
                'textarea.ql-editor',
                'div[contenteditable="true"]'
            ]
            
            for selector in input_candidates:
                if page.query_selector(selector):
                    selectors['input'] = selector
                    logger.info(f"Gemini入力欄セレクタ検出: {selector}")
                    break
                    
            # 送信ボタンを検出
            send_candidates = [
                'button[aria-label="Send message"]',
                'button[aria-label="Submit"]',
                'button[mat-icon-button]',
                'button:has-text("Send")'
            ]
            
            for selector in send_candidates:
                if page.query_selector(selector):
                    selectors['send'] = selector
                    logger.info(f"Gemini送信ボタンセレクタ検出: {selector}")
                    break
                    
            # レスポンスエリアを検出
            response_candidates = [
                'div.response-container',
                'div.model-response',
                'div[data-test-id="response"]',
                'div.markdown-body'
            ]
            
            for selector in response_candidates:
                if page.query_selector(selector):
                    selectors['response'] = selector
                    logger.info(f"Geminiレスポンスセレクタ検出: {selector}")
                    break
                    
        except Exception as e:
            logger.error(f"Geminiセレクタ検出エラー: {e}")
            
        return selectors
        
    def update_all_selectors(self, chrome_profile: str = None):
        """全AIサービスのセレクタを更新"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwrightがインストールされていません")
            return
            
        services = {
            'ChatGPT': ('https://chatgpt.com', self.detect_chatgpt_selectors),
            'Claude': ('https://claude.ai', self.detect_claude_selectors),
            'Gemini': ('https://gemini.google.com', self.detect_gemini_selectors)
        }
        
        with sync_playwright() as p:
            if chrome_profile:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=chrome_profile,
                    headless=False
                )
            else:
                browser_obj = p.chromium.launch(headless=False)
                browser = browser_obj.new_context()
                
            for service_name, (url, detector_func) in services.items():
                try:
                    logger.info(f"{service_name}のセレクタを検出中...")
                    page = browser.new_page()
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # ページが完全に読み込まれるまで待つ
                    page.wait_for_timeout(3000)
                    
                    # セレクタを検出
                    detected_selectors = detector_func(page)
                    
                    if detected_selectors:
                        self.selectors[service_name] = {
                            **detected_selectors,
                            'last_updated': datetime.now().isoformat()
                        }
                        logger.info(f"{service_name}のセレクタ更新完了")
                    else:
                        logger.warning(f"{service_name}のセレクタが検出できませんでした")
                        
                    page.close()
                    
                except Exception as e:
                    logger.error(f"{service_name}のセレクタ更新エラー: {e}")
                    
            browser.close()
            
        # セレクタを保存
        self.save_selectors()
        logger.info("すべてのセレクタ更新が完了しました")
        
        return self.selectors


def main():
    """スタンドアロン実行用"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== AIセレクタ自動更新ツール ===")
    print("各AIサービスのセレクタを自動的に検出・更新します。")
    print("\n注意: 各サービスにログインしている必要があります。")
    
    updater = AISelectorUpdater()
    
    # Chromeプロファイルを使用するか確認
    use_profile = input("\n既存のChromeプロファイルを使用しますか？ (y/n): ").lower() == 'y'
    
    chrome_profile = None
    if use_profile:
        print("\nChromeプロファイルのパスを入力してください。")
        print("例: ~/Library/Application Support/Google/Chrome/Default")
        chrome_profile = input("パス: ").strip()
        
    print("\nセレクタの検出を開始します...")
    result = updater.update_all_selectors(chrome_profile)
    
    if result:
        print("\n=== 検出されたセレクタ ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\nセレクタは {updater.selectors_file} に保存されました。")
    else:
        print("\nセレクタの検出に失敗しました。")


if __name__ == "__main__":
    main()