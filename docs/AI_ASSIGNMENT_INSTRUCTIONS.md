# 各AIへの作業指示書

## 🤖 AI-A への指示

### あなたの担当
- **方式**: ブラウザセッション方式
- **ブランチ**: `feature/model-fetch-browser`

### 作業内容
以下のGitHubリポジトリで、ユーザーのブラウザセッションを利用してAIモデル情報を取得する機能を実装してください。

**リポジトリ**: https://github.com/yamakatsunamamugi/aiauto

**詳細な作業手順**: 
https://github.com/yamakatsunamamugi/aiauto/blob/main/docs/PARALLEL_DEVELOPMENT_GUIDE.md

**あなたのアプローチ**:
- ユーザーがログイン済みのChromeプロファイルを使用
- Playwrightでブラウザを制御し、各AIサービスから実際のモデルリストを取得
- セキュリティとプライバシーに配慮した実装

**開始コマンド**:
```bash
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto
git checkout feature/model-fetch-browser
```

---

## 🤖 AI-B への指示

### あなたの担当
- **方式**: 手動管理方式
- **ブランチ**: `feature/model-fetch-manual`

### 作業内容
以下のGitHubリポジトリで、GUIを使ってモデルリストを手動管理する機能を実装してください。

**リポジトリ**: https://github.com/yamakatsunamamugi/aiauto

**詳細な作業手順**: 
https://github.com/yamakatsunamamugi/aiauto/blob/main/docs/PARALLEL_DEVELOPMENT_GUIDE.md

**あなたのアプローチ**:
- モデルの追加/編集/削除ができるGUIダイアログを作成
- 設定をJSONファイルに保存し、次回起動時に自動読み込み
- ユーザーフレンドリーなインターフェース設計

**開始コマンド**:
```bash
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto
git checkout feature/model-fetch-manual
```

---

## 🤖 AI-C への指示

### あなたの担当
- **方式**: API/創造的方式
- **ブランチ**: `feature/model-fetch-api`

### 作業内容
以下のGitHubリポジトリで、APIまたは独自の創造的な方法でAIモデル情報を取得する機能を実装してください。

**リポジトリ**: https://github.com/yamakatsunamamugi/aiauto

**詳細な作業手順**: 
https://github.com/yamakatsunamamugi/aiauto/blob/main/docs/PARALLEL_DEVELOPMENT_GUIDE.md

**あなたのアプローチ**:
- 各サービスのAPIを活用（利用可能な場合）
- Webスクレイピング、リバースエンジニアリング、その他創造的な方法も可
- 複数の方法を組み合わせたハイブリッドアプローチも歓迎

**開始コマンド**:
```bash
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto
git checkout feature/model-fetch-api
```

---

## 📌 全AI共通の重要事項

### 1. 目標
現在の問題: `src/gui/ai_model_updater.py`が公式ドキュメントから情報を取得しているが、実際のWebアプリで使えるモデルと一致しない。

**解決すべきこと**: 
- ChatGPT、Claude、Geminiの**実際に使用可能な**モデルリストを確実に取得

### 2. 成功例
```python
# 期待される出力例
{
    "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
    "claude": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet"],
    "gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
}
```

### 3. テスト方法
```bash
# GUIアプリを起動
python gui_app.py

# 「最新情報更新」ボタンをクリック
# 各AIサービスのドロップダウンに正しいモデルが表示されることを確認
```

### 4. 注意事項
- 他のAIのブランチには絶対に触らない
- mainブランチは変更しない
- コミットメッセージは日本語でわかりやすく

### 5. 完了報告
実装完了後、以下を報告してください：
1. 実装方法の概要
2. 取得できたモデルリスト
3. メリット・デメリット
4. 発生した課題と解決方法

---

## 🏆 評価基準

最も優れた実装を採用します。評価ポイント：

1. **正確性** (40%): 実際のWebアプリで使えるモデルと完全一致
2. **信頼性** (30%): エラーが少なく安定動作
3. **使いやすさ** (30%): ユーザーの手間が最小限

頑張ってください！最高の実装を期待しています。