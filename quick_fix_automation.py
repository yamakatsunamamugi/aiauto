#!/usr/bin/env python3
"""
プロフェッショナルな即座の解決策
Chrome拡張機能をバイパスして、Seleniumで直接自動化
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class DirectAIAutomation:
    """Chrome拡張機能を使わない直接的なAI自動化"""
    
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.setup_driver()
        
    def setup_driver(self):
        """Chromeドライバーのセットアップ"""
        options = webdriver.ChromeOptions()
        
        # 既存のChromeプロファイルを使用（ログイン状態を保持）
        user_data_dir = Path.home() / "Library/Application Support/Google/Chrome"
        if user_data_dir.exists():
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument("--profile-directory=Default")
        
        if self.headless:
            options.add_argument("--headless")
            
        # その他の最適化オプション
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        
    def process_with_chatgpt(self, text, model="gpt-4o-mini"):
        """ChatGPTで処理"""
        try:
            print(f"🤖 ChatGPT処理開始: {text[:50]}...")
            
            # ChatGPTを開く
            self.driver.get("https://chat.openai.com/")
            time.sleep(2)
            
            # 新しいチャットを開始（クリーンな状態）
            try:
                new_chat_button = self.driver.find_element(By.CSS_SELECTOR, 'a[href="/"]')
                new_chat_button.click()
                time.sleep(1)
            except:
                pass
            
            # テキストエリアを見つける
            textarea = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "prompt-textarea"))
            )
            
            # テキスト入力
            textarea.clear()
            textarea.send_keys(text)
            
            # 送信
            textarea.send_keys(Keys.RETURN)
            
            # 応答を待つ
            print("⏳ 応答待機中...")
            time.sleep(3)  # 初期待機
            
            # ストリーミングが完了するまで待つ
            max_wait = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    # 停止ボタンが消えたら完了
                    stop_button = self.driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="Stop generating"]')
                    if not stop_button:
                        break
                except:
                    break
                time.sleep(0.5)
            
            # 最新の応答を取得
            responses = self.driver.find_elements(By.CSS_SELECTOR, '[data-message-author-role="assistant"]')
            if responses:
                response_text = responses[-1].text
                print("✅ 応答取得成功")
                return {
                    "success": True,
                    "result": response_text,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "応答が見つかりませんでした"
                }
                
        except TimeoutException:
            return {
                "success": False,
                "error": "タイムアウト: ChatGPTが応答しません。ログインを確認してください。"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"エラー: {str(e)}"
            }
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()

def main():
    """テスト実行"""
    print("🚀 直接自動化テスト")
    print("=" * 60)
    
    automation = DirectAIAutomation(headless=False)
    
    try:
        # テストメッセージ
        test_messages = [
            "こんにちは、今日は何曜日ですか？",
            "2 + 2 = ?",
            "Pythonで'Hello World'を出力するコードを書いて"
        ]
        
        for msg in test_messages:
            print(f"\n📝 テスト: {msg}")
            result = automation.process_with_chatgpt(msg)
            
            if result["success"]:
                print(f"✅ 成功: {result['result'][:100]}...")
            else:
                print(f"❌ 失敗: {result['error']}")
            
            time.sleep(2)  # レート制限対策
            
    finally:
        print("\n🏁 テスト完了")
        automation.close()

if __name__ == "__main__":
    main()