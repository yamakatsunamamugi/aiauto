# Google Sheets連携セットアップガイド

担当者B（Google Sheets連携）の実装が完了しました。このガイドでは、セットアップから動作確認までの手順を説明します。

## 📋 実装完了モジュール

### 1. 認証管理 (`src/sheets/auth_manager.py`)
- Google Sheets API認証
- サービスアカウント管理
- アクセス権限確認

### 2. Sheets APIクライアント (`src/sheets/sheets_client.py`)
- スプレッドシートデータ読み書き
- 一括更新機能
- エラーハンドリング

### 3. データ処理ハンドラー (`src/sheets/data_handler.py`)
- CLAUDE.md仕様準拠の処理ロジック
- タスク生成・状態管理
- データ構造検証

### 4. データ構造定義 (`src/sheets/models.py`)
- TaskRow, SheetConfig等のデータモデル
- 列挙型（TaskStatus, AIService）
- バリデーション機能

### 5. 設定ファイル
- `config/sheets_config.json`: Sheets固有設定
- `config/credentials_example.json`: 認証情報テンプレート

## 🔧 初期セットアップ手順

### ステップ1: Google Cloud Console設定

1. **Google Cloud Console** にアクセス
   ```
   https://console.cloud.google.com/
   ```

2. **新しいプロジェクト作成**
   - プロジェクト名: `ai-automation-tool`
   - プロジェクトIDを控えておく

3. **Google Sheets API有効化**
   ```
   ナビゲーション → APIとサービス → ライブラリ
   → 「Google Sheets API」を検索 → 有効にする
   ```

### ステップ2: サービスアカウント作成

1. **認証情報の作成**
   ```
   APIとサービス → 認証情報 → 「認証情報を作成」
   → 「サービスアカウント」
   ```

2. **サービスアカウント詳細**
   - 名前: `ai-automation-service`
   - 説明: `AI自動化ツール用サービスアカウント`
   - ロール: `編集者`

3. **認証キーのダウンロード**
   ```
   作成したサービスアカウント → キー → キーを追加
   → 新しいキーを作成 → JSON → 作成
   ```

4. **認証ファイルの配置**
   ```bash
   # ダウンロードしたJSONファイルを以下に保存
   /Users/roudousha/Dropbox/5.AI-auto/config/credentials.json
   ```

### ステップ3: スプレッドシート設定

1. **テスト用スプレッドシート作成**
   - Google Sheetsで新しいスプレッドシートを作成
   - シート名: `Sheet1`（または任意）

2. **CLAUDE.md仕様に従ったデータ構造作成**
   ```
   A列  B列      C列      D列     E列
   1                               
   2                               
   3                               
   4                               
   5   作業     処理     エラー    コピー   結果
   6   1                         テスト文章1
   7   2                         テスト文章2
   8   3                         テスト文章3
   ```

3. **サービスアカウントの共有設定**
   ```
   スプレッドシート → 共有 → 
   サービスアカウントのメールアドレスを追加
   → 権限を「編集者」に設定 → 送信
   ```

### ステップ4: 依存関係インストール

```bash
cd /Users/roudousha/Dropbox/5.AI-auto
pip install -r requirements.txt
```

## 🧪 動作確認手順

### 1. 環境テスト

```bash
# 認証テスト
python -m src.sheets.auth_manager

# Sheets APIテスト
python -m src.sheets.sheets_client <spreadsheet_id>

# データハンドラーテスト  
python -m src.sheets.data_handler <spreadsheet_url> <sheet_name>
```

### 2. 統合テスト実行

```bash
# 完全な統合テスト
python tests/test_sheets_integration.py <spreadsheet_url> <sheet_name>
```

**例:**
```bash
python tests/test_sheets_integration.py \
  'https://docs.google.com/spreadsheets/d/1abcdef.../edit' \
  'Sheet1'
```

### 3. 期待される出力

```
🚀 Google Sheets連携モジュール 統合テスト開始
============================================================
🔍 環境設定をテスト中...
✅ 環境設定は正常です

🔐 認証機能をテスト中...
✅ 認証が成功しました
  サービスアカウント: ai-automation-service@...

📊 スプレッドシートアクセスをテスト中...
✅ スプレッドシートアクセス成功
  シート一覧: ['Sheet1']

🔍 データ構造検証をテスト中...
✅ データ構造検証成功

📋 タスク生成をテスト中...
✅ タスク生成成功: 3個のタスクを検出

✏️ シート書き込みをテスト中...
✅ シート書き込み成功

📋 テスト結果サマリー
============================================================
✅ PASS 環境設定
✅ PASS 認証
✅ PASS スプレッドシートアクセス
✅ PASS データ構造検証
✅ PASS タスク生成
✅ PASS シート書き込み

📊 結果: 6/6 テスト合格
🎉 すべてのテストが合格しました！
```

## 🔗 他担当者との連携インターフェース

### GUIチーム（担当者A）への提供機能

```python
from src.sheets import create_complete_handler, SheetConfig

# 基本的な使用例
def get_sheet_names(spreadsheet_url: str) -> List[str]:
    \"\"\"シート名一覧を取得\"\"\"
    sheets_client, _ = create_complete_handler()
    spreadsheet_id = extract_spreadsheet_id_from_url(spreadsheet_url)
    return sheets_client.get_sheet_names(spreadsheet_id)

def validate_spreadsheet_access(spreadsheet_url: str) -> bool:
    \"\"\"スプレッドシートアクセス権限確認\"\"\"
    sheets_client, _ = create_complete_handler()
    spreadsheet_id = extract_spreadsheet_id_from_url(spreadsheet_url)
    return sheets_client.auth_manager.validate_spreadsheet_access(spreadsheet_id)
```

### Automationチーム（担当者C）への提供機能

```python
# タスク処理フロー
def get_pending_tasks(config: SheetConfig) -> List[TaskRow]:
    \"\"\"未処理タスクを取得\"\"\"
    _, data_handler = create_complete_handler()
    return data_handler.get_pending_tasks(config)

def update_task_result(config: SheetConfig, task: TaskRow, result: str):
    \"\"\"タスク結果を更新\"\"\"
    _, data_handler = create_complete_handler()
    data_handler.update_task_result(config, task, result)

def mark_task_error(config: SheetConfig, task: TaskRow, error_message: str):
    \"\"\"タスクエラーを記録\"\"\"
    _, data_handler = create_complete_handler()
    data_handler.mark_task_error(config, task, error_message)
```

## ⚠️ トラブルシューティング

### 1. 認証エラー

**症状:** `AuthenticationError: 認証情報ファイルが見つかりません`

**解決方法:**
```bash
# 認証ファイルの存在確認
ls -la config/credentials.json

# ファイルが存在しない場合、Google Cloud Consoleから再ダウンロード
```

### 2. アクセス権限エラー

**症状:** `スプレッドシートへのアクセス権限がありません`

**解決方法:**
1. スプレッドシートの共有設定を確認
2. サービスアカウントのメールアドレスが編集者として追加されているか確認
3. 共有リンクの権限設定を確認

### 3. データ構造エラー

**症状:** `「作業」ヘッダー行が見つかりません`

**解決方法:**
1. 5行目のA列に「作業」という文字列があるか確認
2. セルに余分なスペースがないか確認
3. シート名が正確に指定されているか確認

### 4. API制限エラー

**症状:** `quota exceeded` エラー

**解決方法:**
1. API呼び出し頻度を下げる（`api_delay`を増加）
2. バッチ更新を使用する
3. Google Cloud Consoleでクォータ上限を確認

## 📈 パフォーマンス最適化

### 1. バッチ処理の活用

```python
# 一括更新の使用例
updates = [
    {'row': 6, 'col': 2, 'value': '処理中'},
    {'row': 7, 'col': 2, 'value': '処理中'},
    {'row': 8, 'col': 2, 'value': '処理中'}
]
sheets_client.batch_update_cells(spreadsheet_id, sheet_name, updates)
```

### 2. キャッシュ活用

```python
# データの一括読み込み
sheet_data = data_handler.load_and_validate_sheet(config)
# 複数回のタスク生成で同じデータを再利用
tasks = data_handler.create_task_rows(sheet_data)
```

## 🎯 次のステップ

1. **他担当者との統合テスト**
   - GUIモジュールとの連携確認
   - Automationモジュールとの連携確認

2. **エラーハンドリング強化**
   - 網羅的なエラーケースのテスト
   - リトライ機能の調整

3. **本番運用準備**
   - ログレベルの調整
   - パフォーマンス監視の実装

---

## 📞 サポート

問題が発生した場合は、以下の情報とともにご連絡ください：

1. エラーメッセージの詳細
2. 使用しているスプレッドシートURL
3. `logs/integration_test.log` の内容
4. Python環境情報（`python --version`）

担当者B（Google Sheets連携）の実装は完了しています。
他担当者との統合作業を開始してください。