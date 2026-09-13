# 微信 API 带鉴权转发（让 Claude Code 云端会话直接发公众号）

## 为什么需要

微信公众号接口要求调用方 IP 在后台白名单里。本机流程靠 SSH 隧道借用北京
阿里云服务器的固定 IP（`scripts/wechat_proxy_run.sh`）；Claude Code 云端
会话出口 IP 动态、也无法建 SSH 隧道，所以在该服务器上架一个**带鉴权的
HTTPS 转发**：云端把请求发给它，它原样转给 `api.weixin.qq.com`。

```
云端会话 --HTTPS+X-Relay-Token--> 阿里云BJ(nginx, IP已在白名单) --> api.weixin.qq.com
```

`wechat_draft_sync.py` / `wechat_upload_thumb.py` 已支持两个环境变量：

- `WECHAT_API_BASE`：设为 `https://<你的域名>` 时，所有 API 调用改走转发；
  不设则直连官方地址（本机流程完全不受影响）。
- `WECHAT_RELAY_TOKEN`：设了就会随每个请求带上 `X-Relay-Token` 头。

## 服务器端一次性配置（阿里云 BJ）

前提：有一个域名可用，将其 A 记录指到服务器公网 IP（下称 `RELAY_DOMAIN`）。

```bash
# 1. 安装 nginx 与 certbot（Ubuntu/Debian 示例）
sudo apt install -y nginx certbot python3-certbot-nginx

# 2. 生成转发令牌（保存好，云端要用）
openssl rand -hex 32

# 3. 安装配置：把仓库里 scripts/wechat_relay/nginx-wechat-relay.conf
#    复制为 /etc/nginx/conf.d/wechat-relay.conf，
#    并把其中 RELAY_DOMAIN、RELAY_TOKEN_VALUE 两个占位符替换为真实值
sudo cp nginx-wechat-relay.conf /etc/nginx/conf.d/wechat-relay.conf
sudo sed -i "s/RELAY_DOMAIN/你的域名/; s/RELAY_TOKEN_VALUE/生成的token/" \
    /etc/nginx/conf.d/wechat-relay.conf
sudo nginx -t && sudo systemctl reload nginx

# 4. 签发 HTTPS 证书（certbot 会自动改写配置加上 443/TLS）
sudo certbot --nginx -d 你的域名

# 5. 验证：
#    无 token 应得 403：
curl -si https://你的域名/cgi-bin/token | head -1
#    带 token 应得微信的 JSON 报错（40013 invalid appid，说明已通到微信）：
curl -s -H "X-Relay-Token: 生成的token" \
    "https://你的域名/cgi-bin/token?grant_type=client_credential&appid=x&secret=x"
```

阿里云安全组需放行 80/443 入方向。

## 云端环境配置（claude.ai/code → 该仓库的 Environment）

1. **网络策略**：允许访问 `你的域名`。
2. **环境变量**（Secrets）：

   | 变量 | 值 |
   | --- | --- |
   | `WECHAT_API_BASE` | `https://你的域名` |
   | `WECHAT_RELAY_TOKEN` | 上面生成的 token |
   | `WECHAT_APP_ID` | 公众号 AppID |
   | `WECHAT_APP_SECRET` | 公众号 AppSecret |

之后云端会话即可直接运行（不再需要 `wechat_proxy_run.sh`）：

```bash
python3 scripts/wechat_upload_thumb.py images/wechat-covers/xxx.jpg
python3 scripts/wechat_draft_sync.py create --markdown _posts/xxx.md --skip-download
```

## 安全说明

- 令牌是唯一门禁：泄露即等于把「从白名单 IP 调微信接口」的能力交出去，
  请只存在云端环境变量里，怀疑泄露时换新 token 并 reload nginx。
- nginx 默认日志不记录请求头，token 不会落日志；access_token 出现在 URL
  查询串中会进 access_log，介意可对该 location 关闭 access_log。
- 转发只放行 `/cgi-bin/` 路径与 GET/POST 方法，其余一律 404/403。
