# 担当者C: ブラウザ自動化・AI連携 専用指示書

## 🎯 あなたの役割
**Selenium WebDriverを使用したAIサイト自動操作システム構築**
- ブラウザ自動化の基盤構築
- 各AIサービスの操作自動化
- エラーハンドリング・リトライ機能
- セッション管理・パフォーマンス最適化

## 📁 あなたが編集するファイル

### メインファイル
```
src/automation/
├── browser_manager.py           # 🔥 Seleniumブラウザ管理
├── automation_controller.py     # 🔥 全体制御・オーケストレーション
├── retry_manager.py            # 🔥 リトライ・エラー管理
├── session_manager.py          # 🔥 セッション管理
└── ai_handlers/                # 🔥 AI別操作ハンドラー
    ├── __init__.py
    ├── base_handler.py         # 🔥 共通基底クラス
    ├── chatgpt_handler.py      # 🔥 ChatGPT操作
    ├── claude_handler.py       # 🔥 Claude操作
    ├── gemini_handler.py       # 🔥 Gemini操作
    ├── genspark_handler.py     # 🔥 Genspark操作
    └── google_ai_studio_handler.py  # 🔥 Google AI Studio操作
```

### サポートファイル
```
tests/test_automation.py        # テストファイル（作成）
docs/AI_SITES_RESEARCH.md      # AI サイト調査ドキュメント（作成）
config/browser_config.json     # ブラウザ設定（作成）
```

## 🚀 作業開始手順

### 1日目: Selenium環境構築
```bash
# Git準備
git checkout feature/browser-automation
git pull origin develop
git merge develop

# ディレクトリ作成
mkdir -p src/automation/ai_handlers tests config
touch src/automation/__init__.py
touch src/automation/ai_handlers/__init__.py
```

### Selenium環境確認
```bash
# 必要パッケージインストール確認
pip install selenium webdriver-manager

# Chrome WebDriver動作確認
python -c "
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

print('Selenium環境確認中...')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get('https://www.google.com')
print('Chrome WebDriver動作確認完了')
driver.quit()
print('環境構築成功')
"
```

### 2-3日目: ブラウザ管理システム実装
```python
# src/automation/browser_manager.py
import os
import time
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from src.utils.logger import logger
from src.utils.config_manager import config_manager

class BrowserManager:
    """ブラウザ管理クラス"""
    
    def __init__(self, browser_type: str = "chrome", headless: bool = False, 
                 user_data_dir: Optional[str] = None):
        """
        ブラウザマネージャー初期化
        
        Args:
            browser_type (str): ブラウザ種類（chrome/firefox）
            headless (bool): ヘッドレスモード
            user_data_dir (str): ユーザーデータディレクトリ（ログイン情報保持用）
        """
        self.browser_type = browser_type.lower()
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.driver: Optional[webdriver.Chrome] = None
        self.session_active = False
        
        # 設定読み込み
        self.timeout = config_manager.get("automation.timeout", 30)
        self.retry_count = config_manager.get("automation.retry_count", 3)
        
        logger.info(f"ブラウザマネージャー初期化: {browser_type}, ヘッドレス: {headless}")
    
    def start_browser(self) -> webdriver.Chrome:
        """
        ブラウザ起動
        
        Returns:
            webdriver.Chrome: WebDriverインスタンス
        """
        try:
            if self.driver:
                logger.warning("ブラウザは既に起動済みです")
                return self.driver
            
            if self.browser_type == "chrome":
                self.driver = self._start_chrome()
            elif self.browser_type == "firefox":
                self.driver = self._start_firefox()
            else:
                raise ValueError(f"サポートされていないブラウザ: {self.browser_type}")
            
            self.session_active = True
            logger.info(f"{self.browser_type.capitalize()} ブラウザ起動完了")
            return self.driver
            
        except Exception as e:
            logger.error(f"ブラウザ起動エラー: {e}")
            raise
    
    def _start_chrome(self) -> webdriver.Chrome:
        """Chrome WebDriver起動"""
        options = Options()
        
        # 基本オプション設定
        if self.headless:
            options.add_argument('--headless')
        
        # パフォーマンス最適化オプション
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # 画像読み込み無効化
        
        # メモリ最適化
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        
        # ユーザーデータディレクトリ（ログイン情報保持）
        if self.user_data_dir:
            options.add_argument(f'--user-data-dir={self.user_data_dir}')
        
        # 通知・位置情報などの無効化
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
                "media_stream": 2,
            },
            "profile.managed_default_content_settings": {
                "images": 2  # 画像ブロック
            }
        }
        options.add_experimental_option("prefs", prefs)
        
        # WebDriverサービス設定
        service = Service(ChromeDriverManager().install())
        
        return webdriver.Chrome(service=service, options=options)
    
    def _start_firefox(self) -> webdriver.Firefox:
        """Firefox WebDriver起動"""
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        # パフォーマンス最適化
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("media.volume_scale", "0.0")
        
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=options)
    
    def close_browser(self):
        """ブラウザ終了"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.session_active = False
                logger.info("ブラウザを正常に終了しました")
        except Exception as e:
            logger.error(f"ブラウザ終了エラー: {e}")
    
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """WebDriverインスタンス取得"""
        return self.driver
    
    def is_active(self) -> bool:
        """ブラウザがアクティブかどうか確認"""
        if not self.driver or not self.session_active:
            return False
        
        try:
            # 現在のウィンドウハンドルを取得してアクティブ確認
            self.driver.current_window_handle
            return True
        except:
            self.session_active = False
            return False
    
    def refresh_session(self):
        """セッション更新"""
        try:
            if self.is_active():
                self.driver.refresh()
                time.sleep(2)
                logger.info("ブラウザセッションを更新しました")
        except Exception as e:
            logger.error(f"セッション更新エラー: {e}")
    
    def clear_cache(self):
        """キャッシュクリア"""
        try:
            if self.is_active():
                self.driver.delete_all_cookies()
                logger.info("ブラウザキャッシュをクリアしました")
        except Exception as e:
            logger.error(f"キャッシュクリアエラー: {e}")
    
    def take_screenshot(self, filepath: str) -> bool:
        """スクリーンショット保存"""
        try:
            if self.is_active():
                self.driver.save_screenshot(filepath)
                logger.info(f"スクリーンショット保存: {filepath}")
                return True
        except Exception as e:
            logger.error(f"スクリーンショット保存エラー: {e}")
        return False
    
    def __del__(self):
        """デストラクタ - リソース解放"""
        self.close_browser()
```

### 4-5日目: 基底ハンドラークラス実装
```python
# src/automation/ai_handlers/base_handler.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.utils.logger import logger

class BaseAIHandler(ABC):
    """AI操作の基底クラス"""
    
    def __init__(self, driver, timeout: int = 30):
        """
        基底ハンドラー初期化
        
        Args:
            driver: WebDriverインスタンス
            timeout (int): 要素待機タイムアウト（秒）
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.actions = ActionChains(driver)
        
        # AI別設定（サブクラスで設定）
        self.base_url = ""
        self.site_name = ""
        self.selectors = {}
        
        logger.info(f"{self.__class__.__name__} 初期化完了")
    
    @abstractmethod
    def get_site_info(self) -> Dict[str, str]:
        """サイト情報を取得（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def login_check(self) -> bool:
        """ログイン状態確認（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def navigate_to_chat(self) -> bool:
        """チャット画面に移動（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def input_text(self, text: str) -> bool:
        """テキスト入力（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def submit_request(self) -> bool:
        """リクエスト送信（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def wait_for_response(self) -> bool:
        """応答待機（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def get_response_text(self) -> str:
        """応答テキスト取得（サブクラスで実装）"""
        pass
    
    def process_request(self, input_text: str) -> str:
        """
        一連の処理実行（共通フロー）
        
        Args:
            input_text (str): 入力テキスト
            
        Returns:
            str: AI応答テキスト
        """
        try:
            logger.info(f"{self.site_name}: 処理開始")
            
            # 1. ログイン状態確認
            if not self.login_check():
                raise Exception(f"{self.site_name}: ログインが必要です")
            
            # 2. チャット画面に移動
            if not self.navigate_to_chat():
                raise Exception(f"{self.site_name}: チャット画面への移動に失敗")
            
            # 3. テキスト入力
            if not self.input_text(input_text):
                raise Exception(f"{self.site_name}: テキスト入力に失敗")
            
            # 4. リクエスト送信
            if not self.submit_request():
                raise Exception(f"{self.site_name}: リクエスト送信に失敗")
            
            # 5. 応答待機
            if not self.wait_for_response():
                raise Exception(f"{self.site_name}: 応答待機がタイムアウト")
            
            # 6. 応答テキスト取得
            response = self.get_response_text()
            if not response:
                raise Exception(f"{self.site_name}: 応答テキスト取得に失敗")
            
            logger.info(f"{self.site_name}: 処理完了")
            return response
            
        except Exception as e:
            logger.error(f"{self.site_name}: 処理エラー - {str(e)}")
            self._take_error_screenshot()
            raise
    
    # 共通ユーティリティメソッド
    def wait_and_find_element(self, by: By, value: str, timeout: Optional[int] = None) -> Optional[Any]:
        """要素の存在を待機して取得"""
        try:
            wait_time = timeout or self.timeout
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.warning(f"要素が見つかりません: {by}={value}")
            return None
    
    def wait_and_click(self, by: By, value: str, timeout: Optional[int] = None) -> bool:
        """要素の出現を待機してクリック"""
        try:
            element = self.wait_and_find_element(by, value, timeout)
            if element:
                # JavaScriptクリック（確実性向上）
                self.driver.execute_script("arguments[0].click();", element)
                self._random_delay()
                return True
        except Exception as e:
            logger.error(f"クリックエラー: {e}")
        return False
    
    def safe_send_keys(self, element, text: str, clear_first: bool = True):
        """安全なテキスト入力"""
        try:
            if clear_first:
                element.clear()
                time.sleep(0.5)
            
            # 人間らしい入力速度
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.01, 0.05))
            
            self._random_delay()
            
        except Exception as e:
            logger.error(f"テキスト入力エラー: {e}")
            raise
    
    def scroll_to_element(self, element):
        """要素までスクロール"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
        except Exception as e:
            logger.error(f"スクロールエラー: {e}")
    
    def _random_delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """ランダム待機（人間らしい操作のため）"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _take_error_screenshot(self):
        """エラー時のスクリーンショット保存"""
        try:
            timestamp = int(time.time())
            filename = f"error_{self.site_name}_{timestamp}.png"
            filepath = f"logs/{filename}"
            
            os.makedirs("logs", exist_ok=True)
            self.driver.save_screenshot(filepath)
            logger.info(f"エラースクリーンショット保存: {filepath}")
        except:
            pass
    
    def check_for_errors(self) -> Optional[str]:
        """ページ上のエラーメッセージ確認"""
        error_selectors = [
            '[class*="error"]',
            '[class*="warning"]', 
            '[class*="alert"]',
            '[role="alert"]'
        ]
        
        for selector in error_selectors:
            try:
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in error_elements:
                    if element.is_displayed() and element.text.strip():
                        return element.text.strip()
            except:
                continue
        
        return None
    
    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """ページロード完了待機"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)  # 追加待機
            return True
        except TimeoutException:
            logger.warning("ページロードタイムアウト")
            return False
```

### 6-10日目: ChatGPTハンドラー実装（優先）
```python
# src/automation/ai_handlers/chatgpt_handler.py
import time
from typing import Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from src.automation.ai_handlers.base_handler import BaseAIHandler
from src.utils.logger import logger

class ChatGPTHandler(BaseAIHandler):
    """ChatGPT操作ハンドラー"""
    
    def __init__(self, driver, timeout: int = 60):  # ChatGPTは応答が遅い場合があるため長めに設定
        super().__init__(driver, timeout)
        self.base_url = "https://chat.openai.com"
        self.site_name = "ChatGPT"
        
        # ChatGPT特有のセレクター
        self.selectors = {
            # ログイン確認用
            "chat_input": 'textarea[placeholder*="Message"], textarea[data-id="root"]',
            "login_button": 'button:contains("Log in")',
            
            # チャット操作用
            "message_input": 'textarea[placeholder*="Message"], textarea[data-id="root"]',
            "send_button": 'button[data-testid="send-button"], button[type="submit"]',
            "stop_button": 'button:contains("Stop"), button[aria-label*="Stop"]',
            
            # 応答確認用
            "assistant_messages": '[data-message-author-role="assistant"]',
            "thinking_indicator": '[data-testid*="thinking"], .result-thinking',
            "loading_indicator": '.result-streaming, [class*="loading"]'
        }
    
    def get_site_info(self) -> Dict[str, str]:
        """サイト情報取得"""
        return {
            "name": self.site_name,
            "url": self.base_url,
            "description": "OpenAI ChatGPT"
        }
    
    def login_check(self) -> bool:
        """ログイン状態確認"""
        try:
            logger.info(f"{self.site_name}: ログイン状態確認中")
            
            # ChatGPTサイトに移動
            self.driver.get(self.base_url)
            self.wait_for_page_load()
            
            # チャット入力欄の存在確認
            chat_input = self.wait_and_find_element(
                By.CSS_SELECTOR, 
                self.selectors["chat_input"], 
                timeout=10
            )
            
            if chat_input and chat_input.is_displayed():
                logger.info(f"{self.site_name}: ログイン済み確認")
                return True
            
            # ログインボタンの存在確認
            login_elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Log in')]")
            if login_elements:
                logger.warning(f"{self.site_name}: ログインが必要です")
                return False
            
            # その他のログイン画面要素確認
            if "login" in self.driver.current_url.lower():
                logger.warning(f"{self.site_name}: ログインページにリダイレクトされました")
                return False
            
            logger.info(f"{self.site_name}: ログイン状態と判定")
            return True
            
        except Exception as e:
            logger.error(f"{self.site_name}: ログイン確認エラー - {e}")
            return False
    
    def navigate_to_chat(self) -> bool:
        """チャット画面に移動"""
        try:
            logger.info(f"{self.site_name}: チャット画面への移動")
            
            # 既にチャット画面にいる場合
            current_url = self.driver.current_url
            if "chat.openai.com" in current_url and "/c/" in current_url:
                logger.info(f"{self.site_name}: 既にチャット画面にいます")
                return True
            
            # 新しいチャットを開始
            self.driver.get(self.base_url)
            self.wait_for_page_load()
            
            # チャット入力欄が表示されるまで待機
            chat_input = self.wait_and_find_element(
                By.CSS_SELECTOR, 
                self.selectors["message_input"], 
                timeout=15
            )
            
            if chat_input:
                logger.info(f"{self.site_name}: チャット画面に移動完了")
                return True
            
            logger.error(f"{self.site_name}: チャット画面への移動に失敗")
            return False
            
        except Exception as e:
            logger.error(f"{self.site_name}: チャット画面移動エラー - {e}")
            return False
    
    def input_text(self, text: str) -> bool:
        """テキスト入力"""
        try:
            logger.info(f"{self.site_name}: テキスト入力開始")
            
            # チャット入力欄を取得
            chat_input = self.wait_and_find_element(
                By.CSS_SELECTOR, 
                self.selectors["message_input"], 
                timeout=10
            )
            
            if not chat_input:
                logger.error(f"{self.site_name}: チャット入力欄が見つかりません")
                return False
            
            # フォーカスして既存テキストをクリア
            chat_input.click()
            time.sleep(0.5)
            
            # 全選択してクリア
            chat_input.send_keys(Keys.CONTROL + "a")
            time.sleep(0.2)
            chat_input.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            # テキスト入力（人間らしい速度で）
            self.safe_send_keys(chat_input, text, clear_first=False)
            
            # 入力完了確認
            time.sleep(1)
            current_value = chat_input.get_attribute("value") or self.driver.execute_script(
                "return arguments[0].textContent || arguments[0].innerText", chat_input
            )
            
            if text.strip() in current_value:
                logger.info(f"{self.site_name}: テキスト入力完了")
                return True
            else:
                logger.warning(f"{self.site_name}: テキスト入力が不完全な可能性があります")
                return True  # 部分的でも成功とみなす
            
        except Exception as e:
            logger.error(f"{self.site_name}: テキスト入力エラー - {e}")
            return False
    
    def submit_request(self) -> bool:
        """リクエスト送信"""
        try:
            logger.info(f"{self.site_name}: リクエスト送信")
            
            # 送信ボタンを探す
            send_button = self.wait_and_find_element(
                By.CSS_SELECTOR, 
                self.selectors["send_button"], 
                timeout=5
            )
            
            if send_button and send_button.is_enabled():
                # ボタンクリック
                send_button.click()
                logger.info(f"{self.site_name}: 送信ボタンクリック完了")
                time.sleep(2)
                return True
            
            # Enterキーでの送信も試行
            logger.info(f"{self.site_name}: Enterキーで送信試行")
            chat_input = self.driver.find_element(By.CSS_SELECTOR, self.selectors["message_input"])
            chat_input.send_keys(Keys.ENTER)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"{self.site_name}: リクエスト送信エラー - {e}")
            return False
    
    def wait_for_response(self) -> bool:
        """応答待機"""
        try:
            logger.info(f"{self.site_name}: 応答待機開始")
            
            # 最大待機時間を設定（ChatGPTは時間がかかる場合がある）
            max_wait_time = 120  # 2分
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # 停止ボタンの存在確認（生成中の証拠）
                stop_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Stop')]")
                if stop_buttons and any(btn.is_displayed() for btn in stop_buttons):
                    logger.info(f"{self.site_name}: 応答生成中...")
                    time.sleep(3)
                    continue
                
                # ローディングインジケーターの確認
                loading_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["loading_indicator"])
                if loading_elements and any(elem.is_displayed() for elem in loading_elements):
                    logger.info(f"{self.site_name}: ローディング中...")
                    time.sleep(2)
                    continue
                
                # 送信ボタンが再度有効になったか確認（応答完了の証拠）
                send_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors["send_button"])
                if send_button and send_button.is_enabled():
                    logger.info(f"{self.site_name}: 応答完了検知")
                    time.sleep(2)  # 完全な描画を待つ
                    return True
                
                time.sleep(2)
            
            logger.warning(f"{self.site_name}: 応答待機タイムアウト")
            return False
            
        except Exception as e:
            logger.error(f"{self.site_name}: 応答待機エラー - {e}")
            return False
    
    def get_response_text(self) -> str:
        """応答テキスト取得"""
        try:
            logger.info(f"{self.site_name}: 応答テキスト取得")
            
            # アシスタントメッセージを全て取得
            assistant_messages = self.driver.find_elements(
                By.CSS_SELECTOR, 
                self.selectors["assistant_messages"]
            )
            
            if assistant_messages:
                # 最新のメッセージを取得
                latest_message = assistant_messages[-1]
                
                # テキスト抽出（マークダウンやHTMLタグを含む場合がある）
                response_text = latest_message.get_attribute("textContent") or latest_message.text
                
                if response_text and response_text.strip():
                    logger.info(f"{self.site_name}: 応答テキスト取得完了 ({len(response_text)}文字)")
                    return response_text.strip()
            
            # 代替方法：最新のメッセージ要素を探す
            alternative_selectors = [
                '[class*="message"][class*="assistant"] div[class*="content"]',
                '.message-content',
                '[data-testid*="conversation-turn"] div:last-child'
            ]
            
            for selector in alternative_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        text = elements[-1].text.strip()
                        if text:
                            logger.info(f"{self.site_name}: 代替方法で応答テキスト取得")
                            return text
                except:
                    continue
            
            logger.error(f"{self.site_name}: 応答テキストが見つかりません")
            return ""
            
        except Exception as e:
            logger.error(f"{self.site_name}: 応答テキスト取得エラー - {e}")
            return ""
```

## 🔗 他担当との連携

### 担当者Aに提供するインターフェース
```python
# GUI進捗更新用のコールバック
def set_progress_callback(self, callback):
    """進捗更新コールバック設定"""
    self.progress_callback = callback

def set_log_callback(self, callback):
    """ログ出力コールバック設定"""
    self.log_callback = callback

def get_available_ais(self) -> Dict[str, List[str]]:
    """利用可能なAIとモデル一覧"""
    return {
        "ChatGPT": ["gpt-4", "gpt-3.5-turbo"],
        "Claude": ["claude-3-sonnet", "claude-3-haiku"], 
        "Gemini": ["gemini-pro", "gemini-pro-vision"],
        "Genspark": ["default"],
        "Google AI Studio": ["gemini-pro"]
    }
```

### 担当者Bに提供するインターフェース
```python
# タスク処理用メイン関数
def process_task_batch(self, tasks: List[TaskRow], progress_callback=None) -> List[TaskRow]:
    """タスク一覧を処理して結果を返す"""
    for i, task in enumerate(tasks):
        try:
            if progress_callback:
                progress_callback(i, len(tasks), f"処理中: {task.ai_service}")
            
            handler = self.get_ai_handler(task.ai_service)
            result = handler.process_request(task.copy_text)
            task.result = result
            task.status = TaskStatus.COMPLETED
            
        except Exception as e:
            task.error_message = str(e)
            task.status = TaskStatus.ERROR
            
    return tasks
```

## 📅 開発スケジュール

### 第1週: 基盤構築
- [x] Selenium環境構築
- [ ] ブラウザ管理システム（browser_manager.py）
- [ ] 基底ハンドラークラス（base_handler.py）
- [ ] ChatGPTハンドラー基本実装

### 第2週: AI別実装
- [ ] ChatGPTハンドラー完成・テスト
- [ ] Claudeハンドラー実装
- [ ] Geminiハンドラー実装
- [ ] エラーハンドリング・リトライ機能

### 第3週: 統合・最適化
- [ ] 全AIハンドラー完成
- [ ] パフォーマンス最適化
- [ ] 統合テスト・デバッグ

## 🧪 テスト方法

### 基本環境テスト
```bash
# Selenium動作確認
python -c "
from src.automation.browser_manager import BrowserManager
manager = BrowserManager()
driver = manager.start_browser()
driver.get('https://www.google.com')
print('ブラウザ起動テスト成功')
manager.close_browser()
"
```

### ChatGPTハンドラーテスト
```python
# tests/test_chatgpt.py
from src.automation.browser_manager import BrowserManager
from src.automation.ai_handlers.chatgpt_handler import ChatGPTHandler

def test_chatgpt_handler():
    # ブラウザ起動
    browser = BrowserManager(headless=False)  # テスト時は画面表示
    driver = browser.start_browser()
    
    try:
        # ChatGPTハンドラー作成
        handler = ChatGPTHandler(driver)
        
        # ログイン確認
        if handler.login_check():
            print("✅ ログイン確認成功")
            
            # テスト処理実行
            test_input = "Hello, how are you?"
            response = handler.process_request(test_input)
            
            print(f"✅ 処理成功: {response[:100]}...")
        else:
            print("❌ ログインが必要です")
            
    finally:
        browser.close_browser()

if __name__ == "__main__":
    test_chatgpt_handler()
```

## ⚠️ 重要な注意点

### セキュリティ・利用規約
- **各AIサービスの利用規約遵守**
- **過度なリクエスト送信の回避**
- **ログイン情報の安全な管理**

### パフォーマンス
- **ブラウザリソース管理**
- **適切な待機時間設定**
- **メモリリーク防止**

### 堅牢性
- **DOM構造変更への対応**
- **ネットワークエラー処理**
- **タイムアウト適切設定**

## 📝 AI サイト調査ノート

各AIサイトのDOM構造を調査して記録：

```markdown
# ChatGPT (chat.openai.com)
- チャット入力: textarea[placeholder*="Message"]
- 送信ボタン: button[data-testid="send-button"]
- 応答エリア: [data-message-author-role="assistant"]

# Claude (claude.ai)
- 調査中...

# Gemini (gemini.google.com)
- 調査中...
```

**頑張ってください！ブラウザ自動化は技術的に挑戦的ですが、とても重要な部分です。困った時は遠慮なく質問してください。**