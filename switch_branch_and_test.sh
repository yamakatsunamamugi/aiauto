#!/bin/bash
# ブランチ切り替えとテスト実行スクリプト

echo "🔄 ブランチ切り替えスクリプト"
echo "=================================="

# 1. 現在のブランチを確認
echo "📍 現在のブランチ:"
git branch --show-current

# 2. 変更状況を確認
echo ""
echo "📋 変更ファイルの確認:"
git status --short

# 3. 変更がある場合は一時保存
if [[ -n $(git status --porcelain) ]]; then
    echo ""
    echo "⚠️  未コミットの変更があります"
    echo "💾 変更を一時保存します..."
    git stash save "自動保存: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✅ 変更を保存しました"
fi

# 4. feature/chrome-extensionブランチに切り替え
echo ""
echo "🔄 feature/chrome-extensionブランチに切り替え中..."
git checkout feature/chrome-extension

# 5. 切り替え結果を確認
if [ $? -eq 0 ]; then
    echo "✅ ブランチ切り替え成功！"
    echo "📍 現在のブランチ: $(git branch --show-current)"
else
    echo "❌ ブランチ切り替えに失敗しました"
    exit 1
fi

# 6. my_automation_gui.pyが存在するか確認
echo ""
echo "📄 ファイルの確認:"
if [ -f "my_automation_gui.py" ]; then
    echo "✅ my_automation_gui.py が見つかりました"
else
    echo "❌ my_automation_gui.py が見つかりません"
fi

# 7. アプリを起動するか確認
echo ""
echo "🚀 アプリを起動しますか？ (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "📱 アプリを起動します..."
    python3 my_automation_gui.py
fi