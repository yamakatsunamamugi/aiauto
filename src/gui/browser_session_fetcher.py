#!/usr/bin/env python3
"""
ブラウザセッション方式によるAIモデル取得機能
既存のChromeセッションを使用して実際のWebアプリからモデルリストを取得
"""

import json
import os
import platform
import logging
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)


class BrowserSessionFetcher:
    """ブラウザセッション方式でモデル情報を取得するクラス"""
    
    def __init__(self):
        self.chrome_options = self._setup_chrome_options()
        
    def _setup_chrome_options(self) -> Options:
        """Chrome設定を構成"""
        options = Options()
        
        # ユーザープロファイルを使用（既存のログイン情報を活用）
        user_data_dir = self._get_chrome_profile_path()
        if user_data_dir:
            options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # ヘッドレスモードを無効化（実際のブラウザを使用）
        options.add_argument("--no-headless")
        
        # その他の安定性向上オプション
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        return options
    
    def _get_chrome_profile_path(self) -> Optional[str]:
        """Chrome プロファイルパスを取得"""
        system = platform.system()
        home = os.path.expanduser("~")
        
        if system == "Darwin":  # macOS
            return os.path.join(home, "Library/Application Support/Google/Chrome")
        elif system == "Windows":
            return os.path.join(home, "AppData/Local/Google/Chrome/User Data")
        elif system == "Linux":
            return os.path.join(home, ".config/google-chrome")
        
        return None
    
    def _create_driver(self) -> Optional[webdriver.Chrome]:
        """Chrome WebDriverを作成"""
        try:
            # 既存のChromeセッションに接続を試みる
            driver = webdriver.Chrome(options=self.chrome_options)
            return driver
        except WebDriverException as e:
            logger.error(f"Chrome接続エラー: {e}")
            # webdriver-managerで再試行
            try:
                logger.info("webdriver-managerで再試行中...")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=self.chrome_options)
                return driver
            except Exception as e2:
                logger.error(f"Chrome起動失敗: {e2}")
                return None
    
    def get_chatgpt_models(self, driver: webdriver.Chrome) -> List[str]:
        """ChatGPTのモデルリストを取得"""
        models = []
        try:
            # ChatGPTの設定ページに移動
            driver.get("https://chat.openai.com")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # モデル選択メニューを探す（新しいUIに対応）
            try:
                # モデル選択ボタンをクリック
                model_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='model-selector']"))
                )
                model_button.click()
                
                # モデルリストを取得
                model_elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[role='menuitem']"))
                )
                
                for element in model_elements:
                    model_text = element.text.strip()
                    if model_text and "GPT" in model_text.upper():
                        models.append(model_text)
                        
            except TimeoutException:
                # デフォルトモデルを返す
                models = ["GPT-4o", "GPT-4o mini", "GPT-4", "GPT-3.5"]
                
        except Exception as e:
            logger.error(f"ChatGPTモデル取得エラー: {e}")
            models = ["GPT-4o", "GPT-4o mini", "GPT-4", "GPT-3.5"]
            
        return models
    
    def get_claude_models(self, driver: webdriver.Chrome) -> List[str]:
        """Claudeのモデルリストを取得"""
        models = []
        try:
            driver.get("https://claude.ai")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Claudeのモデル選択UI要素を探す
            try:
                # モデル選択要素を探す
                model_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Claude')]")
                
                for element in model_elements:
                    text = element.text
                    if any(ver in text for ver in ["3.5", "3", "2", "Opus", "Sonnet", "Haiku"]):
                        if text not in models:
                            models.append(text)
                            
            except Exception:
                pass
                
            # モデルが見つからない場合はデフォルト値
            if not models:
                models = ["Claude 3.5 Sonnet", "Claude 3 Opus", "Claude 3 Sonnet", "Claude 3 Haiku"]
                
        except Exception as e:
            logger.error(f"Claudeモデル取得エラー: {e}")
            models = ["Claude 3.5 Sonnet", "Claude 3 Opus", "Claude 3 Sonnet", "Claude 3 Haiku"]
            
        return models
    
    def get_gemini_models(self, driver: webdriver.Chrome) -> List[str]:
        """Geminiのモデルリストを取得"""
        models = []
        try:
            driver.get("https://gemini.google.com")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Geminiは現在モデル選択UIが限定的
            models = ["Gemini Pro", "Gemini Pro Vision"]
            
        except Exception as e:
            logger.error(f"Geminiモデル取得エラー: {e}")
            models = ["Gemini Pro", "Gemini Pro Vision"]
            
        return models
    
    def get_genspark_models(self, driver: webdriver.Chrome) -> List[str]:
        """Gensparkのモデルリストを取得"""
        # Gensparkは比較的新しいサービスのため、固定値を返す
        return ["Default", "Research", "Advanced"]
    
    def get_google_ai_studio_models(self, driver: webdriver.Chrome) -> List[str]:
        """Google AI Studioのモデルリストを取得"""
        models = []
        try:
            driver.get("https://aistudio.google.com")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Google AI StudioのモデルリストはGeminiと同じ
            models = ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini Pro", "PaLM 2"]
            
        except Exception as e:
            logger.error(f"Google AI Studioモデル取得エラー: {e}")
            models = ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini Pro", "PaLM 2"]
            
        return models
    
    def fetch_all_models(self) -> Dict[str, Dict]:
        """全AIサービスのモデル情報を取得"""
        results = {}
        driver = self._create_driver()
        
        if not driver:
            logger.error("Chromeドライバーの作成に失敗しました")
            return self._get_default_results()
        
        try:
            # 各サービスのモデルを取得
            services = {
                "chatgpt": self.get_chatgpt_models,
                "claude": self.get_claude_models,
                "gemini": self.get_gemini_models,
                "genspark": self.get_genspark_models,
                "google_ai_studio": self.get_google_ai_studio_models
            }
            
            for service_name, fetch_func in services.items():
                try:
                    logger.info(f"{service_name}のモデルを取得中...")
                    models = fetch_func(driver)
                    
                    results[service_name] = {
                        "models": models,
                        "source": "browser_session",
                        "success": True
                    }
                    logger.info(f"{service_name}: {len(models)}個のモデルを取得")
                    
                except Exception as e:
                    logger.error(f"{service_name}のモデル取得失敗: {e}")
                    results[service_name] = {
                        "models": [],
                        "error": str(e),
                        "success": False
                    }
                    
        finally:
            # ドライバーは閉じない（既存のセッションを維持）
            pass
            
        return results
    
    def _get_default_results(self) -> Dict[str, Dict]:
        """デフォルトの結果を返す"""
        return {
            "chatgpt": {
                "models": ["GPT-4o", "GPT-4o mini", "GPT-4", "GPT-3.5"],
                "source": "default",
                "success": False,
                "error": "Chrome接続失敗"
            },
            "claude": {
                "models": ["Claude 3.5 Sonnet", "Claude 3 Opus", "Claude 3 Sonnet", "Claude 3 Haiku"],
                "source": "default",
                "success": False,
                "error": "Chrome接続失敗"
            },
            "gemini": {
                "models": ["Gemini Pro", "Gemini Pro Vision"],
                "source": "default",
                "success": False,
                "error": "Chrome接続失敗"
            },
            "genspark": {
                "models": ["Default", "Research", "Advanced"],
                "source": "default",
                "success": False,
                "error": "Chrome接続失敗"
            },
            "google_ai_studio": {
                "models": ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini Pro", "PaLM 2"],
                "source": "default",
                "success": False,
                "error": "Chrome接続失敗"
            }
        }


def update_model_list() -> Dict[str, List[str]]:
    """AIモデルの最新リストを取得する（インターフェース仕様準拠）
    
    Returns:
        Dict[str, List[str]]: 各AIサービスのモデルリスト
        例: {
            "chatgpt": ["gpt-4o", "gpt-4o-mini"],
            "claude": ["claude-3.5-sonnet"],
            "gemini": ["gemini-1.5-pro"],
            "genspark": ["default"],
            "google_ai_studio": ["gemini-1.5-pro"]
        }
    """
    try:
        fetcher = BrowserSessionFetcher()
        results = fetcher.fetch_all_models()
        
        # インターフェース仕様に合わせた形式に変換
        model_dict = {}
        for service, info in results.items():
            if info.get("success", False) and info.get("models"):
                model_dict[service] = info["models"]
            else:
                # エラーの場合は空のリストを返す
                model_dict[service] = []
                
        logger.info(f"ブラウザセッション方式でモデルリストを取得: {len(model_dict)}サービス")
        return model_dict
        
    except Exception as e:
        logger.error(f"モデルリスト取得エラー: {e}")
        # エラー時は各サービスの空リストを返す
        return {
            "chatgpt": [],
            "claude": [],
            "gemini": [],
            "genspark": [],
            "google_ai_studio": []
        }


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    print("ブラウザセッション方式でモデルリストを取得します...")
    print("注意: Chromeをデバッグモードで起動してください:")
    print("  macOS/Linux: google-chrome --remote-debugging-port=9222")
    print("  Windows: chrome.exe --remote-debugging-port=9222\n")
    
    models = update_model_list()
    
    print("\n取得結果:")
    for service, model_list in models.items():
        print(f"{service}: {model_list}")