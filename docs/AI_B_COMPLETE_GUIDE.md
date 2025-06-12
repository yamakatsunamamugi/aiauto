# 🤖 AI-B 完全作業マニュアル（手動管理方式）

## 🎯 あなたのミッション
GUIでモデルリストを手動管理できる機能を実装し、ユーザーが簡単に最新のモデルを設定できるようにする。

---

## 📋 基本情報

### リポジトリ情報
- **URL**: https://github.com/yamakatsunamamugi/aiauto
- **ブランチ**: `feature/model-fetch-manual`
- **作成するファイル**: 
  - `src/gui/manual_model_manager.py`（メイン実装）
  - `config/manual_models.json`（モデル設定ファイル）

### 現在の問題
- 既存の`ai_model_updater.py`は公式ドキュメントから情報を取得している
- しかし、実際のWebアプリで使えるモデルと一致しない
- ユーザーが手動で正しいモデルを設定できる仕組みが必要

---

## 🚀 作業手順

### 1. 環境準備

```bash
# リポジトリをクローン
git clone https://github.com/yamakatsunamamugi/aiauto.git
cd aiauto

# 自分のブランチに切り替え（重要！）
git checkout feature/model-fetch-manual

# 現在のブランチを確認（必ず実行）
git branch
# * feature/model-fetch-manual ← これが表示されることを確認
```

### 2. ファイル作成

```bash
# メインのPythonファイルを作成
touch src/gui/manual_model_manager.py

# 設定ファイル用ディレクトリ確認
mkdir -p config

# 設定ファイルを作成
touch config/manual_models.json
```

### 3. 設定ファイルの実装

まず`config/manual_models.json`に以下の内容を記述：

```json
{
  "last_updated": "2025-01-12",
  "models": {
    "chatgpt": [
      "gpt-4o",
      "gpt-4o-mini",
      "gpt-4-turbo",
      "gpt-4",
      "gpt-3.5-turbo"
    ],
    "claude": [
      "claude-3.5-sonnet",
      "claude-3-opus",
      "claude-3-sonnet",
      "claude-3-haiku"
    ],
    "gemini": [
      "gemini-1.5-pro",
      "gemini-1.5-flash",
      "gemini-pro",
      "gemini-pro-vision"
    ],
    "genspark": [
      "default",
      "advanced"
    ],
    "google_ai_studio": [
      "gemini-1.5-pro",
      "gemini-1.5-flash",
      "gemini-pro"
    ]
  },
  "notes": {
    "chatgpt": "2024年12月時点の利用可能モデル",
    "claude": "Anthropic公式サイトで確認済み",
    "gemini": "Google AI Studioと共通",
    "genspark": "詳細なモデル名は非公開",
    "google_ai_studio": "Geminiモデルを使用"
  }
}
```

### 4. Pythonコードの実装

`src/gui/manual_model_manager.py`に以下を実装：

```python
"""
手動管理方式でAIモデル情報を管理
ユーザーが手動で編集可能な設定ファイルからモデル情報を読み込む
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

logger = logging.getLogger(__name__)

# 設定ファイルのパス
CONFIG_PATH = "config/manual_models.json"


def update_model_list() -> dict:
    """
    【必須関数】手動設定ファイルからモデルリストを読み込む
    
    Returns:
        dict: 各AIサービスのモデルリスト
        {
            "chatgpt": ["gpt-4o", "gpt-4o-mini", ...],
            "claude": ["claude-3.5-sonnet", ...],
            "gemini": ["gemini-1.5-pro", ...],
            "genspark": ["default", ...],
            "google_ai_studio": ["gemini-1.5-pro", ...]
        }
    """
    try:
        # 設定ファイルが存在する場合は読み込む
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("models", get_default_models())
        else:
            # ファイルが存在しない場合はデフォルト値を返す
            logger.info("設定ファイルが見つかりません。デフォルト値を使用します。")
            return get_default_models()
            
    except json.JSONDecodeError as e:
        logger.error(f"JSONファイルの解析エラー: {e}")
        return get_default_models()
    except Exception as e:
        logger.error(f"設定ファイル読み込みエラー: {e}")
        return get_default_models()


def get_default_models() -> dict:
    """デフォルトのモデルリストを返す"""
    return {
        "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "claude": ["claude-3.5-sonnet", "claude-3-opus"],
        "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
        "genspark": ["default"],
        "google_ai_studio": ["gemini-1.5-pro"]
    }


def save_models(models: dict, notes: Optional[dict] = None):
    """モデル情報を設定ファイルに保存"""
    try:
        data = {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "models": models,
            "notes": notes or {}
        }
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info("モデル情報を保存しました")
        return True
        
    except Exception as e:
        logger.error(f"保存エラー: {e}")
        return False


class ModelEditorDialog:
    """モデル編集用のGUIダイアログ"""
    
    def __init__(self, parent=None):
        self.result = None
        self.models = update_model_list()
        
        # ダイアログ作成
        self.dialog = tk.Toplevel(parent) if parent else tk.Tk()
        self.dialog.title("🤖 AIモデル手動設定")
        self.dialog.geometry("800x600")
        
        self._create_widgets()
        
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 説明ラベル
        ttk.Label(main_frame, text="各AIサービスで使用可能なモデルを編集してください。\n1行に1つのモデル名を記入してください。").grid(
            row=0, column=0, columnspan=2, pady=(0, 10)
        )
        
        # 各サービスのエディタを作成
        self.editors = {}
        services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
        
        for i, service in enumerate(services):
            row = i + 1
            
            # サービス名ラベル
            ttk.Label(main_frame, text=f"{service}:").grid(
                row=row, column=0, sticky=tk.W, padx=(0, 10)
            )
            
            # テキストエディタ
            editor = scrolledtext.ScrolledText(
                main_frame, height=4, width=50, wrap=tk.WORD
            )
            editor.grid(row=row, column=1, pady=5, sticky=(tk.W, tk.E))
            
            # 現在のモデルを表示
            current_models = self.models.get(service, [])
            editor.insert(tk.END, "\n".join(current_models))
            
            self.editors[service] = editor
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(services) + 1, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self._cancel).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="デフォルトに戻す", command=self._reset_to_default).pack(side=tk.LEFT, padx=5)
        
        # ウィンドウの重み設定
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def _save(self):
        """編集内容を保存"""
        try:
            # 各エディタから内容を取得
            new_models = {}
            for service, editor in self.editors.items():
                text = editor.get(1.0, tk.END).strip()
                # 空行を除外してリスト化
                models = [line.strip() for line in text.split('\n') if line.strip()]
                new_models[service] = models
            
            # 保存
            if save_models(new_models):
                messagebox.showinfo("成功", "モデル情報を保存しました")
                self.result = new_models
                self.dialog.destroy()
            else:
                messagebox.showerror("エラー", "保存に失敗しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"保存エラー: {e}")
    
    def _cancel(self):
        """キャンセル"""
        self.dialog.destroy()
    
    def _reset_to_default(self):
        """デフォルト値に戻す"""
        if messagebox.askyesno("確認", "デフォルト値に戻しますか？"):
            default_models = get_default_models()
            for service, editor in self.editors.items():
                editor.delete(1.0, tk.END)
                editor.insert(tk.END, "\n".join(default_models.get(service, [])))
    
    def show(self):
        """ダイアログを表示"""
        self.dialog.wait_window()
        return self.result


# テスト用
if __name__ == "__main__":
    print("手動管理方式のテスト")
    
    # 現在の設定を表示
    print("\n現在のモデル設定:")
    models = update_model_list()
    print(json.dumps(models, indent=2, ensure_ascii=False))
    
    # GUI編集ダイアログのテスト
    print("\nGUI編集ダイアログを開きますか？ (y/n): ", end="")
    if input().lower() == 'y':
        editor = ModelEditorDialog()
        result = editor.show()
        if result:
            print("\n更新後のモデル:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 5. テスト

```bash
# 設定ファイルの内容を確認
cat config/manual_models.json

# 関数のテスト
python -c "from src.gui.manual_model_manager import update_model_list; print(update_model_list())"

# GUIテスト（対話的）
python src/gui/manual_model_manager.py
```

### 6. コミット＆プッシュ

```bash
# 変更を確認
git status

# ファイルを追加
git add src/gui/manual_model_manager.py config/manual_models.json

# コミット（メッセージは日本語でわかりやすく）
git commit -m "feat: 手動管理方式でモデル取得機能を実装

- JSONファイルでモデルリストを管理
- GUI編集ダイアログを実装
- エラーハンドリングとデフォルト値を設定"

# プッシュ
git push origin feature/model-fetch-manual
```

---

## 🚫 絶対禁止事項（NEVER）

以下のことは**絶対にしないでください**：

1. **NEVER: `src/gui/main_window.py`を編集しない**
   - 読むのはOK、編集は絶対NG
   
2. **NEVER: 他のAIのファイルを変更しない**
   - `browser_session_fetcher.py`（AI-A用）
   - `api_model_fetcher.py`（AI-C用）
   
3. **NEVER: mainブランチで作業しない**
   - 必ず`feature/model-fetch-manual`で作業

4. **NEVER: ユーザーの確認なしに設定ファイルを削除しない**

5. **NEVER: JSONファイルに無効な形式を保存しない**

---

## ✅ 必須事項（YOU MUST）

以下は**必ず実行してください**：

1. **YOU MUST: 正しいブランチで作業する**
   ```bash
   git branch  # 必ず確認
   ```

2. **YOU MUST: `update_model_list()`関数を実装する**
   - 引数: なし
   - 戻り値: dict型（5つのAIサービス全て含む）

3. **YOU MUST: エラーハンドリングを実装する**
   - JSONパースエラー
   - ファイル読み込みエラー
   - 必ずデフォルト値を返す

4. **YOU MUST: 有効なJSONファイルを作成する**
   - 正しい形式
   - UTF-8エンコーディング

5. **YOU MUST: ファイルが存在しない場合の処理を実装**

---

## ⚠️ 重要事項（IMPORTANT）

1. **IMPORTANT: ユーザーが編集しやすい形式**
   - わかりやすいJSON構造
   - コメント（notes）を含める

2. **IMPORTANT: バックアップを考慮**
   - 設定が壊れても復旧できるようにデフォルト値を持つ

3. **IMPORTANT: GUI使いやすさ**
   - 直感的な操作
   - エラーメッセージをわかりやすく

4. **IMPORTANT: 将来の拡張性**
   - 新しいAIサービスを追加しやすい構造

---

## 📊 期待される出力

`update_model_list()`の戻り値：

```python
{
    "chatgpt": [
        "gpt-4o",
        "gpt-4o-mini", 
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo"
    ],
    "claude": [
        "claude-3.5-sonnet",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku"
    ],
    "gemini": [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro",
        "gemini-pro-vision"
    ],
    "genspark": [
        "default",
        "advanced"
    ],
    "google_ai_studio": [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro"
    ]
}
```

---

## 🆘 トラブルシューティング

### JSONファイルが壊れた場合
```python
# デフォルト値で上書き
from src.gui.manual_model_manager import get_default_models, save_models
save_models(get_default_models())
```

### ブランチを間違えた場合
```bash
# 変更を一時保存
git stash

# 正しいブランチに切り替え
git checkout feature/model-fetch-manual

# 変更を復元
git stash pop
```

### 文字化けする場合
- ファイルのエンコーディングをUTF-8に設定
- `encoding='utf-8'`を必ず指定

---

## 📝 完了報告

実装が完了したら、以下の情報を報告してください：

1. **実装内容**
   - JSON形式の設計
   - GUI機能の説明

2. **使い方**
   - 設定ファイルの編集方法
   - GUIダイアログの使い方

3. **工夫した点**

4. **改善提案**

---

頑張ってください！シンプルで使いやすい実装を期待しています。🚀