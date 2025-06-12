# 🤖 AI-C 完全作業マニュアル（API/創造的方式）

## 🎯 あなたのミッション
APIや創造的な方法を使って、各AIサービスから実際に使用可能なモデルリストを取得する機能を実装する。

---

## 📋 基本情報

### リポジトリ情報
- **URL**: https://github.com/yamakatsunamamugi/aiauto
- **ブランチ**: `feature/model-fetch-api`
- **作成するファイル**: `src/gui/api_model_fetcher.py`

### 現在の問題
- 既存の`ai_model_updater.py`は公式ドキュメントから情報を取得している
- しかし、実際のWebアプリで使えるモデルと一致しない
- APIや他の方法で正確な情報を取得する必要がある

---

## 🚀 作業手順

### 1. 環境準備

```bash
# リポジトリをクローン
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto

# 自分のブランチに切り替え（重要！）
git checkout feature/model-fetch-api

# 現在のブランチを確認（必ず実行）
git branch
# * feature/model-fetch-api ← これが表示されることを確認
```

### 2. ファイル作成

```bash
# 新しいファイルを作成
touch src/gui/api_model_fetcher.py

# 必要に応じて設定ファイルも作成
touch config/api_settings.json
```

### 3. 実装

以下のコードを`src/gui/api_model_fetcher.py`に実装してください：

```python
"""
API/創造的方式でAIモデル情報を取得
各AIサービスのAPIやWebスクレイピング等を組み合わせて正確な情報を取得
"""

import json
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


def update_model_list() -> dict:
    """
    【必須関数】APIや創造的な方法でモデルリストを取得
    
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
    models = {}
    
    # 各サービスのモデルを取得
    models["chatgpt"] = fetch_openai_models()
    models["claude"] = fetch_claude_models()
    models["gemini"] = fetch_gemini_models()
    models["genspark"] = fetch_genspark_models()
    models["google_ai_studio"] = fetch_google_ai_studio_models()
    
    # 結果をキャッシュに保存
    save_to_cache(models)
    
    return models


def fetch_openai_models() -> List[str]:
    """OpenAI/ChatGPTのモデルを取得"""
    try:
        # 方法1: OpenAI APIを使用（APIキーが必要）
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                # GPTモデルのみフィルタリング
                models = [
                    m["id"] for m in data.get("data", [])
                    if m["id"].startswith("gpt")
                ]
                # 実際にChatGPTで使えるモデルのみ
                chat_models = [
                    m for m in models
                    if any(pattern in m for pattern in ["gpt-4o", "gpt-4-turbo", "gpt-3.5"])
                ]
                return sorted(chat_models, reverse=True)
        
        # 方法2: 既知のモデルリストを返す
        return get_known_openai_models()
        
    except Exception as e:
        logger.error(f"OpenAIモデル取得エラー: {e}")
        return get_known_openai_models()


def fetch_claude_models() -> List[str]:
    """Claudeのモデルを取得"""
    try:
        # 方法1: Anthropic APIのドキュメントをスクレイピング
        # （実装例）
        
        # 方法2: 既知のモデルリストを返す
        return get_known_claude_models()
        
    except Exception as e:
        logger.error(f"Claudeモデル取得エラー: {e}")
        return get_known_claude_models()


def fetch_gemini_models() -> List[str]:
    """Geminiのモデルを取得"""
    try:
        # 方法1: Google AI APIを使用
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                models = [
                    m["name"].replace("models/", "")
                    for m in data.get("models", [])
                    if "gemini" in m["name"]
                ]
                return models
        
        # 方法2: 既知のモデルリストを返す
        return get_known_gemini_models()
        
    except Exception as e:
        logger.error(f"Geminiモデル取得エラー: {e}")
        return get_known_gemini_models()


def fetch_genspark_models() -> List[str]:
    """Gensparkのモデルを取得"""
    # Gensparkは詳細なモデル名を公開していない
    return ["default", "advanced"]


def fetch_google_ai_studio_models() -> List[str]:
    """Google AI Studioのモデルを取得"""
    # Geminiと同じモデルを使用
    return fetch_gemini_models()


def get_known_openai_models() -> List[str]:
    """既知のOpenAIモデルリスト"""
    return [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo"
    ]


def get_known_claude_models() -> List[str]:
    """既知のClaudeモデルリスト"""
    return [
        "claude-3.5-sonnet",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku"
    ]


def get_known_gemini_models() -> List[str]:
    """既知のGeminiモデルリスト"""
    return [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro",
        "gemini-pro-vision"
    ]


def save_to_cache(models: dict):
    """取得したモデル情報をキャッシュに保存"""
    try:
        cache_data = {
            "method": "api_fetch",
            "timestamp": datetime.now().isoformat(),
            "models": models
        }
        
        os.makedirs("config", exist_ok=True)
        with open("config/api_models_cache.json", 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"キャッシュ保存エラー: {e}")


def load_from_cache() -> Optional[dict]:
    """キャッシュからモデル情報を読み込む"""
    try:
        cache_path = "config/api_models_cache.json"
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # キャッシュの有効期限チェック（24時間）
            timestamp = datetime.fromisoformat(data["timestamp"])
            if (datetime.now() - timestamp).total_seconds() < 86400:
                return data["models"]
                
    except Exception as e:
        logger.error(f"キャッシュ読み込みエラー: {e}")
    
    return None


class ModelFetcherWithRetry:
    """リトライ機能付きモデル取得クラス"""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay
    
    def fetch_with_retry(self, fetch_func, service_name: str) -> List[str]:
        """リトライ付きでモデルを取得"""
        for attempt in range(self.max_retries):
            try:
                result = fetch_func()
                if result:
                    return result
            except Exception as e:
                logger.warning(f"{service_name} 取得失敗 (試行 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))
        
        # すべて失敗した場合は空リストを返す
        return []


# 環境変数からAPIキーを取得する例
def setup_api_keys():
    """APIキーの設定方法を表示"""
    print("""
    APIキーの設定方法:
    
    1. OpenAI API:
       export OPENAI_API_KEY="your-api-key"
    
    2. Google API:
       export GOOGLE_API_KEY="your-api-key"
    
    3. または config/api_settings.json に保存:
       {
         "openai_api_key": "your-key",
         "google_api_key": "your-key"
       }
    """)


# テスト用
if __name__ == "__main__":
    print("API/創造的方式でモデル情報を取得します...")
    
    # キャッシュから取得を試みる
    cached = load_from_cache()
    if cached:
        print("キャッシュから取得:")
        print(json.dumps(cached, indent=2, ensure_ascii=False))
    else:
        print("新規取得:")
        result = update_model_list()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # APIキー設定の説明
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n注意: APIキーが設定されていません")
        setup_api_keys()
```

### 4. 追加の実装アイデア

```python
# 方法1: Webスクレイピング（requests + BeautifulSoup）
def scrape_model_info():
    from bs4 import BeautifulSoup
    
    # 例: モデル情報ページをスクレイピング
    response = requests.get("https://example.com/models")
    soup = BeautifulSoup(response.content, 'html.parser')
    # モデル名を抽出

# 方法2: リバースエンジニアリング（ブラウザのネットワークタブを分析）
def fetch_from_internal_api():
    # ChatGPTやClaudeの内部APIを使用
    headers = {
        "User-Agent": "Mozilla/5.0...",
        "Accept": "application/json"
    }
    # 内部APIエンドポイントにアクセス

# 方法3: ハイブリッドアプローチ
def hybrid_fetch():
    # 1. まずAPIを試す
    # 2. 失敗したらキャッシュ
    # 3. それも失敗したら既知のリスト
```

### 5. テスト

```bash
# 単体テスト
python src/gui/api_model_fetcher.py

# 関数が正しく動作するか確認
python -c "from src.gui.api_model_fetcher import update_model_list; print(update_model_list())"

# APIキーを設定してテスト
export OPENAI_API_KEY="your-key"
python src/gui/api_model_fetcher.py
```

### 6. コミット＆プッシュ

```bash
# 変更を確認
git status

# ファイルを追加
git add src/gui/api_model_fetcher.py
git add config/api_settings.json  # 作成した場合

# コミット（メッセージは日本語でわかりやすく）
git commit -m "feat: API方式でモデル取得機能を実装

- OpenAI、Google APIを使用したモデル取得
- キャッシュ機能とリトライ機能を実装
- 既知のモデルリストをフォールバックとして使用"

# プッシュ
git push origin feature/model-fetch-api
```

---

## 🚫 絶対禁止事項（NEVER）

以下のことは**絶対にしないでください**：

1. **NEVER: `src/gui/main_window.py`を編集しない**
   - 読むのはOK、編集は絶対NG
   
2. **NEVER: 他のAIのファイルを変更しない**
   - `browser_session_fetcher.py`（AI-A用）
   - `manual_model_manager.py`（AI-B用）
   
3. **NEVER: mainブランチで作業しない**
   - 必ず`feature/model-fetch-api`で作業

4. **NEVER: APIキーをハードコーディングしない**
   ```python
   # ❌ 悪い例
   api_key = "sk-1234567890abcdef"
   
   # ✅ 良い例
   api_key = os.environ.get("OPENAI_API_KEY")
   ```

5. **NEVER: レート制限を無視しない**

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
   - ネットワークエラー
   - APIエラー
   - タイムアウト

4. **YOU MUST: タイムアウトを設定する**
   ```python
   requests.get(url, timeout=10)  # 最大10秒
   ```

5. **YOU MUST: 空の辞書でもクラッシュしない**

---

## ⚠️ 重要事項（IMPORTANT）

1. **IMPORTANT: APIキーの管理**
   - 環境変数を使用
   - 設定ファイルは.gitignoreに追加

2. **IMPORTANT: レート制限対策**
   - リトライ間隔を設ける
   - キャッシュを活用

3. **IMPORTANT: フォールバック機構**
   - API → キャッシュ → 既知のリスト

4. **IMPORTANT: 複数の方法を組み合わせる**
   - 一つの方法に依存しない

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

### requestsライブラリがない場合
```bash
pip install requests
```

### APIキーが機能しない場合
- 有効期限を確認
- 権限を確認
- 環境変数が正しく設定されているか確認

### ネットワークエラーの場合
- プロキシ設定を確認
- ファイアウォール設定を確認
- VPNの影響を確認

---

## 💡 創造的なアプローチの例

1. **ブラウザの開発者ツールを分析**
   - Network タブで API コールを確認
   - 実際のエンドポイントを発見

2. **公開されていないAPIを利用**
   - 内部APIのリバースエンジニアリング
   - ただし利用規約に注意

3. **複数の情報源を組み合わせる**
   - 公式API + スクレイピング + 既知の情報

4. **コミュニティの情報を活用**
   - GitHub、Reddit、フォーラムの情報

---

## 📝 完了報告

実装が完了したら、以下の情報を報告してください：

1. **使用した方法**
   - API、スクレイピング、その他

2. **取得成功率**
   - 各サービスの成功/失敗

3. **創造的な工夫**
   - 独自のアプローチ

4. **改善提案**
   - より良い方法のアイデア

---

創造的な解決方法を期待しています！頑張ってください！🚀