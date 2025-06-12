#!/usr/bin/env python3
"""
高度なAI処理システム
各作業毎のモデル選択とDeepResearch等の設定対応
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.automation.extension_bridge import ExtensionBridge
from src.sheets.sheets_client import SheetsClient

class AdvancedAIProcessor:
    """高度なAI処理クラス"""
    
    def __init__(self):
        """初期化"""
        self.bridge = ExtensionBridge()
        self.sheets_client = SheetsClient()
        
        # 利用可能なAIモデル定義
        self.available_models = {
            "chatgpt": [
                "gpt-4o",
                "gpt-4o-mini", 
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ],
            "claude": [
                "claude-3.5-sonnet",
                "claude-3-opus",
                "claude-3-haiku"
            ],
            "gemini": [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro"
            ],
            "genspark": [
                "default"
            ],
            "google_ai_studio": [
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ]
        }
        
        # AI設定オプション
        self.ai_settings = {
            "chatgpt": {
                "deep_research": True,
                "web_search": True,
                "code_interpreter": True,
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "claude": {
                "thinking_mode": True,
                "artifacts": True,
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "gemini": {
                "safety_settings": "default",
                "temperature": 0.7,
                "max_tokens": 4000
            }
        }
    
    def process_spreadsheet_with_settings(self, spreadsheet_url: str, sheet_name: str) -> bool:
        """スプレッドシートを設定付きで処理"""
        
        print("🚀 高度なAI処理システム開始")
        print("=" * 50)
        
        # 1. スプレッドシート解析
        sheet_id = self.extract_sheet_id(spreadsheet_url)
        if not sheet_id:
            print("❌ 無効なスプレッドシートURL")
            return False
        
        data = self.sheets_client.read_range(sheet_id, f"{sheet_name}!A1:Z100")
        if not data:
            print("❌ スプレッドシートデータが見つかりません")
            return False
        
        # 2. 列構造解析
        column_info = self.analyze_spreadsheet_structure(data)
        if not column_info:
            print("❌ スプレッドシート構造が不正です")
            return False
        
        print("✅ スプレッドシート解析完了")
        print(f"📋 作業指示行: {column_info['work_row'] + 1}行目")
        print(f"📝 処理対象列: {[chr(65 + col) for col in column_info['copy_columns']]}")
        
        # 3. 各作業毎の設定取得
        work_configs = self.get_work_configurations(data, column_info)
        print(f"⚙️ 作業設定: {len(work_configs)}個の設定を取得")
        
        # 4. 作業実行
        return self.execute_advanced_processing(sheet_id, sheet_name, data, column_info, work_configs)
    
    def analyze_spreadsheet_structure(self, data: List[List[str]]) -> Optional[Dict]:
        """スプレッドシート構造を解析"""
        
        # 作業指示行検索
        work_row = None
        for i, row in enumerate(data):
            if len(row) > 0 and '作業' in str(row[0]):
                work_row = i
                break
        
        if work_row is None:
            return None
        
        # 列情報取得
        header_row = data[work_row]
        copy_columns = []
        model_columns = []
        setting_columns = []
        
        for j, cell in enumerate(header_row):
            cell_str = str(cell).strip().lower()
            if cell_str == 'コピー':
                copy_columns.append(j)
            elif 'モデル' in cell_str or 'model' in cell_str:
                model_columns.append(j)
            elif '設定' in cell_str or 'setting' in cell_str:
                setting_columns.append(j)
        
        return {
            'work_row': work_row,
            'copy_columns': copy_columns,
            'model_columns': model_columns,
            'setting_columns': setting_columns,
            'header_row': header_row
        }
    
    def get_work_configurations(self, data: List[List[str]], column_info: Dict) -> List[Dict]:
        """各作業の設定を取得"""
        
        configs = []
        work_row = column_info['work_row']
        
        for copy_col in column_info['copy_columns']:
            # 対応するモデル列と設定列を検索
            model_col = None
            setting_col = None
            
            # コピー列に最も近いモデル列を検索
            for model_c in column_info['model_columns']:
                if abs(model_c - copy_col) <= 3:  # 3列以内
                    model_col = model_c
                    break
            
            # コピー列に最も近い設定列を検索
            for setting_c in column_info['setting_columns']:
                if abs(setting_c - copy_col) <= 3:  # 3列以内
                    setting_col = setting_c
                    break
            
            config = {
                'copy_col': copy_col,
                'process_col': copy_col - 2,
                'paste_col': copy_col + 1,
                'error_col': copy_col - 1,
                'model_col': model_col,
                'setting_col': setting_col,
                'default_ai': 'chatgpt',
                'default_model': 'gpt-4o',
                'default_settings': self.ai_settings['chatgpt'].copy()
            }
            
            configs.append(config)
        
        return configs
    
    def execute_advanced_processing(self, sheet_id: str, sheet_name: str, 
                                  data: List[List[str]], column_info: Dict, 
                                  work_configs: List[Dict]) -> bool:
        """高度な処理実行"""
        
        print("\n🤖 高度なAI処理開始...")
        total_processed = 0
        total_success = 0
        
        for config_idx, config in enumerate(work_configs):
            print(f"\n📝 設定 {config_idx + 1}/{len(work_configs)} を処理中...")
            print(f"  コピー列: {chr(65 + config['copy_col'])}")
            
            # 処理対象行を検索
            work_row = column_info['work_row']
            row_idx = work_row + 1
            
            while row_idx < len(data):
                # A列チェック（処理対象判定）
                if (len(data[row_idx]) == 0 or 
                    not str(data[row_idx][0]).strip() or
                    not str(data[row_idx][0]).strip().isdigit()):
                    if not str(data[row_idx][0]).strip():
                        break  # 空行で終了
                    row_idx += 1
                    continue
                
                # 処理済みチェック
                if (len(data[row_idx]) > config['process_col'] and 
                    str(data[row_idx][config['process_col']]).strip() == '処理済み'):
                    row_idx += 1
                    continue
                
                # コピーテキスト取得
                if len(data[row_idx]) <= config['copy_col']:
                    row_idx += 1
                    continue
                
                copy_text = str(data[row_idx][config['copy_col']]).strip()
                if not copy_text:
                    row_idx += 1
                    continue
                
                print(f"    行 {row_idx + 1}: {copy_text[:40]}...")
                
                # この行の設定を取得
                row_config = self.get_row_specific_config(data[row_idx], config)
                
                print(f"      AI: {row_config['ai_service']}")
                print(f"      モデル: {row_config['model']}")
                print(f"      設定: {list(row_config['settings'].keys())}")
                
                try:
                    # AI処理実行（設定付き）
                    result = self.process_with_advanced_settings(
                        text=copy_text,
                        ai_service=row_config['ai_service'],
                        model=row_config['model'],
                        settings=row_config['settings']
                    )
                    
                    if result['success']:
                        # 成功時の処理
                        response_text = result['result']
                        
                        # 結果書き込み
                        paste_range = f"{sheet_name}!{chr(65 + config['paste_col'])}{row_idx + 1}"
                        self.sheets_client.write_range(sheet_id, paste_range, [[response_text]])
                        
                        # 処理完了マーク
                        process_range = f"{sheet_name}!{chr(65 + config['process_col'])}{row_idx + 1}"
                        self.sheets_client.write_range(sheet_id, process_range, [["処理済み"]])
                        
                        total_success += 1
                        print(f"      ✅ 成功")
                    else:
                        # エラー記録
                        error_range = f"{sheet_name}!{chr(65 + config['error_col'])}{row_idx + 1}"
                        self.sheets_client.write_range(sheet_id, error_range, [[result['error']]])
                        print(f"      ❌ 失敗: {result['error']}")
                    
                    total_processed += 1
                    
                except Exception as e:
                    # エラー記録
                    error_range = f"{sheet_name}!{chr(65 + config['error_col'])}{row_idx + 1}"
                    self.sheets_client.write_range(sheet_id, error_range, [[str(e)]])
                    print(f"      ❌ エラー: {e}")
                    total_processed += 1
                
                row_idx += 1
                time.sleep(2)  # レート制限対策
        
        # 結果表示
        print(f"\n📊 処理完了")
        print(f"  総処理数: {total_processed}")
        print(f"  成功数: {total_success}")
        print(f"  成功率: {total_success/total_processed*100:.1f}%" if total_processed > 0 else "  成功率: 0%")
        
        return total_success > 0
    
    def get_row_specific_config(self, row_data: List[str], base_config: Dict) -> Dict:
        """行固有の設定を取得"""
        
        config = {
            'ai_service': base_config['default_ai'],
            'model': base_config['default_model'],
            'settings': base_config['default_settings'].copy()
        }
        
        # モデル列から設定取得
        if (base_config['model_col'] is not None and 
            len(row_data) > base_config['model_col']):
            
            model_text = str(row_data[base_config['model_col']]).strip()
            if model_text:
                # AI:モデル 形式の解析
                if ':' in model_text:
                    ai_part, model_part = model_text.split(':', 1)
                    config['ai_service'] = ai_part.strip().lower()
                    config['model'] = model_part.strip()
                else:
                    config['model'] = model_text
        
        # 設定列から詳細設定取得
        if (base_config['setting_col'] is not None and 
            len(row_data) > base_config['setting_col']):
            
            settings_text = str(row_data[base_config['setting_col']]).strip()
            if settings_text:
                try:
                    # JSON形式または key=value 形式の解析
                    if settings_text.startswith('{'):
                        custom_settings = json.loads(settings_text)
                        config['settings'].update(custom_settings)
                    else:
                        # key=value,key2=value2 形式
                        for setting_pair in settings_text.split(','):
                            if '=' in setting_pair:
                                key, value = setting_pair.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                # 特定の設定を処理
                                if key.lower() == 'deepresearch':
                                    config['settings']['deep_research'] = value.lower() in ['true', '1', 'yes']
                                elif key.lower() == 'websearch':
                                    config['settings']['web_search'] = value.lower() in ['true', '1', 'yes']
                                elif key.lower() == 'temperature':
                                    config['settings']['temperature'] = float(value)
                                else:
                                    config['settings'][key] = value
                                    
                except Exception as e:
                    print(f"      ⚠️ 設定解析エラー: {e}")
        
        return config
    
    def process_with_advanced_settings(self, text: str, ai_service: str, 
                                     model: str, settings: Dict) -> Dict:
        """高度な設定でAI処理実行"""
        
        # 基本的なAI処理
        result = self.bridge.process_with_extension(
            text=text,
            ai_service=ai_service,
            model=model
        )
        
        # 設定情報を結果に追加
        if result.get('success'):
            result['used_settings'] = settings
            result['model'] = model
            result['ai_service'] = ai_service
        
        return result
    
    def extract_sheet_id(self, url: str) -> Optional[str]:
        """スプレッドシートURLからIDを抽出"""
        if '/spreadsheets/d/' in url:
            return url.split('/spreadsheets/d/')[1].split('/')[0]
        return None
    
    def show_available_models(self):
        """利用可能なモデル一覧を表示"""
        print("🤖 利用可能なAIとモデル:")
        for ai, models in self.available_models.items():
            print(f"  {ai.upper()}:")
            for model in models:
                print(f"    - {model}")
    
    def show_available_settings(self):
        """利用可能な設定一覧を表示"""
        print("⚙️ 利用可能な設定:")
        for ai, settings in self.ai_settings.items():
            print(f"  {ai.upper()}:")
            for key, default_value in settings.items():
                print(f"    - {key}: {default_value}")

if __name__ == "__main__":
    processor = AdvancedAIProcessor()
    
    print("🎯 高度なAI自動化システム")
    print("各作業毎にAIモデルと設定を指定できます")
    
    processor.show_available_models()
    print()
    processor.show_available_settings()
    
    print("\n📋 スプレッドシート構造例:")
    print("A列: 作業番号 (1, 2, 3...)")
    print("B列: 処理状況")
    print("C列: エラー")
    print("D列: コピー (AIに送信するテキスト)")
    print("E列: モデル (例: chatgpt:gpt-4o, claude:claude-3.5-sonnet)")
    print("F列: 設定 (例: deepresearch=true,temperature=0.8)")
    print("G列: 貼り付け (AI回答)")
    
    # テスト実行
    # processor.process_spreadsheet_with_settings(
    #     spreadsheet_url="YOUR_SPREADSHEET_URL",
    #     sheet_name="Sheet1"
    # )