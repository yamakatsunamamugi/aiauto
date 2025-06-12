# ブラウザ自動化によるスプレッドシート×AI統合システム

## 概要

このシステムは、**APIキーを一切使わずに**、既にログイン済みのWeb版AIサービス（ChatGPT Plus、Claude Pro等）をブラウザ自動化で操作し、Googleスプレッドシートと連携させるものです。

## 主な特徴

- 🚫 **API不要** - APIキーや従量課金なし
- 🔐 **既存のログインセッションを活用** - 有料プランの全機能が使用可能
- 🤖 **複数AI対応** - ChatGPT、Claude、Gemini等に対応
- 🚀 **高度な機能対応** - DeepThink、Web検索等の特別な機能も利用可能
- 📊 **スプレッドシート統合** - 自動的にデータを読み取り、結果を書き込み

## システム構成

```
5.AI-auto/
├── gui_automation_app_browser.py     # メインGUIアプリケーション（ブラウザ自動化統合版）
├── src/
│   └── automation/
│       ├── browser_automation_handler.py  # ブラウザ自動化ハンドラー
│       └── extension_bridge.py           # Chrome拡張機能連携（既存）
├── test_browser_automation.py        # テストスクリプト
└── BROWSER_AUTOMATION_README.md      # このファイル
```

## セットアップ手順

### 1. 必要なパッケージのインストール

```bash
# Playwrightのインストール
pip install playwright

# Playwrightのブラウザをインストール
playwright install chromium

# その他の依存関係
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. 各AIサービスへのログイン

1. 通常のChromeブラウザで以下のサービスにログイン：
   - https://chatgpt.com (ChatGPT Plus推奨)
   - https://claude.ai (Claude Pro推奨)
   - https://gemini.google.com (Gemini Advanced推奨)

2. ログイン後、**ブラウザを一度完全に終了**

### 3. Google Sheets APIの設定

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Google Sheets APIを有効化
3. サービスアカウントを作成し、JSONキーをダウンロード
4. `config/credentials.json`として保存

## 使用方法

### GUIアプリケーションの起動

```bash
python gui_automation_app_browser.py
```

### 初心者向け使用手順

1. **自動化モード選択**
   - 「ブラウザ自動化モード（API不要）」を選択

2. **スプレッドシート設定**
   - GoogleスプレッドシートのURLを入力
   - 「URLから読込」をクリック
   - 対象シートを選択

3. **シート情報読込**
   - 「シート情報読込」をクリック
   - 作業指示行（5行目のA列に「作業指示行」）が自動検出される

4. **各コピー列のAI設定**
   - 各列で使用するAIサービスを選択
   - モデルを選択（最新モデルが利用可能）
   - DeepThink等の機能を有効化

5. **自動化実行**
   - 「自動化開始」をクリック
   - 処理の進捗がリアルタイムで表示される

## スプレッドシートの構造

```
行  | A列        | B列 | C列     | D列   | E列     | F列       |
----|-----------|-----|---------|-------|---------|-----------|
5   | 作業指示行 |     | 処理    | エラー | コピー  | 貼り付け  |
6   | 1         |     | 未処理  |       | テキスト1| (AI回答)  |
7   | 2         |     | 未処理  |       | テキスト2| (AI回答)  |
```

- **A列**: 連番（1,2,3...）がある行が処理対象
- **処理列**: コピー列の2つ左（処理状態を記録）
- **エラー列**: コピー列の1つ左（エラー情報を記録）
- **コピー列**: AIに送信するテキスト
- **貼り付け列**: コピー列の1つ右（AIの回答を記録）

## テストの実行

```bash
# 対話型テストを実行
python test_browser_automation.py
```

テストメニュー：
1. 基本機能テスト - 各AIサービスの動作確認
2. バッチ処理テスト - 複数タスクの連続処理
3. 特別機能テスト - DeepThink等の高度な機能
4. 対話型テスト - 手動でテキストを入力して確認

## 高度な設定

### ブラウザプロファイルの指定

デフォルトでは標準のChromeプロファイルを使用しますが、カスタムプロファイルも指定可能：

```python
# カスタムプロファイルパスの例
profile_paths = {
    "macOS": "~/Library/Application Support/Google/Chrome/Profile 1",
    "Windows": r"C:\Users\USERNAME\AppData\Local\Google\Chrome\User Data\Profile 1",
    "Linux": "~/.config/google-chrome/Profile 1"
}
```

### ヘッドレスモード

バックグラウンドで実行したい場合：

```python
handler = BrowserAutomationHandler()
handler.start(headless=True)
```

## トラブルシューティング

### よくある問題と解決方法

1. **「Playwright not installed」エラー**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **ログインセッションが認識されない**
   - Chromeを完全に終了してから再実行
   - プロファイルパスが正しいか確認

3. **AIサービスのセレクターが見つからない**
   - 最新版のbrowser_automation_handler.pyを使用
   - AIサービスのUI変更に対応する必要がある場合あり

4. **処理が遅い**
   - レート制限を考慮して、各リクエスト間に2秒の待機時間を設定
   - 同時実行数を調整

## セキュリティ上の注意

- ブラウザプロファイルには個人情報が含まれるため、取り扱いに注意
- 共有環境では使用しない
- 定期的にセッションをクリーンアップ

## 今後の拡張予定

- [ ] Genspark、Google AI Studioへの対応
- [ ] 画像アップロード機能
- [ ] マルチスレッド処理
- [ ] エラーリトライの高度化
- [ ] 処理統計の可視化

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能提案は、GitHubのIssuesまでお願いします。

---

作成日: 2024/12/12
最終更新: 2024/12/12