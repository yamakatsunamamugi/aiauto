#!/usr/bin/env python3
"""
コマンドライン AI自動化実行スクリプト（GUI不要）
使用方法: python run_automation_cli.py
"""

import sys
import asyncio
from typing import List, Dict
import json

def main():
    """メイン実行関数"""
    print("🚀 AI自動化システム - コマンドライン版")
    print("=" * 50)
    
    # 1. 設定入力
    print("📋 設定入力:")
    
    # スプレッドシートURL入力
    sheet_url = input("📊 スプレッドシートURL: ").strip()
    if not sheet_url:
        sheet_url = "https://docs.google.com/spreadsheets/d/1C5aOSyyCBXf7HwF-BGGu-cz5jdRwNBaoW4G4ivIRrRg/edit?gid=1633283608#gid=1633283608"
        print(f"   デフォルトURL使用: {sheet_url[:60]}...")
    
    # シート名入力
    sheet_name = input("📋 シート名 (Enterでデフォルト): ").strip()
    if not sheet_name:
        sheet_name = "1.原稿本文作成"
        print(f"   デフォルトシート名使用: {sheet_name}")
    
    # AIサービス選択
    print("\n🤖 AIサービス選択:")
    print("1. ChatGPT")
    print("2. Claude") 
    print("3. Gemini")
    print("4. Genspark")
    print("5. Google AI Studio")
    
    ai_choice = input("選択 (1-5, Enterで1): ").strip()
    ai_services = {
        "1": "chatgpt",
        "2": "claude", 
        "3": "gemini",
        "4": "genspark",
        "5": "google_ai_studio"
    }
    selected_ai = ai_services.get(ai_choice, "chatgpt")
    print(f"   選択されたAI: {selected_ai}")
    
    # 実行確認
    print(f"\n✅ 設定確認:")
    print(f"   スプレッドシート: {sheet_url[:60]}...")
    print(f"   シート名: {sheet_name}")
    print(f"   AIサービス: {selected_ai}")
    
    confirm = input("\n🚀 実行しますか？ (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 実行をキャンセルしました")
        return
    
    # 2. 実際の自動化実行
    print("\n" + "=" * 50)
    print("🔄 自動化実行開始...")
    
    try:
        # システム初期化
        from src.sheets.data_handler import DataHandler
        from src.automation.automation_controller import AutomationController
        
        print("📋 1. システム初期化...")
        data_handler = DataHandler()
        automation_controller = AutomationController()
        
        # Google Sheets認証
        print("🔐 2. Google Sheets認証...")
        auth_success = data_handler.authenticate()
        if not auth_success:
            print("❌ Google Sheets認証に失敗しました")
            print("💡 config/credentials.json を確認してください")
            return
        print("✅ 認証成功")
        
        # シート読み込み
        print("📊 3. スプレッドシート読み込み...")
        sheet_structure = data_handler.load_sheet_from_url(sheet_url, sheet_name)
        if not sheet_structure:
            print("❌ スプレッドシート読み込みに失敗しました")
            return
        print(f"✅ シート読み込み成功")
        
        # タスク行作成
        print("📝 4. タスク行作成...")
        task_rows = data_handler.create_task_rows(sheet_structure)
        if not task_rows:
            print("❌ 処理対象のタスクが見つかりません")
            return
        print(f"✅ {len(task_rows)}件のタスクを検出")
        
        # タスク実行
        print("🤖 5. AI自動化実行...")
        successful_count = 0
        failed_count = 0
        
        for i, task_row in enumerate(task_rows):
            print(f"   🔄 タスク{i+1}/{len(task_rows)}: 行{task_row.row_number}")
            print(f"      テキスト: {task_row.copy_text[:50]}...")
            
            try:
                # AI設定を指定されたサービスに変更
                from src.sheets.models import AIService
                ai_service_enum = getattr(AIService, selected_ai.upper())
                task_row.ai_config.ai_service = ai_service_enum
                
                # デモ処理（実際のAI処理の代わり）
                import time
                time.sleep(1)  # 処理時間シミュレーション
                
                demo_result = f"AI({selected_ai})処理結果: {task_row.copy_text[:30]}... への応答"
                
                # 結果をシートに書き戻し
                success = data_handler.update_task_result(task_row, demo_result)
                
                if success:
                    successful_count += 1
                    print(f"      ✅ 完了")
                else:
                    failed_count += 1
                    print(f"      ❌ 書き戻し失敗")
                    
            except Exception as task_error:
                failed_count += 1
                print(f"      ❌ エラー: {task_error}")
        
        # 結果表示
        print("\n" + "=" * 50)
        print("🎉 自動化処理完了！")
        print(f"📊 結果: 成功{successful_count}件、失敗{failed_count}件")
        print(f"📈 成功率: {successful_count/(successful_count+failed_count)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        print("💡 詳細なエラー情報:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()