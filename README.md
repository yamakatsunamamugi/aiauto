# AI自動化ツール

Googleスプレッドシートのデータを読み取り、複数のAIサービスを自動操作して結果を書き戻すツールです。

## 機能概要

- **Googleスプレッドシート連携**: データの読み取り・書き込み
- **複数AI対応**: ChatGPT、Claude、Gemini、Genspark、Google AI Studio
- **GUI操作**: 初心者にも分かりやすいインターフェース
- **自動化**: ブラウザ操作の完全自動化
- **エラーハンドリング**: 詳細なログとリトライ機能

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. Google Sheets API設定

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
2. Google Sheets APIを有効化
3. 認証情報（サービスアカウント）を作成
4. `config/credentials.json`に認証情報を配置

### 3. 設定ファイル

`config/settings.json`で各種設定を調整できます。

## 使用方法

### 基本実行

```bash
python main.py
```

### スプレッドシート設定

1. GUIでスプレッドシートURLを入力
2. 対象シートを選択
3. 各AI設定を選択
4. 処理開始

### データ形式

- **5行目**: ヘッダー行（A列に「作業」）
- **処理行**: A列に連番（1、2、3...）
- **コピー列**: 「コピー」ヘッダーの列
- **処理列**: コピー列-2の位置
- **エラー列**: コピー列-1の位置  
- **貼り付け列**: コピー列+1の位置

## 開発

### ブランチ構成

- `main`: 本番用
- `develop`: 開発統合用
- `feature/gui-components`: GUI担当
- `feature/sheets-integration`: Sheets担当
- `feature/browser-automation`: 自動化担当

### 担当分担

- **担当者A**: GUI・設定管理
- **担当者B**: Google Sheets連携
- **担当者C**: ブラウザ自動化・AI連携

## ログ

詳細なログは `logs/app.log` に出力されます。

## トラブルシューティング

### よくある問題

1. **Google Sheets認証エラー**
   - `config/credentials.json`の配置を確認
   - APIが有効化されているか確認

2. **ブラウザ起動エラー**
   - ChromeDriverのバージョン確認
   - Seleniumの更新

3. **AI操作エラー**
   - 各AIサイトにログイン済みか確認
   - ネットワーク接続を確認

## ライセンス

MIT License