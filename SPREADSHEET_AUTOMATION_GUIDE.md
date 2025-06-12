# スプレッドシート×AI自動化ツール使用ガイド

## 概要
このツールは、Googleスプレッドシートのデータを基に、APIを使わずにブラウザ自動化でAIサービス（ChatGPT、Claude等）を操作し、結果をスプレッドシートに書き戻すGUIアプリケーションです。

## 必要な準備

### 1. 依存ライブラリのインストール

```bash
# 必要なライブラリをインストール
pip install -r requirements_spreadsheet_automation.txt

# Playwrightのブラウザをインストール
playwright install chromium
```

### 2. Google Sheets認証設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. Google Sheets APIを有効化
3. サービスアカウントを作成し、認証情報（JSON）をダウンロード
4. ダウンロードしたJSONファイルを `config/credentials.json` として保存

### 3. スプレッドシートの準備

スプレッドシートは以下の形式で準備してください：

```
A列     B列    C列      D列      E列      F列       G列
作業指示行              処理     エラー   コピー    貼り付け
1       データ1         未処理            テキスト1
2       データ2         未処理            テキスト2
3       データ3         未処理            テキスト3
```

- **作業指示行**: A列に「作業指示行」という文字を含む行（通常5行目）
- **処理列**: コピー列の2つ左（処理済み/未処理を記録）
- **エラー列**: コピー列の1つ左（エラー内容を記録）
- **コピー列**: AIに送信するテキスト
- **貼り付け列**: AIからの回答を記録

## 起動方法

### 方法1: 起動スクリプトを使用（推奨）
```bash
python run_spreadsheet_automation.py
```

### 方法2: 直接起動
```bash
python spreadsheet_ai_automation_gui.py
```

## 使い方

### 1. 基本設定タブ

1. **スプレッドシートURL**: GoogleスプレッドシートのURLを入力
2. **シート名**: 「シート一覧取得」ボタンでシートを選択
3. **認証ファイル**: `config/credentials.json` のパスを確認
4. **Chromeプロファイル**: 既存のChromeプロファイルを使用する場合はパスを入力

### 2. AI設定タブ

1. **列を追加**: 各コピー列で使用するAIを設定
   - コピー列: 列名（例: F）
   - AIサービス: ChatGPT、Claude、Gemini等から選択
   - モデル: 使用するモデルを選択
   - 設定: Deep Think等のオプション

2. **ログイン状態確認**: 各AIサービスのログイン状態を確認

### 3. 処理実行

1. すべての設定を完了後、「処理開始」ボタンをクリック
2. 処理状況タブで進捗を確認
3. ログタブで詳細なログを確認

## 注意事項

- **初回実行時**: 各AIサービスに手動でログインが必要です
- **レート制限**: AIサービスのレート制限を避けるため、処理間に待機時間があります
- **エラー時**: エラー列にエラー内容が記録され、5回まで自動リトライします

## トラブルシューティング

### ブラウザが起動しない
```bash
# Playwrightを再インストール
pip uninstall playwright
pip install playwright
playwright install chromium
```

### 認証エラー
1. サービスアカウントにスプレッドシートの編集権限があるか確認
2. スプレッドシートをサービスアカウントのメールアドレスと共有

### AIサービスにログインできない
1. Chromeプロファイルパスを指定して、既存のログイン済みプロファイルを使用
2. または、新規ブラウザで手動ログイン後、セッションを保持

## Chromeプロファイルの見つけ方

### macOS
```bash
# デフォルトのプロファイルパス
~/Library/Application Support/Google/Chrome/Default
```

### Windows
```
C:\Users\[ユーザー名]\AppData\Local\Google\Chrome\User Data\Default
```

### Linux
```
~/.config/google-chrome/Default
```