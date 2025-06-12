# AIモデル取得機能 - 並行開発タスク

## 背景
現在の`src/gui/ai_model_updater.py`は公式ドキュメントページから情報を取得していますが、実際のWebアプリで選択可能なモデルと一致しない問題があります。

## タスク
各AIサービス（ChatGPT、Claude、Gemini）から**実際に使用可能な**モデルリストを確実に取得する機能を実装してください。

## リポジトリ情報
- URL: https://github.com/yamakatsunamamugi/aiauto
- 各ブランチ:
  - `feature/model-fetch-browser` - ブラウザセッション方式
  - `feature/model-fetch-manual` - 手動管理方式
  - `feature/model-fetch-api` - API/その他の方式

## 要件
1. **正確性**: 実際のWebアプリで選択可能なモデルと完全に一致すること
2. **信頼性**: エラーが少なく、安定して動作すること
3. **使いやすさ**: ユーザーの手間が最小限であること
4. **実装場所**: `src/gui/ai_model_updater.py`を改良または新しいファイルで置き換え

## 各方式の説明

### 1. ブラウザセッション方式 (`feature/model-fetch-browser`)
- ユーザーのChromeプロファイルを使用
- ログイン済みのセッションからモデル情報を取得
- Playwrightでブラウザを制御

### 2. 手動管理方式 (`feature/model-fetch-manual`)
- GUIでモデルリストを手動で追加/編集/削除
- 設定ファイルに保存
- 初回設定後は自動的に読み込み

### 3. API/その他の方式 (`feature/model-fetch-api`)
- 各サービスのAPIを使用（可能な場合）
- または独自の創造的な解決方法
- ハイブリッドアプローチも可

## 実装手順
```bash
# 1. ブランチに切り替え
git checkout feature/model-fetch-[your-approach]

# 2. 実装
# src/gui/ai_model_updater.py を編集
# または新しいファイルを作成

# 3. テスト
python test_model_fetcher.py

# 4. コミット
git add .
git commit -m "feat: [approach]方式でモデル取得機能を実装"

# 5. プッシュ
git push origin feature/model-fetch-[your-approach]
```

## 成功基準
- ChatGPT: gpt-4o, gpt-4o-mini などの実際のモデルが取得できる
- Claude: claude-3.5-sonnet, claude-3-opus などが取得できる
- Gemini: gemini-1.5-pro, gemini-1.5-flash などが取得できる

## 評価方法
最も効果的な実装（正確性、信頼性、使いやすさの総合評価）を本番環境に採用します。

## 期限
実装完了後、動作確認結果を報告してください。