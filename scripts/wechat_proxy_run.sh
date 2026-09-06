#!/bin/bash
# Run a command with WeChat API traffic routed through the Beijing Aliyun proxy.
# Usage: scripts/wechat_proxy_run.sh python3 scripts/wechat_draft_sync.py list
set -euo pipefail

LOCAL_PORT=18888
SSH_HOST=aliyun-bj  # see ~/.ssh/config

if ! curl -s --max-time 3 --proxy "http://127.0.0.1:${LOCAL_PORT}" https://api.weixin.qq.com/cgi-bin/token -o /dev/null; then
    echo "[wechat-proxy] opening SSH tunnel to ${SSH_HOST}..." >&2
    ssh -o BatchMode=yes -f -N -L "${LOCAL_PORT}:127.0.0.1:8888" "${SSH_HOST}"
    sleep 1
fi

export HTTPS_PROXY="http://127.0.0.1:${LOCAL_PORT}"
export https_proxy="http://127.0.0.1:${LOCAL_PORT}"
exec "$@"
