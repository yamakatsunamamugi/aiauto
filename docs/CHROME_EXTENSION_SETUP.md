# Chrome拡張機能セットアップガイド

## 概要

AI自動化システム用Chrome拡張機能のセットアップと使用方法について説明します。

この拡張機能は以下の5つのAIサービスに対応しています：
- **ChatGPT** (chat.openai.com)
- **Claude** (claude.ai)
- **Gemini** (gemini.google.com)
- **Genspark** (www.genspark.ai)
- **Google AI Studio** (aistudio.google.com)

## システム要件

- **Google Chrome** 88以降
- **Python 3.8以降**
- **macOS** または **Windows** または **Linux**
- 各AIサービスへのアクセス権限

## セットアップ手順

### 1. Chrome拡張機能のインストール

#### 1.1 開発者モードを有効化

1. Chromeを開く
2. アドレスバーに `chrome://extensions/` と入力してEnter
3. 右上の「開発者モード」をONにする

![開発者モード](https://via.placeholder.com/400x200?text=Developer+Mode+ON)

#### 1.2 拡張機能を読み込み

1. 「パッケージ化されていない拡張機能を読み込む」をクリック
2. プロジェクトの `chrome-extension` フォルダを選択
3. 「フォルダーの選択」をクリック

```
📁 AI自動化プロジェクト/
  └── 📁 chrome-extension/
      ├── manifest.json
      ├── content.js
      ├── background.js
      ├── popup.html
      ├── popup.js
      └── styles.css
```

#### 1.3 インストール確認

拡張機能が正常にインストールされると：
- 拡張機能一覧に「AI Automation Bridge」が表示される
- Chrome右上のツールバーに拡張機能アイコンが表示される

### 2. AIサービスでのログイン

各AIサービスで事前にログインしておく必要があります：

#### 2.1 ChatGPT
1. https://chat.openai.com にアクセス
2. OpenAIアカウントでログイン
3. ブラウザにログイン状態を保存

#### 2.2 Claude
1. https://claude.ai にアクセス
2. Anthropicアカウントでログイン
3. ブラウザにログイン状態を保存

#### 2.3 Gemini
1. https://gemini.google.com にアクセス
2. Googleアカウントでログイン
3. ブラウザにログイン状態を保存

#### 2.4 Genspark
1. https://www.genspark.ai にアクセス
2. アカウントでログイン
3. ブラウザにログイン状態を保存

#### 2.5 Google AI Studio
1. https://aistudio.google.com にアクセス
2. Googleアカウントでログイン
3. ブラウザにログイン状態を保存

### 3. Pythonライブラリのインストール

拡張機能統合のために追加ライブラリが必要な場合：

```bash
# プロジェクトディレクトリで実行
pip install psutil  # Chrome プロセス監視用（オプション）
```

### 4. 動作確認

#### 4.1 拡張機能ポップアップの確認

1. Chrome右上の拡張機能アイコンをクリック
2. 「AI Automation Bridge」ポップアップが表示される
3. 対応AIサービスの一覧が表示される

#### 4.2 接続テスト

1. 対応AIサービスのいずれかにアクセス
2. 拡張機能ポップアップを開く
3. 「接続テスト」ボタンをクリック
4. テスト用プロンプトが送信され、応答が返される

## 使用方法

### 1. GUI アプリケーションの起動

```bash
# プロジェクトディレクトリで実行
python gui_app.py
```

### 2. 自動化の実行

1. **スプレッドシートURL**を入力
2. **シート名**を選択
3. **シート情報読込**ボタンをクリック
4. 各列の**AIサービス**と**モデル**を選択
5. **自動化開始**ボタンをクリック

### 3. 実行の流れ

1. Pythonアプリケーションがタスクを特定
2. Chrome拡張機能が対応するAIサイトを操作
3. AI処理結果をスプレッドシートに書き戻し
4. 全タスク完了まで順次実行

## トラブルシューティング

### よくある問題と解決方法

#### 1. 拡張機能が認識されない

**症状**: Python側で「Chrome拡張機能が利用できません」エラー

**解決方法**:
- Chrome拡張機能が正しくインストールされているか確認
- 開発者モードがONになっているか確認
- 拡張機能を一度無効化して再度有効化

#### 2. AIサイトでログインエラー

**症状**: 「ログインが必要です」エラー

**解決方法**:
- 対象AIサービスで手動ログイン
- ブラウザのCookieとセッションを確認
- プライベートモードでないことを確認

#### 3. 応答タイムアウト

**症状**: 「応答タイムアウト」エラー

**解決方法**:
- インターネット接続を確認
- AIサービスが利用可能か確認
- タイムアウト設定を調整（extension_config.json）

#### 4. セレクタが見つからない

**症状**: 「テキスト入力エリアが見つかりません」エラー

**解決方法**:
- AIサイトのUIが変更されている可能性
- content.jsのセレクタを更新
- 最新版の拡張機能を取得

### 設定ファイルの調整

`config/extension_config.json` で動作をカスタマイズできます：

```json
{
  "extension": {
    "timeout": 120,
    "retry_count": 3,
    "debug_mode": false
  },
  "ai_services": {
    "chatgpt": {
      "enabled": true,
      "default_model": "gpt-4o",
      "timeout": 120
    },
    "claude": {
      "enabled": true,
      "default_model": "claude-3.5-sonnet",
      "timeout": 120
    }
  }
}
```

### ログの確認

問題の詳細を確認するため、以下のログを確認してください：

1. **Python側ログ**: GUI アプリケーションの実行ログ
2. **Chrome デベロッパーツール**: F12でコンソールを確認
3. **拡張機能ログ**: chrome://extensions/ > 詳細 > 拡張機能エラーを確認

## 高度な設定

### 1. カスタムセレクタの追加

AIサイトのUIが変更された場合、`content.js`でセレクタを更新できます：

```javascript
const configs = {
    chatgpt: {
        textarea: '#prompt-textarea, .new-textarea-selector',
        sendButton: 'button[data-testid="send-button"], .new-button-selector',
        // 他のセレクタ...
    }
};
```

### 2. デバッグモードの有効化

詳細なログ出力のためデバッグモードを有効化：

```json
{
  "extension": {
    "debug_mode": true
  }
}
```

### 3. 複数Chromeプロファイルでの使用

異なるGoogleアカウントでの使用：

```bash
# 専用プロファイルでChromeを起動
google-chrome --user-data-dir="/path/to/ai-automation-profile" --load-extension="/path/to/chrome-extension"
```

## セキュリティ注意事項

### 1. 認証情報の管理

- APIキーや認証情報をハードコードしない
- ブラウザのパスワード管理機能を適切に使用
- 本番環境では専用アカウントを使用

### 2. アクセス権限

- 拡張機能は最小限の権限のみ要求
- 不要なサイトへのアクセス権限は削除
- 定期的に権限を見直し

### 3. ネットワークセキュリティ

- HTTPS接続を使用
- プロキシ環境での動作確認
- ファイアウォール設定の確認

## FAQ

**Q: 拡張機能は他のブラウザでも使用できますか？**
A: 現在はGoogle Chrome専用です。他のChromiumベースブラウザ（Edge、Brave等）でも動作する可能性がありますが、テストされていません。

**Q: 複数のタブで同時にAI処理はできますか？**
A: 現在の実装では順次処理のみサポートしています。同時処理は今後の拡張予定です。

**Q: AIサービスの利用料金はかかりますか？**
A: 各AIサービスの料金体系に従います。大量処理時は料金にご注意ください。

**Q: 拡張機能のアップデート方法は？**
A: 新しいファイルをダウンロードして、chrome://extensions/ で「再読み込み」ボタンをクリックしてください。

## サポート

問題が解決しない場合：

1. **ログの収集**: Python実行ログとChrome デベロッパーツールのログ
2. **環境情報**: OS、Chrome バージョン、Python バージョン
3. **エラーの詳細**: エラーメッセージの全文
4. **再現手順**: 問題が発生する具体的な手順

## 更新履歴

### v1.0.0 (2024-12-06)
- 初回リリース
- 5つのAIサービス対応
- Python-拡張機能間通信実装
- 基本的なエラーハンドリング

---

**開発者**: AI-B (Chrome拡張機能統合担当)
**最終更新**: 2024年12月6日