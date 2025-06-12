#!/usr/bin/env python3
"""
Chrome拡張機能を使わず、直接ブラウザを操作するテストスクリプト
"""

import sys
from pathlib import Path
import time

# プロジェクトパスを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def test_chatgpt_direct():
    print("🤖 ChatGPT直接操作テスト")
    print("=" * 60)
    
    # Chromeオプション設定
    options = webdriver.ChromeOptions()
    options.add_argument("--user-data-dir=/tmp/chrome_test_profile")
    
    print("⚠️ 注意: このテストを実行する前に、通常のChromeでChatGPTにログインしてください")
    print("\n続行しますか？ (y/n): ", end='')
    
    if input().lower() != 'y':
        print("テスト中止")
        return
    
    try:
        # Chromeドライバー起動
        print("\n🌐 Chromeを起動中...")
        driver = webdriver.Chrome(options=options)
        
        # ChatGPTを開く
        print("📝 ChatGPTを開いています...")
        driver.get("https://chat.openai.com/")
        
        # ページ読み込み待機
        time.sleep(3)
        
        # ログイン状態の確認
        print("🔐 ログイン状態を確認中...")
        
        try:
            # テキストエリアを探す
            textarea = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "prompt-textarea"))
            )
            print("✅ ログイン済み - テキストエリアが見つかりました")
            
            # テストメッセージ送信
            test_message = "これはSeleniumからのテストメッセージです。2+2は？"
            print(f"\n📤 メッセージ送信: {test_message}")
            
            textarea.clear()
            textarea.send_keys(test_message)
            textarea.send_keys(Keys.RETURN)
            
            # 応答待機
            print("⏳ 応答を待っています...")
            time.sleep(5)
            
            # 応答を取得
            try:
                responses = driver.find_elements(By.CSS_SELECTOR, '[data-message-author-role="assistant"]')
                if responses:
                    latest_response = responses[-1].text
                    print(f"\n✅ 応答受信:\n{latest_response[:200]}...")
                else:
                    print("❌ 応答が見つかりません")
            except Exception as e:
                print(f"❌ 応答取得エラー: {e}")
            
        except Exception as e:
            print(f"❌ ログインしていないか、UIが変更されています: {e}")
            print("\n💡 手動でログインしてください:")
            print("1. 表示されたブラウザでChatGPTにログイン")
            print("2. ログイン後、このスクリプトを再実行")
        
        print("\n🔍 ブラウザは開いたままです。確認後、Enterキーを押して終了してください...")
        input()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
            print("✅ ブラウザを終了しました")

if __name__ == "__main__":
    test_chatgpt_direct()