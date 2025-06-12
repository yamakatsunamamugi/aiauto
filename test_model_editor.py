#!/usr/bin/env python3
"""
モデル編集機能のテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.gui.model_json_editor import ModelJsonEditor

def test_model_editor():
    """モデル編集ダイアログのテスト"""
    print("📝 モデル編集ダイアログをテストします...")
    
    # エディタを表示
    editor = ModelJsonEditor()
    result = editor.show()
    
    if result:
        print("\n✅ 保存されたデータ:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n❌ キャンセルされました")

if __name__ == "__main__":
    test_model_editor()