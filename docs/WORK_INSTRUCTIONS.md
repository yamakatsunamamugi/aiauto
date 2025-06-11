# AI自動化ツール - 3人チーム開発指示書

## 📋 目次
1. [プロジェクト概要](#プロジェクト概要)
2. [Git管理基本ルール](#git管理基本ルール)
3. [担当者A: GUI・設定管理担当](#担当者a-gui設定管理担当)
4. [担当者B: Google Sheets連携担当](#担当者b-google-sheets連携担当)
5. [担当者C: ブラウザ自動化・AI連携担当](#担当者c-ブラウザ自動化ai連携担当)
6. [統合・テスト手順](#統合テスト手順)
7. [トラブルシューティング](#トラブルシューティング)

---

## 🎯 プロジェクト概要

### 最終目標
Googleスプレッドシートのデータを読み取り、複数のAIサービス（ChatGPT、Claude、Gemini、Genspark、Google AI Studio）を自動操作して、結果をスプレッドシートに書き戻すGUIアプリケーション

### 技術スタック
- **GUI**: tkinter（Python標準）
- **Web自動化**: Selenium WebDriver
- **API**: Google Sheets API
- **言語**: Python 3.8+
- **設定管理**: JSON
- **ログ**: Python logging

### 開発期間
- **全体**: 4週間
- **フェーズ1**: 基盤構築（1週間）
- **フェーズ2**: 機能実装（2週間）
- **フェーズ3**: 統合・テスト（1週間）

---

## 🔄 Git管理基本ルール

### ブランチ構成
```
main (本番用 - 最終リリース時のみ更新)
├── develop (開発統合用 - 各機能の統合)
    ├── feature/gui-components      # 担当者A
    ├── feature/sheets-integration  # 担当者B  
    └── feature/browser-automation  # 担当者C
```

### 🚨 絶対に守るべきルール

#### 1. 作業開始前の必須手順
```bash
# 1. 最新のdevelopを取得
git checkout develop
git pull origin develop

# 2. 自分の担当ブランチに切り替え
git checkout feature/[あなたの担当]

# 3. developの最新をマージ
git merge develop
```

#### 2. コミット規約（厳守）
```bash
git commit -m "種類(スコープ): 概要

詳細説明（任意）

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**種類の分類:**
- `feat`: 新機能追加
- `fix`: バグ修正
- `docs`: ドキュメント更新
- `style`: コード整形
- `refactor`: リファクタリング
- `test`: テスト追加
- `chore`: ビルド設定など

**例:**
```bash
git commit -m "feat(gui): メインウィンドウのレイアウト実装

- tkinterでベースレイアウト作成
- スプレッドシートURL入力フィールド追加
- AI選択プルダウンメニュー実装

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### 3. プッシュ・マージ手順
```bash
# 1. 作業完了後、ローカルコミット
git add .
git commit -m "コミットメッセージ"

# 2. リモートにプッシュ
git push origin feature/[あなたの担当]

# 3. developへの統合（週1回の統合日）
git checkout develop
git pull origin develop
git merge feature/[あなたの担当]
git push origin develop
```

### ⚠️ コンフリクト回避ルール

#### 共通ファイルの編集ルール
1. **main.py**: 最初に基本形を作成後、編集時は事前連絡
2. **requirements.txt**: 新しいライブラリ追加時は他担当者に連絡
3. **config/settings.json**: テンプレートのみ編集、個人設定は`.local.json`使用

#### ファイル編集権限
- `src/gui/`: 担当者Aのみ
- `src/sheets/`: 担当者Bのみ  
- `src/automation/`: 担当者Cのみ
- `src/utils/`: 全員（事前相談必須）

---

## 👨‍💻 担当者A: GUI・設定管理担当

### 🎯 あなたの担当範囲
- GUIアプリケーション全体
- 設定管理システム
- ユーザーインターフェース
- 進捗表示・ログ表示

### 📁 担当ファイル
```
src/gui/
├── main_window.py        # メインGUIウィンドウ
├── components.py         # UI部品（ボタン、リスト等）
├── settings_dialog.py    # 設定画面
└── progress_window.py    # 進捗表示画面

main.py                   # メインエントリーポイント（一部）
src/utils/config_manager.py  # 設定管理（一部追加）
```

### 🔧 実装すべき機能

#### フェーズ1（1週間目）: 基本GUI構築
**マイルストーン1.1**: メインウィンドウ基盤
```python
# src/gui/main_window.py - 実装内容
class MainWindow:
    def __init__(self):
        # tkinterメインウィンドウ作成
        # レイアウト設定（Grid/Pack使用）
    
    def setup_ui(self):
        # スプレッドシートURL入力フィールド
        # シート名選択コンボボックス
        # 開始・停止ボタン
        # 進捗バー
        # ログ表示エリア（ScrolledText）
```

**作業手順:**
1. tkinterでメインウィンドウ作成
2. 基本レイアウト設計（グリッド配置）
3. 入力フィールド配置
4. ボタン配置・イベントハンドラー設定

**テスト方法:**
```bash
python main.py
# GUIが表示されることを確認
```

**マイルストーン1.2**: AI設定画面
```python
# src/gui/settings_dialog.py - 実装内容
class SettingsDialog:
    def __init__(self, parent):
        # ダイアログウィンドウ作成
        
    def setup_ai_selection(self):
        # AI選択タブ作成
        # 各AI別設定画面
        # モデル選択プルダウン
        # 詳細設定チェックボックス
```

#### フェーズ2（2-3週間目）: 高度な機能実装
**マイルストーン2.1**: 進捗表示システム
```python
# src/gui/progress_window.py - 実装内容
class ProgressWindow:
    def update_progress(self, current, total):
        # 進捗バー更新
        # 現在の処理内容表示
        # 残り時間計算・表示
        
    def display_results(self, results):
        # 処理結果一覧表示
        # エラー情報表示
        # 統計情報表示
```

**マイルストーン2.2**: ログ表示・管理
```python
# src/gui/components.py - 実装内容
class LogViewer:
    def __init__(self):
        # ScrolledTextでログ表示エリア作成
        
    def add_log(self, level, message):
        # ログレベル別色分け表示
        # 自動スクロール
        # ログフィルター機能
```

### 🔗 他担当との連携ポイント

#### 担当者Bとの連携
```python
# インターフェース定義（あなたが作成）
class SheetsInterface:
    def get_sheet_names(self, url: str) -> List[str]:
        """スプレッドシートのシート名一覧を取得"""
        pass
    
    def get_column_headers(self, url: str, sheet: str) -> List[str]:
        """指定シートのヘッダー行を取得"""
        pass
```

#### 担当者Cとの連携
```python
# インターフェース定義（あなたが作成）
class AutomationInterface:
    def get_available_ais(self) -> Dict[str, List[str]]:
        """利用可能なAIとモデル一覧を取得"""
        pass
    
    def start_automation(self, config: dict, callback: callable):
        """自動化処理開始（進捗コールバック付き）"""
        pass
```

### 📝 作業開始手順

#### 初日のセットアップ
```bash
# 1. 環境確認
python --version  # 3.8以上であることを確認

# 2. ブランチ切り替え
git checkout feature/gui-components
git pull origin develop
git merge develop

# 3. 依存関係インストール
pip install -r requirements.txt

# 4. 基本ファイル作成
mkdir -p src/gui
touch src/gui/__init__.py
touch src/gui/main_window.py
touch src/gui/components.py
```

#### 日次作業フロー
```bash
# 朝の作業開始時
git pull origin develop
git merge develop  # 他担当の更新を取得

# 作業実施
# ... コーディング ...

# 夕方の作業終了時
git add src/gui/
git commit -m "feat(gui): [今日の作業内容]"
git push origin feature/gui-components
```

### 🧪 テスト項目
- [ ] GUIが正常に起動する
- [ ] スプレッドシートURL入力が機能する
- [ ] AI選択プルダウンが動作する
- [ ] 進捗表示が正確に更新される
- [ ] ログが適切に表示される
- [ ] エラー時にユーザーフレンドリーなメッセージが表示される

---

## 📊 担当者B: Google Sheets連携担当

### 🎯 あなたの担当範囲
- Google Sheets API連携
- データ読み書き処理
- 認証システム
- データ構造設計

### 📁 担当ファイル
```
src/sheets/
├── sheets_client.py      # Google Sheets API操作
├── data_handler.py       # データ処理・変換
├── auth_manager.py       # 認証管理
└── models.py             # データ構造定義

config/
├── credentials.json      # Google API認証情報（作成）
└── sheets_config.json    # Sheets固有設定（作成）
```

### 🔧 実装すべき機能

#### フェーズ1（1週間目）: Google Sheets API基盤
**マイルストーン1.1**: 認証システム
```python
# src/sheets/auth_manager.py - 実装内容
class AuthManager:
    def __init__(self):
        self.credentials_path = "config/credentials.json"
        self.token_path = "config/token.json"
    
    def authenticate(self) -> Credentials:
        """Google Sheets API認証"""
        # サービスアカウント認証実装
        # トークン管理
        # 認証エラーハンドリング
    
    def check_permissions(self, spreadsheet_url: str) -> bool:
        """スプレッドシートアクセス権限確認"""
        pass
```

**Google API設定手順（あなたが実施）:**
1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
2. Google Sheets API有効化
3. サービスアカウント作成
4. `config/credentials.json`に認証情報配置
5. スプレッドシートに共有権限付与

**マイルストーン1.2**: 基本読み書き機能
```python
# src/sheets/sheets_client.py - 実装内容
class SheetsClient:
    def __init__(self, auth_manager: AuthManager):
        self.auth = auth_manager
        self.service = self._build_service()
    
    def get_sheet_names(self, spreadsheet_url: str) -> List[str]:
        """シート名一覧を取得"""
        pass
    
    def read_range(self, spreadsheet_url: str, range_name: str) -> List[List[str]]:
        """指定範囲のデータを読み取り"""
        pass
    
    def write_range(self, spreadsheet_url: str, range_name: str, data: List[List[str]]):
        """指定範囲にデータを書き込み"""
        pass
```

#### フェーズ2（2-3週間目）: データ処理システム
**マイルストーン2.1**: データ構造定義
```python
# src/sheets/models.py - 実装内容
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TaskRow:
    """処理対象行のデータ構造"""
    row_number: int
    copy_text: str
    ai_service: str
    ai_model: str
    status: str  # '未処理', '処理中', '処理済み', 'エラー'
    result: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class SheetConfig:
    """シート設定情報"""
    spreadsheet_url: str
    sheet_name: str
    header_row: int = 5
    work_column: str = 'A'
    copy_columns: List[str] = None
```

**マイルストーン2.2**: データ処理ロジック
```python
# src/sheets/data_handler.py - 実装内容
class DataHandler:
    def __init__(self, sheets_client: SheetsClient):
        self.client = sheets_client
    
    def find_work_header_row(self, spreadsheet_url: str, sheet_name: str) -> int:
        """「作業」列を含む行を特定"""
        # A列を検索して「作業」文字を含む行を特定
        # 5行目から検索開始
        pass
    
    def find_copy_columns(self, spreadsheet_url: str, sheet_name: str, header_row: int) -> List[int]:
        """「コピー」列を全て特定"""
        # ヘッダー行で「コピー」完全一致する列を全て検索
        # 列番号をリストで返す
        pass
    
    def get_task_rows(self, spreadsheet_url: str, sheet_name: str) -> List[TaskRow]:
        """処理対象行を全て取得"""
        # A列が「1」から始まる連番行を取得
        # 各「コピー」列に対応するTaskRowを作成
        pass
    
    def update_task_status(self, task: TaskRow, status: str, result: str = None, error: str = None):
        """タスク状態をスプレッドシートに更新"""
        # 処理列：status更新
        # エラー列：error更新  
        # 貼り付け列：result更新
        pass
```

### 🔗 他担当との連携ポイント

#### 担当者Aとの連携
```python
# あなたが実装するインターフェース
def get_sheet_names(self, url: str) -> List[str]:
    """GUIのシート選択コンボボックス用"""
    return self.client.get_sheet_names(url)

def get_column_headers(self, url: str, sheet: str) -> List[str]:
    """GUI設定画面用"""
    return self.client.read_range(url, f"{sheet}!5:5")[0]
```

#### 担当者Cとの連携
```python
# あなたが実装するデータ提供インターフェース
def get_pending_tasks(self) -> List[TaskRow]:
    """未処理タスク一覧を提供"""
    pass

def update_task_result(self, task: TaskRow, result: str):
    """処理結果を受け取って更新"""
    pass

def mark_task_error(self, task: TaskRow, error_message: str):
    """エラー状態を更新"""
    pass
```

### 📝 作業開始手順

#### 初日のGoogle API設定
```bash
# 1. Google Cloud Console設定
# https://console.cloud.google.com/
# - 新しいプロジェクト作成
# - Google Sheets API有効化
# - サービスアカウント作成
# - 認証JSONダウンロード

# 2. ローカル環境設定
git checkout feature/sheets-integration
git pull origin develop
git merge develop

mkdir -p src/sheets config
touch src/sheets/__init__.py
# credentials.jsonを config/ に配置
```

#### Google API認証テスト
```python
# test_auth.py - 認証テスト用
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def test_auth():
    creds = Credentials.from_service_account_file(
        'config/credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=creds)
    print("認証成功！")

if __name__ == "__main__":
    test_auth()
```

### 🧪 テスト項目
- [ ] Google Sheets API認証が成功する
- [ ] スプレッドシート読み取りが機能する
- [ ] シート名一覧取得が機能する
- [ ] 「作業」行の特定が正確に動作する
- [ ] 「コピー」列の特定が全て正確に動作する
- [ ] データ書き込みが正確に動作する
- [ ] エラー時に適切にハンドリングされる

---

## 🤖 担当者C: ブラウザ自動化・AI連携担当

### 🎯 あなたの担当範囲
- Selenium WebDriver管理
- 各AIサイトの自動操作
- エラーハンドリング・リトライ
- ブラウザセッション管理

### 📁 担当ファイル
```
src/automation/
├── browser_manager.py    # Seleniumブラウザ管理
├── ai_handlers/         # AI別操作ハンドラー
│   ├── __init__.py
│   ├── base_handler.py  # 共通基底クラス
│   ├── chatgpt_handler.py
│   ├── claude_handler.py
│   ├── gemini_handler.py
│   ├── genspark_handler.py
│   └── google_ai_studio_handler.py
├── automation_controller.py  # 全体制御
└── retry_manager.py     # リトライ・エラー管理
```

### 🔧 実装すべき機能

#### フェーズ1（1週間目）: Selenium基盤構築
**マイルストーン1.1**: ブラウザ管理システム
```python
# src/automation/browser_manager.py - 実装内容
class BrowserManager:
    def __init__(self, browser_type: str = "chrome", headless: bool = False):
        self.browser_type = browser_type
        self.headless = headless
        self.driver = None
    
    def start_browser(self):
        """ブラウザ起動"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options)
        return self.driver
    
    def close_browser(self):
        """ブラウザ終了"""
        if self.driver:
            self.driver.quit()
    
    def get_driver(self):
        """WebDriverインスタンス取得"""
        return self.driver
```

**環境構築手順:**
```bash
# 1. Chrome WebDriver自動管理
pip install webdriver-manager

# 2. テスト実行
python -c "
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get('https://www.google.com')
print('Selenium動作確認完了')
driver.quit()
"
```

**マイルストーン1.2**: 基底ハンドラークラス
```python
# src/automation/ai_handlers/base_handler.py - 実装内容
from abc import ABC, abstractmethod
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BaseAIHandler(ABC):
    def __init__(self, driver, timeout: int = 30):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.timeout = timeout
    
    @abstractmethod
    def login_check(self) -> bool:
        """ログイン状態確認"""
        pass
    
    @abstractmethod
    def input_text(self, text: str) -> bool:
        """テキスト入力"""
        pass
    
    @abstractmethod
    def submit_request(self) -> bool:
        """リクエスト送信"""
        pass
    
    @abstractmethod
    def wait_for_response(self) -> bool:
        """応答待機"""
        pass
    
    @abstractmethod
    def get_response_text(self) -> str:
        """応答テキスト取得"""
        pass
    
    def process_request(self, input_text: str) -> str:
        """一連の処理実行"""
        try:
            if not self.login_check():
                raise Exception("ログインが必要です")
            
            if not self.input_text(input_text):
                raise Exception("テキスト入力に失敗しました")
            
            if not self.submit_request():
                raise Exception("リクエスト送信に失敗しました")
            
            if not self.wait_for_response():
                raise Exception("応答待機がタイムアウトしました")
            
            return self.get_response_text()
        except Exception as e:
            raise Exception(f"処理エラー: {str(e)}")
```

#### フェーズ2（2-3週間目）: AI別ハンドラー実装
**マイルストーン2.1**: ChatGPTハンドラー（優先実装）
```python
# src/automation/ai_handlers/chatgpt_handler.py - 実装内容
class ChatGPTHandler(BaseAIHandler):
    def __init__(self, driver, timeout: int = 30):
        super().__init__(driver, timeout)
        self.base_url = "https://chat.openai.com"
        
    def login_check(self) -> bool:
        """ChatGPTログイン状態確認"""
        self.driver.get(self.base_url)
        try:
            # チャット入力欄の存在確認
            chat_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='Message']"))
            )
            return True
        except:
            return False
    
    def input_text(self, text: str) -> bool:
        """テキスト入力"""
        try:
            chat_input = self.driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='Message']")
            chat_input.clear()
            chat_input.send_keys(text)
            return True
        except Exception as e:
            print(f"テキスト入力エラー: {e}")
            return False
    
    def submit_request(self) -> bool:
        """送信ボタンクリック"""
        try:
            send_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='send-button']")
            send_button.click()
            return True
        except Exception as e:
            print(f"送信エラー: {e}")
            return False
    
    def wait_for_response(self) -> bool:
        """応答完了待機"""
        try:
            # 送信ボタンが再度有効になるまで待機
            self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='send-button']"))
            )
            return True
        except:
            return False
    
    def get_response_text(self) -> str:
        """最新の応答テキスト取得"""
        try:
            messages = self.driver.find_elements(By.CSS_SELECTOR, "[data-message-author-role='assistant']")
            if messages:
                return messages[-1].text
            return ""
        except Exception as e:
            print(f"応答取得エラー: {e}")
            return ""
```

**マイルストーン2.2**: その他AIハンドラー
- Claude, Gemini, Genspark, Google AI Studio
- 各サイトのDOM構造を調査して同様に実装

**マイルストーン2.3**: リトライ・エラー管理
```python
# src/automation/retry_manager.py - 実装内容
class RetryManager:
    def __init__(self, max_retries: int = 5, delay: int = 10):
        self.max_retries = max_retries
        self.delay = delay
    
    def execute_with_retry(self, func, *args, **kwargs):
        """リトライ付き実行"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                print(f"リトライ {attempt + 1}/{self.max_retries}: {str(e)}")
                time.sleep(self.delay)
```

### 🔗 他担当との連携ポイント

#### 担当者Aとの連携
```python
# あなたが実装するインターフェース
def get_available_ais(self) -> Dict[str, List[str]]:
    """利用可能なAIとモデル一覧"""
    return {
        "chatgpt": ["gpt-4", "gpt-3.5-turbo"],
        "claude": ["claude-3-sonnet", "claude-3-haiku"],
        "gemini": ["gemini-pro", "gemini-pro-vision"]
    }

def start_automation(self, config: dict, progress_callback: callable):
    """自動化処理開始"""
    # progress_callback(current, total, message) で進捗報告
    pass
```

#### 担当者Bとの連携
```python
# データ受け渡しインターフェース
def process_task_batch(self, tasks: List[TaskRow]) -> List[TaskRow]:
    """タスク一覧を処理して結果を返す"""
    for task in tasks:
        try:
            handler = self.get_ai_handler(task.ai_service)
            result = handler.process_request(task.copy_text)
            task.result = result
            task.status = "処理済み"
        except Exception as e:
            task.error_message = str(e)
            task.status = "エラー"
    return tasks
```

### 📝 作業開始手順

#### 初日のSelenium環境構築
```bash
# 1. 作業ブランチ準備
git checkout feature/browser-automation
git pull origin develop
git merge develop

# 2. ディレクトリ作成
mkdir -p src/automation/ai_handlers
touch src/automation/__init__.py
touch src/automation/ai_handlers/__init__.py

# 3. Selenium動作確認
python -c "
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
print('Selenium環境確認中...')
driver = webdriver.Chrome(ChromeDriverManager().install())
driver.get('https://chat.openai.com')
print('ChatGPT接続確認完了')
driver.quit()
"
```

#### 各AIサイトのDOM調査
```python
# ai_site_research.py - DOM構造調査用
from selenium import webdriver
from selenium.webdriver.common.by import By

def research_chatgpt():
    driver = webdriver.Chrome()
    driver.get("https://chat.openai.com")
    
    # 手動でログイン後、以下を実行
    input("ログイン完了後、Enterを押してください...")
    
    # DOM構造確認
    elements = driver.find_elements(By.TAG_NAME, "textarea")
    for i, elem in enumerate(elements):
        print(f"Textarea {i}: {elem.get_attribute('placeholder')}")
    
    driver.quit()

# 各AIサイトで同様の調査を実施
```

### 🧪 テスト項目
- [ ] Chrome WebDriverが正常に起動する
- [ ] ChatGPTサイトにアクセスできる
- [ ] ログイン状態を正確に判定できる
- [ ] テキスト入力が正常に動作する
- [ ] 送信ボタンが正常にクリックできる
- [ ] 応答完了を正確に検知できる
- [ ] 応答テキストを正確に取得できる
- [ ] エラー時に適切にリトライされる
- [ ] 5回リトライ後に適切にエラー報告される

---

## 🔄 統合・テスト手順

### 週次統合スケジュール

#### 毎週金曜日: 統合日
```bash
# 各担当者の作業
# 1. 自分のブランチで最新作業をコミット
git add .
git commit -m "週次統合前の作業完了"
git push origin feature/[担当]

# 2. developブランチで統合
git checkout develop
git pull origin develop

# 3. 各ブランチを順次マージ
git merge feature/gui-components
git merge feature/sheets-integration  
git merge feature/browser-automation

# 4. 統合テスト実行
python main.py

# 5. 問題なければdevelopをプッシュ
git push origin develop
```

### 統合テストシナリオ

#### テストケース1: 基本動作確認
1. アプリケーション起動
2. スプレッドシートURL入力
3. シート選択
4. AI設定選択  
5. 処理開始
6. 結果確認

#### テストケース2: エラーハンドリング
1. 無効なスプレッドシートURL
2. アクセス権限なしスプレッドシート
3. AIサイトログイン未完了
4. ネットワークエラー
5. 各種タイムアウト

### デバッグ・トラブルシューティング

#### ログ確認方法
```bash
# アプリケーションログ
tail -f logs/app.log

# Seleniumデバッグ用
# headless=Falseでブラウザ表示して動作確認
```

#### よくある問題と解決法

**1. Google Sheets認証エラー**
```bash
# 解決手順
1. config/credentials.json の存在確認
2. サービスアカウントにスプレッドシート共有権限付与
3. Google Cloud Console でAPI有効化確認
```

**2. Selenium要素取得エラー**
```bash
# 解決手順  
1. 対象AIサイトのDOM構造変更確認
2. CSS Selector/XPath更新
3. 待機時間調整
```

**3. GUI表示エラー**
```bash
# 解決手順
1. tkinter インストール確認
2. Python バージョン確認（3.8以上）
3. 仮想環境確認
```

---

## 📞 コミュニケーション・報告ルール

### 日次報告（必須）
**毎日17:00までに以下を共有:**
- 今日完了した作業
- 明日の作業予定  
- 困っている点・質問
- 他担当への依頼事項

### 週次ミーティング（必須）
**毎週金曜日16:00-17:00:**
- 週の成果共有
- 統合テスト結果確認
- 来週の作業計画
- 課題・改善点討議

### 緊急時の連絡
**以下の場合は即座に連絡:**
- 3回以上同じエラーが解決できない
- 他担当の作業に影響する変更が必要
- 仕様について解釈が分からない
- スケジュールに大幅な遅れが発生

---

## ⚠️ 重要な注意事項

### セキュリティ
- **認証情報をGitにコミットしない**
- **API キーを直接コードに書かない**
- **テスト用アカウントを使用する**

### パフォーマンス
- **ブラウザは必要時のみ起動**
- **長時間処理時は進捗表示必須**
- **メモリリークに注意**

### エラーハンドリング
- **すべての例外をキャッチ**
- **ユーザーフレンドリーなエラーメッセージ**
- **詳細なログ出力**

---

## 🎯 最終目標の確認

### 完成時の動作
1. GUIアプリケーション起動
2. スプレッドシートURL・シート選択
3. AI・モデル選択
4. 自動処理開始
5. 進捗リアルタイム表示
6. 結果スプレッドシート反映
7. エラー時適切な対応・リトライ

### 完成基準
- [ ] 全機能が動作する
- [ ] エラーハンドリングが適切
- [ ] ログが詳細に出力される
- [ ] ドキュメントが整備されている
- [ ] テストが通る

**この指示書を基に、各担当者は自分の作業を確実に進めてください。質問がある場合は、遠慮なく相談してください。**