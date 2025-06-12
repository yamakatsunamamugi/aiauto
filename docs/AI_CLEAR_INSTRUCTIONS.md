# 🎯 各AIへの明確な作業指示

## 共通事項（全AI必読）

### リポジトリ
```
https://github.com/yamakatsunamamugi/aiauto
```

### あなたの役割
AIモデル取得機能の問題を解決する実装を作成する

### 現在の問題
- `src/gui/ai_model_updater.py`が公式ドキュメントから情報を取得している
- しかし、実際のWebアプリで使えるモデルと一致しない
- 例：ChatGPTのドキュメントには「gpt-4-32k」があるが、実際のchat.openai.comでは選択できない

---

## 🤖 AI-A への指示

### あなたの情報
- **担当**: ブラウザセッション方式
- **ブランチ**: `feature/model-fetch-browser`
- **作成するファイル**: `src/gui/browser_session_fetcher.py`

### 作業内容

1. **リポジトリをクローン**
```bash
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto
git checkout feature/model-fetch-browser
```

2. **ファイルを作成**
```bash
# 新規ファイルを作成
touch src/gui/browser_session_fetcher.py
```

3. **実装**
```python
# src/gui/browser_session_fetcher.py
from playwright.sync_api import sync_playwright
import os

def update_model_list() -> dict:
    """
    ブラウザセッションからモデルリストを取得
    
    Returns:
        dict: 各AIサービスのモデルリスト
    """
    # Chromeのユーザープロファイルパス
    # Mac: ~/Library/Application Support/Google/Chrome
    # Windows: %LOCALAPPDATA%\Google\Chrome\User Data
    
    # ここにあなたの実装を書く
    # ヒント: ログイン済みのChromeを使ってモデル選択メニューを開く
    
    return {
        "chatgpt": [],
        "claude": [],
        "gemini": [],
        "genspark": [],
        "google_ai_studio": []
    }
```

4. **テスト**
```bash
python -c "from src.gui.browser_session_fetcher import update_model_list; print(update_model_list())"
```

5. **コミット&プッシュ**
```bash
git add src/gui/browser_session_fetcher.py
git commit -m "feat: ブラウザセッション方式でモデル取得機能を実装"
git push origin feature/model-fetch-browser
```

### 触ってはいけないファイル
- ❌ `src/gui/main_window.py`
- ❌ `src/gui/ai_model_updater.py`
- ❌ `gui_app.py`
- ❌ 他のAIが作るファイル（manual_model_manager.py, api_model_fetcher.py）

---

## 🤖 AI-B への指示

### あなたの情報
- **担当**: 手動管理方式
- **ブランチ**: `feature/model-fetch-manual`
- **作成するファイル**: `src/gui/manual_model_manager.py`

### 作業内容

1. **リポジトリをクローン**
```bash
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto
git checkout feature/model-fetch-manual
```

2. **ファイルを作成**
```bash
# 新規ファイルを作成
touch src/gui/manual_model_manager.py
touch config/manual_models.json
```

3. **実装**
```python
# src/gui/manual_model_manager.py
import json
import tkinter as tk
from tkinter import ttk

def update_model_list() -> dict:
    """
    手動設定ファイルからモデルリストを読み込む
    
    Returns:
        dict: 各AIサービスのモデルリスト
    """
    # config/manual_models.jsonから読み込む
    # ファイルがなければデフォルト値を返す
    
    return {
        "chatgpt": ["gpt-4o", "gpt-4o-mini"],
        "claude": ["claude-3.5-sonnet"],
        "gemini": ["gemini-1.5-pro"],
        "genspark": ["default"],
        "google_ai_studio": ["gemini-1.5-pro"]
    }

def show_model_editor():
    """モデル編集用のGUIダイアログを表示"""
    # ここにGUI実装
    pass
```

4. **設定ファイルの例**
```json
{
  "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
  "claude": ["claude-3.5-sonnet", "claude-3-opus"],
  "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
  "genspark": ["default"],
  "google_ai_studio": ["gemini-1.5-pro"]
}
```

5. **テスト**
```bash
python -c "from src.gui.manual_model_manager import update_model_list; print(update_model_list())"
```

6. **コミット&プッシュ**
```bash
git add src/gui/manual_model_manager.py config/manual_models.json
git commit -m "feat: 手動管理方式でモデル取得機能を実装"
git push origin feature/model-fetch-manual
```

### 触ってはいけないファイル
- ❌ `src/gui/main_window.py`
- ❌ `src/gui/ai_model_updater.py`
- ❌ `gui_app.py`
- ❌ 他のAIが作るファイル（browser_session_fetcher.py, api_model_fetcher.py）

---

## 🤖 AI-C への指示

### あなたの情報
- **担当**: API/創造的方式
- **ブランチ**: `feature/model-fetch-api`
- **作成するファイル**: `src/gui/api_model_fetcher.py`

### 作業内容

1. **リポジトリをクローン**
```bash
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto
git checkout feature/model-fetch-api
```

2. **ファイルを作成**
```bash
# 新規ファイルを作成
touch src/gui/api_model_fetcher.py
```

3. **実装**
```python
# src/gui/api_model_fetcher.py
import requests
import json

def update_model_list() -> dict:
    """
    APIや創造的な方法でモデルリストを取得
    
    Returns:
        dict: 各AIサービスのモデルリスト
    """
    models = {}
    
    # OpenAI API の例
    # response = requests.get("https://api.openai.com/v1/models")
    
    # または他の創造的な方法
    # - Webスクレイピング
    # - リバースエンジニアリング
    # - 複数の方法の組み合わせ
    
    return {
        "chatgpt": [],
        "claude": [],
        "gemini": [],
        "genspark": [],
        "google_ai_studio": []
    }
```

4. **テスト**
```bash
python -c "from src.gui.api_model_fetcher import update_model_list; print(update_model_list())"
```

5. **コミット&プッシュ**
```bash
git add src/gui/api_model_fetcher.py
git commit -m "feat: API方式でモデル取得機能を実装"
git push origin feature/model-fetch-api
```

### 触ってはいけないファイル
- ❌ `src/gui/main_window.py`
- ❌ `src/gui/ai_model_updater.py`
- ❌ `gui_app.py`
- ❌ 他のAIが作るファイル（browser_session_fetcher.py, manual_model_manager.py）

---

## 📊 成功の基準

### 必須要件
あなたの`update_model_list()`関数が以下を返すこと：

```python
{
    "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
    "claude": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
    "gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
    "genspark": ["default"],
    "google_ai_studio": ["gemini-1.5-pro", "gemini-1.5-flash"]
}
```

### 重要
- 実際のWebアプリで選択可能なモデルのみを含める
- 存在しないモデル（gpt-5など）は含めない
- APIドキュメントにあっても実際に使えないモデルは含めない

---

## 🚨 最終確認

作業完了前に必ず確認：

```bash
# 1. 正しいブランチか確認
git branch
# あなたのブランチに * がついているか

# 2. 変更ファイルを確認
git status
# あなたの専用ファイルのみが表示されるか

# 3. 他のファイルを触っていないか確認
git diff --name-only
# あなたの専用ファイルのみが表示されるか
```

頑張ってください！🚀