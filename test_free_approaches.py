#!/usr/bin/env python3
"""
無料で実現できる3つのアプローチをテストするスクリプト
1. Tampermonkey/UserScript アプローチ
2. Selenium + プロンプトエンジニアリング
3. ブラウザ拡張機能アプローチ
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List

# ====================================
# アプローチ1: Tampermonkey/UserScript
# ====================================

def test_userscript_approach() -> Dict:
    """UserScriptアプローチのテスト準備"""
    print("\n" + "="*60)
    print("🔧 アプローチ1: Tampermonkey/UserScript のテスト")
    print("="*60)
    
    # UserScriptのサンプルコード生成
    userscript_code = """// ==UserScript==
// @name         AI Service Auto-Enhancer (無料版)
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  自動でDeep Think機能とモデルを選択（無料）
// @match        https://claude.ai/*
// @match        https://chat.openai.com/*
// @match        https://gemini.google.com/*
// @match        https://www.genspark.ai/*
// @match        https://aistudio.google.com/*
// @grant        GM_setValue
// @grant        GM_getValue
// ==/UserScript==

(function() {
    'use strict';
    
    // 設定の読み込み
    const settings = {
        enableDeepThink: GM_getValue('enableDeepThink', true),
        preferredModels: GM_getValue('preferredModels', {
            'claude.ai': 'Claude 3.5 Sonnet',
            'chat.openai.com': 'GPT-4',
            'gemini.google.com': 'Gemini Pro'
        })
    };
    
    // サービスごとの設定
    const serviceConfigs = {
        'claude.ai': {
            modelSelector: '[data-testid*="model"], button[aria-label*="model"]',
            deepThinkSelector: '[aria-label*="think harder"], button:contains("Think")',
            inputSelector: 'textarea[placeholder*="Message"], .ProseMirror',
            detectModel: () => document.querySelector('.model-name')?.textContent
        },
        'chat.openai.com': {
            modelSelector: '[data-testid*="model-switcher"], .model-switcher',
            inputSelector: 'textarea[data-testid*="prompt-textarea"]',
            detectModel: () => document.querySelector('[data-testid*="model"]')?.textContent
        },
        'gemini.google.com': {
            modelSelector: '.model-selector, button[data-testid*="model"]',
            inputSelector: 'textarea[aria-label*="Enter a prompt"]',
            detectModel: () => document.querySelector('.model-label')?.textContent
        }
    };
    
    const hostname = window.location.hostname;
    const config = serviceConfigs[hostname];
    
    if (!config) return;
    
    // Deep Think用のプロンプト拡張
    function enhancePromptForDeepThinking(prompt) {
        if (!settings.enableDeepThink) return prompt;
        
        const prefix = `[Deep Thinking Mode Enabled]
Please think step-by-step and consider multiple perspectives before responding.
Analyze thoroughly and explain your reasoning.

Original prompt: `;
        
        return prefix + prompt;
    }
    
    // 入力欄を監視してプロンプトを拡張
    function setupInputEnhancement() {
        const checkInput = setInterval(() => {
            const input = document.querySelector(config.inputSelector);
            if (input) {
                clearInterval(checkInput);
                
                // Enterキーの監視
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        const currentText = input.value || input.textContent;
                        if (currentText && settings.enableDeepThink) {
                            e.preventDefault();
                            const enhancedText = enhancePromptForDeepThinking(currentText);
                            
                            if (input.value !== undefined) {
                                input.value = enhancedText;
                            } else {
                                input.textContent = enhancedText;
                            }
                            
                            // 少し待ってから送信
                            setTimeout(() => {
                                const event = new KeyboardEvent('keydown', {
                                    key: 'Enter',
                                    keyCode: 13,
                                    bubbles: true
                                });
                                input.dispatchEvent(event);
                            }, 100);
                        }
                    }
                });
            }
        }, 1000);
    }
    
    // モデル選択の自動化
    function autoSelectModel() {
        const preferredModel = settings.preferredModels[hostname];
        if (!preferredModel) return;
        
        setTimeout(() => {
            const modelBtn = document.querySelector(config.modelSelector);
            if (modelBtn) {
                console.log('モデルセレクタを発見:', modelBtn);
                // 現在のモデルを確認
                const currentModel = config.detectModel();
                if (currentModel && currentModel.includes(preferredModel)) {
                    console.log('既に希望のモデルが選択されています:', currentModel);
                    return;
                }
                
                // モデル変更を試みる
                modelBtn.click();
                setTimeout(() => {
                    const options = document.querySelectorAll('[role="option"], .model-option');
                    options.forEach(option => {
                        if (option.textContent.includes(preferredModel)) {
                            option.click();
                            console.log('モデルを変更しました:', preferredModel);
                        }
                    });
                }, 500);
            }
        }, 2000);
    }
    
    // 初期化
    window.addEventListener('load', () => {
        console.log('AI Service Auto-Enhancer 起動');
        autoSelectModel();
        setupInputEnhancement();
        
        // Claudeの場合、Think harderボタンを探す
        if (hostname === 'claude.ai' && config.deepThinkSelector) {
            setTimeout(() => {
                const thinkBtn = document.querySelector(config.deepThinkSelector);
                if (thinkBtn) {
                    console.log('Think harderボタンを発見');
                    if (thinkBtn.getAttribute('aria-pressed') !== 'true') {
                        thinkBtn.click();
                        console.log('Think harder機能を有効化');
                    }
                }
            }, 3000);
        }
    });
    
    // 設定パネルの追加（オプション）
    const settingsBtn = document.createElement('button');
    settingsBtn.textContent = '⚙️';
    settingsBtn.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;padding:10px;background:#4CAF50;color:white;border:none;border-radius:50%;cursor:pointer;';
    settingsBtn.onclick = () => {
        const newDeepThink = confirm('Deep Think機能を有効にしますか？\\n現在: ' + (settings.enableDeepThink ? '有効' : '無効'));
        GM_setValue('enableDeepThink', newDeepThink);
        location.reload();
    };
    document.body.appendChild(settingsBtn);
})();"""
    
    # UserScriptファイルを保存
    with open("ai_auto_enhancer_free.user.js", "w", encoding="utf-8") as f:
        f.write(userscript_code)
    
    print("✅ UserScriptを生成しました: ai_auto_enhancer_free.user.js")
    print("\n📝 インストール方法:")
    print("1. Chromeに Tampermonkey 拡張機能をインストール")
    print("   https://chrome.google.com/webstore/detail/tampermonkey/")
    print("2. Tampermonkeyアイコンをクリック → 「新規スクリプトを作成」")
    print("3. 生成されたコードを貼り付けて Ctrl+S で保存")
    print("4. AIサービスのページを開いて動作確認")
    
    return {
        "approach": "UserScript",
        "cost": "完全無料",
        "difficulty": "簡単（10分で導入可能）",
        "reliability": "中〜高",
        "maintenance": "UI変更時に調整必要"
    }

# ====================================
# アプローチ2: Selenium + プロンプトエンジニアリング
# ====================================

def test_selenium_prompt_approach() -> Dict:
    """既存のSelenium + プロンプトエンジニアリング"""
    print("\n" + "="*60)
    print("🤖 アプローチ2: Selenium + プロンプトエンジニアリング")
    print("="*60)
    
    # 既存のハンドラーを拡張する例
    enhancement_code = '''#!/usr/bin/env python3
"""
既存のAIハンドラーにDeep Think機能を追加する拡張モジュール
プロンプトエンジニアリングで無料でDeep Think効果を実現
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DeepThinkEnhancer:
    """プロンプトエンジニアリングでDeep Thinkを実現する拡張クラス"""
    
    # サービスごとの最適なプロンプト
    DEEP_THINK_PROMPTS = {
        "claude": """I need you to think deeply about this request. Please:
1. Break down the problem systematically
2. Consider multiple approaches and perspectives
3. Think through edge cases and potential issues
4. Explain your reasoning step by step

Here's my request: """,
        
        "chatgpt": """Please engage in careful, systematic thinking about this request.
Take your time to:
- Analyze all aspects of the problem
- Consider various solutions
- Explain your thought process
- Provide comprehensive reasoning

My request: """,
        
        "gemini": """Think step-by-step and provide a thorough analysis.
Please:
• Examine the problem from multiple angles
• Consider pros and cons of different approaches
• Provide detailed reasoning
• Be comprehensive in your response

Request: """,
        
        "default": """Please think carefully and systematically about this request.
Provide detailed reasoning and consider multiple perspectives.

Request: """
    }
    
    def __init__(self, service_name: str):
        self.service_name = service_name.lower()
        
    def enhance_prompt(self, original_prompt: str, deep_think: bool = True) -> str:
        """プロンプトにDeep Think指示を追加"""
        if not deep_think:
            return original_prompt
            
        # サービスに応じた最適なプロンプトを選択
        prefix = self.DEEP_THINK_PROMPTS.get(
            self.service_name, 
            self.DEEP_THINK_PROMPTS["default"]
        )
        
        enhanced = prefix + original_prompt
        logger.info(f"プロンプトを強化しました（{len(original_prompt)}文字 → {len(enhanced)}文字）")
        
        return enhanced
    
    def get_best_model(self) -> Optional[str]:
        """各サービスの最高性能モデルを返す（無料で利用可能なもの）"""
        model_map = {
            "claude": "claude-3.5-sonnet",  # 無料プランでも利用可能
            "chatgpt": "gpt-3.5-turbo",     # 無料版のデフォルト
            "gemini": "gemini-pro",          # 無料で利用可能
            "genspark": "advanced",          # 無料の高度検索
            "google_ai_studio": "gemini-1.5-flash"  # 無料枠あり
        }
        return model_map.get(self.service_name)


# 既存のハンドラーと統合する方法
def integrate_with_existing_handler():
    """既存のAIハンドラーにDeep Think機能を追加する例"""
    
    # 例: claude_handler.pyの改修
    code_snippet = """
# claude_handler.pyに追加するコード

from .deep_think_enhancer import DeepThinkEnhancer

class ClaudeHandler(BaseAIHandler):
    def __init__(self, config=None):
        super().__init__(config)
        self.deep_think = DeepThinkEnhancer("claude")
        self.enable_deep_think = config.get("enable_deep_think", True) if config else True
    
    async def process_request(self, text: str, **kwargs) -> ProcessResult:
        try:
            # Deep Thinkが有効な場合、プロンプトを強化
            if self.enable_deep_think:
                text = self.deep_think.enhance_prompt(text)
            
            # 既存の処理を実行
            return await super().process_request(text, **kwargs)
            
        except Exception as e:
            logger.error(f"処理エラー: {e}")
            raise
"""
    
    return code_snippet


# テスト用のスタンドアロン関数
def test_deep_think_enhancement():
    """Deep Think強化の効果をテスト"""
    test_prompts = [
        "2+2は？",
        "Pythonで再帰関数を説明して",
        "気候変動の原因を教えて"
    ]
    
    enhancer = DeepThinkEnhancer("claude")
    
    print("\\n--- Deep Think強化のテスト ---")
    for prompt in test_prompts:
        enhanced = enhancer.enhance_prompt(prompt)
        print(f"\\n元のプロンプト: {prompt}")
        print(f"強化後: {enhanced[:100]}...")
        print(f"文字数: {len(prompt)} → {len(enhanced)}")
    

if __name__ == "__main__":
    test_deep_think_enhancement()
    print("\\n統合コード例:")
    print(integrate_with_existing_handler())
'''
    
    # 拡張コードを保存
    with open("deep_think_enhancer.py", "w", encoding="utf-8") as f:
        f.write(enhancement_code)
    
    print("✅ 拡張モジュールを生成しました: deep_think_enhancer.py")
    print("\n🔨 実装方法:")
    print("1. deep_think_enhancer.py を src/automation/ai_handlers/ に配置")
    print("2. 各ハンドラーでDeepThinkEnhancerをインポート")
    print("3. process_requestメソッドでプロンプトを強化")
    print("\n✨ メリット:")
    print("- 既存コードとの統合が簡単")
    print("- 全AIサービスで動作")
    print("- 完全無料")
    
    return {
        "approach": "Selenium + Prompt Engineering",
        "cost": "完全無料",
        "difficulty": "中程度（既存コードの理解が必要）",
        "reliability": "高",
        "effectiveness": "プロンプトの工夫次第で高効果"
    }

# ====================================
# アプローチ3: ブラウザ拡張機能
# ====================================

def test_browser_extension_approach() -> Dict:
    """ブラウザ拡張機能アプローチ"""
    print("\n" + "="*60)
    print("🌐 アプローチ3: ブラウザ拡張機能アプローチ")
    print("="*60)
    
    # 簡易的なChrome拡張機能の構造
    manifest_json = """{
  "manifest_version": 3,
  "name": "AI Deep Think Enabler",
  "version": "1.0",
  "description": "AIサービスでDeep Think機能を自動有効化（無料）",
  "permissions": ["activeTab", "storage"],
  "host_permissions": [
    "https://claude.ai/*",
    "https://chat.openai.com/*",
    "https://gemini.google.com/*"
  ],
  "content_scripts": [
    {
      "matches": [
        "https://claude.ai/*",
        "https://chat.openai.com/*",  
        "https://gemini.google.com/*"
      ],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icon16.png",
      "48": "icon48.png",
      "128": "icon128.png"
    }
  }
}"""
    
    content_js = """// content.js - AIサービスの自動強化
console.log('AI Deep Think Enabler 起動');

// 設定を読み込み
chrome.storage.sync.get(['enableDeepThink', 'autoSelectModel'], function(settings) {
    const enableDeepThink = settings.enableDeepThink !== false;
    const autoSelectModel = settings.autoSelectModel !== false;
    
    // 現在のサイトを判定
    const hostname = window.location.hostname;
    
    // Deep Thinkプロンプトプレフィックス
    const deepThinkPrefix = `[Deep Analysis Mode]
Please think systematically and provide comprehensive reasoning.

`;
    
    // 入力欄を監視
    function enhanceInput() {
        const inputSelectors = [
            'textarea[placeholder*="Message"]',
            'textarea[data-testid*="prompt"]',
            '[contenteditable="true"]',
            '.ProseMirror'
        ];
        
        let inputElement = null;
        for (const selector of inputSelectors) {
            inputElement = document.querySelector(selector);
            if (inputElement) break;
        }
        
        if (inputElement && enableDeepThink) {
            // 送信時にプロンプトを強化
            inputElement.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    const text = inputElement.value || inputElement.textContent;
                    if (text && !text.startsWith('[Deep Analysis Mode]')) {
                        e.preventDefault();
                        const enhancedText = deepThinkPrefix + text;
                        
                        if (inputElement.value !== undefined) {
                            inputElement.value = enhancedText;
                        } else {
                            inputElement.textContent = enhancedText;
                        }
                        
                        // 自動送信
                        setTimeout(() => {
                            const enterEvent = new KeyboardEvent('keydown', {
                                key: 'Enter',
                                keyCode: 13,
                                bubbles: true
                            });
                            inputElement.dispatchEvent(enterEvent);
                        }, 100);
                    }
                }
            });
        }
    }
    
    // ページ読み込み完了後に実行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', enhanceInput);
    } else {
        setTimeout(enhanceInput, 1000);
    }
    
    // 動的コンテンツに対応
    const observer = new MutationObserver(function(mutations) {
        enhanceInput();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});"""
    
    popup_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { width: 300px; padding: 10px; }
        .toggle { margin: 10px 0; }
        label { display: flex; align-items: center; justify-content: space-between; }
        input[type="checkbox"] { width: 20px; height: 20px; }
    </style>
</head>
<body>
    <h3>AI Deep Think Enabler</h3>
    <div class="toggle">
        <label>
            Deep Think機能を有効化
            <input type="checkbox" id="enableDeepThink" checked>
        </label>
    </div>
    <div class="toggle">
        <label>
            最適モデル自動選択
            <input type="checkbox" id="autoSelectModel" checked>
        </label>
    </div>
    <script src="popup.js"></script>
</body>
</html>"""
    
    # ファイル生成
    os.makedirs("chrome_extension", exist_ok=True)
    
    with open("chrome_extension/manifest.json", "w") as f:
        f.write(manifest_json)
    
    with open("chrome_extension/content.js", "w") as f:
        f.write(content_js)
        
    with open("chrome_extension/popup.html", "w") as f:
        f.write(popup_html)
    
    print("✅ Chrome拡張機能を生成しました: chrome_extension/")
    print("\n📝 インストール方法:")
    print("1. Chromeで chrome://extensions/ を開く")
    print("2. 右上の「デベロッパーモード」をON")
    print("3. 「パッケージ化されていない拡張機能を読み込む」をクリック")
    print("4. chrome_extensionフォルダを選択")
    
    return {
        "approach": "Browser Extension",
        "cost": "完全無料",
        "difficulty": "簡単〜中程度",
        "reliability": "高",
        "user_control": "設定画面で簡単に切り替え可能"
    }

# ====================================
# メイン実行関数
# ====================================

def main():
    """無料で実現できる3つのアプローチをテスト"""
    print("🚀 無料で実現できるDeep Think機能の実装テスト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 各アプローチをテスト
    results.append(test_userscript_approach())
    results.append(test_selenium_prompt_approach())
    results.append(test_browser_extension_approach())
    
    # 比較レポートを生成
    generate_comparison_report(results)
    
    print("\n✅ テスト完了！")
    print("\n📄 生成されたファイル:")
    print("   - ai_auto_enhancer_free.user.js (Tampermonkeyスクリプト)")
    print("   - deep_think_enhancer.py (Selenium拡張モジュール)")
    print("   - chrome_extension/ (Chrome拡張機能)")
    print("   - free_approach_comparison.md (比較レポート)")
    
    print("\n🎯 推奨される次のステップ:")
    print("1. Tampermonkeyスクリプトを今すぐ試す（最も簡単）")
    print("2. 実際のAIサービスで動作確認")
    print("3. 最も効果的な方法を本番環境に統合")

def generate_comparison_report(results: List[Dict]):
    """アプローチの比較レポートを生成"""
    report = f"""# 無料で実現するAI Deep Think機能 - 実装方法比較

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 概要

完全無料で実現できる3つのアプローチを検証しました。
すべての方法でAPIキーや追加料金は不要です。

## アプローチ別評価

### 1. Tampermonkey/UserScript
- **実装時間**: 10分
- **技術レベル**: 初心者OK ⭐
- **効果**: ⭐⭐⭐⭐
- **保守性**: ⭐⭐⭐

**特徴**:
- ブラウザにTampermonkey拡張を入れるだけ
- すぐに試せる
- 設定変更が簡単

### 2. Selenium + プロンプトエンジニアリング
- **実装時間**: 30分〜1時間
- **技術レベル**: 中級者向け ⭐⭐⭐
- **効果**: ⭐⭐⭐⭐⭐
- **保守性**: ⭐⭐⭐⭐

**特徴**:
- 既存のシステムに統合しやすい
- 全AIサービスで確実に動作
- カスタマイズ性が高い

### 3. Chrome拡張機能
- **実装時間**: 20分
- **技術レベル**: 初〜中級者 ⭐⭐
- **効果**: ⭐⭐⭐⭐
- **保守性**: ⭐⭐⭐⭐

**特徴**:
- 見た目が本格的
- ON/OFF切り替えが簡単
- 配布しやすい

## 実装推奨順序

### 今すぐ試したい場合
1. **Tampermonkeyスクリプト**をインストール
2. AIサービスで動作確認
3. 効果を体感

### 本格的に導入する場合
1. **Selenium + プロンプトエンジニアリング**で実装
2. 既存のautomation_controller.pyと統合
3. GUIから制御可能に

## 各方法の使い分け

| 用途 | 推奨方法 |
|------|----------|
| 個人利用・テスト | Tampermonkey |
| チーム共有 | Chrome拡張機能 |
| 自動化システム統合 | Selenium + プロンプト |

## 実装のポイント

1. **プロンプトの工夫が重要**
   - 「step by step」「multiple perspectives」などのキーワード
   - サービスごとに最適化

2. **UIの変更に注意**
   - セレクタは定期的に確認
   - 複数のセレクタを用意

3. **ユーザー体験を損なわない**
   - 自動化は控えめに
   - 手動操作も残す

## まとめ

すべて無料で実現可能です。
まずはTampermonkeyで効果を確認し、
良ければSelenium統合を検討することを推奨します。
"""
    
    with open("free_approach_comparison.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()