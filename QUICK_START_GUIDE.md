# 🚀 AI自動化システム クイックスタートガイド

## 🎯 3つの実行方法

### 方法A: 📱 GUI版（推奨・最も簡単）
```bash
python gui_app.py
```
- **メリット**: 直感的、設定が簡単
- **必要**: Google Sheets認証

### 方法B: 🖥️ コマンドライン版（中級者向け）
```bash
python run_automation_cli.py
```
- **メリット**: GUI不要、自動化可能
- **必要**: Google Sheets認証

### 方法C: 🧪 開発者テスト版（認証不要）
```bash
python test_automation_demo.py
```
- **メリット**: 認証不要、即座にテスト可能
- **用途**: 動作確認、開発テスト

---

## 📋 最低限の準備事項

### 🔧 Google Sheets認証設定（方法A・B用）

1. **Google Cloud Console設定**
   - [Google Cloud Console](https://console.cloud.google.com) にアクセス
   - 新しいプロジェクトを作成
   - Google Sheets API を有効化
   - サービスアカウントキーを作成

2. **認証ファイル配置**
   ```bash
   # ダウンロードした認証JSONファイルを配置
   cp ~/Downloads/your-credentials.json config/credentials.json
   ```

3. **スプレッドシート権限設定**
   - 対象スプレッドシートにサービスアカウントのメールアドレスを編集者として追加

### 🤖 AIサービスログイン（実際のAI処理用）

各AIサービスにブラウザでログイン：
- [ChatGPT](https://chat.openai.com)
- [Claude](https://claude.ai)
- [Gemini](https://gemini.google.com)
- [Genspark](https://www.genspark.ai)
- [Google AI Studio](https://aistudio.google.com)

---

## 🎮 実行手順

### 💡 まずは開発者テストで動作確認
```bash
# 認証不要・即座に実行可能
python test_automation_demo.py
```

### 🚀 実際のスプレッドシートで実行

**GUI版の場合:**
```bash
python gui_app.py
```
1. スプレッドシートURL入力
2. シート名選択  
3. AI設定選択
4. 「自動化開始」ボタンクリック

**CLI版の場合:**
```bash
python run_automation_cli.py
```
対話形式で設定を入力

---

## 📊 テスト用スプレッドシート形式

```
A    B      C       D      E
行   処理   エラー   コピー  貼り付け
1    未処理          こんにちは、元気ですか？
2    未処理          今日の天気はどうですか？
3    未処理          AIについて教えて
```

**重要なポイント:**
- 5行目のA列に「作業」と記載
- 「コピー」列にAIに送信するテキスト
- A列に連番（1,2,3...）で処理対象行を指定

---

## 🔍 トラブルシューティング

### よくある問題

1. **Google Sheets認証エラー**
   ```
   ❌ Google Sheets API認証に失敗しました
   💡 config/credentials.json を確認してください
   ```
   → 認証ファイルの配置とAPI有効化を確認

2. **スプレッドシート読み込みエラー**
   ```
   ❌ スプレッドシート読み込みに失敗しました
   ```
   → URL、シート名、権限設定を確認

3. **処理対象タスクなし**
   ```
   ❌ 処理対象のタスクが見つかりません
   ```
   → スプレッドシート形式を確認

### ログ確認
```bash
# ログファイル確認
tail -f logs/app.log

# 詳細なエラー情報
python gui_app.py --debug
```

---

## 🎉 成功例

### 開発者テスト実行例
```bash
$ python test_automation_demo.py

🧪 AI自動化システム - 開発者テストモード
==================================================
💡 このモードは認証不要でシステム動作をテストできます

📋 1. システム初期化テスト...
   ✅ モジュールインポート成功
📝 2. デモタスクデータ作成...
   ✅ 5件のデモタスク作成成功
🤖 4. 模擬自動化実行開始...
   🔄 処理中 1/5: chatgpt
      ✅ 完了 (0.83秒)
   [... 続く ...]

🎉 模擬自動化処理完了！
📊 処理結果:
   ✅ 成功: 5件
   📈 成功率: 100.0%
```

---

## 📞 サポート

- **ログ確認**: `logs/app.log`
- **設定確認**: `config/` ディレクトリ
- **テスト実行**: `python test_automation_demo.py`

**🎯 推奨：まずは `python test_automation_demo.py` で動作確認してから実際のスプレッドシートで試してください！**