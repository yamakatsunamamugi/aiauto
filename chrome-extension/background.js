/**
 * AI自動化 バックグラウンドスクリプト
 * 担当者：AI-B
 */

class AIAutomationBackground {
    constructor() {
        this.activeRequests = new Map();
        this.setupMessageHandlers();
        this.setupStorageDefaults();
        console.log('AI自動化 バックグラウンドスクリプト初期化完了');
    }

    setupMessageHandlers() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'processAIRequest') {
                this.handleAIRequest(request, sender.tab)
                    .then(result => sendResponse(result))
                    .catch(error => sendResponse({
                        success: false,
                        error: error.message
                    }));
                return true;
            }

            if (request.action === 'getExtensionStatus') {
                sendResponse({
                    success: true,
                    status: 'active',
                    activeRequests: this.activeRequests.size
                });
                return true;
            }
        });
    }

    async setupStorageDefaults() {
        const defaults = {
            aiServices: {
                chatgpt: { enabled: true, defaultModel: 'gpt-4o' },
                claude: { enabled: true, defaultModel: 'claude-3.5-sonnet' },
                gemini: { enabled: true, defaultModel: 'gemini-1.5-pro' },
                genspark: { enabled: true, defaultModel: 'default' },
                google_ai_studio: { enabled: true, defaultModel: 'gemini-1.5-pro' }
            },
            preferences: {
                timeout: 120000, // 2分
                retryCount: 3,
                debugMode: false
            }
        };

        // 既存設定がない場合のみデフォルト値を設定
        const existing = await chrome.storage.local.get(['aiServices', 'preferences']);
        if (!existing.aiServices) {
            await chrome.storage.local.set({ aiServices: defaults.aiServices });
        }
        if (!existing.preferences) {
            await chrome.storage.local.set({ preferences: defaults.preferences });
        }
    }

    async handleAIRequest(request, tab) {
        const requestId = `${Date.now()}-${Math.random()}`;
        this.activeRequests.set(requestId, {
            ...request,
            startTime: Date.now(),
            tabId: tab?.id
        });

        try {
            console.log(`AI処理リクエスト開始: ${requestId}`);
            
            // リクエストをストレージに保存（content scriptが読み取り用）
            await chrome.storage.local.set({
                pendingRequest: {
                    ...request,
                    request_id: requestId
                }
            });

            // content scriptでの処理完了を待機
            const result = await this.waitForContentScriptResponse(requestId, tab);

            this.activeRequests.delete(requestId);
            console.log(`AI処理リクエスト完了: ${requestId}`);
            
            return result;

        } catch (error) {
            this.activeRequests.delete(requestId);
            console.error(`AI処理リクエストエラー: ${requestId}`, error);
            throw error;
        }
    }

    async waitForContentScriptResponse(requestId, tab, timeout = 120000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            try {
                // レスポンスをストレージから確認
                const result = await chrome.storage.local.get([`response_${requestId}`]);
                const response = result[`response_${requestId}`];
                
                if (response) {
                    // レスポンスを削除
                    await chrome.storage.local.remove([`response_${requestId}`]);
                    return response;
                }

                // タブが存在しない場合はエラー
                if (tab?.id) {
                    try {
                        await chrome.tabs.get(tab.id);
                    } catch (e) {
                        throw new Error('対象タブが閉じられました');
                    }
                }

                await this.sleep(1000);
            } catch (error) {
                if (error.message.includes('タブが閉じられました')) {
                    throw error;
                }
                console.warn('レスポンス確認中のエラー:', error);
                await this.sleep(1000);
            }
        }

        throw new Error('content scriptからの応答タイムアウト');
    }

    async getStorageData(key) {
        return new Promise((resolve) => {
            chrome.storage.local.get([key], (result) => {
                resolve(result[key]);
            });
        });
    }

    async setStorageData(key, value) {
        return new Promise((resolve) => {
            chrome.storage.local.set({[key]: value}, () => {
                resolve();
            });
        });
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // 統計情報取得
    getActiveRequestsCount() {
        return this.activeRequests.size;
    }

    getActiveRequests() {
        const requests = [];
        for (const [id, request] of this.activeRequests) {
            requests.push({
                id,
                ai_service: request.ai_service,
                startTime: request.startTime,
                duration: Date.now() - request.startTime
            });
        }
        return requests;
    }
}

// バックグラウンドスクリプト初期化
const aiAutomationBackground = new AIAutomationBackground();