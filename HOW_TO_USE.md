# 🚀 スプレッドシート自動化システムの使用方法

## 📋 事前準備

### 1. Chrome拡張機能のインストール
1. Google Chromeを開く
2. URLバーに `chrome://extensions/` を入力
3. 右上の「デベロッパーモード」をONにする
4. 「パッケージ化されていない拡張機能を読み込む」をクリック
5. 以下のフォルダを選択：
   ```
   /Users/roudousha/Dropbox/5.AI-auto/chrome-extension
   ```
6. 「AI Automation Bridge」が拡張機能一覧に表示されることを確認

### 2. 各AIサイトへのログイン
以下のサイトに事前にログインしておく：
- ChatGPT: https://chatgpt.com
- Claude: https://claude.ai
- Gemini: https://gemini.google.com
- Genspark: https://www.genspark.ai
- Google AI Studio: https://aistudio.google.com

### 3. Googleスプレッドシートの準備
- スプレッドシートを開く
- 以下のメールアドレスに編集権限を付与：
  ```
  ai-automation-bot@my-ai-automation-462102.iam.gserviceaccount.com
  ```

## 🎯 使用手順

### Step 1: GUIアプリケーションの起動
```bash
cd /Users/roudousha/Dropbox/5.AI-auto
python3 gui_automation_app_fixed.py
```

### Step 2: スプレッドシート読み込み
1. スプレッドシートのURLを入力
2. 「URLから読込」ボタンをクリック
3. シート名を選択
4. 「シート情報読込」ボタンをクリック

### Step 3: AI設定
各コピー列について：
1. 使用するAIを選択（ChatGPT、Claude等）
2. モデルを選択
3. DeepThink等の設定をチェック
4. 必要に応じて「詳細設定」から温度等を調整

### Step 4: 自動化実行
1. 「自動化開始」ボタンをクリック
2. 処理の進行状況をログで確認
3. エラーが発生した場合は、エラー列に記録される

## ⚠️ 注意事項

### Chrome拡張機能が動作しない場合
- 現在はモック応答モードで動作します
- 実際のAI処理にはChrome拡張機能のインストールが必要です

### エラーが発生した場合
- ログウィンドウでエラー詳細を確認
- スプレッドシートのエラー列を確認
- 5回までリトライされます

## 📊 処理結果の確認

処理完了後、スプレッドシートで以下を確認：
- **処理列**: 「処理済み」と表示
- **エラー列**: エラーがあった場合の詳細
- **貼り付け列**: AIの回答結果

## 🔧 トラブルシューティング

### Q: Chrome拡張機能がインストールできない
A: デベロッパーモードがONになっているか確認

### Q: AIサイトが応答しない
A: 各AIサイトにログインしているか確認

### Q: スプレッドシートが読み込めない
A: サービスアカウントに編集権限を付与しているか確認