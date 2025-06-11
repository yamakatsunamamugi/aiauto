"""
列毎AI設定ダイアログモジュール

スプレッドシートの各列に対して個別のAI設定を管理するダイアログを提供します。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional
import json
import copy

from src.gui.components import LabeledCombobox, ValidationMixin


class AIModelConfig:
    """AI設定情報クラス"""
    
    # 最新のAI設定情報（2024年調査結果）
    AI_CONFIGS = {
        "chatgpt": {
            "display_name": "ChatGPT",
            "url": "https://chat.openai.com",
            "models": {
                "gpt-4.1": {
                    "name": "GPT-4.1 (最新)",
                    "description": "最新のコーディング・指示理解強化モデル",
                    "context_tokens": 1000000
                },
                "gpt-4o": {
                    "name": "GPT-4o (オムニ)", 
                    "description": "マルチモーダル対応、高速応答",
                    "context_tokens": 128000
                },
                "gpt-4o-mini": {
                    "name": "GPT-4o Mini",
                    "description": "高速・低コスト版",
                    "context_tokens": 128000
                },
                "gpt-4-turbo": {
                    "name": "GPT-4 Turbo",
                    "description": "拡張コンテキスト版",
                    "context_tokens": 128000
                }
            },
            "modes": {
                "creative": "クリエイティブ",
                "balanced": "バランス",
                "precise": "正確性重視"
            },
            "features": {
                "deep_research": "詳細研究モード",
                "code_interpreter": "コード実行",
                "web_browsing": "Web検索",
                "vision": "画像解析"
            }
        },
        "claude": {
            "display_name": "Claude (Anthropic)",
            "url": "https://claude.ai",
            "models": {
                "claude-3.5-sonnet": {
                    "name": "Claude 3.5 Sonnet",
                    "description": "最新の高性能モデル",
                    "context_tokens": 200000
                },
                "claude-3.5-haiku": {
                    "name": "Claude 3.5 Haiku",
                    "description": "高速・効率重視",
                    "context_tokens": 200000
                },
                "claude-3-opus": {
                    "name": "Claude 3 Opus",
                    "description": "最高性能モデル",
                    "context_tokens": 200000
                }
            },
            "modes": {
                "balanced": "バランス",
                "creative": "クリエイティブ",
                "precise": "正確性重視"
            },
            "features": {
                "computer_use": "コンピューター操作",
                "artifacts": "アーティファクト生成",
                "vision": "画像解析",
                "analysis": "高度な分析"
            }
        },
        "gemini": {
            "display_name": "Google Gemini",
            "url": "https://gemini.google.com",
            "models": {
                "gemini-2.5-pro": {
                    "name": "Gemini 2.5 Pro",
                    "description": "最新の高性能モデル（思考モード付き）",
                    "context_tokens": 1000000
                },
                "gemini-2.0-flash": {
                    "name": "Gemini 2.0 Flash",
                    "description": "高速・低遅延モデル",
                    "context_tokens": 1000000
                },
                "gemini-2.0-flash-lite": {
                    "name": "Gemini 2.0 Flash-Lite",
                    "description": "最高効率モデル",
                    "context_tokens": 1000000
                },
                "gemini-1.5-pro": {
                    "name": "Gemini 1.5 Pro",
                    "description": "安定版高性能モデル",
                    "context_tokens": 1000000
                }
            },
            "modes": {
                "creative": "クリエイティブ",
                "balanced": "バランス", 
                "precise": "正確性重視",
                "thinking": "思考モード"
            },
            "features": {
                "deep_research": "詳細研究",
                "multimodal": "マルチモーダル",
                "live_api": "リアルタイム音声",
                "code_execution": "コード実行"
            }
        },
        "perplexity": {
            "display_name": "Perplexity AI",
            "url": "https://perplexity.ai",
            "models": {
                "claude-sonnet-4": {
                    "name": "Claude Sonnet 4.0",
                    "description": "最高性能言語モデル",
                    "context_tokens": 200000
                },
                "grok-3-beta": {
                    "name": "Grok 3 Beta",
                    "description": "数学・科学・コーディング特化",
                    "context_tokens": 128000
                },
                "o4-mini": {
                    "name": "o4-mini",
                    "description": "高精度指示追従モデル",
                    "context_tokens": 128000
                },
                "sonar": {
                    "name": "Sonar",
                    "description": "検索特化モデル",
                    "context_tokens": 70000
                }
            },
            "modes": {
                "best": "最適モード",
                "pro_search": "詳細検索",
                "reasoning": "推論モード",
                "research": "研究モード"
            },
            "features": {
                "deep_research": "詳細研究（2-4分）",
                "real_time_search": "リアルタイム検索",
                "citation": "引用機能",
                "multi_source": "複数ソース統合"
            }
        },
        "genspark": {
            "display_name": "Genspark AI",
            "url": "https://genspark.ai",
            "models": {
                "genspark-multi": {
                    "name": "Genspark Multi-Model",
                    "description": "OpenAI・Anthropic・Google統合",
                    "context_tokens": 128000
                },
                "sparkpage-generator": {
                    "name": "Sparkpage Generator",
                    "description": "カスタム要約ページ生成",
                    "context_tokens": 100000
                }
            },
            "modes": {
                "balanced": "バランス",
                "comprehensive": "包括的",
                "quick": "高速"
            },
            "features": {
                "sparkpage": "Sparkページ生成",
                "ai_copilot": "AIコパイロット",
                "real_time_verification": "リアルタイム検証",
                "multi_source": "複数ソース統合"
            }
        }
    }


class ColumnAISettingsDialog:
    """列毎AI設定ダイアログ"""
    
    def __init__(self, parent, config_manager, sheet_columns: List[str] = None):
        self.parent = parent
        self.config_manager = config_manager
        self.sheet_columns = sheet_columns or ["A", "B", "C", "D", "E"]
        
        # 既存設定の読み込み
        self.column_settings = copy.deepcopy(
            config_manager.get("column_ai_settings", {})
        )
        
        # ダイアログ作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("列毎AI設定")
        self.dialog.geometry("900x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 中央配置
        self.center_window()
        
        # UI構築
        self.setup_ui()
        self.load_settings()
        
    def center_window(self):
        """ウィンドウを中央に配置"""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"900x600+{x}+{y}")
        
    def setup_ui(self):
        """UI構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 説明ラベル
        ttk.Label(main_frame, text="スプレッドシートの列毎にAIサービスとモデルを設定できます",
                 font=("", 10)).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # メインコンテンツ
        self.create_main_content(main_frame)
        
        # ボタンフレーム
        self.create_button_frame(main_frame)
        
    def create_main_content(self, parent):
        """メインコンテンツ作成"""
        # ノートブック（タブ）
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 列設定タブ
        self.create_column_settings_tab()
        
        # テンプレートタブ
        self.create_template_tab()
        
        # プレビュータブ
        self.create_preview_tab()
        
    def create_column_settings_tab(self):
        """列設定タブ"""
        # タブフレーム
        self.column_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.column_tab, text="列設定")
        
        # スクロール可能フレーム
        canvas = tk.Canvas(self.column_tab)
        scrollbar = ttk.Scrollbar(self.column_tab, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.column_tab.columnconfigure(0, weight=1)
        self.column_tab.rowconfigure(0, weight=1)
        
        # 列設定ウィジェットを作成
        self.column_widgets = {}
        self.create_column_setting_widgets()
        
    def create_column_setting_widgets(self):
        """列設定ウィジェット作成"""
        # ヘッダー
        header_frame = ttk.Frame(self.scrollable_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        ttk.Label(header_frame, text="列", font=("", 10, "bold")).grid(row=0, column=0, padx=(0, 10))
        ttk.Label(header_frame, text="AI サービス", font=("", 10, "bold")).grid(row=0, column=1, padx=(0, 10))
        ttk.Label(header_frame, text="モデル", font=("", 10, "bold")).grid(row=0, column=2, padx=(0, 10))
        ttk.Label(header_frame, text="モード", font=("", 10, "bold")).grid(row=0, column=3, padx=(0, 10))
        ttk.Label(header_frame, text="機能", font=("", 10, "bold")).grid(row=0, column=4, padx=(0, 10))
        ttk.Label(header_frame, text="詳細設定", font=("", 10, "bold")).grid(row=0, column=5)
        
        # 各列の設定
        for i, column in enumerate(self.sheet_columns):
            self.create_column_row(i + 1, column)
            
    def create_column_row(self, row: int, column: str):
        """列設定行を作成"""
        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
        row_frame.columnconfigure(1, weight=1)
        
        # 列名
        ttk.Label(row_frame, text=f"{column}列", width=6).grid(row=0, column=0, padx=(0, 10))
        
        # AIサービス選択
        ai_services = list(AIModelConfig.AI_CONFIGS.keys())
        ai_service_combo = ttk.Combobox(row_frame, values=ai_services, state="readonly", width=15)
        ai_service_combo.grid(row=0, column=1, padx=(0, 10))
        ai_service_combo.bind("<<ComboboxSelected>>", lambda e, col=column: self.on_ai_service_changed(col))
        
        # モデル選択
        model_combo = ttk.Combobox(row_frame, state="readonly", width=20)
        model_combo.grid(row=0, column=2, padx=(0, 10))
        
        # モード選択
        mode_combo = ttk.Combobox(row_frame, state="readonly", width=15)
        mode_combo.grid(row=0, column=3, padx=(0, 10))
        
        # 機能選択
        feature_combo = ttk.Combobox(row_frame, state="readonly", width=15)
        feature_combo.grid(row=0, column=4, padx=(0, 10))
        
        # 詳細設定ボタン
        detail_button = ttk.Button(row_frame, text="詳細", width=8,
                                 command=lambda col=column: self.open_detail_settings(col))
        detail_button.grid(row=0, column=5)
        
        # ウィジェット保存
        self.column_widgets[column] = {
            "ai_service": ai_service_combo,
            "model": model_combo,
            "mode": mode_combo,
            "feature": feature_combo,
            "detail_button": detail_button
        }
        
    def on_ai_service_changed(self, column: str):
        """AIサービス変更時の処理"""
        widgets = self.column_widgets[column]
        ai_service = widgets["ai_service"].get()
        
        if ai_service and ai_service in AIModelConfig.AI_CONFIGS:
            config = AIModelConfig.AI_CONFIGS[ai_service]
            
            # モデル選択肢更新
            models = list(config["models"].keys())
            widgets["model"]["values"] = models
            if models:
                widgets["model"].current(0)
                
            # モード選択肢更新
            modes = list(config["modes"].values())
            widgets["mode"]["values"] = modes
            if modes:
                widgets["mode"].current(0)
                
            # 機能選択肢更新
            features = list(config["features"].values())
            widgets["feature"]["values"] = features
            if features:
                widgets["feature"].current(0)
                
    def open_detail_settings(self, column: str):
        """詳細設定ダイアログを開く"""
        DetailSettingsDialog(self.dialog, column, self.column_settings.get(column, {}))
        
    def create_template_tab(self):
        """テンプレートタブ"""
        template_tab = ttk.Frame(self.notebook)
        self.notebook.add(template_tab, text="テンプレート")
        
        template_frame = ttk.Frame(template_tab, padding="10")
        template_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        template_tab.columnconfigure(0, weight=1)
        template_tab.rowconfigure(0, weight=1)
        
        # テンプレート説明
        ttk.Label(template_frame, text="よく使用される設定をテンプレートとして保存・適用できます",
                 font=("", 10)).grid(row=0, column=0, sticky=tk.W, pady=(0, 20))
        
        # プリセットテンプレート
        preset_frame = ttk.LabelFrame(template_frame, text="プリセットテンプレート", padding="10")
        preset_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        preset_frame.columnconfigure(0, weight=1)
        
        presets = [
            ("高性能モード", "最新の高性能モデルを各AIで選択"),
            ("バランスモード", "性能とコストのバランスを重視"),
            ("高速モード", "応答速度を重視した設定"),
            ("研究モード", "詳細分析・研究向けの設定")
        ]
        
        for i, (name, desc) in enumerate(presets):
            preset_row = ttk.Frame(preset_frame)
            preset_row.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=2)
            preset_row.columnconfigure(0, weight=1)
            
            ttk.Label(preset_row, text=name, font=("", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
            ttk.Label(preset_row, text=desc, foreground="gray").grid(row=1, column=0, sticky=tk.W)
            ttk.Button(preset_row, text="適用", width=8,
                      command=lambda p=name: self.apply_preset_template(p)).grid(row=0, column=1, rowspan=2)
                      
    def apply_preset_template(self, preset_name: str):
        """プリセットテンプレートを適用"""
        templates = {
            "高性能モード": {
                "ai_service": "chatgpt",
                "model": "gpt-4.1",
                "mode": "precise",
                "feature": "deep_research"
            },
            "バランスモード": {
                "ai_service": "claude",
                "model": "claude-3.5-sonnet", 
                "mode": "balanced",
                "feature": "analysis"
            },
            "高速モード": {
                "ai_service": "gemini",
                "model": "gemini-2.0-flash",
                "mode": "balanced",
                "feature": "multimodal"
            },
            "研究モード": {
                "ai_service": "perplexity",
                "model": "claude-sonnet-4",
                "mode": "research",
                "feature": "deep_research"
            }
        }
        
        template = templates.get(preset_name)
        if template:
            for column in self.sheet_columns:
                self.apply_template_to_column(column, template)
                
        messagebox.showinfo("適用完了", f"{preset_name}を全列に適用しました。")
        
    def apply_template_to_column(self, column: str, template: Dict[str, str]):
        """列にテンプレートを適用"""
        widgets = self.column_widgets[column]
        
        # AIサービス設定
        ai_service = template["ai_service"]
        if ai_service in widgets["ai_service"]["values"]:
            widgets["ai_service"].set(ai_service)
            self.on_ai_service_changed(column)
            
            # モデル設定
            model = template["model"]
            if model in widgets["model"]["values"]:
                widgets["model"].set(model)
                
            # モード設定
            mode_key = template["mode"]
            if ai_service in AIModelConfig.AI_CONFIGS:
                mode_value = AIModelConfig.AI_CONFIGS[ai_service]["modes"].get(mode_key)
                if mode_value and mode_value in widgets["mode"]["values"]:
                    widgets["mode"].set(mode_value)
                    
            # 機能設定
            feature_key = template["feature"]
            if ai_service in AIModelConfig.AI_CONFIGS:
                feature_value = AIModelConfig.AI_CONFIGS[ai_service]["features"].get(feature_key)
                if feature_value and feature_value in widgets["feature"]["values"]:
                    widgets["feature"].set(feature_value)
                    
    def create_preview_tab(self):
        """プレビュータブ"""
        preview_tab = ttk.Frame(self.notebook)
        self.notebook.add(preview_tab, text="設定プレビュー")
        
        preview_frame = ttk.Frame(preview_tab, padding="10")
        preview_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_tab.columnconfigure(0, weight=1)
        preview_tab.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        
        # プレビュー更新ボタン
        ttk.Button(preview_frame, text="設定プレビュー更新", 
                  command=self.update_preview).grid(row=0, column=0, pady=(0, 10))
        
        # プレビューテキスト
        from tkinter import scrolledtext
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=20, width=80, 
                                                    wrap=tk.WORD, state="disabled")
        self.preview_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def update_preview(self):
        """設定プレビューを更新"""
        preview_data = {}
        
        for column in self.sheet_columns:
            widgets = self.column_widgets[column]
            ai_service = widgets["ai_service"].get()
            
            if ai_service:
                preview_data[f"{column}列"] = {
                    "AIサービス": AIModelConfig.AI_CONFIGS[ai_service]["display_name"],
                    "モデル": widgets["model"].get(),
                    "モード": widgets["mode"].get(),
                    "機能": widgets["feature"].get()
                }
                
        # プレビューテキスト更新
        self.preview_text.config(state="normal")
        self.preview_text.delete(1.0, tk.END)
        
        preview_content = "=== 列毎AI設定プレビュー ===\n\n"
        for column, settings in preview_data.items():
            preview_content += f"【{column}】\n"
            for key, value in settings.items():
                preview_content += f"  {key}: {value}\n"
            preview_content += "\n"
            
        self.preview_text.insert(tk.END, preview_content)
        self.preview_text.config(state="disabled")
        
    def create_button_frame(self, parent):
        """ボタンフレーム作成"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="OK", command=self.save_and_close, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="適用", command=self.apply_settings, width=10).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="検証", command=self.validate_settings, width=10).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_frame, text="キャンセル", command=self.cancel, width=10).grid(row=0, column=3, padx=(0, 5))
        ttk.Button(button_frame, text="リセット", command=self.reset_settings, width=10).grid(row=0, column=4)
        
    def load_settings(self):
        """既存設定を読み込み"""
        for column in self.sheet_columns:
            if column in self.column_settings:
                settings = self.column_settings[column]
                widgets = self.column_widgets[column]
                
                # AIサービス設定
                ai_service = settings.get("ai_service")
                if ai_service and ai_service in widgets["ai_service"]["values"]:
                    widgets["ai_service"].set(ai_service)
                    self.on_ai_service_changed(column)
                    
                    # その他設定
                    widgets["model"].set(settings.get("model", ""))
                    widgets["mode"].set(settings.get("mode", ""))
                    widgets["feature"].set(settings.get("feature", ""))
                    
    def save_settings(self) -> bool:
        """設定を保存"""
        try:
            # 設定を収集
            for column in self.sheet_columns:
                widgets = self.column_widgets[column]
                ai_service = widgets["ai_service"].get()
                
                if ai_service:
                    self.column_settings[column] = {
                        "ai_service": ai_service,
                        "model": widgets["model"].get(),
                        "mode": widgets["mode"].get(),
                        "feature": widgets["feature"].get()
                    }
                elif column in self.column_settings:
                    del self.column_settings[column]
            
            # 設定を検証
            from src.utils.column_validation import validate_column_ai_settings
            is_valid, validation_message = validate_column_ai_settings(self.column_settings)
            
            if not is_valid:
                # 検証エラーがある場合は確認ダイアログを表示
                result = messagebox.askyesnocancel(
                    "設定検証",
                    f"設定に問題があります。保存を続行しますか？\n\n{validation_message}",
                    icon="warning"
                )
                
                if result is None:  # キャンセル
                    return False
                elif not result:  # いいえ
                    return False
                # はいの場合は続行
            
            return True
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存エラー: {e}")
            return False
            
    def apply_settings(self):
        """設定を適用"""
        if self.save_settings():
            self.config_manager.set("column_ai_settings", self.column_settings)
            if self.config_manager.save_config():
                messagebox.showinfo("情報", "列毎AI設定を適用しました。")
            else:
                messagebox.showerror("エラー", "設定ファイルの保存に失敗しました。")
                
    def save_and_close(self):
        """設定保存して閉じる"""
        if self.save_settings():
            self.config_manager.set("column_ai_settings", self.column_settings)
            if self.config_manager.save_config():
                self.dialog.destroy()
            else:
                messagebox.showerror("エラー", "設定ファイルの保存に失敗しました。")
                
    def cancel(self):
        """キャンセル"""
        self.dialog.destroy()
        
    def validate_settings(self):
        """設定を検証"""
        try:
            # 現在の設定を収集
            current_settings = {}
            for column in self.sheet_columns:
                widgets = self.column_widgets[column]
                ai_service = widgets["ai_service"].get()
                
                if ai_service:
                    current_settings[column] = {
                        "ai_service": ai_service,
                        "model": widgets["model"].get(),
                        "mode": widgets["mode"].get(),
                        "feature": widgets["feature"].get()
                    }
            
            # 検証実行
            from src.utils.column_validation import validate_column_ai_settings
            is_valid, validation_message = validate_column_ai_settings(current_settings)
            
            # 結果を表示
            if is_valid:
                messagebox.showinfo("検証結果", "設定に問題はありません。\n\n" + validation_message)
            else:
                messagebox.showwarning("検証結果", "設定に問題があります。\n\n" + validation_message)
                
        except Exception as e:
            messagebox.showerror("エラー", f"検証中にエラーが発生しました: {e}")
    
    def reset_settings(self):
        """設定をリセット"""
        if messagebox.askyesno("確認", "設定をリセットしますか？"):
            self.column_settings.clear()
            for column in self.sheet_columns:
                widgets = self.column_widgets[column]
                widgets["ai_service"].set("")
                widgets["model"].set("")
                widgets["mode"].set("")
                widgets["feature"].set("")


class DetailSettingsDialog:
    """詳細設定ダイアログ"""
    
    def __init__(self, parent, column: str, settings: Dict[str, Any]):
        self.parent = parent
        self.column = column
        self.settings = settings.copy()
        
        # ダイアログ作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"{column}列 詳細設定")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI構築"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        
        # 設定項目（今後拡張予定）
        ttk.Label(main_frame, text=f"{self.column}列の詳細設定", 
                 font=("", 12, "bold")).grid(row=0, column=0, pady=(0, 20))
        
        ttk.Label(main_frame, text="詳細設定項目は今後実装予定です。").grid(row=1, column=0)
        
        # 閉じるボタン
        ttk.Button(main_frame, text="閉じる", 
                  command=self.dialog.destroy).grid(row=2, column=0, pady=(20, 0))


if __name__ == "__main__":
    # テスト実行
    root = tk.Tk()
    root.withdraw()
    
    from src.utils.config_manager import ConfigManager
    config = ConfigManager()
    
    dialog = ColumnAISettingsDialog(root, config, ["A", "B", "C", "D", "E"])
    root.wait_window(dialog.dialog)
    
    root.destroy()