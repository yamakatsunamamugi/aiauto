/**
 * AI自動化 コンテンツスクリプト
 * 担当者：AI-B
 */

class AIAutomationContent {
    constructor() {
        this.currentSite = this.detectAISite();
        this.config = this.getAIConfig(this.currentSite);
        this.isProcessing = false;
        this.setupMessageListener();
        this.setupFileWatcher();
        console.log(`AI自動化 コンテンツスクリプト初期化完了: ${this.currentSite}`);
    }

    detectAISite() {
        const hostname = window.location.hostname;
        const url = window.location.href;
        console.log('AI自動化: サイト検出中', { hostname, url });
        
        if (hostname.includes('openai.com') || hostname.includes('chatgpt.com')) {
            console.log('AI自動化: ChatGPTを検出');
            return 'chatgpt';
        }
        if (hostname.includes('claude.ai')) return 'claude';
        if (hostname.includes('gemini.google.com')) return 'gemini';
        if (hostname.includes('genspark.ai')) return 'genspark';
        if (hostname.includes('aistudio.google.com')) return 'google_ai_studio';
        
        console.log('AI自動化: 未対応サイト', hostname);
        return 'unknown';
    }

    getAIConfig(site) {
        const configs = {
            chatgpt: {
                modelSelector: 'button[data-testid="model-selector"], .model-selector-button',
                textarea: '#prompt-textarea, div[contenteditable="true"]',
                sendButton: 'button[data-testid="send-button"], button[aria-label="Send prompt"]',
                responseContainer: '[data-message-author-role="assistant"], .message-content',
                modelOptions: '[data-testid="model-option"], .model-option',
                stopButton: 'button[data-testid="stop-button"]',
                loadingIndicator: '.result-streaming, .generating',
                // 高度な設定
                settingsButton: 'button[aria-label="Settings"], .settings-button',
                deepThinkToggle: '[data-testid="deep-think"], .deep-think-toggle',
                customInstructions: '.custom-instructions, [data-testid="custom-instructions"]',
                temperatureSlider: '.temperature-slider, [data-testid="temperature"]'
            },
            claude: {
                modelSelector: '.model-selector-button, button[aria-label*="model"]',
                textarea: 'div[contenteditable="true"], .ProseMirror',
                sendButton: 'button[aria-label="Send Message"], button[type="submit"]',
                responseContainer: '.message-content, [data-testid="user-message"]',
                modelOptions: '.model-option, [role="menuitem"]',
                stopButton: 'button[aria-label="Stop generating"]',
                loadingIndicator: '.typing-indicator, .generating'
            },
            gemini: {
                modelSelector: '.model-selector, .model-dropdown-button',
                textarea: '.ql-editor, div[contenteditable="true"]',
                sendButton: '.send-button, button[aria-label="Send"]',
                responseContainer: '.response-container, .model-response',
                modelOptions: '.model-choice, .dropdown-item',
                stopButton: '.stop-button',
                loadingIndicator: '.loading, .thinking'
            },
            genspark: {
                modelSelector: '.model-selector, .ai-model-picker',
                textarea: 'textarea, div[contenteditable="true"]',
                sendButton: '.submit-btn, button[type="submit"]',
                responseContainer: '.response, .ai-response',
                modelOptions: '.model-item, .model-choice',
                stopButton: '.stop-btn',
                loadingIndicator: '.loading, .processing'
            },
            google_ai_studio: {
                modelSelector: '.model-picker, .model-selector',
                textarea: '.input-area, div[contenteditable="true"]',
                sendButton: '.send-button, button[aria-label="Send"]',
                responseContainer: '.output-text, .response-content',
                modelOptions: '.model-selection, [role="option"]',
                stopButton: '.stop-button',
                loadingIndicator: '.loading, .generating'
            }
        };
        return configs[site] || {};
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'processAI') {
                this.processTextWithAI(request.text, request.model)
                    .then(result => sendResponse(result))
                    .catch(error => sendResponse({
                        success: false,
                        error: error.message,
                        site: this.currentSite
                    }));
                return true; // 非同期レスポンスを有効化
            }
        });
    }

    setupFileWatcher() {
        // 一時ディレクトリを監視してリクエストファイルを処理
        setInterval(async () => {
            try {
                // ブラウザ内でファイルシステムアクセスはできないため、
                // 代替として chrome.storage を使用
                const result = await chrome.storage.local.get(['pendingRequest']);
                if (result.pendingRequest) {
                    const request = result.pendingRequest;
                    console.log('処理中のリクエストを検出:', request);
                    
                    // リクエストをクリア
                    await chrome.storage.local.remove(['pendingRequest']);
                    
                    // AI処理実行
                    const response = await this.processTextWithAI(
                        request.text, 
                        request.model
                    );
                    
                    // レスポンスを保存
                    await chrome.storage.local.set({
                        [`response_${request.request_id}`]: response
                    });
                }
            } catch (error) {
                console.error('ファイル監視エラー:', error);
            }
        }, 1000); // 1秒間隔で確認
    }

    async processTextWithAI(text, model) {
        if (this.isProcessing) {
            throw new Error('既に処理中です');
        }

        this.isProcessing = true;
        console.log(`AI処理開始: ${this.currentSite}, モデル: ${model}`);

        try {
            // 1. モデル選択
            if (model && this.config.modelSelector) {
                await this.selectModel(model);
            }

            // 2. テキスト入力
            await this.inputText(text);

            // 3. 送信
            await this.sendMessage();

            // 4. 応答待機
            const response = await this.waitForResponse();

            console.log(`AI処理完了: ${this.currentSite}`);
            return {
                success: true,
                result: response,
                site: this.currentSite,
                model: model,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            console.error(`AI処理エラー: ${this.currentSite}`, error);
            throw new Error(`${this.currentSite}処理エラー: ${error.message}`);
        } finally {
            this.isProcessing = false;
        }
    }

    async selectModel(model) {
        console.log(`モデル選択開始: ${model}`);
        
        const modelSelector = document.querySelector(this.config.modelSelector);
        if (!modelSelector) {
            console.warn('モデル選択ボタンが見つかりません');
            return;
        }

        // モデル選択ボタンをクリック
        modelSelector.click();
        await this.sleep(1500);

        // モデル選択（サイト別処理）
        const modelOptions = document.querySelectorAll(this.config.modelOptions);
        console.log(`利用可能なモデル数: ${modelOptions.length}`);
        
        for (const option of modelOptions) {
            const optionText = option.textContent.toLowerCase();
            const targetModel = model.toLowerCase();
            
            if (optionText.includes(targetModel) || 
                targetModel.includes(optionText)) {
                console.log(`モデルを選択: ${option.textContent}`);
                option.click();
                await this.sleep(500);
                return;
            }
        }
        
        console.warn(`指定されたモデルが見つかりません: ${model}`);
    }

    async inputText(text) {
        console.log(`テキスト入力開始: ${text.length}文字`);
        
        const textarea = document.querySelector(this.config.textarea);
        if (!textarea) {
            throw new Error('テキスト入力エリアが見つかりません');
        }

        // 既存のテキストをクリア
        if (textarea.contentEditable === 'true') {
            textarea.textContent = '';
            await this.sleep(200);
        } else {
            textarea.value = '';
        }

        // テキスト入力（contenteditable対応）
        if (textarea.contentEditable === 'true') {
            // 段階的にテキストを入力（人間らしい入力）
            const chunks = this.splitTextIntoChunks(text, 100);
            for (const chunk of chunks) {
                textarea.textContent += chunk;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                await this.sleep(50);
            }
        } else {
            textarea.value = text;
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        }

        await this.sleep(500);
        console.log('テキスト入力完了');
    }

    splitTextIntoChunks(text, chunkSize) {
        const chunks = [];
        for (let i = 0; i < text.length; i += chunkSize) {
            chunks.push(text.slice(i, i + chunkSize));
        }
        return chunks;
    }

    async sendMessage() {
        console.log('メッセージ送信開始');
        
        const sendButton = document.querySelector(this.config.sendButton);
        if (!sendButton) {
            throw new Error('送信ボタンが見つかりません');
        }

        // 送信ボタンが有効になるまで待機
        let attempts = 0;
        while (sendButton.disabled && attempts < 10) {
            await this.sleep(500);
            attempts++;
        }

        sendButton.click();
        await this.sleep(1000);
        console.log('メッセージ送信完了');
    }

    async waitForResponse(maxWaitTime = 120000) { // 2分に延長
        console.log('応答待機開始');
        const startTime = Date.now();
        let lastResponseLength = 0;
        let stableCount = 0;

        while (Date.now() - startTime < maxWaitTime) {
            try {
                // 停止ボタンの存在確認（生成中の indicator）
                const stopButton = document.querySelector(this.config.stopButton);
                const loadingIndicator = document.querySelector(this.config.loadingIndicator);
                
                if (stopButton || loadingIndicator) {
                    console.log('まだ生成中...');
                    await this.sleep(2000);
                    continue;
                }

                const responseElements = document.querySelectorAll(this.config.responseContainer);

                if (responseElements.length > 0) {
                    const latestResponse = responseElements[responseElements.length - 1];
                    const responseText = latestResponse.textContent.trim();

                    if (responseText && responseText.length > 10) {
                        // 応答の長さが安定しているかチェック
                        if (responseText.length === lastResponseLength) {
                            stableCount++;
                            if (stableCount >= 3) { // 3回連続で同じ長さなら完了
                                console.log(`応答取得完了: ${responseText.length}文字`);
                                return responseText;
                            }
                        } else {
                            stableCount = 0;
                            lastResponseLength = responseText.length;
                        }
                    }
                }

                await this.sleep(1000);
            } catch (error) {
                console.error('応答待機中のエラー:', error);
                await this.sleep(1000);
            }
        }

        throw new Error('応答タイムアウト');
    }

    async isResponseComplete(responseElement) {
        // 生成中インジケータの確認
        const loadingIndicators = [
            '.typing-indicator',
            '.generating',
            '.loading',
            '[data-testid="loading"]',
            '.result-streaming'
        ];

        for (const indicator of loadingIndicators) {
            if (document.querySelector(indicator)) {
                return false;
            }
        }

        // 停止ボタンの存在確認
        if (document.querySelector(this.config.stopButton)) {
            return false;
        }

        return true;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// コンテンツスクリプト初期化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new AIAutomationContent();
    });
} else {
    new AIAutomationContent();
}