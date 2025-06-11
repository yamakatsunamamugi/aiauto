#!/usr/bin/env python3
"""
Google Sheets API設定チェックスクリプト

このスクリプトは、Google Sheets APIの設定が正しく行われているか確認します。
初心者の方でも簡単に実行できるように設計されています。
"""

import os
import json
import sys
from pathlib import Path


def check_credentials_file():
    """credentials.jsonファイルの存在と内容を確認"""
    print("=" * 60)
    print("📋 Google Sheets API設定チェック")
    print("=" * 60)
    
    # ファイルパスの確認
    project_root = Path(__file__).parent
    credentials_path = project_root / "config" / "credentials.json"
    credentials_example_path = project_root / "config" / "credentials_example.json"
    
    print(f"\n1️⃣ credentials.jsonファイルの確認")
    print(f"   期待される場所: {credentials_path}")
    
    if not credentials_path.exists():
        print("   ❌ ファイルが見つかりません！")
        print("\n   📝 対処方法:")
        print("   1. docs/google_sheets_api_setup_guide.md を参照してください")
        print("   2. Google Cloud ConsoleからJSONファイルをダウンロード")
        print("   3. ファイル名を 'credentials.json' に変更")
        print(f"   4. {credentials_path} に保存")
        
        if credentials_example_path.exists():
            print(f"\n   💡 ヒント: {credentials_example_path} に例があります")
        
        return False
    
    print("   ✅ ファイルが見つかりました！")
    
    # ファイル内容の確認
    print("\n2️⃣ credentials.jsonの内容確認")
    try:
        with open(credentials_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        required_fields = {
            'type': 'サービスアカウントタイプ',
            'project_id': 'プロジェクトID',
            'private_key_id': '秘密鍵ID',
            'private_key': '秘密鍵',
            'client_email': 'サービスアカウントメール',
            'client_id': 'クライアントID',
        }
        
        all_valid = True
        for field, description in required_fields.items():
            if field in data and data[field]:
                print(f"   ✅ {description}: 設定済み")
                if field == 'client_email':
                    print(f"      → {data[field]}")
                    print(f"      ⚠️  このメールアドレスをスプレッドシートに共有してください！")
            else:
                print(f"   ❌ {description}: 未設定")
                all_valid = False
        
        if data.get('type') != 'service_account':
            print(f"   ❌ タイプが正しくありません: {data.get('type')} (期待値: service_account)")
            all_valid = False
        
        return all_valid
        
    except json.JSONDecodeError:
        print("   ❌ JSONファイルの形式が正しくありません！")
        return False
    except Exception as e:
        print(f"   ❌ ファイル読み込みエラー: {e}")
        return False


def check_dependencies():
    """必要なPythonパッケージの確認"""
    print("\n3️⃣ 必要なパッケージの確認")
    
    packages = {
        'google.auth': 'google-auth',
        'googleapiclient': 'google-api-python-client',
        'google.oauth2': 'google-auth'
    }
    
    all_installed = True
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"   ✅ {package}: インストール済み")
        except ImportError:
            print(f"   ❌ {package}: 未インストール")
            all_installed = False
    
    if not all_installed:
        print("\n   📝 対処方法:")
        print("   以下のコマンドを実行してください：")
        print("   pip install -r requirements.txt")
    
    return all_installed


def test_authentication():
    """実際に認証を試行"""
    print("\n4️⃣ Google Sheets API認証テスト")
    
    try:
        from src.sheets.auth_manager import create_auth_manager, AuthenticationError
        
        auth_manager = create_auth_manager()
        print("   ✅ 認証成功！")
        print(f"   サービスアカウント: {auth_manager.get_service_account_email()}")
        
        return True
        
    except ImportError:
        print("   ❌ sheetsモジュールが見つかりません")
        return False
    except AuthenticationError as e:
        print(f"   ❌ 認証エラー: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 予期しないエラー: {e}")
        return False


def main():
    """メイン処理"""
    # 各チェックを実行
    credentials_ok = check_credentials_file()
    dependencies_ok = check_dependencies()
    
    if credentials_ok and dependencies_ok:
        auth_ok = test_authentication()
    else:
        auth_ok = False
    
    # 結果のまとめ
    print("\n" + "=" * 60)
    print("📊 チェック結果のまとめ")
    print("=" * 60)
    
    if credentials_ok and dependencies_ok and auth_ok:
        print("✅ すべての設定が完了しています！")
        print("   AI自動化ツールを使用する準備ができました。")
        print("\n🚀 次のステップ:")
        print("   1. 使用するGoogleスプレッドシートにサービスアカウントを共有")
        print("   2. python main.py でツールを起動")
    else:
        print("❌ 設定が完了していません")
        print("\n📝 必要な作業:")
        if not credentials_ok:
            print("   - credentials.jsonファイルの設定")
        if not dependencies_ok:
            print("   - 必要なパッケージのインストール (pip install -r requirements.txt)")
        if credentials_ok and dependencies_ok and not auth_ok:
            print("   - Google Cloud ConsoleでのAPI設定確認")
        
        print("\n詳細は docs/google_sheets_api_setup_guide.md を参照してください。")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()