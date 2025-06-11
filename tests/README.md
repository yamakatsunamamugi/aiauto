# AI自動化ツール テストスイート

## 概要
このディレクトリには、AI自動化ツールの各コンポーネントに対するテストが含まれています。

## テスト構造

```
tests/
├── unit/                  # 単体テスト
│   ├── automation/       # 自動化モジュールのテスト
│   ├── gui/             # GUIモジュールのテスト
│   └── sheets/          # Sheetsモジュールのテスト
├── integration/          # 統合テスト
├── e2e/                 # End-to-Endテスト
├── performance/         # パフォーマンステスト
└── fixtures/            # テスト用フィクスチャ
```

## 担当者別テスト範囲

### 担当者C（Automation）
- `tests/unit/automation/`: ブラウザ自動化の単体テスト
- `tests/e2e/test_ai_automation_e2e.py`: AI連携のE2Eテスト
- `tests/performance/`: パフォーマンス・負荷テスト

## テスト実行方法

### 全テスト実行
```bash
pytest
```

### 特定モジュールのテスト実行
```bash
# Automationテストのみ
pytest tests/unit/automation/

# カバレッジレポート付き
pytest tests/unit/automation/ --cov=src.automation --cov-report=html
```

### E2Eテスト実行（実際のサイトにアクセス）
```bash
# 環境変数でスキップを無効化
SKIP_LIVE_TESTS=false pytest tests/e2e/ -m e2e
```

### パフォーマンステスト実行
```bash
pytest tests/performance/ -m performance
```

## テスト作成ガイドライン

1. **単体テスト**: 個々のクラス・関数の動作を検証
2. **統合テスト**: モジュール間の連携を検証
3. **E2Eテスト**: 実際のユーザーシナリオを検証
4. **パフォーマンステスト**: 処理速度とリソース使用を検証

## カバレッジ目標

- 単体テスト: 80%以上
- 重要機能: 90%以上
- 全体: 70%以上