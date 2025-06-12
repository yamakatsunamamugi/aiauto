# 🎯 AI自動化プロジェクト - 現状と次のステップ

## 📊 プロジェクト全体像

### プロジェクトの目的
Googleスプレッドシートのデータを読み取り、複数のAIサービス（ChatGPT、Claude、Gemini等）に自動でテキストを入力し、結果をスプレッドシートに書き戻すGUIアプリケーション。

### 主要コンポーネント
1. **GUI（メインウィンドウ）** - ユーザーインターフェース
2. **Google Sheets連携** - データの読み書き
3. **AI自動化** - 各AIサービスの操作
4. **設定管理** - モデル選択、認証情報等

---

## ✅ 完了した作業（現在の段階）

### 1. **基本システム構築**（完了）
- ✅ GUIアプリケーションの基本構造
- ✅ Google Sheets API連携
- ✅ スプレッドシート構造の解析機能
- ✅ エラーハンドリングとログ機能

### 2. **GUI機能**（完了）
- ✅ スプレッドシートURL入力とシート選択
- ✅ データプレビュー表示
- ✅ 列ごとのAI設定機能
- ✅ 実行制御（開始/停止）
- ✅ ログ表示

### 3. **モデル管理システム**（完了）
- ✅ 検証済みJSONファイルによるモデル管理
- ✅ GUI上でのJSON編集機能
- ✅ 各AIサービスのモデル選択

### 4. **テスト済み機能**
- ✅ スプレッドシート読み込み
- ✅ 「作業指示行」の検出（A列4行目）
- ✅ コピー列の特定
- ✅ タスク行の作成

---

## 🚧 未実装の機能（これからやること）

### 1. **AI自動化の実装**（最重要）

現在、以下の部分がダミー実装になっています：

```python
# src/gui/main_window.py の623-625行目
# AI処理（デモ版）
import time
time.sleep(1)  # 処理時間のシミュレーション

# デモ結果
demo_result = f"AI処理結果: {task_row.copy_text[:50]}... への応答"
```

**必要な実装：**
- 各AIサービスへの自動ログイン
- テキストの入力
- 応答の取得
- 結果の書き戻し

### 2. **AIハンドラーの完成**

`src/automation/ai_handlers/`ディレクトリに基本構造はありますが、実装が不完全です：

- `chatgpt_handler.py` - ChatGPTの自動操作
- `claude_handler.py` - Claudeの自動操作
- `gemini_handler.py` - Geminiの自動操作
- `genspark_handler.py` - Gensparkの自動操作
- `google_ai_studio_handler.py` - Google AI Studioの自動操作

### 3. **ブラウザ管理**

`src/automation/browser_manager.py`は基本実装のみ。必要な機能：
- 既存のChromeプロファイル使用（ログイン済み）
- セッション管理
- タブ切り替え

### 4. **結果の書き戻し**

現在はログに表示するだけ。実際にスプレッドシートに書き戻す処理が必要。

---

## 📝 新しいAIへの作業指示

### 作業内容：AI自動化機能の実装

**リポジトリ**: https://github.com/yamakatsunamamugi/aiauto

**現在の状態**: GUIとスプレッドシート連携は完成。AI自動化部分が未実装。

**あなたのタスク**:
1. AI自動化機能を実装する
2. 各AIサービスへの自動操作を完成させる
3. 結果をスプレッドシートに書き戻す

### 詳細な実装手順

#### 1. プロジェクトの理解（Explore）
```bash
# リポジトリをクローン
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto

# 主要ファイルを確認
- src/gui/main_window.py（623行目付近のデモ実装を確認）
- src/automation/ai_handlers/base_handler.py（基本クラス）
- src/automation/ai_handlers/chatgpt_handler.py（未実装）
```

#### 2. 実装計画（Plan）
1. ブラウザ管理の改善
2. 各AIハンドラーの実装
3. main_window.pyとの統合
4. テスト

#### 3. 実装すべき機能

**3.1 ブラウザ管理**（src/automation/browser_manager.py）
```python
def get_browser_with_profile(self):
    """ユーザーのChromeプロファイルを使用してブラウザを起動"""
    # macOS: ~/Library/Application Support/Google/Chrome
    # Windows: %LOCALAPPDATA%\Google\Chrome\User Data
```

**3.2 ChatGPTハンドラー**（src/automation/ai_handlers/chatgpt_handler.py）
```python
class ChatGPTHandler(BaseAIHandler):
    def process_text(self, text: str) -> str:
        """
        1. chat.openai.comにアクセス
        2. テキストエリアにtextを入力
        3. 送信ボタンをクリック
        4. 応答を待つ
        5. 結果を取得して返す
        """
```

**3.3 main_window.pyの修正**
```python
# 623行目付近を実際の実装に置き換え
from src.automation.automation_controller import AutomationController

# AI処理
result = self.automation_controller.process_task(task_row)
```

#### 4. テスト方法
```bash
# GUIアプリを起動
python gui_app.py

# 1. テスト用スプレッドシートURL（デフォルトで入力済み）
# 2. 「シート情報読込」をクリック
# 3. AI設定を選択
# 4. 「自動化開始」をクリック
```

### 重要な注意事項

1. **ログイン処理**
   - 各AIサービスは事前にブラウザでログイン済みを想定
   - 自動ログインは実装しない（複雑になるため）

2. **エラーハンドリング**
   - 各ステップで詳細なログを出力
   - リトライ機能を実装（最大5回）

3. **セレクタの取得**
   - 各AIサービスのDOM要素は変更される可能性がある
   - `config/ai_service_selectors.json`に外部化

### 期待される成果物

1. **動作するAI自動化機能**
   - 各AIサービスでテキスト処理が可能
   - 結果がスプレッドシートに書き戻される

2. **完成したハンドラー**
   - 最低でもChatGPTとClaudeは動作すること

3. **テスト結果**
   - 実際のスプレッドシートで動作確認

### コミット方法
```bash
git add .
git commit -m "feat: AI自動化機能を実装

- ChatGPTハンドラーの実装
- Claudeハンドラーの実装
- ブラウザプロファイル対応
- main_window.pyとの統合

作業内容：[具体的な変更内容]
次のステップ：[残りの作業]"

git push origin main
```

---

## 🔍 参考情報

### 既存のセレクタ情報
`config/ai_service_selectors.json`に各AIサービスのDOM要素情報があります。

### ログの確認方法
```bash
# リアルタイムでログを確認
tail -f logs/app_*.log
```

### デバッグ方法
1. `headless=False`でブラウザを表示
2. `time.sleep()`で一時停止して確認
3. スクリーンショットを保存

---

## 📞 質問がある場合

実装で不明な点があれば、以下を確認してください：
1. 既存のコードのコメント
2. `docs/`ディレクトリのドキュメント
3. テストファイルの実装例

頑張ってください！🚀