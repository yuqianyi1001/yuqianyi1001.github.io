#!/bin/zsh
# 逐张导出 PNG，张数按 cards.html 里的卡片自动计算
#   ./render.sh        竖屏 1080×1440 → out/
#   ./render.sh land   横屏 1920×1080 → out-16x9/
cd "$(dirname "$0")"
CHROME="${CHROME:-$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell}"
N=$(grep -c '<section class="card' cards.html)
if [[ "$1" == "land" ]]; then OUT=out-16x9; SIZE=1920,1080; Q="&land=1"; else OUT=out; SIZE=1080,1440; Q=""; fi
rm -rf $OUT && mkdir -p $OUT
for i in $(seq 1 $N); do
  "$CHROME" --headless --hide-scrollbars --window-size=$SIZE --force-device-scale-factor=1 \
    --virtual-time-budget=2000 --screenshot="$OUT/card-$i.png" "file://$PWD/cards.html?c=$i$Q" 2>/dev/null
done
ls $OUT
