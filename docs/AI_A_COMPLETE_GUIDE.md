# 🤖 AI-A 完全作業マニュアル（ブラウザセッション方式）

## 🎯 あなたのミッション
ユーザーのブラウザセッションを利用して、各AIサービスから実際に使用可能なモデルリストを取得する機能を実装する。

---

## 📋 基本情報

### リポジトリ情報
- **URL**: https://github.com/yamakatsunamamugi/aiauto
- **ブランチ**: `feature/model-fetch-browser`
- **作成するファイル**: `src/gui/browser_session_fetcher.py`

### 現在の問題
- 既存の`ai_model_updater.py`は公式ドキュメントから情報を取得している
- しかし、実際のWebアプリで使えるモデルと一致しない
- 例：ChatGPTのドキュメントには「gpt-4-32k」があるが、実際には選択できない

---

## 🚀 作業手順

### 1. 環境準備

```bash
# リポジトリをクローン
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto

# 自分のブランチに切り替え（重要！）
git checkout feature/model-fetch-browser

# 現在のブランチを確認（必ず実行）
git branch
# * feature/model-fetch-browser ← これが表示されることを確認
```

### 2. ファイル作成

```bash
# 新しいファイルを作成
touch src/gui/browser_session_fetcher.py
```

### 3. 実装

以下のコードを`src/gui/browser_session_fetcher.py`に実装してください：

```python
"""
ブラウザセッション方式でAIモデル情報を取得
実際のWebアプリケーションから確実にモデル情報を取得
"""

import json
import os
from typing import Dict, List
from datetime import datetime
import logging

# Playwrightを使用
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("警告: Playwrightがインストールされていません")
    print("pip install playwright && playwright install chromium")

logger = logging.getLogger(__name__)


def update_model_list() -> dict:
    """
    【必須関数】ブラウザセッションからモデルリストを取得
    
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
    try:
        # ここにあなたの実装を書く
        # ヒント:
        # 1. ユーザーのChromeプロファイルを使用
        # 2. 各AIサービスのWebページにアクセス
        # 3. モデル選択メニューからリストを取得
        
        # デフォルト値（実装前の仮データ）
        return {
            "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "claude": ["claude-3.5-sonnet", "claude-3-opus"],
            "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "genspark": ["default"],
            "google_ai_studio": ["gemini-1.5-pro"]
        }
        
    except Exception as e:
        logger.error(f"モデル取得エラー: {e}")
        # エラー時は空の辞書を返す（クラッシュしない）
        return {
            "chatgpt": [],
            "claude": [],
            "gemini": [],
            "genspark": [],
            "google_ai_studio": []
        }


def get_chrome_profile_path() -> str:
    """
    Chromeプロファイルのパスを取得（OS別）
    """
    import platform
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif system == "Windows":
        return os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data")
    else:  # Linux
        return os.path.expanduser("~/.config/google-chrome")


# テスト用
if __name__ == "__main__":
    print("ブラウザセッション方式でモデル情報を取得します...")
    result = update_model_list()
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 4. 実装のヒント

```python
# Playwrightでブラウザを起動する例
def fetch_chatgpt_models():
    with sync_playwright() as p:
        # ユーザープロファイルを使用
        browser = p.chromium.launch(
            headless=False,  # デバッグ時は表示
            channel="chrome",
            args=[f"--user-data-dir={get_chrome_profile_path()}"]
        )
        
        page = browser.new_page()
        page.goto("https://chat.openai.com")
        
        # モデル選択ボタンを探す
        # 例: page.locator("button[aria-label*='Model']")
        
        browser.close()
```

### 5. テスト

```bash
# 単体テスト
python src/gui/browser_session_fetcher.py

# 関数が正しく動作するか確認
python -c "from src.gui.browser_session_fetcher import update_model_list; print(update_model_list())"
```

### 6. コミット＆プッシュ

```bash
# 変更を確認
git status

# ファイルを追加
git add src/gui/browser_session_fetcher.py

# コミット（メッセージは日本語でわかりやすく）
git commit -m "feat: ブラウザセッション方式でモデル取得機能を実装

- ユーザーのChromeプロファイルを使用してログイン済みセッションを活用
- ChatGPT、Claude、Geminiから実際のモデルリストを取得
- エラーハンドリングとOS別対応を実装"

# プッシュ
git push origin feature/model-fetch-browser
```

---

## 🚫 絶対禁止事項（NEVER）

以下のことは**絶対にしないでください**：

1. **NEVER: `src/gui/main_window.py`を編集しない**
   - 読むのはOK、編集は絶対NG
   
2. **NEVER: 他のAIのファイルを変更しない**
   - `manual_model_manager.py`（AI-B用）
   - `api_model_fetcher.py`（AI-C用）
   
3. **NEVER: mainブランチで作業しない**
   - 必ず`feature/model-fetch-browser`で作業

4. **NEVER: ユーザーの個人情報をログに出力しない**
   - パスワード、Cookie、セッション情報など

5. **NEVER: テストなしでプッシュしない**

---

## ✅ 必須事項（YOU MUST）

以下は**必ず実行してください**：

1. **YOU MUST: 正しいブランチで作業する**
   ```bash
   git branch  # 必ず確認
   ```

2. **YOU MUST: `update_model_list()`関数を実装する**
   - 引数: なし
   - 戻り値: dict型（5つのAIサービス全て含む）

3. **YOU MUST: エラーハンドリングを実装する**
   ```python
   try:
       # 処理
   except Exception as e:
       logger.error(f"エラー: {e}")
       return {}  # 空の辞書を返す
   ```

4. **YOU MUST: 実際のWebアプリで使えるモデルのみ返す**
   - ドキュメントにあっても使えないモデルは含めない

5. **YOU MUST: コミット前にテストする**

---

## ⚠️ 重要事項（IMPORTANT）

1. **IMPORTANT: プライバシーに配慮**
   - ユーザーのセッション情報を適切に扱う
   - 個人情報を外部に送信しない

2. **IMPORTANT: 複数OS対応**
   - Windows、macOS、Linuxで動作するように

3. **IMPORTANT: タイムアウト設定**
   - 各ページの読み込みは最大30秒まで

4. **IMPORTANT: ユーザビリティ**
   - エラー時もアプリがクラッシュしないように

---

## 📊 期待される出力

```python
{
    "chatgpt": [
        "gpt-4o",
        "gpt-4o-mini", 
        "gpt-4-turbo",
        "gpt-4"
    ],
    "claude": [
        "claude-3.5-sonnet",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku"
    ],
    "gemini": [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro"
    ],
    "genspark": [
        "default"
    ],
    "google_ai_studio": [
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    ]
}
```

---

## 🆘 トラブルシューティング

### Playwrightがインストールされていない場合
```bash
pip install playwright
playwright install chromium
```

### ブランチを間違えた場合
```bash
# 変更を一時保存
git stash

# 正しいブランチに切り替え
git checkout feature/model-fetch-browser

# 変更を復元
git stash pop
```

### プッシュでエラーが出る場合
```bash
# リモートの最新を取得
git pull origin feature/model-fetch-browser

# 再度プッシュ
git push origin feature/model-fetch-browser
```

---

## 📝 完了報告

実装が完了したら、以下の情報を報告してください：

1. **実装方法の概要**
   - どのようにモデルリストを取得したか

2. **取得できたモデル**
   - 各サービスのモデルリスト

3. **発生した課題と解決方法**

4. **改善提案**

---

頑張ってください！質問があれば作業前に確認してください。🚀