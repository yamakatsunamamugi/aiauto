# AI並行開発 安全作業ガイド

## 🚨 重要: 各AIは自分専用のファイルで作業してください

混乱や事故を防ぐため、各AIは**決められたファイルのみ**を編集してください。

---

## 📁 各AIの専用ファイル

### 🤖 AI-A（ブラウザセッション方式）
**作成・編集して良いファイル:**
```
src/gui/browser_session_fetcher.py    ← このファイルを新規作成
config/browser_settings.json           ← 必要なら作成可
```

### 🤖 AI-B（手動管理方式）
**作成・編集して良いファイル:**
```
src/gui/manual_model_manager.py        ← このファイルを新規作成
src/gui/model_edit_dialog.py           ← 必要なら作成可
config/manual_models.json              ← モデルリスト保存用
```

### 🤖 AI-C（API/創造的方式）
**作成・編集して良いファイル:**
```
src/gui/api_model_fetcher.py           ← このファイルを新規作成
config/api_settings.json               ← 必要なら作成可
```

---

## 🚫 絶対に触ってはいけないファイル

以下のファイルは**読むことはOK**ですが、**編集は厳禁**です：

```
❌ src/gui/main_window.py              ← メインGUI（読むだけ）
❌ src/gui/ai_model_updater.py         ← 既存の更新機能（読むだけ）
❌ gui_app.py                          ← アプリ起動ファイル（読むだけ）
❌ 他のAIが作成したファイル              ← 絶対に編集しない
```

---

## 📝 具体的な実装手順

### ステップ1: 自分のブランチを確認
```bash
# 現在のブランチを確認（重要！）
git branch

# 自分のブランチになっていることを確認
# AI-A → feature/model-fetch-browser
# AI-B → feature/model-fetch-manual  
# AI-C → feature/model-fetch-api
```

### ステップ2: 自分専用のファイルを作成

**AI-A の例:**
```python
# src/gui/browser_session_fetcher.py を新規作成
class BrowserSessionFetcher:
    """ブラウザセッションからモデル情報を取得"""
    
    def get_models(self):
        # あなたの実装をここに書く
        pass
```

**AI-B の例:**
```python
# src/gui/manual_model_manager.py を新規作成
class ManualModelManager:
    """手動でモデルを管理"""
    
    def show_edit_dialog(self):
        # あなたの実装をここに書く
        pass
```

**AI-C の例:**
```python
# src/gui/api_model_fetcher.py を新規作成
class APIModelFetcher:
    """APIからモデル情報を取得"""
    
    def fetch_from_api(self):
        # あなたの実装をここに書く
        pass
```

### ステップ3: main_window.pyとの連携

`main_window.py`を編集せずに連携する方法：

```python
# あなたの専用ファイルに以下のような関数を作成
def update_model_list():
    """
    この関数がmain_window.pyから呼ばれます
    
    Returns:
        dict: {"chatgpt": [...], "claude": [...], "gemini": [...]}
    """
    # あなたの実装
    return {
        "chatgpt": ["gpt-4o", "gpt-4o-mini"],
        "claude": ["claude-3.5-sonnet"],
        "gemini": ["gemini-1.5-pro"]
    }
```

### ステップ4: テスト用スクリプトを作成

```python
# test_my_implementation.py を作成（AI-Aの例）
from src.gui.browser_session_fetcher import BrowserSessionFetcher

def test():
    fetcher = BrowserSessionFetcher()
    models = fetcher.get_models()
    print("取得したモデル:", models)
    
    # 期待される結果と比較
    assert "gpt-4o" in models.get("chatgpt", [])
    print("✅ テスト成功！")

if __name__ == "__main__":
    test()
```

---

## ✅ 作業チェックリスト

### 作業前の確認
- [ ] 正しいブランチにいることを確認した（`git branch`）
- [ ] 他のファイルを編集していないことを確認した（`git status`）

### 実装時の確認
- [ ] 自分専用のファイルのみを作成・編集している
- [ ] main_window.pyは読むだけで編集していない
- [ ] 他のAIのファイルには触れていない

### 提出前の確認
- [ ] テストスクリプトで動作確認した
- [ ] 取得したモデルリストが正しい
- [ ] `git status`で余計なファイルを編集していないか確認

---

## 🎯 期待される成果物

各AIは以下を提出してください：

1. **実装ファイル** （自分専用のファイル）
2. **テスト結果** （取得できたモデルリスト）
3. **簡単な使い方説明**

例：
```
## AI-A 実装完了報告

### 実装ファイル
- src/gui/browser_session_fetcher.py

### 取得結果
ChatGPT: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
Claude: ["claude-3.5-sonnet", "claude-3-opus"]
Gemini: ["gemini-1.5-pro", "gemini-1.5-flash"]

### 使い方
1. Chromeにログイン済みであることを確認
2. update_model_list()を呼ぶだけ
```

---

## ⚠️ トラブル回避のポイント

1. **ブランチを間違えたら**: 作業を中止して正しいブランチに切り替え
2. **間違えてファイルを編集したら**: `git checkout -- ファイル名`で元に戻す
3. **コンフリクトが心配**: 自分専用のファイルなら絶対にコンフリクトしません

質問があれば作業を始める前に確認してください！