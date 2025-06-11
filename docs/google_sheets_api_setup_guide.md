# Google Sheets API 設定ガイド（初心者向け）

## 📋 概要

このガイドでは、AI自動化ツールがGoogleスプレッドシートにアクセスするために必要な、Google Sheets APIの設定手順を初心者向けに詳しく説明します。

## 🎯 必要な作業

1. Google Cloud Projectの作成
2. Google Sheets APIの有効化
3. サービスアカウントの作成
4. 認証キー（credentials.json）のダウンロード
5. スプレッドシートへのアクセス権限設定

## 📝 詳細手順

### ステップ1: Google Cloud Consoleにアクセス

1. ブラウザで以下のURLを開きます：
   ```
   https://console.cloud.google.com
   ```

2. Googleアカウントでログインします（Googleスプレッドシートで使用しているアカウントを推奨）

### ステップ2: 新しいプロジェクトを作成

1. 画面上部の「プロジェクトを選択」をクリック
2. 「新しいプロジェクト」をクリック
3. プロジェクト名を入力：`ai-automation-tool`
4. 「作成」をクリック

### ステップ3: Google Sheets APIを有効化

1. 左側のメニューから「APIとサービス」→「ライブラリ」を選択
2. 検索バーに「Google Sheets API」と入力
3. 「Google Sheets API」をクリック
4. 「有効にする」ボタンをクリック

### ステップ4: サービスアカウントを作成

1. 左側のメニューから「APIとサービス」→「認証情報」を選択
2. 画面上部の「+ 認証情報を作成」をクリック
3. 「サービスアカウント」を選択
4. 以下の情報を入力：
   - **サービスアカウント名**: `ai-automation-service`
   - **サービスアカウントID**: 自動入力されます
   - **説明**: `AI自動化ツール用のサービスアカウント`
5. 「作成して続行」をクリック
6. 「ロールを選択」で「編集者」を検索して選択
7. 「続行」→「完了」をクリック

### ステップ5: 認証キーをダウンロード

1. 作成したサービスアカウントの名前をクリック
2. 「キー」タブを選択
3. 「鍵を追加」→「新しい鍵を作成」をクリック
4. キーのタイプで「JSON」を選択
5. 「作成」をクリック
6. 自動的にJSONファイルがダウンロードされます

### ステップ6: credentials.jsonとして保存

1. ダウンロードしたJSONファイルを見つけます（通常はダウンロードフォルダ）
2. ファイル名を `credentials.json` に変更
3. AI自動化ツールのフォルダ内の `config` フォルダに移動：
   ```
   /Users/roudousha/Dropbox/5.AI-auto/config/credentials.json
   ```

### ステップ7: スプレッドシートへのアクセス権限を設定

1. credentials.jsonファイルをテキストエディタで開く
2. `"client_email"` の値をコピー（例：`ai-automation-service@your-project-id.iam.gserviceaccount.com`）
3. 自動化したいGoogleスプレッドシートを開く
4. 右上の「共有」ボタンをクリック
5. コピーしたメールアドレスを貼り付け
6. 権限を「編集者」に設定
7. 「送信」をクリック

## ✅ 設定確認方法

ターミナルまたはコマンドプロンプトで以下を実行：

```bash
cd /Users/roudousha/Dropbox/5.AI-auto
python -m src.sheets.auth_manager
```

成功すると以下のように表示されます：
```
✅ 認証が成功しました
サービスアカウント: ai-automation-service@your-project-id.iam.gserviceaccount.com
```

## ❌ よくあるエラーと対処法

### エラー1: 認証情報ファイルが見つかりません
**原因**: credentials.jsonが正しい場所にない
**対処**: ファイルが `/Users/roudousha/Dropbox/5.AI-auto/config/credentials.json` にあることを確認

### エラー2: Google Sheets APIが有効になっていません
**原因**: APIの有効化を忘れている
**対処**: ステップ3を再度実行

### エラー3: スプレッドシートへのアクセス権限がありません
**原因**: サービスアカウントに共有していない
**対処**: ステップ7を再度実行

## 🔒 セキュリティ注意事項

- **credentials.jsonは機密情報です**。他人と共有しないでください
- Gitにコミットしないよう注意（.gitignoreに追加済み）
- 不要になったら、Google Cloud Consoleから鍵を削除してください

## 📞 サポート

設定で問題が発生した場合は、以下の情報と共に連絡してください：
- エラーメッセージの全文
- 実行したコマンド
- Google Cloud Consoleのスクリーンショット