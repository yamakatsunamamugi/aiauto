/**
 * AI自動化 ポップアップスクリプト
 * 担当者：AI-B
 */

class AIAutomationPopup {
    constructor() {
        this.setupEventListeners();
        this.updateStatus();
        this.startPeriodicUpdate();
    }

    setupEventListeners() {
        // 接続テストボタン
        document.getElementById('test-button').addEventListener('click', () => {
            this.runConnectionTest();
        });

        // ストレージクリアボタン
        document.getElementById('clear-storage').addEventListener('click', () => {
            this.clearStorage();
        });
    }

    async updateStatus() {
        try {
            // 拡張機能の状態確認
            const response = await chrome.runtime.sendMessage({
                action: 'getExtensionStatus'
            });

            if (response.success) {
                this.setStatus('active', '動作中');
                document.getElementById('active-requests').textContent = response.activeRequests || 0;
            } else {
                this.setStatus('error', 'エラー');
            }

            // 現在のタブ情報取得
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tabs.length > 0) {
                const currentTab = tabs[0];
                const site = this.detectSiteFromUrl(currentTab.url);
                document.getElementById('current-site').textContent = site;
                
                // サイト別ステータス更新
                this.updateSiteStatus(site);
            }

            // ストレージ情報取得
            const storageData = await chrome.storage.local.get(['totalProcessed']);
            document.getElementById('total-processed').textContent = storageData.totalProcessed || 0;

        } catch (error) {
            console.error('ステータス更新エラー:', error);
            this.setStatus('error', 'エラー');
        }
    }

    detectSiteFromUrl(url) {
        if (!url) return '不明';
        
        if (url.includes('openai.com')) return 'ChatGPT';
        if (url.includes('claude.ai')) return 'Claude';
        if (url.includes('gemini.google.com')) return 'Gemini';
        if (url.includes('genspark.ai')) return 'Genspark';
        if (url.includes('aistudio.google.com')) return 'Google AI Studio';
        
        return 'その他';
    }

    updateSiteStatus(currentSite) {
        // 全てのサービスステータスをリセット
        const statusElements = document.querySelectorAll('.service-status');
        statusElements.forEach(el => {
            el.textContent = '-';
            el.className = 'service-status';
        });

        // 現在のサイトを有効表示
        const siteMapping = {
            'ChatGPT': 'chatgpt',
            'Claude': 'claude',
            'Gemini': 'gemini',
            'Genspark': 'genspark',
            'Google AI Studio': 'google_ai_studio'
        };

        const serviceKey = siteMapping[currentSite];
        if (serviceKey) {
            const statusEl = document.querySelector(`[data-service="${serviceKey}"]`);
            if (statusEl) {
                statusEl.textContent = '✓ アクティブ';
                statusEl.className = 'service-status active';
            }
        }
    }

    setStatus(type, message) {
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        
        indicator.className = `status-indicator ${type}`;
        text.textContent = message;
    }

    async runConnectionTest() {
        const testButton = document.getElementById('test-button');
        const resultDiv = document.getElementById('test-result');
        
        testButton.disabled = true;
        testButton.textContent = 'テスト中...';
        resultDiv.textContent = '';

        try {
            // 現在のタブ取得
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tabs.length === 0) {
                throw new Error('アクティブなタブが見つかりません');
            }

            const currentTab = tabs[0];
            const site = this.detectSiteFromUrl(currentTab.url);
            
            if (site === 'その他') {
                throw new Error('対応していないサイトです');
            }

            // テスト用のAI処理リクエスト
            const testRequest = {
                action: 'processAIRequest',
                text: 'テスト: この文章に「OK」と返答してください。',
                ai_service: this.getServiceKey(site),
                model: 'default'
            };

            const response = await chrome.runtime.sendMessage(testRequest);

            if (response.success) {
                resultDiv.innerHTML = `<div class="success">✅ 接続テスト成功<br>応答: ${response.result?.substring(0, 100)}...</div>`;
                
                // 処理数をインクリメント
                const storageData = await chrome.storage.local.get(['totalProcessed']);
                await chrome.storage.local.set({
                    totalProcessed: (storageData.totalProcessed || 0) + 1
                });
            } else {
                resultDiv.innerHTML = `<div class="error">❌ 接続テスト失敗<br>エラー: ${response.error}</div>`;
            }

        } catch (error) {
            resultDiv.innerHTML = `<div class="error">❌ 接続テスト失敗<br>エラー: ${error.message}</div>`;
        } finally {
            testButton.disabled = false;
            testButton.textContent = '接続テスト';
        }
    }

    getServiceKey(siteName) {
        const mapping = {
            'ChatGPT': 'chatgpt',
            'Claude': 'claude',
            'Gemini': 'gemini',
            'Genspark': 'genspark',
            'Google AI Studio': 'google_ai_studio'
        };
        return mapping[siteName] || 'unknown';
    }

    async clearStorage() {
        try {
            await chrome.storage.local.clear();
            document.getElementById('test-result').innerHTML = '<div class="success">✅ ストレージをクリアしました</div>';
            
            // ストレージクリア後の統計リセット
            document.getElementById('total-processed').textContent = '0';
            document.getElementById('active-requests').textContent = '0';
            
        } catch (error) {
            document.getElementById('test-result').innerHTML = `<div class="error">❌ ストレージクリア失敗: ${error.message}</div>`;
        }
    }

    startPeriodicUpdate() {
        // 5秒間隔でステータス更新
        setInterval(() => {
            this.updateStatus();
        }, 5000);
    }
}

// ポップアップ初期化
document.addEventListener('DOMContentLoaded', () => {
    new AIAutomationPopup();
});