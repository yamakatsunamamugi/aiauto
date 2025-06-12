# 実装インターフェース仕様書

## 各AIの実装を統合するための共通インターフェース

### 必須: update_model_list() 関数

各AIは自分の実装ファイルに以下の関数を**必ず**実装してください：

```python
def update_model_list() -> dict:
    """
    最新のモデルリストを取得する
    
    Returns:
        dict: 各AIサービスのモデルリスト
        {
            "chatgpt": ["gpt-4o", "gpt-4o-mini", ...],
            "claude": ["claude-3.5-sonnet", ...],
            "gemini": ["gemini-1.5-pro", ...],
            "genspark": ["default", ...],
            "google_ai_studio": ["gemini-1.5-pro", ...]
        }
    """
    # あなたの実装をここに書く
    pass
```

### 実装例

**AI-A (browser_session_fetcher.py):**
```python
from playwright.sync_api import sync_playwright

def update_model_list() -> dict:
    """ブラウザセッションから取得"""
    try:
        # ブラウザ操作のコード
        with sync_playwright() as p:
            # ... 実装 ...
            return {
                "chatgpt": ["gpt-4o", "gpt-4o-mini"],
                "claude": ["claude-3.5-sonnet"],
                "gemini": ["gemini-1.5-pro"]
            }
    except Exception as e:
        print(f"エラー: {e}")
        return {}
```

**AI-B (manual_model_manager.py):**
```python
import json
import os

def update_model_list() -> dict:
    """手動設定ファイルから読み込み"""
    config_path = "config/manual_models.json"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # デフォルト値
        return {
            "chatgpt": ["gpt-4o"],
            "claude": ["claude-3.5-sonnet"],
            "gemini": ["gemini-1.5-pro"]
        }
```

**AI-C (api_model_fetcher.py):**
```python
import requests

def update_model_list() -> dict:
    """APIから取得"""
    models = {}
    
    # OpenAI API
    try:
        # API呼び出しの実装
        models["chatgpt"] = ["gpt-4o", "gpt-4o-mini"]
    except:
        models["chatgpt"] = []
    
    # 他のサービスも同様に
    return models
```

### エラーハンドリング

- エラーが発生した場合は空の辞書 `{}` を返す
- または部分的な結果を返す（取得できたサービスのみ）
- エラーメッセージは標準出力に表示

### テスト方法

```python
# test_implementation.py
from src.gui.あなたのファイル名 import update_model_list

# 関数を呼び出し
result = update_model_list()

# 結果を確認
print("取得結果:")
print(json.dumps(result, indent=2, ensure_ascii=False))

# 必須チェック
assert isinstance(result, dict), "辞書を返す必要があります"
assert "chatgpt" in result, "chatgptのキーが必要です"
assert "claude" in result, "claudeのキーが必要です"
assert "gemini" in result, "geminiのキーが必要です"
```

### 重要な注意事項

1. **関数名は必ず `update_model_list`** にする
2. **引数なし、戻り値は辞書型**
3. **5つのAIサービス全てのキーを含める**（値が空リストでもOK）
4. **同期関数として実装**（非同期にしない）

この仕様に従えば、どの実装も簡単に切り替えて使えます！