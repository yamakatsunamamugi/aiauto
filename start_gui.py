#!/usr/bin/env python3
"""
GUIアプリケーション起動スクリプト
"""
import subprocess
import sys
import os

def main():
    print("🚀 スプレッドシート自動化GUIアプリを起動します")
    print("=" * 60)
    
    # アプリケーションパス
    app_path = os.path.join(os.path.dirname(__file__), "gui_automation_app_fixed.py")
    
    print(f"📱 アプリケーション: {app_path}")
    print("\n⏳ 起動中...")
    
    try:
        # GUIアプリケーションを起動
        subprocess.run([sys.executable, app_path], check=True)
    except KeyboardInterrupt:
        print("\n⏹️ アプリケーションを終了しました")
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        
if __name__ == "__main__":
    main()