# 🚨 厳格なファイル編集ルール

## 各AIが作成・編集できるファイル（これ以外は絶対に触らない）

### AI-A（ブラウザセッション方式）
**作成するファイル（1つのみ）**：
```
src/gui/browser_session_fetcher.py
```

### AI-B（手動管理方式）
**作成するファイル（2つのみ）**：
```
src/gui/manual_model_manager.py
config/manual_models.json
```

### AI-C（API方式）
**作成するファイル（1つのみ）**：
```
src/gui/api_model_fetcher.py
```

## 🚫 絶対に触ってはいけないファイル

```
❌ src/gui/main_window.py
❌ src/gui/ai_model_updater.py  
❌ gui_app.py
❌ その他すべての既存ファイル
```

## 統合方法

最終的に採用された実装は、私（統合担当）が`main_window.py`に組み込みます。
各AIは自分のファイルに`update_model_list()`関数を実装するだけです。

```python
# 各AIが実装する関数
def update_model_list() -> dict:
    """モデルリストを返す"""
    return {
        "chatgpt": [...],
        "claude": [...],
        "gemini": [...],
        "genspark": [...],
        "google_ai_studio": [...]
    }
```

## なぜこのルールが重要か

- 複数のAIが同じファイルを編集するとコンフリクトが発生
- main_window.pyは中核ファイルなので、壊れるとアプリ全体が動かなくなる
- 各AIの実装を独立させることで、並行作業が可能になる