# Git ワークフロー完全ガイド

## 🚨 絶対に守るべき基本ルール

### 1. 作業開始前（毎日必須）
```bash
# ステップ1: developブランチで最新を取得
git checkout develop
git pull origin develop

# ステップ2: 自分の担当ブランチに移動
git checkout feature/[あなたの担当]
# 担当者A: feature/gui-components
# 担当者B: feature/sheets-integration  
# 担当者C: feature/browser-automation

# ステップ3: developの最新変更をマージ
git merge develop
```

### 2. 作業中のコミット（こまめに実行）
```bash
# ファイル追加
git add [変更したファイル]
# または全て追加
git add .

# コミット（必ず詳細なメッセージ）
git commit -m "feat(スコープ): 概要

詳細説明
- 具体的な変更内容1
- 具体的な変更内容2

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# リモートにプッシュ
git push origin feature/[あなたの担当]
```

### 3. 週次統合（毎週金曜日）
```bash
# 全員で実施
git checkout develop
git pull origin develop

# 担当者Aのマージ
git merge feature/gui-components

# 担当者Bのマージ  
git merge feature/sheets-integration

# 担当者Cのマージ
git merge feature/browser-automation

# 統合テスト実行
python main.py

# 問題なければプッシュ
git push origin develop
```

## 📝 コミットメッセージ規約

### 種類（必須）
- `feat`: 新機能追加
- `fix`: バグ修正
- `docs`: ドキュメント更新
- `style`: コード整形
- `refactor`: リファクタリング
- `test`: テスト追加

### スコープ（推奨）
- `gui`: GUI関連
- `sheets`: Google Sheets関連
- `automation`: ブラウザ自動化関連
- `config`: 設定関連
- `utils`: ユーティリティ関連

### 良い例
```bash
git commit -m "feat(gui): スプレッドシート選択機能実装

- URL入力フィールド追加
- シート名取得・プルダウン表示
- バリデーション機能追加

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 悪い例
```bash
git commit -m "update"  # ❌ 内容が不明
git commit -m "fix bug"  # ❌ どのバグか不明
git commit -m "WIP"  # ❌ 不完全な状態でコミット
```

## ⚠️ トラブル対応

### コンフリクトが発生した場合
```bash
# 1. 状況確認
git status

# 2. コンフリクトファイルを手動編集
# <<<<<<< HEAD と >>>>>>> の間を適切に修正

# 3. 修正完了後
git add [修正したファイル]
git commit -m "fix: コンフリクト解決"
```

### 間違ったコミットの取り消し
```bash
# 最新コミットを取り消し（ファイルは残す）
git reset --soft HEAD~1

# ファイルも含めて完全に取り消し
git reset --hard HEAD~1
# ⚠️ 注意: 変更が完全に失われます
```

### プッシュできない場合
```bash
# リモートの最新を取得してから再プッシュ
git pull origin feature/[あなたの担当]
git push origin feature/[あなたの担当]
```

## 📂 ファイル編集権限

### 担当者A（GUI）のみ編集可能
- `src/gui/` 以下全て
- `main.py`（GUIアプリ起動部分のみ）

### 担当者B（Sheets）のみ編集可能  
- `src/sheets/` 以下全て
- `config/credentials.json`
- `config/sheets_config.json`

### 担当者C（Automation）のみ編集可能
- `src/automation/` 以下全て

### 全員で相談が必要
- `requirements.txt`
- `config/settings.json`
- `src/utils/` 以下
- `README.md`

## 🔄 日次・週次フロー

### 毎日の作業フロー
1. **朝（9:00）**: 最新developをマージ
2. **作業中**: 機能単位でこまめにコミット
3. **夕方（17:00）**: 進捗プッシュ・日次報告

### 毎週の統合フロー
1. **金曜16:00**: 各自の作業完了・プッシュ
2. **金曜16:30**: 統合作業開始
3. **金曜17:00**: 統合テスト・レビュー
4. **金曜17:30**: 来週計画・課題共有