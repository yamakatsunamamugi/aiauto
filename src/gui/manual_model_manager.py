#!/usr/bin/env python3
"""
手動AIモデルリスト管理機能
ユーザーが手動でAIモデルのリストを編集・管理できる機能を提供
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ManualModelManager:
    """手動モデル管理クラス"""
    
    def __init__(self):
        self.config_file = "config/manual_models.json"
        self.models_data = self._load_models()
        
    def _load_models(self) -> Dict:
        """保存されたモデル情報を読み込む"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"モデル設定読み込みエラー: {e}")
        
        # デフォルト値
        return {
            "chatgpt": {
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "last_updated": datetime.now().isoformat(),
                "source": "default"
            },
            "claude": {
                "models": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "last_updated": datetime.now().isoformat(),
                "source": "default"
            },
            "gemini": {
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
                "last_updated": datetime.now().isoformat(),
                "source": "default"
            },
            "genspark": {
                "models": ["default", "research", "advanced"],
                "last_updated": datetime.now().isoformat(),
                "source": "default"
            },
            "google_ai_studio": {
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "palm-2"],
                "last_updated": datetime.now().isoformat(),
                "source": "default"
            }
        }
    
    def save_models(self) -> bool:
        """モデル情報を保存"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.models_data, f, indent=2, ensure_ascii=False)
            logger.info(f"モデル設定を保存: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"モデル設定保存エラー: {e}")
            return False
    
    def get_models(self, service: str) -> List[str]:
        """指定サービスのモデルリストを取得"""
        if service in self.models_data:
            return self.models_data[service].get("models", [])
        return []
    
    def update_models(self, service: str, models: List[str]) -> bool:
        """指定サービスのモデルリストを更新"""
        self.models_data[service] = {
            "models": models,
            "last_updated": datetime.now().isoformat(),
            "source": "manual"
        }
        return self.save_models()
    
    def get_all_models(self) -> Dict[str, List[str]]:
        """全サービスのモデルリストを取得"""
        return {service: data.get("models", []) for service, data in self.models_data.items()}


class ManualModelDialog:
    """手動モデル管理ダイアログ"""
    
    def __init__(self, parent):
        self.parent = parent
        self.manager = ManualModelManager()
        self.dialog = None
        self.result = False
        
        # 各サービスのテキストウィジェットを保存
        self.text_widgets = {}
        
    def show(self) -> bool:
        """ダイアログを表示"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("AIモデル手動管理")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        
        # モーダルダイアログにする
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._load_current_models()
        
        # ダイアログのクローズイベント
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # 中央に配置
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # ダイアログが閉じられるまで待機
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 説明ラベル
        info_label = ttk.Label(main_frame, text="各AIサービスのモデルリストを編集できます。1行に1つのモデル名を入力してください。")
        info_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # ノートブック（タブ）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 各サービスのタブを作成
        services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
        service_names = {
            "chatgpt": "ChatGPT",
            "claude": "Claude",
            "gemini": "Gemini",
            "genspark": "Genspark",
            "google_ai_studio": "Google AI Studio"
        }
        
        for service in services:
            # タブフレーム
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=service_names.get(service, service))
            
            tab_frame.columnconfigure(0, weight=1)
            tab_frame.rowconfigure(1, weight=1)
            
            # ツールバー
            toolbar = ttk.Frame(tab_frame)
            toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
            
            # プリセットボタン
            ttk.Button(toolbar, text="最新モデル", 
                      command=lambda s=service: self._apply_preset(s, "latest")).pack(side=tk.LEFT, padx=2)
            ttk.Button(toolbar, text="基本モデル", 
                      command=lambda s=service: self._apply_preset(s, "basic")).pack(side=tk.LEFT, padx=2)
            ttk.Button(toolbar, text="軽量モデル", 
                      command=lambda s=service: self._apply_preset(s, "light")).pack(side=tk.LEFT, padx=2)
            ttk.Button(toolbar, text="クリア", 
                      command=lambda s=service: self._clear_models(s)).pack(side=tk.LEFT, padx=20)
            
            # テキストエリア
            text_frame = ttk.Frame(tab_frame)
            text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            text_frame.columnconfigure(0, weight=1)
            text_frame.rowconfigure(0, weight=1)
            
            text = scrolledtext.ScrolledText(text_frame, width=60, height=20, wrap=tk.WORD)
            text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            self.text_widgets[service] = text
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0), sticky=tk.E)
        
        # ボタン
        ttk.Button(button_frame, text="保存", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self._on_cancel).pack(side=tk.LEFT, padx=5)
        
    def _load_current_models(self):
        """現在のモデルリストを読み込む"""
        all_models = self.manager.get_all_models()
        
        for service, text_widget in self.text_widgets.items():
            models = all_models.get(service, [])
            text_widget.delete(1.0, tk.END)
            text_widget.insert(1.0, "\n".join(models))
    
    def _apply_preset(self, service: str, preset_type: str):
        """プリセットを適用"""
        presets = {
            "chatgpt": {
                "latest": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "basic": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
                "light": ["gpt-4o-mini", "gpt-3.5-turbo"]
            },
            "claude": {
                "latest": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "basic": ["claude-3.5-sonnet", "claude-3-opus"],
                "light": ["claude-3-haiku"]
            },
            "gemini": {
                "latest": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "gemini-pro-vision"],
                "basic": ["gemini-1.5-pro", "gemini-pro"],
                "light": ["gemini-1.5-flash"]
            },
            "genspark": {
                "latest": ["default", "research", "advanced"],
                "basic": ["default", "research"],
                "light": ["default"]
            },
            "google_ai_studio": {
                "latest": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "palm-2"],
                "basic": ["gemini-1.5-pro", "gemini-pro"],
                "light": ["gemini-1.5-flash"]
            }
        }
        
        if service in presets and preset_type in presets[service]:
            models = presets[service][preset_type]
            text_widget = self.text_widgets[service]
            text_widget.delete(1.0, tk.END)
            text_widget.insert(1.0, "\n".join(models))
    
    def _clear_models(self, service: str):
        """モデルリストをクリア"""
        text_widget = self.text_widgets[service]
        text_widget.delete(1.0, tk.END)
    
    def _on_save(self):
        """保存ボタン処理"""
        try:
            # 各サービスのモデルリストを収集
            for service, text_widget in self.text_widgets.items():
                text_content = text_widget.get(1.0, tk.END).strip()
                
                # 空行を除いてリスト化
                models = [line.strip() for line in text_content.split('\n') if line.strip()]
                
                # モデルリストを更新
                if not self.manager.update_models(service, models):
                    raise Exception(f"{service}のモデル保存に失敗しました")
            
            self.result = True
            messagebox.showinfo("成功", "モデルリストを保存しました")
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("エラー", f"保存エラー: {e}")
    
    def _on_cancel(self):
        """キャンセルボタン処理"""
        self.result = False
        self.dialog.destroy()


def show_manual_model_dialog(parent) -> bool:
    """手動モデル管理ダイアログを表示"""
    dialog = ManualModelDialog(parent)
    return dialog.show()


def update_models_manual(service: str, models: List[str]) -> bool:
    """手動でモデルリストを更新（外部から呼び出し用）"""
    manager = ManualModelManager()
    return manager.update_models(service, models)


def get_manual_models() -> Dict[str, List[str]]:
    """手動管理されたモデルリストを取得"""
    manager = ManualModelManager()
    return manager.get_all_models()


def update_model_list() -> Dict[str, List[str]]:
    """AIモデルの最新リストを取得する（インターフェース仕様準拠）
    
    Returns:
        Dict[str, List[str]]: 各AIサービスのモデルリスト
        例: {
            "chatgpt": ["gpt-4o", "gpt-4o-mini"],
            "claude": ["claude-3.5-sonnet"],
            "gemini": ["gemini-1.5-pro"],
            "genspark": ["default"],
            "google_ai_studio": ["gemini-1.5-pro"]
        }
    """
    try:
        manager = ManualModelManager()
        all_models = manager.get_all_models()
        
        # 仕様で要求される5つのサービスが確実に含まれるようにする
        required_services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
        result = {}
        
        for service in required_services:
            if service in all_models:
                result[service] = all_models[service]
            else:
                result[service] = []
                logger.warning(f"サービス '{service}' のモデルリストが見つかりません。空のリストを返します。")
        
        logger.info(f"モデルリストを取得しました: {len(result)} サービス")
        return result
        
    except Exception as e:
        logger.error(f"モデルリスト取得エラー: {e}")
        # エラー時は各サービスの空リストを返す
        return {
            "chatgpt": [],
            "claude": [],
            "gemini": [],
            "genspark": [],
            "google_ai_studio": []
        }


if __name__ == "__main__":
    # テスト実行
    root = tk.Tk()
    root.withdraw()
    
    result = show_manual_model_dialog(root)
    print(f"ダイアログ結果: {result}")
    
    if result:
        models = get_manual_models()
        print("保存されたモデル:")
        for service, model_list in models.items():
            print(f"{service}: {model_list}")