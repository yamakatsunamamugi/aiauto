#!/usr/bin/env python3
"""
スプレッドシート×AI自動化GUIアプリケーション起動スクリプト
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """必要なライブラリがインストールされているか確認"""
    required_packages = {
        'playwright': 'playwright',
        'gspread': 'gspread',
        'google.auth': 'google-auth'
    }
    
    missing_packages = []
    
    for package_import, package_name in required_packages.items():
        try:
            __import__(package_import)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("=== 必要なライブラリがインストールされていません ===")
        print(f"不足しているパッケージ: {', '.join(missing_packages)}")
        print("\n以下のコマンドを実行してインストールしてください：")
        print(f"pip install -r requirements_spreadsheet_automation.txt")
        print("\nPlaywrightの場合は追加で以下も実行してください：")
        print("playwright install chromium")
        return False
    
    # Playwrightのブラウザがインストールされているか確認
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except Exception:
        print("\n=== Playwrightのブラウザがインストールされていません ===")
        print("以下のコマンドを実行してください：")
        print("playwright install chromium")
        return False
    
    return True

def setup_credentials():
    """認証ファイルの確認"""
    cred_path = Path("config/credentials.json")
    example_path = Path("config/credentials_example.json")
    
    if not cred_path.exists():
        print("\n=== Google Sheets認証ファイルが見つかりません ===")
        print(f"認証ファイルを {cred_path} に配置してください。")
        
        if example_path.exists():
            print(f"\n{example_path} を参考に設定してください。")
        else:
            print("\nGoogle Cloud Consoleでサービスアカウントを作成し、")
            print("認証情報をJSONファイルとしてダウンロードしてください。")
            print("\n詳細: https://docs.gspread.org/en/latest/oauth2.html")
        
        return False
    
    return True

def main():
    """メイン処理"""
    print("=== スプレッドシート×AI自動化GUIアプリケーション ===")
    print("起動準備中...\n")
    
    # 必要な準備を確認
    if not check_requirements():
        sys.exit(1)
    
    if not setup_credentials():
        print("\n認証ファイルの設定後、再度実行してください。")
        sys.exit(1)
    
    print("\n準備完了！アプリケーションを起動します...\n")
    
    # アプリケーションを起動
    try:
        subprocess.run([sys.executable, "spreadsheet_ai_automation_gui.py"])
    except KeyboardInterrupt:
        print("\n\nアプリケーションを終了しました。")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()