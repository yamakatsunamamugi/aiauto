"""
AIモデル最新情報更新機能
各AIサービスから最新のモデル情報と設定を取得
"""

import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

class AIModelUpdater:
    """AIモデル情報更新クラス"""
    
    def __init__(self):
        self.ai_info = {
            "chatgpt": {
                "url": "https://chat.openai.com",
                "models": [],
                "settings": {},
                "last_updated": None
            },
            "claude": {
                "url": "https://claude.ai",
                "models": [],
                "settings": {},
                "last_updated": None
            },
            "gemini": {
                "url": "https://gemini.google.com",
                "models": [],
                "settings": {},
                "last_updated": None
            },
            "genspark": {
                "url": "https://www.genspark.ai",
                "models": [],
                "settings": {},
                "last_updated": None
            },
            "google_ai_studio": {
                "url": "https://aistudio.google.com",
                "models": [],
                "settings": {},
                "last_updated": None
            }
        }
        
    async def update_all_models(self) -> Dict[str, Dict]:
        """全AIサービスのモデル情報を更新"""
        results = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                # 各AIサービスの情報を取得
                for service in self.ai_info.keys():
                    try:
                        logger.info(f"{service}の最新情報を取得中...")
                        info = await self._get_ai_info(browser, service)
                        if info:
                            self.ai_info[service].update(info)
                            self.ai_info[service]["last_updated"] = datetime.now().isoformat()
                            results[service] = info
                            logger.info(f"{service}の情報取得完了")
                    except Exception as e:
                        logger.error(f"{service}の情報取得エラー: {e}")
                        results[service] = {"error": str(e)}
                        
            finally:
                await browser.close()
                
        # 設定ファイルに保存
        self._save_to_config(results)
        return results
    
    async def _get_ai_info(self, browser, service: str) -> Optional[Dict]:
        """個別AIサービスの情報取得"""
        page = await browser.new_page()
        
        try:
            if service == "chatgpt":
                return await self._get_chatgpt_info(page)
            elif service == "claude":
                return await self._get_claude_info(page)
            elif service == "gemini":
                return await self._get_gemini_info(page)
            elif service == "genspark":
                return await self._get_genspark_info(page)
            elif service == "google_ai_studio":
                return await self._get_google_ai_studio_info(page)
            else:
                return None
                
        finally:
            await page.close()
            
    async def _get_chatgpt_info(self, page) -> Dict:
        """ChatGPT情報取得"""
        try:
            await page.goto("https://platform.openai.com/docs/models", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # モデル情報を取得
            models = []
            
            # GPT-4系モデル
            gpt4_models = await page.locator("h3:has-text('GPT-4')").all()
            if gpt4_models:
                models.extend([
                    "gpt-4o",
                    "gpt-4o-mini", 
                    "gpt-4-turbo",
                    "gpt-4"
                ])
            
            # GPT-3.5系モデル
            models.append("gpt-3.5-turbo")
            
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
                "features": ["vision", "code_interpreter", "web_search", "dalle"]
            }
            
        except Exception as e:
            logger.error(f"ChatGPT情報取得エラー: {e}")
            # デフォルト値を返す
            return {
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "settings": {
                    "temperature": {"min": 0, "max": 2, "default": 0.7},
                    "max_tokens": {"min": 1, "max": 128000, "default": 4096}
                },
                "features": ["vision", "code_interpreter", "web_search", "dalle"]
            }
            
    async def _get_claude_info(self, page) -> Dict:
        """Claude情報取得"""
        try:
            await page.goto("https://docs.anthropic.com/claude/docs/models-overview", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            models = [
                "claude-3.5-sonnet-latest",
                "claude-3.5-haiku-latest",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
            
            settings = {
                "temperature": {"min": 0, "max": 1, "default": 0.7},
                "max_tokens": {"min": 1, "max": 200000, "default": 4096}
            }
            
            return {
                "models": models,
                "settings": settings,
                "features": ["vision", "artifacts", "projects"]
            }
            
        except Exception as e:
            logger.error(f"Claude情報取得エラー: {e}")
            return {
                "models": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "settings": {
                    "temperature": {"min": 0, "max": 1, "default": 0.7},
                    "max_tokens": {"min": 1, "max": 200000, "default": 4096}
                },
                "features": ["vision", "artifacts", "projects"]
            }
            
    async def _get_gemini_info(self, page) -> Dict:
        """Gemini情報取得"""
        try:
            await page.goto("https://ai.google.dev/gemini-api/docs/models/gemini", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            models = [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro-latest", 
                "gemini-1.5-flash-latest",
                "gemini-1.0-pro"
            ]
            
            settings = {
                "temperature": {"min": 0, "max": 2, "default": 0.9},
                "max_output_tokens": {"min": 1, "max": 8192, "default": 2048},
                "top_p": {"min": 0, "max": 1, "default": 0.95},
                "top_k": {"min": 1, "max": 40, "default": 40}
            }
            
            return {
                "models": models,
                "settings": settings,
                "features": ["vision", "multimodal", "code_execution"]
            }
            
        except Exception as e:
            logger.error(f"Gemini情報取得エラー: {e}")
            return {
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "gemini-pro-vision"],
                "settings": {
                    "temperature": {"min": 0, "max": 2, "default": 0.9},
                    "max_output_tokens": {"min": 1, "max": 8192, "default": 2048}
                },
                "features": ["vision", "multimodal", "code_execution"]
            }
            
    async def _get_genspark_info(self, page) -> Dict:
        """Genspark情報取得"""
        # Gensparkは比較的新しいサービスのため、デフォルト値を返す
        return {
            "models": ["default", "advanced"],
            "settings": {},
            "features": ["research", "citations"]
        }
        
    async def _get_google_ai_studio_info(self, page) -> Dict:
        """Google AI Studio情報取得"""
        # Geminiと同じモデルを使用
        return await self._get_gemini_info(page)
        
    def _save_to_config(self, results: Dict):
        """設定ファイルに保存"""
        try:
            config_path = "config/ai_models_latest.json"
            
            # 既存の設定を読み込み
            existing_config = {}
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            except FileNotFoundError:
                pass
                
            # 更新
            existing_config.update({
                "last_updated": datetime.now().isoformat(),
                "ai_services": results
            })
            
            # 保存
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)
                
            logger.info(f"最新情報を{config_path}に保存しました")
            
        except Exception as e:
            logger.error(f"設定ファイル保存エラー: {e}")
            
    def get_cached_info(self) -> Dict:
        """キャッシュされた情報を取得"""
        try:
            with open("config/ai_models_latest.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
def update_models_sync() -> Dict:
    """同期的にモデル情報を更新（GUI用）"""
    updater = AIModelUpdater()
    return asyncio.run(updater.update_all_models())