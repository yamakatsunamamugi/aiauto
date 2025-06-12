"""
GUI上でモデルのJSONを編集する機能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime
from typing import Dict, Optional

class ModelJsonEditor:
    """モデルJSON編集ダイアログ"""
    
    def __init__(self, parent=None):
        self.result = None
        self.json_path = "config/ai_models_verified.json"
        
        # ダイアログ作成
        self.dialog = tk.Toplevel(parent) if parent else tk.Tk()
        self.dialog.title("🤖 AIモデル設定エディタ")
        self.dialog.geometry("900x700")
        
        self._create_widgets()
        self._load_current_json()
        
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 上部: 説明とボタン
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_frame, text="各AIサービスで使用可能なモデルを編集できます。").pack(side=tk.LEFT)
        
        # ボタン
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="📖 フォーマット整形", command=self._format_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✅ 検証", command=self._validate_json).pack(side=tk.LEFT, padx=2)
        
        # 中央: ノートブック（タブ）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # タブ1: 簡易編集
        self.simple_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.simple_frame, text="簡易編集")
        self._create_simple_editor()
        
        # タブ2: JSON直接編集
        self.json_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.json_frame, text="JSON編集")
        self._create_json_editor()
        
        # 下部: ボタン
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(bottom_frame, text="💾 保存", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🔄 再読込", command=self._load_current_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🏭 デフォルトに戻す", command=self._reset_to_default).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="❌ キャンセル", command=self._cancel).pack(side=tk.RIGHT, padx=5)
        
    def _create_simple_editor(self):
        """簡易編集タブを作成"""
        # スクロール可能なフレーム
        canvas = tk.Canvas(self.simple_frame)
        scrollbar = ttk.Scrollbar(self.simple_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 各サービスのエディタ
        self.model_editors = {}
        services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
        
        for i, service in enumerate(services):
            # サービス名
            service_frame = ttk.LabelFrame(scrollable_frame, text=f"📍 {service}", padding="10")
            service_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
            
            # モデルリスト
            ttk.Label(service_frame, text="モデル（1行に1つ）:").grid(row=0, column=0, sticky=tk.W)
            
            editor = tk.Text(service_frame, height=5, width=50)
            editor.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
            
            self.model_editors[service] = editor
            
            # ヒント
            hints = {
                "chatgpt": "例: gpt-4o, gpt-4o-mini, gpt-4-turbo",
                "claude": "例: claude-3.5-sonnet, claude-3-opus",
                "gemini": "例: gemini-1.5-pro, gemini-1.5-flash",
                "genspark": "例: default",
                "google_ai_studio": "例: gemini-1.5-pro"
            }
            ttk.Label(service_frame, text=hints.get(service, ""), foreground="gray").grid(row=2, column=0, sticky=tk.W)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _create_json_editor(self):
        """JSON直接編集タブを作成"""
        # JSON表示エリア
        self.json_text = scrolledtext.ScrolledText(self.json_frame, wrap=tk.NONE, width=80, height=25)
        self.json_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # シンタックスハイライト（簡易版）
        self.json_text.tag_configure("key", foreground="blue")
        self.json_text.tag_configure("string", foreground="green")
        self.json_text.tag_configure("number", foreground="purple")
        
    def _load_current_json(self):
        """現在のJSONを読み込み"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.current_data = json.load(f)
            else:
                # デフォルトデータ
                self.current_data = self._get_default_data()
            
            # 簡易エディタに反映
            self._update_simple_editor()
            
            # JSONエディタに反映
            self._update_json_editor()
            
        except Exception as e:
            messagebox.showerror("エラー", f"JSON読み込みエラー: {e}")
            self.current_data = self._get_default_data()
    
    def _update_simple_editor(self):
        """簡易エディタを更新"""
        models = self.current_data.get("models", {})
        
        for service, editor in self.model_editors.items():
            editor.delete(1.0, tk.END)
            if service in models:
                editor.insert(1.0, "\n".join(models[service]))
    
    def _update_json_editor(self):
        """JSONエディタを更新"""
        self.json_text.delete(1.0, tk.END)
        json_str = json.dumps(self.current_data, indent=2, ensure_ascii=False)
        self.json_text.insert(1.0, json_str)
    
    def _format_json(self):
        """JSON整形"""
        try:
            # 現在のJSONテキストを取得
            json_str = self.json_text.get(1.0, tk.END).strip()
            data = json.loads(json_str)
            
            # 整形して再表示
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(1.0, formatted)
            
            messagebox.showinfo("成功", "JSONを整形しました")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("エラー", f"JSON形式エラー: {e}")
    
    def _validate_json(self):
        """JSON検証"""
        try:
            # 現在のタブを確認
            current_tab = self.notebook.tab(self.notebook.select(), "text")
            
            if current_tab == "簡易編集":
                # 簡易エディタから取得
                models = {}
                for service, editor in self.model_editors.items():
                    text = editor.get(1.0, tk.END).strip()
                    models[service] = [line.strip() for line in text.split('\n') if line.strip()]
                
                # データ構造を作成
                data = self.current_data.copy()
                data["models"] = models
                data["last_verified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            else:
                # JSONエディタから取得
                json_str = self.json_text.get(1.0, tk.END).strip()
                data = json.loads(json_str)
            
            # 必須フィールドチェック
            required = ["models", "last_verified"]
            missing = [field for field in required if field not in data]
            
            if missing:
                messagebox.showwarning("警告", f"必須フィールドが不足: {', '.join(missing)}")
                return False
            
            # サービスチェック
            required_services = ["chatgpt", "claude", "gemini", "genspark", "google_ai_studio"]
            missing_services = [s for s in required_services if s not in data.get("models", {})]
            
            if missing_services:
                messagebox.showwarning("警告", f"サービスが不足: {', '.join(missing_services)}")
                return False
            
            messagebox.showinfo("成功", "✅ JSON検証に合格しました")
            return True
            
        except json.JSONDecodeError as e:
            messagebox.showerror("エラー", f"JSON形式エラー: {e}")
            return False
        except Exception as e:
            messagebox.showerror("エラー", f"検証エラー: {e}")
            return False
    
    def _save(self):
        """保存"""
        try:
            # 検証
            if not self._validate_json():
                return
            
            # 現在のタブから取得
            current_tab = self.notebook.tab(self.notebook.select(), "text")
            
            if current_tab == "簡易編集":
                # 簡易エディタから取得
                models = {}
                for service, editor in self.model_editors.items():
                    text = editor.get(1.0, tk.END).strip()
                    models[service] = [line.strip() for line in text.split('\n') if line.strip()]
                
                # データ更新
                self.current_data["models"] = models
                self.current_data["last_verified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.current_data["verified_by"] = "gui_editor"
                
            else:
                # JSONエディタから取得
                json_str = self.json_text.get(1.0, tk.END).strip()
                self.current_data = json.loads(json_str)
            
            # ファイルに保存
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, indent=2, ensure_ascii=False)
            
            self.result = self.current_data
            messagebox.showinfo("成功", f"設定を保存しました:\n{self.json_path}")
            
        except Exception as e:
            messagebox.showerror("エラー", f"保存エラー: {e}")
    
    def _reset_to_default(self):
        """デフォルトに戻す"""
        if messagebox.askyesno("確認", "デフォルト設定に戻しますか？"):
            self.current_data = self._get_default_data()
            self._update_simple_editor()
            self._update_json_editor()
    
    def _get_default_data(self) -> Dict:
        """デフォルトデータ"""
        return {
            "last_verified": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "verified_by": "default",
            "version": "1.0",
            "models": {
                "chatgpt": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "claude": ["claude-3.5-sonnet", "claude-3-opus"],
                "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
                "genspark": ["default"],
                "google_ai_studio": ["gemini-1.5-pro"]
            },
            "notes": {
                "chatgpt": "ChatGPTで利用可能なモデル",
                "claude": "Claudeで利用可能なモデル",
                "gemini": "Geminiで利用可能なモデル",
                "genspark": "モデル名は非公開",
                "google_ai_studio": "Google AI Studioで利用可能なモデル"
            }
        }
    
    def _cancel(self):
        """キャンセル"""
        self.dialog.destroy()
    
    def show(self) -> Optional[Dict]:
        """ダイアログを表示"""
        self.dialog.wait_window()
        return self.result


# テスト用
if __name__ == "__main__":
    editor = ModelJsonEditor()
    result = editor.show()
    if result:
        print("保存されたデータ:")
        print(json.dumps(result, indent=2, ensure_ascii=False))