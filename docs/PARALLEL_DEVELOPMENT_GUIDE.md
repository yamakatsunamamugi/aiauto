# AI並行開発ガイド - モデル取得機能の実装

## 概要
3つのAI（A、B、C）が同じ問題を異なるアプローチで解決し、最も優れた実装を採用します。

## 各AIの担当

### 🤖 AI-A: ブラウザセッション方式
- **ブランチ名**: `feature/model-fetch-browser`
- **アプローチ**: ユーザーのChromeプロファイルを使用してモデル情報を取得

### 🤖 AI-B: 手動管理方式
- **ブランチ名**: `feature/model-fetch-manual`
- **アプローチ**: GUIでモデルリストを手動管理する機能を実装

### 🤖 AI-C: API/創造的方式
- **ブランチ名**: `feature/model-fetch-api`
- **アプローチ**: APIまたは独自の方法でモデル情報を取得

---

## 📝 作業手順（全AI共通）

### 1. リポジトリの準備

```bash
# リポジトリをクローン（初回のみ）
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto

# すでにクローン済みの場合は最新を取得
git fetch origin
```

### 2. 自分のブランチに切り替え

**AI-A の場合:**
```bash
git checkout feature/model-fetch-browser
```

**AI-B の場合:**
```bash
git checkout feature/model-fetch-manual
```

**AI-C の場合:**
```bash
git checkout feature/model-fetch-api
```

### 3. 実装作業

#### 主な編集対象ファイル
- `src/gui/ai_model_updater.py` - 既存のモデル更新機能
- または新規ファイルを作成してもOK

#### 実装の要件
1. ChatGPT、Claude、Geminiの実際に使えるモデルを取得
2. エラーハンドリングを含める
3. ユーザーが使いやすい設計

### 4. 動作確認

```bash
# GUIアプリを起動して動作確認
python gui_app.py

# 最新情報更新ボタンを押して、正しいモデルが取得できるか確認
```

### 5. コミット

```bash
# 変更したファイルを確認
git status

# すべての変更をステージング
git add .

# コミット（メッセージは自分の方式に合わせて変更）
git commit -m "feat: ブラウザセッション方式でモデル取得機能を実装

- Chromeプロファイルからセッション情報を取得
- 各AIサービスの実際のモデルリストを抽出
- エラーハンドリングを追加"
```

### 6. GitHubにプッシュ

```bash
# 自分のブランチ名を確認
git branch

# プッシュ（ブランチ名は自分のものに置き換え）
git push origin feature/model-fetch-browser
```

---

## ⚠️ 重要な注意事項

### 1. ブランチを間違えないように！
作業前に必ず `git branch` で現在のブランチを確認してください：
```bash
git branch
# * feature/model-fetch-browser  ← アスタリスクが付いているのが現在のブランチ
#   feature/model-fetch-manual
#   feature/model-fetch-api
#   main
```

### 2. 他のAIのブランチには触らない
- AI-Aは `feature/model-fetch-browser` のみ
- AI-Bは `feature/model-fetch-manual` のみ
- AI-Cは `feature/model-fetch-api` のみ

### 3. mainブランチは変更しない
`main`ブランチは本番用なので、直接変更しないでください。

### 4. コンフリクトを避ける
- 基本的に`src/gui/ai_model_updater.py`を編集
- 新しいファイルを作る場合は、他のAIと重複しない名前にする
  - AI-A: `ai_model_browser.py`
  - AI-B: `ai_model_manual.py`
  - AI-C: `ai_model_api.py`

---

## 📊 成功基準

### 必須要件
✅ 以下のモデルが正しく取得できること：
- **ChatGPT**: gpt-4o, gpt-4o-mini, gpt-4-turbo など
- **Claude**: claude-3.5-sonnet, claude-3-opus など
- **Gemini**: gemini-1.5-pro, gemini-1.5-flash など

### 評価ポイント
1. **正確性** (40点): 実際のWebアプリと一致するか
2. **信頼性** (30点): エラーが少ないか
3. **使いやすさ** (30点): ユーザーの手間が少ないか

---

## 🔍 作業状況の確認方法

### 自分の作業内容を確認
```bash
# 変更したファイルの一覧
git status

# 変更内容の詳細
git diff

# コミット履歴
git log --oneline -5
```

### GitHubで確認
1. https://github.com/yamakatsunamamugi/aiauto にアクセス
2. 上部の「Branch: main」をクリック
3. 自分のブランチ名を選択
4. 自分の変更が反映されているか確認

---

## 💡 ヒント

### AI-A（ブラウザセッション）の場合
```python
# Chromeプロファイルのパス例
# Mac: ~/Library/Application Support/Google/Chrome
# Windows: %LOCALAPPDATA%\Google\Chrome\User Data

# Playwrightでユーザープロファイルを使用
browser = await playwright.chromium.launch(
    channel="chrome",
    headless=False,
    args=[f"--user-data-dir={profile_path}"]
)
```

### AI-B（手動管理）の場合
```python
# 設定ファイルの例
{
    "chatgpt": {
        "models": ["gpt-4o", "gpt-4o-mini"],
        "last_updated": "2025-01-12"
    }
}

# GUIダイアログでモデルを追加/削除
```

### AI-C（API/創造的）の場合
```python
# OpenAI APIの例
response = requests.get(
    "https://api.openai.com/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)

# または別の創造的なアプローチを試す
```

---

## 🆘 困ったときは

1. **ブランチを間違えてコミットした場合**
```bash
# コミットを取り消し（直前のコミットのみ）
git reset --soft HEAD~1

# 正しいブランチに切り替え
git checkout 正しいブランチ名

# 再度コミット
git add .
git commit -m "メッセージ"
```

2. **プッシュでエラーが出る場合**
```bash
# リモートの最新を取得
git pull origin 自分のブランチ名

# 再度プッシュ
git push origin 自分のブランチ名
```

---

## 📅 作業完了後

1. GitHubにプッシュ完了
2. 実装内容の説明（どのような方法で実装したか）
3. テスト結果（各AIサービスで取得できたモデルリスト）
4. 改善点や課題があれば報告

以上の内容を報告してください。最も優れた実装を本番環境に採用します！