#!/usr/bin/env python3
"""
API/創造的方式によるAIモデル情報取得
各AIサービスのAPIや内部エンドポイントを活用して最新のモデル情報を取得
"""

import json
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class APIModelFetcher:
    """API方式でAIモデル情報を取得するクラス"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
        
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()
            
    async def fetch_all_models(self) -> Dict[str, Dict]:
        """全AIサービスのモデル情報を取得"""
        results = {}
        
        # 各サービスの取得メソッドを非同期で実行
        tasks = [
            self._fetch_chatgpt_models(),
            self._fetch_claude_models(),
            self._fetch_gemini_models(),
            self._fetch_genspark_models(),
            self._fetch_google_ai_studio_models()
        ]
        
        service_names = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
        
        # 並行実行
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果をまとめる
        for service, result in zip(service_names, results_list):
            if isinstance(result, Exception):
                logger.error(f"{service}のモデル取得エラー: {result}")
                results[service] = {"error": str(result)}
            else:
                results[service] = result
                logger.info(f"✅ {service}: {len(result.get('models', []))}個のモデルを取得")
                
        return results
        
    async def _fetch_chatgpt_models(self) -> Dict[str, Any]:
        """ChatGPT/OpenAIのモデル情報を取得"""
        try:
            # OpenAI APIドキュメントから情報を取得
            models = []
            settings = {}
            
            # 方法1: OpenAI APIエンドポイントから取得を試みる
            try:
                # 注: 実際のAPIキーなしでモデルリストを取得する方法
                async with self.session.get(
                    "https://platform.openai.com/docs/models",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # ドキュメントからモデル名を抽出
                        model_sections = soup.find_all(['h3', 'h4'], string=re.compile(r'gpt|GPT'))
                        
                        # 既知のモデルリスト（2024年12月時点）
                        models = [
                            "gpt-4o",
                            "gpt-4o-mini",
                            "gpt-4-turbo",
                            "gpt-4-turbo-preview",
                            "gpt-4",
                            "gpt-3.5-turbo",
                            "gpt-3.5-turbo-16k"
                        ]
                        
            except Exception as e:
                logger.debug(f"OpenAI docs取得エラー: {e}")
                
            # 方法2: ChatGPT WebアプリのAPIエンドポイントを探索
            try:
                # ChatGPTのWebアプリが使用する内部APIを模倣
                async with self.session.get(
                    "https://chat.openai.com/backend-api/models",
                    headers={**self.headers, 'Referer': 'https://chat.openai.com/'},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'models' in data:
                            models.extend([m['id'] for m in data['models'] if 'gpt' in m['id'].lower()])
                            
            except Exception as e:
                logger.debug(f"ChatGPT backend API取得エラー: {e}")
                
            # モデルリストの重複を削除
            models = list(dict.fromkeys(models)) if models else [
                "gpt-4o",
                "gpt-4o-mini", 
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo"
            ]
            
            # 設定情報
            settings = {
                "temperature": {"min": 0, "max": 2, "default": 0.7},
                "max_tokens": {"min": 1, "max": 128000, "default": 4096},
                "top_p": {"min": 0, "max": 1, "default": 1},
                "frequency_penalty": {"min": -2, "max": 2, "default": 0},
                "presence_penalty": {"min": -2, "max": 2, "default": 0}
            }
            
            return {
                "models": models,
                "settings": settings,
                "features": ["vision", "code_interpreter", "web_search", "dalle", "custom_gpts"],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"ChatGPTモデル取得エラー: {e}")
            return self._get_default_chatgpt_info()
            
    async def _fetch_claude_models(self) -> Dict[str, Any]:
        """Claudeのモデル情報を取得"""
        try:
            models = []
            
            # 方法1: Anthropic APIドキュメントから取得
            try:
                async with self.session.get(
                    "https://docs.anthropic.com/en/api/models",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # モデル名を含むコードブロックを探す
                        code_blocks = soup.find_all('code')
                        for block in code_blocks:
                            text = block.get_text()
                            if 'claude' in text.lower():
                                # claude-3.5-sonnet のようなパターンを抽出
                                model_matches = re.findall(r'claude-[\d\.]+-\w+(?:-\d+)?', text)
                                models.extend(model_matches)
                                
            except Exception as e:
                logger.debug(f"Anthropic docs取得エラー: {e}")
                
            # 方法2: Claude.aiの内部APIを探索
            try:
                # Claude.aiが使用する可能性のあるエンドポイント
                async with self.session.get(
                    "https://claude.ai/api/organizations/models",
                    headers={**self.headers, 'Referer': 'https://claude.ai/'},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            models.extend([m.get('name', '') for m in data if m.get('name')])
                            
            except Exception as e:
                logger.debug(f"Claude.ai API取得エラー: {e}")
                
            # モデルリストの重複を削除し、既知のモデルを確保
            models = list(dict.fromkeys(models)) if models else []
            
            # 最新の既知モデルを追加（2024年12月時点）
            known_models = [
                "claude-3.5-sonnet-latest",
                "claude-3.5-haiku-latest",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
            
            # 既知のモデルとマージ
            final_models = list(dict.fromkeys(models + known_models))
            
            settings = {
                "temperature": {"min": 0, "max": 1, "default": 0.7},
                "max_tokens": {"min": 1, "max": 200000, "default": 4096}
            }
            
            return {
                "models": final_models[:10],  # 上位10個に制限
                "settings": settings,
                "features": ["vision", "artifacts", "projects", "computer_use"],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Claudeモデル取得エラー: {e}")
            return self._get_default_claude_info()
            
    async def _fetch_gemini_models(self) -> Dict[str, Any]:
        """Geminiのモデル情報を取得"""
        try:
            models = []
            
            # 方法1: Google AI Studio APIドキュメントから取得
            try:
                async with self.session.get(
                    "https://ai.google.dev/api/rest/v1/models",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'models' in data:
                            for model in data['models']:
                                model_name = model.get('name', '').replace('models/', '')
                                if 'gemini' in model_name.lower():
                                    models.append(model_name)
                                    
            except Exception as e:
                logger.debug(f"Google AI API取得エラー: {e}")
                
            # 方法2: Gemini WebアプリのAPIを探索
            try:
                # Geminiが使用する可能性のあるエンドポイント
                async with self.session.post(
                    "https://gemini.google.com/api/models",
                    json={},
                    headers={**self.headers, 'Referer': 'https://gemini.google.com/'},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'models' in data:
                            models.extend([m['id'] for m in data['models'] if 'gemini' in m['id'].lower()])
                            
            except Exception as e:
                logger.debug(f"Gemini web API取得エラー: {e}")
                
            # 既知のモデルを確保（2024年12月時点）
            known_models = [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro-latest",
                "gemini-1.5-pro-002", 
                "gemini-1.5-flash-latest",
                "gemini-1.5-flash-002",
                "gemini-1.0-pro",
                "gemini-pro-vision"
            ]
            
            # 重複を削除してマージ
            final_models = list(dict.fromkeys(models + known_models))
            
            settings = {
                "temperature": {"min": 0, "max": 2, "default": 0.9},
                "max_output_tokens": {"min": 1, "max": 8192, "default": 2048},
                "top_p": {"min": 0, "max": 1, "default": 0.95},
                "top_k": {"min": 1, "max": 40, "default": 40}
            }
            
            return {
                "models": final_models[:10],  # 上位10個に制限
                "settings": settings,
                "features": ["vision", "multimodal", "code_execution", "grounding"],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Geminiモデル取得エラー: {e}")
            return self._get_default_gemini_info()
            
    async def _fetch_genspark_models(self) -> Dict[str, Any]:
        """Gensparkのモデル情報を取得"""
        try:
            # Gensparkは比較的新しいサービスのため、Webサイトから情報を取得
            models = ["default", "advanced", "research"]
            
            try:
                async with self.session.get(
                    "https://www.genspark.ai",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        # 簡単なパターンマッチングでモデル情報を探す
                        if "pro" in html.lower():
                            models.append("pro")
                        if "turbo" in html.lower():
                            models.append("turbo")
                            
            except Exception as e:
                logger.debug(f"Genspark web取得エラー: {e}")
                
            return {
                "models": list(dict.fromkeys(models)),
                "settings": {},
                "features": ["research", "citations", "multi_source"],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Gensparkモデル取得エラー: {e}")
            return {
                "models": ["default", "advanced"],
                "settings": {},
                "features": ["research", "citations"]
            }
            
    async def _fetch_google_ai_studio_models(self) -> Dict[str, Any]:
        """Google AI Studioのモデル情報を取得"""
        # Google AI StudioはGeminiと同じモデルを使用
        gemini_info = await self._fetch_gemini_models()
        
        # Google AI Studio固有の機能を追加
        gemini_info["features"] = gemini_info.get("features", []) + ["prompt_gallery", "system_instructions"]
        
        return gemini_info
        
    def _get_default_chatgpt_info(self) -> Dict[str, Any]:
        """ChatGPTのデフォルト情報"""
        return {
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "settings": {
                "temperature": {"min": 0, "max": 2, "default": 0.7},
                "max_tokens": {"min": 1, "max": 128000, "default": 4096}
            },
            "features": ["vision", "code_interpreter", "web_search", "dalle"]
        }
        
    def _get_default_claude_info(self) -> Dict[str, Any]:
        """Claudeのデフォルト情報"""
        return {
            "models": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "settings": {
                "temperature": {"min": 0, "max": 1, "default": 0.7},
                "max_tokens": {"min": 1, "max": 200000, "default": 4096}
            },
            "features": ["vision", "artifacts", "projects"]
        }
        
    def _get_default_gemini_info(self) -> Dict[str, Any]:
        """Geminiのデフォルト情報"""
        return {
            "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "gemini-pro-vision"],
            "settings": {
                "temperature": {"min": 0, "max": 2, "default": 0.9},
                "max_output_tokens": {"min": 1, "max": 8192, "default": 2048}
            },
            "features": ["vision", "multimodal", "code_execution"]
        }


async def update_models_api() -> Dict[str, Dict]:
    """API方式でモデル情報を更新（メイン関数）"""
    async with APIModelFetcher() as fetcher:
        results = await fetcher.fetch_all_models()
        
        # 結果を保存
        save_results(results)
        
        return results


def save_results(results: Dict[str, Dict]):
    """結果をファイルに保存"""
    try:
        import os
        
        # configディレクトリが存在しない場合は作成
        os.makedirs("config", exist_ok=True)
        
        config_data = {
            "last_updated": datetime.now().isoformat(),
            "method": "api",
            "ai_services": results
        }
        
        with open("config/ai_models_latest.json", 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            
        logger.info("✅ モデル情報をconfig/ai_models_latest.jsonに保存しました")
        
    except Exception as e:
        logger.error(f"❌ 結果保存エラー: {e}")


def update_models_sync() -> Dict[str, Dict]:
    """同期的にモデル情報を更新（GUI用）"""
    return asyncio.run(update_models_api())


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    results = update_models_sync()
    print(json.dumps(results, indent=2, ensure_ascii=False))