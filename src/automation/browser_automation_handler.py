"""
ブラウザ自動化ハンドラー - API不要でWeb版AIサービスを操作
Playwrightを使用して既存のログインセッションを活用

作成日: 2024/12/12
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import platform
from abc import ABC, abstractmethod

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not installed. Install with: pip install playwright")

class AIServiceHandler(ABC):
    """AIサービス別ハンドラーの基底クラス"""
    
    @abstractmethod
    def send_message(self, page: Page, message: str) -> bool:
        """メッセージを送信"""
        pass
    
    @abstractmethod
    def wait_for_response(self, page: Page, timeout: int = 60) -> bool:
        """レスポンスを待機"""
        pass
    
    @abstractmethod
    def get_response(self, page: Page) -> str:
        """レスポンスを取得"""
        pass
    
    @abstractmethod
    def select_model(self, page: Page, model: str) -> bool:
        """モデルを選択"""
        pass
    
    @abstractmethod
    def enable_features(self, page: Page, features: List[str]) -> bool:
        """特別な機能を有効化（DeepThink等）"""
        pass


class ChatGPTHandler(AIServiceHandler):
    """ChatGPT Web版の操作ハンドラー"""
    
    def send_message(self, page: Page, message: str) -> bool:
        try:
            # テキストエリアを探す
            textarea = page.locator('textarea[placeholder*="Message"]').first
            if not textarea:
                textarea = page.locator('textarea').first
            
            textarea.fill(message)
            
            # 送信ボタンをクリック
            send_button = page.locator('button[data-testid="send-button"]').first
            if not send_button:
                send_button = page.locator('button:has-text("Send")').first
            
            send_button.click()
            return True
        except Exception as e:
            logging.error(f"ChatGPT send_message error: {e}")
            return False
    
    def wait_for_response(self, page: Page, timeout: int = 60) -> bool:
        try:
            # ストリーミング中のインジケーターが消えるまで待つ
            page.wait_for_function(
                """() => {
                    const buttons = document.querySelectorAll('button');
                    return !Array.from(buttons).some(btn => 
                        btn.textContent?.includes('Stop generating')
                    );
                }""",
                timeout=timeout * 1000
            )
            return True
        except Exception as e:
            logging.error(f"ChatGPT wait_for_response error: {e}")
            return False
    
    def get_response(self, page: Page) -> str:
        try:
            # 最新のアシスタントメッセージを取得
            messages = page.locator('div[data-message-author-role="assistant"]').all()
            if messages:
                return messages[-1].inner_text()
            return ""
        except Exception as e:
            logging.error(f"ChatGPT get_response error: {e}")
            return ""
    
    def select_model(self, page: Page, model: str) -> bool:
        try:
            # モデル選択ドロップダウンをクリック
            model_selector = page.locator('button:has-text("GPT-")').first
            if model_selector:
                model_selector.click()
                page.wait_for_timeout(1000)
                
                # モデルを選択
                model_option = page.locator(f'div[role="option"]:has-text("{model}")').first
                if model_option:
                    model_option.click()
                    return True
            return False
        except Exception as e:
            logging.error(f"ChatGPT select_model error: {e}")
            return False
    
    def enable_features(self, page: Page, features: List[str]) -> bool:
        """ChatGPTの特別な機能を有効化"""
        try:
            for feature in features:
                if feature.lower() == "deepthink" or feature.lower() == "search":
                    # 検索ボタンを探してクリック
                    search_button = page.locator('button:has-text("Search")').first
                    if search_button:
                        search_button.click()
                        page.wait_for_timeout(1000)
            return True
        except Exception as e:
            logging.error(f"ChatGPT enable_features error: {e}")
            return False


class ClaudeHandler(AIServiceHandler):
    """Claude Web版の操作ハンドラー"""
    
    def send_message(self, page: Page, message: str) -> bool:
        try:
            # 入力フィールドを探す
            input_field = page.locator('div[contenteditable="true"]').last
            input_field.fill(message)
            
            # Enterキーで送信
            input_field.press("Enter")
            return True
        except Exception as e:
            logging.error(f"Claude send_message error: {e}")
            return False
    
    def wait_for_response(self, page: Page, timeout: int = 60) -> bool:
        try:
            # Claudeの応答完了を待つ
            page.wait_for_function(
                """() => {
                    const messages = document.querySelectorAll('div[data-test-id="assistant-message"]');
                    if (messages.length === 0) return false;
                    const lastMessage = messages[messages.length - 1];
                    return !lastMessage.querySelector('.loading-indicator');
                }""",
                timeout=timeout * 1000
            )
            return True
        except Exception as e:
            logging.error(f"Claude wait_for_response error: {e}")
            return False
    
    def get_response(self, page: Page) -> str:
        try:
            messages = page.locator('div[data-test-id="assistant-message"]').all()
            if messages:
                return messages[-1].inner_text()
            return ""
        except Exception as e:
            logging.error(f"Claude get_response error: {e}")
            return ""
    
    def select_model(self, page: Page, model: str) -> bool:
        try:
            # Claudeのモデル選択（プロジェクト設定で行う場合が多い）
            return True
        except Exception as e:
            logging.error(f"Claude select_model error: {e}")
            return False
    
    def enable_features(self, page: Page, features: List[str]) -> bool:
        """Claudeの特別な機能を有効化"""
        try:
            # プロジェクト機能やアーティファクトは自動的に有効
            return True
        except Exception as e:
            logging.error(f"Claude enable_features error: {e}")
            return False


class GeminiHandler(AIServiceHandler):
    """Gemini Web版の操作ハンドラー"""
    
    def send_message(self, page: Page, message: str) -> bool:
        try:
            # Geminiの入力フィールド
            input_field = page.locator('div[contenteditable="true"]').first
            input_field.fill(message)
            
            # 送信ボタンをクリック
            send_button = page.locator('button[aria-label*="Send"]').first
            send_button.click()
            return True
        except Exception as e:
            logging.error(f"Gemini send_message error: {e}")
            return False
    
    def wait_for_response(self, page: Page, timeout: int = 60) -> bool:
        try:
            # Geminiの応答完了を待つ
            page.wait_for_selector('div[data-is-streaming="false"]', timeout=timeout * 1000)
            return True
        except Exception as e:
            logging.error(f"Gemini wait_for_response error: {e}")
            return False
    
    def get_response(self, page: Page) -> str:
        try:
            # 最新のレスポンスを取得
            responses = page.locator('div.model-response').all()
            if responses:
                return responses[-1].inner_text()
            return ""
        except Exception as e:
            logging.error(f"Gemini get_response error: {e}")
            return ""
    
    def select_model(self, page: Page, model: str) -> bool:
        """Geminiのモデル選択"""
        return True  # Geminiは自動的に最新モデルを使用
    
    def enable_features(self, page: Page, features: List[str]) -> bool:
        """Geminiの特別な機能を有効化"""
        return True


class BrowserAutomationHandler:
    """ブラウザ自動化メインハンドラー"""
    
    def __init__(self, profile_path: Optional[str] = None):
        """
        初期化
        
        Args:
            profile_path: Chromeプロファイルのパス（既存のログイン情報を使用）
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required. Install with: pip install playwright")
        
        self.logger = logging.getLogger(__name__)
        self.profile_path = profile_path or self._get_default_profile_path()
        self.playwright = None
        self.browser = None
        self.context = None
        self.pages = {}  # AIサービスごとのページを保持
        
        # AIサービスハンドラー
        self.handlers = {
            'chatgpt': ChatGPTHandler(),
            'claude': ClaudeHandler(),
            'gemini': GeminiHandler()
        }
        
        # AIサービスのURL
        self.service_urls = {
            'chatgpt': 'https://chatgpt.com',
            'claude': 'https://claude.ai',
            'gemini': 'https://gemini.google.com',
            'genspark': 'https://www.genspark.ai',
            'google_ai_studio': 'https://aistudio.google.com'
        }
        
        self.logger.info(f"BrowserAutomationHandler initialized with profile: {self.profile_path}")
    
    def _get_default_profile_path(self) -> str:
        """デフォルトのChromeプロファイルパスを取得"""
        system = platform.system()
        home = Path.home()
        
        if system == "Darwin":  # macOS
            return str(home / "Library/Application Support/Google/Chrome/Default")
        elif system == "Windows":
            return str(home / "AppData/Local/Google/Chrome/User Data/Default")
        else:  # Linux
            return str(home / ".config/google-chrome/Default")
    
    def start(self, headless: bool = False):
        """ブラウザを起動"""
        try:
            self.playwright = sync_playwright().start()
            
            # 既存のChromeプロファイルを使用
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.profile_path,
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            self.logger.info("Browser started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            raise
    
    def open_ai_service(self, service: str) -> Optional[Page]:
        """AIサービスのページを開く"""
        if service not in self.service_urls:
            self.logger.error(f"Unknown AI service: {service}")
            return None
        
        try:
            # 新しいページを開く
            page = self.context.new_page()
            page.goto(self.service_urls[service])
            
            # ページロード待機
            page.wait_for_load_state('networkidle')
            
            self.pages[service] = page
            self.logger.info(f"Opened {service} page")
            
            return page
            
        except Exception as e:
            self.logger.error(f"Failed to open {service}: {e}")
            return None
    
    def process_text(self, service: str, text: str, model: Optional[str] = None,
                    features: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        テキストをAIサービスで処理
        
        Args:
            service: AIサービス名
            text: 処理するテキスト
            model: 使用するモデル
            features: 有効化する機能（DeepThink等）
            
        Returns:
            処理結果の辞書
        """
        start_time = time.time()
        
        try:
            # ページを開くまたは既存のページを使用
            if service not in self.pages:
                page = self.open_ai_service(service)
                if not page:
                    return {
                        "success": False,
                        "error": f"Failed to open {service}",
                        "service": service
                    }
            else:
                page = self.pages[service]
            
            # ハンドラーを取得
            handler = self.handlers.get(service)
            if not handler:
                # 汎用ハンドラーを使用
                self.logger.warning(f"No specific handler for {service}, using generic approach")
                return self._process_with_generic_handler(page, text)
            
            # モデル選択（指定されている場合）
            if model:
                handler.select_model(page, model)
            
            # 機能有効化（指定されている場合）
            if features:
                handler.enable_features(page, features)
            
            # メッセージ送信
            if not handler.send_message(page, text):
                return {
                    "success": False,
                    "error": "Failed to send message",
                    "service": service
                }
            
            # レスポンス待機
            if not handler.wait_for_response(page):
                return {
                    "success": False,
                    "error": "Response timeout",
                    "service": service
                }
            
            # レスポンス取得
            response = handler.get_response(page)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "result": response,
                "service": service,
                "model": model,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing text with {service}: {e}")
            return {
                "success": False,
                "error": str(e),
                "service": service,
                "processing_time": time.time() - start_time
            }
    
    def _process_with_generic_handler(self, page: Page, text: str) -> Dict[str, Any]:
        """汎用的なハンドラーでテキスト処理"""
        try:
            # 一般的な入力フィールドを探す
            input_selectors = [
                'textarea',
                'div[contenteditable="true"]',
                'input[type="text"]'
            ]
            
            for selector in input_selectors:
                elements = page.locator(selector).all()
                if elements:
                    elements[0].fill(text)
                    page.keyboard.press("Enter")
                    break
            
            # レスポンスを待つ
            page.wait_for_timeout(5000)
            
            return {
                "success": True,
                "result": "Generic processing completed",
                "service": "generic"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service": "generic"
            }
    
    def process_batch(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数のタスクをバッチ処理
        
        Args:
            tasks: 処理タスクのリスト
                [{"service": "chatgpt", "text": "...", "model": "gpt-4o"}, ...]
                
        Returns:
            処理結果のリスト
        """
        results = []
        
        for task in tasks:
            service = task.get('service', 'chatgpt')
            text = task.get('text', '')
            model = task.get('model')
            features = task.get('features', [])
            
            result = self.process_text(service, text, model, features)
            results.append(result)
            
            # レート制限対策
            time.sleep(2)
        
        return results
    
    def close(self):
        """ブラウザを閉じる"""
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
            
            self.logger.info("Browser closed")
            
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
    
    def __enter__(self):
        """コンテキストマネージャー対応"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー対応"""
        self.close()


class BrowserAutomationConfig:
    """ブラウザ自動化の設定管理"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent.parent / "config" / "browser_automation.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        default_config = {
            "browser": {
                "headless": False,
                "profile_path": None,
                "timeout": 60
            },
            "services": {
                "chatgpt": {
                    "enabled": True,
                    "default_model": "gpt-4o",
                    "features": ["DeepThink", "Web検索"]
                },
                "claude": {
                    "enabled": True,
                    "default_model": "claude-3.5-sonnet",
                    "features": ["プロジェクト", "アーティファクト"]
                },
                "gemini": {
                    "enabled": True,
                    "default_model": "gemini-1.5-pro",
                    "features": ["マルチモーダル"]
                }
            },
            "rate_limiting": {
                "delay_between_requests": 2,
                "max_concurrent_pages": 3
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # デフォルト設定とマージ
                    self._merge_configs(default_config, loaded_config)
            except Exception as e:
                logging.warning(f"Failed to load config: {e}")
        
        return default_config
    
    def _merge_configs(self, base: Dict, update: Dict):
        """設定をマージ"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value
    
    def save(self):
        """設定を保存"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    # ブラウザ自動化ハンドラーのテスト
    with BrowserAutomationHandler() as handler:
        # ChatGPTでテスト
        result = handler.process_text(
            service="chatgpt",
            text="Pythonで簡単なHello Worldプログラムを書いて",
            model="gpt-4o",
            features=["DeepThink"]
        )
        
        if result["success"]:
            print(f"Success: {result['result'][:100]}...")
        else:
            print(f"Error: {result['error']}")