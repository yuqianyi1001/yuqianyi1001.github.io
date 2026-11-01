#!/bin/zsh
# 逐张导出 1920×1080 PNG → out/（张数按 cards.html 里的卡片自动计算）
cd "$(dirname "$0")"
CHROME="${CHROME:-$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell}"
N=$(grep -c '<section class="card' cards.html)
rm -rf out && mkdir -p out
for i in $(seq 1 $N); do
  "$CHROME" --headless --hide-scrollbars --window-size=1920,1080 --force-device-scale-factor=1 \
    --virtual-time-budget=2000 --screenshot="out/card-$i.png" "file://$PWD/cards.html?c=$i" 2>/dev/null
done
ls out
