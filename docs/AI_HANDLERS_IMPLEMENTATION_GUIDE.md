# AI ハンドラー実装指示書

## 概要
残りのAIサービス（Claude、Gemini、Genspark、Google AI Studio）のハンドラー実装を行います。
ChatGPTハンドラーをベースとして、各サービス固有の操作に対応した実装を行ってください。

## 前提条件
- Playwrightの基本知識
- 非同期プログラミング（async/await）の理解
- 各AIサービスのDOM構造調査経験

## 実装対象ファイル

### 1. Claude ハンドラー
**ファイル**: `src/automation/ai_handlers/claude_handler.py`
**URL**: https://claude.ai

### 2. Gemini ハンドラー  
**ファイル**: `src/automation/ai_handlers/gemini_handler.py`
**URL**: https://gemini.google.com

### 3. Genspark ハンドラー
**ファイル**: `src/automation/ai_handlers/genspark_handler.py`
**URL**: https://www.genspark.ai

### 4. Google AI Studio ハンドラー
**ファイル**: `src/automation/ai_handlers/google_ai_studio_handler.py`
**URL**: https://aistudio.google.com

## 実装手順

### Step 1: DOM構造調査
各AIサービスにアクセスし、以下の要素を特定してください：

1. **ログイン状態確認要素**
   - チャット入力欄の存在
   - ログインボタンの有無
   - ユーザー情報表示

2. **入力欄のセレクター**
   - テキスト入力エリア
   - プレースホルダーテキスト
   - data-testid属性

3. **送信ボタンのセレクター**  
   - 送信ボタン
   - aria-label属性
   - アイコンボタンの場合

4. **応答エリアのセレクター**
   - AI応答が表示される領域
   - メッセージコンテナ
   - ストリーミング表示エリア

### Step 2: 基本テンプレート
```python
\"\"\"
[サービス名]ハンドラー

[サービス名] ([URL]) の自動操作を実装
手動ログイン前提でセッション状態を確認し、安全な自動化を提供
\"\"\"

import asyncio
from typing import Optional, List
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.logger import logger
from .base_handler import BaseAIHandler, SessionExpiredError


class [ServiceName]Handler(BaseAIHandler):
    \"\"\"[サービス名]自動操作ハンドラー\"\"\"
    
    SERVICE_NAME = "[サービス名]"
    SERVICE_URL = "[URL]"
    
    def __init__(self, page: Page, config: Optional[dict] = None):
        super().__init__(page, config)
        logger.info(f"{self.SERVICE_NAME}ハンドラーを初期化しました")

    async def login_check(self) -> bool:
        # 実装必要
        pass

    async def get_input_selector(self) -> str:
        # 実装必要
        pass

    async def get_submit_selector(self) -> str:
        # 実装必要
        pass

    async def get_response_selector(self) -> str:
        # 実装必要
        pass

    async def wait_for_response_complete(self) -> bool:
        # 実装必要
        pass
```

### Step 3: 各メソッドの実装詳細

#### login_check() メソッド
```python
async def login_check(self) -> bool:
    try:
        # サービスURLにアクセス
        current_url = self.page.url
        if "[ドメイン]" not in current_url:
            await self.page.goto(self.SERVICE_URL, wait_until="networkidle")
            await asyncio.sleep(3)
        
        # ログイン状態確認（複数パターン）
        login_indicators = [
            "[主要な入力欄セレクター]",
            "[代替セレクター1]",
            "[代替セレクター2]"
        ]
        
        for indicator in login_indicators:
            try:
                element = await self.page.wait_for_selector(indicator, timeout=5000)
                if element:
                    logger.info(f"{self.SERVICE_NAME}: ログイン状態を確認しました")
                    return True
            except PlaywrightTimeoutError:
                continue
        
        return False
        
    except Exception as e:
        logger.error(f"{self.SERVICE_NAME}: ログイン状態確認でエラー: {e}")
        return False
```

#### get_input_selector() メソッド
```python
async def get_input_selector(self) -> str:
    selectors = [
        "[最も確実なセレクター]",
        "[代替セレクター1]",
        "[代替セレクター2]"
    ]
    
    for selector in selectors:
        try:
            element = await self.page.wait_for_selector(selector, timeout=3000)
            if element:
                logger.debug(f"{self.SERVICE_NAME}: 入力欄を発見: {selector}")
                return selector
        except PlaywrightTimeoutError:
            continue
    
    return "[デフォルトセレクター]"
```

#### wait_for_response_complete() メソッド
```python
async def wait_for_response_complete(self) -> bool:
    try:
        self._log_operation("応答完了待機開始")
        
        # サービス固有の応答完了検知ロジック
        # 例: 送信ボタンが再度有効になる
        # 例: ストリーミングインジケーターが消える
        # 例: 特定の要素が表示される
        
        max_wait_time = self.wait_timeout // 1000
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # 応答完了の確認ロジック
            # サービス固有の実装が必要
            
            elapsed_time = asyncio.get_event_loop().time() - start_time
            if elapsed_time > max_wait_time:
                logger.warning(f"{self.SERVICE_NAME}: 応答完了の待機がタイムアウトしました")
                return False
            
            await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"{self.SERVICE_NAME}: 応答完了待機でエラー: {e}")
        return False
```

## 各サービス固有の注意点

### Claude (claude.ai)
- Anthropic社のサービス
- ストリーミング応答あり
- モデル選択機能あり
- 応答完了検知: ストリーミング終了のチェック

### Gemini (gemini.google.com)  
- Google製サービス
- Googleアカウントでのログイン
- 応答完了検知: 送信ボタンの状態変化

### Genspark (genspark.ai)
- 新しいAIサーチエンジン
- 特殊なUI/UX
- DOM構造の詳細調査が必要

### Google AI Studio (aistudio.google.com)
- Google製の開発者向けツール
- 複雑なインターフェース
- 複数のモデル選択肢

## テスト方法

### 1. 基本動作テスト
```python
# テスト用スクリプト例
async def test_handler():
    from src.automation.browser_manager import BrowserManager
    from src.automation.ai_handlers.[handler_name] import [HandlerClass]
    
    async with BrowserManager() as browser:
        page = await browser.create_new_page()
        handler = [HandlerClass](page)
        
        # ログイン状態確認
        is_logged_in = await handler.login_check()
        print(f"ログイン状態: {is_logged_in}")
        
        if is_logged_in:
            # テキスト処理
            response = await handler.process_request("こんにちは")
            print(f"応答: {response}")
```

### 2. 必須テスト項目
- [ ] ログイン状態確認
- [ ] テキスト入力
- [ ] 送信ボタンクリック
- [ ] 応答完了待機
- [ ] 応答テキスト抽出
- [ ] エラーハンドリング

## 注意事項

### セキュリティ・コンプライアンス
- 各サービスの利用規約を遵守
- 過度なリクエスト頻度を避ける
- ユーザーデータの適切な取り扱い

### パフォーマンス
- 適切な待機時間の設定
- リソース使用量の最適化
- メモリリークの防止

### エラーハンドリング
- ネットワークエラーへの対応
- DOM変更への適応
- 詳細なログ出力

## 完成条件
1. 全ての抽象メソッドが実装済み
2. 基本動作テストが成功
3. エラーケースでの適切な例外処理
4. 詳細なログ出力の実装
5. コードコメントの充実

## 提出物
1. 実装したハンドラーファイル
2. テスト結果レポート
3. 発見した問題点・改善提案
4. DOM構造調査結果（セレクター一覧）

## サポート
実装中に問題が発生した場合は、以下の情報と共にご連絡ください：
- エラーメッセージ
- 問題が発生した手順
- ブラウザのスクリーンショット
- 該当サービスのDOM構造

この指示書に従って実装することで、一貫性のある高品質なAIハンドラーを作成できます。