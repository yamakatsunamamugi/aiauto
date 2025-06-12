"""
Chrome拡張機能連携ブリッジ
担当者：AI-B

Chrome拡張機能とPythonアプリケーション間の通信を管理するモジュール
ファイルベースの通信とchrome.storageを使用した双方向通信を実装
"""

import json
import time
import tempfile
import os
import subprocess
import signal
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class ExtensionBridge:
    """Chrome拡張機能との連携クラス"""

    def __init__(self):
        """ExtensionBridge初期化"""
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_automation_bridge"
        self.temp_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.request_timeout = 120  # 2分タイムアウト
        self.chrome_process = None
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "error_history": []
        }
        
        # 拡張機能設定
        self.extension_id = None
        self.supported_sites = {
            "chatgpt": "https://chatgpt.com",
            "claude": "https://claude.ai", 
            "gemini": "https://gemini.google.com",
            "genspark": "https://www.genspark.ai",
            "google_ai_studio": "https://aistudio.google.com"
        }
        
        self.logger.info("ExtensionBridge初期化完了")

    def process_with_extension(self, text: str, ai_service: str, 
                             model: str = None) -> Dict[str, Any]:
        """
        Chrome拡張機能経由でAI処理を実行
        
        Args:
            text: 処理対象テキスト
            ai_service: AIサービス名 (chatgpt, claude, gemini, etc.)
            model: 使用モデル（オプション）
            
        Returns:
            Dict: 処理結果
                - success: bool
                - result: str（成功時）
                - error: str（失敗時）
                - ai_service: str
                - model: str
                - processing_time: float
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # AIサービスの検証
            if ai_service not in self.supported_sites:
                raise ValueError(f"未対応のAIサービス: {ai_service}")

            # Chrome拡張機能の存在確認
            if not self._check_chrome_extension():
                return self._launch_chrome_with_extension(ai_service, text, model)

            # リクエストID生成
            request_id = f"{ai_service}_{int(time.time())}_{hash(text) % 10000}"
            
            self.logger.info(f"拡張機能リクエスト送信: {ai_service} - {text[:50]}...")

            # ブラウザでの処理実行
            result = self._execute_browser_automation(request_id, text, ai_service, model)

            processing_time = time.time() - start_time

            if result["success"]:
                self.stats["successful_requests"] += 1
                self._update_average_response_time(processing_time)
                self.logger.info(f"拡張機能処理完了: {processing_time:.2f}秒")
            else:
                self.stats["failed_requests"] += 1
                self._add_error_to_history(result.get('error', 'Unknown error'))
                self.logger.error(f"拡張機能処理失敗: {result.get('error', 'Unknown error')}")

            result["processing_time"] = processing_time
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.stats["failed_requests"] += 1

            error_msg = f"拡張機能連携エラー: {str(e)}"
            self.logger.error(error_msg)
            self._add_error_to_history(error_msg)

            return {
                "success": False,
                "error": error_msg,
                "ai_service": ai_service,
                "model": model,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }

    def _check_chrome_extension(self) -> bool:
        """Chrome拡張機能の存在確認"""
        try:
            # Chromeプロセスの確認
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'chrome' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if 'AI Automation Bridge' in cmdline or 'load-extension' in cmdline:
                            self.logger.debug("Chrome拡張機能プロセスを検出")
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            return False
        except ImportError:
            self.logger.warning("psutil未インストール、Chrome確認をスキップ")
            return False
        except Exception as e:
            self.logger.warning(f"Chrome確認エラー: {e}")
            return False

    def _launch_chrome_with_extension(self, ai_service: str, text: str, model: str) -> Dict[str, Any]:
        """Chrome拡張機能を有効にしてChromeを起動"""
        try:
            extension_path = Path(__file__).parent.parent.parent / "chrome-extension"
            
            if not extension_path.exists():
                raise FileNotFoundError(f"拡張機能が見つかりません: {extension_path}")

            # Chromeコマンド構築
            chrome_args = [
                self._get_chrome_executable(),
                f"--load-extension={extension_path}",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                f"--user-data-dir={self.temp_dir / 'chrome_profile'}",
                self.supported_sites[ai_service]
            ]

            self.logger.info(f"Chrome起動: {ai_service}")
            
            # Chromeプロセス起動
            self.chrome_process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # 起動待機
            time.sleep(5)

            # リクエスト処理
            request_id = f"{ai_service}_{int(time.time())}_{hash(text) % 10000}"
            return self._execute_browser_automation(request_id, text, ai_service, model)

        except Exception as e:
            return {
                "success": False,
                "error": f"Chrome起動エラー: {str(e)}",
                "ai_service": ai_service,
                "model": model,
                "timestamp": datetime.now().isoformat()
            }

    def _get_chrome_executable(self) -> str:
        """OS別のChrome実行ファイルパスを取得"""
        import platform
        system = platform.system()
        
        chrome_paths = {
            "Darwin": [  # macOS
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium"
            ],
            "Windows": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ],
            "Linux": [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser"
            ]
        }
        
        for path in chrome_paths.get(system, []):
            if Path(path).exists():
                return path
        
        # デフォルトコマンド
        return "google-chrome" if system == "Linux" else "chrome"

    def _execute_browser_automation(self, request_id: str, text: str, 
                                  ai_service: str, model: str) -> Dict[str, Any]:
        """ブラウザ自動化実行"""
        try:
            # リクエストファイル作成
            request_file = self.temp_dir / f"request_{request_id}.json"
            response_file = self.temp_dir / f"response_{request_id}.json"

            request_data = {
                "text": text,
                "ai_service": ai_service,
                "model": model,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "action": "processAI"
            }

            # リクエストファイル書き込み
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(request_data, f, ensure_ascii=False, indent=2)

            self.logger.debug(f"リクエストファイル作成: {request_file}")

            # 拡張機能の処理完了を待機
            result = self._wait_for_extension_response(response_file, request_id)

            # ファイルクリーンアップ
            self._cleanup_files(request_file, response_file)

            return result

        except Exception as e:
            self.logger.error(f"ブラウザ自動化エラー: {e}")
            return {
                "success": False,
                "error": f"ブラウザ自動化エラー: {str(e)}",
                "request_id": request_id
            }

    def _wait_for_extension_response(self, response_file: Path, 
                                   request_id: str) -> Dict[str, Any]:
        """拡張機能からの応答を待機"""
        start_time = time.time()
        check_interval = 1.0  # 1秒間隔

        self.logger.debug(f"応答待機開始: {request_id}")

        while time.time() - start_time < self.request_timeout:
            try:
                # レスポンスファイル確認
                if response_file.exists() and response_file.stat().st_size > 0:
                    try:
                        with open(response_file, 'r', encoding='utf-8') as f:
                            response_data = json.load(f)

                        # レスポンス検証
                        if response_data.get("request_id") == request_id:
                            self.logger.debug(f"応答受信完了: {request_id}")
                            return response_data
                        else:
                            self.logger.warning(f"リクエストID不一致: 期待値={request_id}, 実際={response_data.get('request_id')}")

                    except (json.JSONDecodeError, IOError) as e:
                        self.logger.warning(f"レスポンスファイル読み込みエラー: {e}")

                # Chrome拡張機能からの生成ファイル確認（代替手段）
                generated_files = list(self.temp_dir.glob(f"*{request_id}*"))
                if generated_files:
                    self.logger.debug(f"生成ファイル検出: {len(generated_files)}件")

                time.sleep(check_interval)

            except Exception as e:
                self.logger.warning(f"応答待機中のエラー: {e}")
                time.sleep(check_interval)

        # タイムアウト
        self.logger.error(f"拡張機能応答タイムアウト: {request_id}")
        return {
            "success": False,
            "error": f"拡張機能応答タイムアウト（{self.request_timeout}秒）",
            "request_id": request_id
        }

    def _cleanup_files(self, *files):
        """ファイルクリーンアップ"""
        for file_path in files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    self.logger.debug(f"ファイル削除: {file_path}")
            except Exception as e:
                self.logger.warning(f"ファイル削除エラー: {e}")

    def _update_average_response_time(self, current_time: float):
        """平均応答時間を更新"""
        if self.stats["successful_requests"] == 1:
            self.stats["average_response_time"] = current_time
        else:
            total_time = self.stats["average_response_time"] * (self.stats["successful_requests"] - 1)
            self.stats["average_response_time"] = (total_time + current_time) / self.stats["successful_requests"]

    def _add_error_to_history(self, error_msg: str):
        """エラー履歴に追加"""
        self.stats["error_history"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error_msg
        })
        
        # 履歴が100件を超えたら古いものを削除
        if len(self.stats["error_history"]) > 100:
            self.stats["error_history"] = self.stats["error_history"][-100:]

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        stats = self.stats.copy()
        stats["success_rate"] = (
            (stats["successful_requests"] / stats["total_requests"] * 100)
            if stats["total_requests"] > 0 else 0
        )
        return stats

    def get_supported_ai_services(self) -> List[str]:
        """対応AIサービス一覧を取得"""
        return list(self.supported_sites.keys())

    def check_extension_status(self) -> Dict[str, Any]:
        """拡張機能の状態を確認"""
        try:
            # Chrome拡張機能の存在確認
            if self._check_chrome_extension():
                return {
                    "status": "active",
                    "message": "Chrome拡張機能が動作中"
                }

            # 拡張機能ファイルの存在確認
            extension_path = Path(__file__).parent.parent.parent / "chrome-extension"
            if not extension_path.exists():
                return {
                    "status": "missing",
                    "message": "拡張機能ファイルが見つかりません"
                }

            # マニフェストファイル確認
            manifest_path = extension_path / "manifest.json"
            if not manifest_path.exists():
                return {
                    "status": "invalid",
                    "message": "manifest.jsonが見つかりません"
                }

            return {
                "status": "ready",
                "message": "拡張機能は利用可能（Chrome未起動）"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"状態確認エラー: {str(e)}"
            }

    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            # Chromeプロセス終了
            if self.chrome_process and self.chrome_process.poll() is None:
                self.chrome_process.terminate()
                try:
                    self.chrome_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.chrome_process.kill()
                self.logger.info("Chromeプロセスを終了しました")

            # 一時ファイルクリーンアップ
            for file_path in self.temp_dir.glob("*"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                except Exception as e:
                    self.logger.warning(f"一時ファイル削除エラー: {e}")

            self.logger.info("ExtensionBridgeクリーンアップ完了")

        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")

    def __enter__(self):
        """コンテキストマネージャー対応"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー対応"""
        self.cleanup()


class ExtensionConfig:
    """拡張機能設定管理クラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent.parent / "config" / "extension_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        default_config = {
            "extension": {
                "timeout": 120,
                "retry_count": 3,
                "debug_mode": False
            },
            "ai_services": {
                "chatgpt": {
                    "enabled": True,
                    "default_model": "gpt-4o",
                    "timeout": 120
                },
                "claude": {
                    "enabled": True,
                    "default_model": "claude-3.5-sonnet",
                    "timeout": 120
                },
                "gemini": {
                    "enabled": True,
                    "default_model": "gemini-1.5-pro",
                    "timeout": 120
                },
                "genspark": {
                    "enabled": True,
                    "default_model": "default",
                    "timeout": 120
                },
                "google_ai_studio": {
                    "enabled": True,
                    "default_model": "gemini-1.5-pro",
                    "timeout": 120
                }
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # デフォルト設定とマージ
                    default_config.update(loaded_config)
                    return default_config
            except Exception as e:
                logging.getLogger(__name__).warning(f"設定ファイル読み込みエラー: {e}")
        
        return default_config
    
    def save_config(self):
        """設定ファイル保存"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.getLogger(__name__).error(f"設定ファイル保存エラー: {e}")
    
    def get(self, key: str, default=None):
        """設定値取得"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value