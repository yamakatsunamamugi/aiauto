# Ollama統合システム セットアップガイド

## 概要

このガイドでは、ローカルAI（Ollama）を使った高速・無料AI処理システムのセットアップ方法を説明します。

担当者：AI-A（Ollama統合）  
作成日：2024年6月12日

## 前提条件

- macOS または Linux
- Python 3.8 以上
- メモリ 8GB 以上（推奨16GB以上）
- ディスク容量 10GB 以上の空き容量

## 1. Ollamaのインストール

### macOSの場合

```bash
# Homebrewを使用してインストール
brew install ollama

# Ollamaサービスを開始
brew services start ollama
```

### Linuxの場合

```bash
# 公式インストールスクリプトを使用
curl -fsSL https://ollama.com/install.sh | sh

# サービスを開始
sudo systemctl start ollama
sudo systemctl enable ollama
```

## 2. AIモデルのダウンロード

### 推奨モデル

```bash
# 基本モデル（高速・軽量）
ollama pull llama3.1:8b

# 追加モデル（オプション）
ollama pull llama3.2:3b      # より高速
ollama pull phi-4:14b        # 高品質
ollama pull gemma2:9b        # Google製
ollama pull deepseek-r1:7b   # 論理的思考
```

### モデル一覧確認

```bash
# インストール済みモデルの確認
ollama list

# モデル情報の詳細確認
ollama show llama3.1:8b
```

## 3. Python依存関係のインストール

```bash
# プロジェクトディレクトリに移動
cd /path/to/5.AI-auto

# Ollama専用依存関係をインストール
pip install -r requirements_ollama.txt

# または直接インストール
pip install ollama
```

## 4. システム統合確認

### 基本テスト

```bash
# Ollamaサービスの動作確認
ollama list

# Python統合テストの実行
python tests/test_ollama_integration.py
```

### GUIアプリでのテスト

```bash
# GUIアプリケーションを起動
python gui_app.py

# または
python run_gui.py
```

## 5. 設定とカスタマイズ

### モデル設定

デフォルトモデルや設定は `src/automation/ollama_config.py` で管理されています：

```python
from src.automation.ollama_config import OllamaConfig

# デフォルト設定の取得
config = OllamaConfig.get_default_config()

# 用途別推奨設定
recommendations = OllamaConfig.get_model_recommendations()
```

### パフォーマンス設定

| 用途 | 推奨モデル | 設定 |
|------|------------|------|
| 高速処理 | llama3.2:3b | temperature=0.5, num_predict=1000 |
| 品質重視 | llama3.1:8b | temperature=0.7, num_predict=2000 |
| 論理的思考 | deepseek-r1:7b | temperature=0.3, num_predict=3000 |
| 創造性重視 | llama3.1:8b | temperature=0.9, num_predict=2500 |

## 6. トラブルシューティング

### よくある問題と解決策

#### Ollamaサービスが起動しない

```bash
# サービス状態の確認
brew services list | grep ollama

# 手動起動
ollama serve

# ポート確認（デフォルト：11434）
lsof -i :11434
```

#### モデルダウンロードが失敗する

```bash
# ネットワーク接続確認
ping ollama.com

# ディスク容量確認
df -h

# 手動でモデルを削除して再ダウンロード
ollama rm llama3.1:8b
ollama pull llama3.1:8b
```

#### Python統合エラー

```bash
# ollama パッケージの再インストール
pip uninstall ollama
pip install ollama

# 環境変数の確認
echo $OLLAMA_HOST  # デフォルト: http://localhost:11434
```

#### メモリ不足エラー

```bash
# システムメモリ確認
free -h  # Linux
vm_stat  # macOS

# より軽量なモデルを使用
ollama pull llama3.2:3b
```

### ログの確認

```bash
# Ollamaログの確認
tail -f ~/.ollama/logs/server.log

# アプリケーションログの確認
tail -f logs/app.log
```

## 7. 高度な設定

### 環境変数

```bash
# Ollamaサーバーのホストを変更
export OLLAMA_HOST=http://localhost:11434

# モデル保存ディレクトリを変更
export OLLAMA_MODELS=/path/to/models

# GPUメモリ制限（NVIDIA GPU使用時）
export OLLAMA_GPU_MEMORY_FRACTION=0.8
```

### カスタムシステムプロンプト

```python
# src/automation/ollama_config.py で設定をカスタマイズ
CUSTOM_PROMPTS = {
    "business": "あなたはビジネスエキスパートです。専門的で簡潔に回答してください。",
    "creative": "あなたはクリエイティブライターです。想像力豊かに回答してください。",
    "technical": "あなたは技術エキスパートです。正確で詳細な技術情報を提供してください。"
}
```

## 8. パフォーマンス最適化

### ハードウェア推奨仕様

| 処理レベル | CPU | メモリ | ストレージ |
|------------|-----|--------|------------|
| 軽量処理 | 4コア | 8GB | SSD 20GB |
| 標準処理 | 8コア | 16GB | SSD 50GB |
| 高負荷処理 | 16コア | 32GB | SSD 100GB |

### モデル選択指針

- **3Bモデル**: 高速だが品質は基本的
- **7B-8Bモデル**: バランス型（推奨）
- **14B以上**: 高品質だが低速

## 9. セキュリティ考慮事項

- Ollamaは完全にローカルで動作し、外部にデータを送信しません
- モデルファイルは暗号化されて保存されます
- ネットワーク接続はモデルダウンロード時のみ必要です

## 10. 更新とメンテナンス

### Ollamaの更新

```bash
# Ollamaの更新
brew update && brew upgrade ollama

# モデルの更新確認
ollama list
```

### 定期メンテナンス

```bash
# 不要なモデルの削除
ollama rm <model_name>

# ログファイルのローテーション
logrotate ~/.ollama/logs/server.log
```

## サポート

問題が発生した場合は、以下の情報を収集してください：

1. OS とバージョン
2. Ollama バージョン（`ollama --version`）
3. Python バージョン
4. エラーメッセージの詳細
5. システムリソース使用状況

---

**担当者：AI-A（Ollama統合）**  
**最終更新：2024年6月12日**