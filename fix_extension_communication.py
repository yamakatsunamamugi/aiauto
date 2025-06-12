#!/usr/bin/env python3
"""
Chrome拡張機能との通信問題を修正するスクリプト
"""

import os
import json
import time
import subprocess
from pathlib import Path

def main():
    print("🔧 Chrome拡張機能通信の修正")
    print("=" * 60)
    
    # 1. Native Messaging Hostの設定
    print("\n1️⃣ Native Messaging Hostの設定")
    
    # manifest.jsonの作成
    host_manifest = {
        "name": "com.aiauto.bridge",
        "description": "AI Automation Bridge Native Host",
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://YOUR_EXTENSION_ID/"
        ]
    }
    
    # ホストスクリプトの作成
    host_script = '''#!/usr/bin/env python3
import sys
import json
import struct

def send_message(message):
    encoded = json.dumps(message).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('I', len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()

def read_message():
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    length = struct.unpack('I', raw_length)[0]
    message = sys.stdin.buffer.read(length).decode('utf-8')
    return json.loads(message)

while True:
    message = read_message()
    if message:
        # エコーバック（テスト用）
        send_message({"echo": message})
'''
    
    print("\n🛠️ 解決方法:")
    print("\n方法1: Chrome拡張機能を更新（推奨）")
    print("1. Chrome拡張機能のmanifest.jsonに以下を追加:")
    print('   "permissions": ["nativeMessaging"]')
    print("\n2. Native Messaging Hostを設定")
    print("\n3. またはWebSocketサーバーを使用")
    
    print("\n方法2: 既存の通信方法を使用")
    print("Chrome拡張機能は現在chrome.storageを使用しています。")
    print("PythonからはChrome DevTools Protocolを使用して通信できます。")
    
    print("\n📝 簡単な解決策:")
    print("1. Chromeで http://localhost:8080 などのローカルサーバーを立てる")
    print("2. そのページ経由でchrome.storageにアクセス")
    print("3. または、Seleniumを使用してChromeを操作")
    
    # Seleniumを使用した簡易テスト
    print("\n🚀 Seleniumを使用したテスト方法:")
    print("""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Chrome拡張機能を有効にして起動
options = Options()
options.add_extension('/path/to/extension.crx')  # または拡張機能フォルダを指定

driver = webdriver.Chrome(options=options)
driver.get('https://chat.openai.com/')

# JavaScript経由でchrome.storageにアクセス
driver.execute_script('''
    chrome.storage.local.set({
        pendingRequest: {
            request_id: "test_123",
            text: "テストメッセージ",
            model: "gpt-4o-mini"
        }
    });
''')
""")

if __name__ == "__main__":
    main()