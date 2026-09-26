#!/bin/bash
# Deploy scripts/wechat_auto_sync.py to the Beijing Aliyun server and install its cron job.
# Usage: scripts/wechat_auto_sync_deploy.sh            (copy code only)
#        scripts/wechat_auto_sync_deploy.sh --setup    (first time: python, venv, .env, cron)
#
# Server layout: /opt/wechat-sync/{*.py,*.css,*.html,.env,venv,state/state.json,logs/sync.log}
# The local SSH tunnel flow (scripts/wechat_proxy_run.sh) is not touched.
set -euo pipefail

SSH_HOST=aliyun-bj  # see ~/.ssh/config
REMOTE_DIR=/opt/wechat-sync
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

ssh "$SSH_HOST" "mkdir -p $REMOTE_DIR/state $REMOTE_DIR/logs"
scp -q "$SCRIPT_DIR/wechat_auto_sync.py" "$SCRIPT_DIR/wechat_draft_sync.py" "$SCRIPT_DIR/wechat_upload_thumb.py" \
    "$SCRIPT_DIR/markdown_.css" "$SCRIPT_DIR/wechat_footer.html" "$SSH_HOST:$REMOTE_DIR/"
echo "code copied to $SSH_HOST:$REMOTE_DIR"

if [[ "${1:-}" != "--setup" ]]; then
    exit 0
fi

# WeChat credentials: taken from ~/.env (WEIXIN_AppID / WEIXIN_AppSecret), never printed.
grep -E '^(WEIXIN_AppID|WEIXIN_AppSecret|WECHAT_APP_ID|WECHAT_APP_SECRET)=' "$HOME/.env" \
    | ssh "$SSH_HOST" "umask 077 && cat > $REMOTE_DIR/.env"

ssh "$SSH_HOST" bash -s <<EOF
set -euo pipefail
command -v python3.11 >/dev/null || dnf install -y -q python3.11
[ -x $REMOTE_DIR/venv/bin/python ] || python3.11 -m venv $REMOTE_DIR/venv
$REMOTE_DIR/venv/bin/pip install -q -i https://mirrors.aliyun.com/pypi/simple/ pyyaml markdown
CRON_LINE="*/10 * * * * cd $REMOTE_DIR && flock -n state/lock venv/bin/python wechat_auto_sync.py run >> logs/sync.log 2>&1"
{ crontab -l 2>/dev/null | grep -v 'wechat_auto_sync.py' || true; echo "\$CRON_LINE"; } | crontab -
crontab -l | grep wechat_auto_sync
EOF
