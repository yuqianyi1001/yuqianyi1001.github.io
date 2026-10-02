#!/usr/bin/env python3
"""Poll the GitHub repo for new posts and save them as WeChat drafts.

Runs from cron on the Beijing Aliyun server (its IP is in the WeChat
whitelist). It never clones the repo: it reads the `_posts` listing and the
needed files (the post Markdown plus the images it references) through the
GitHub API, pinned to one commit per run.

Which posts are synced:
- posts whose filename date is on or after SYNC_SINCE (default 2026-09-25);
- older posts only when their front matter has `wechat_sync: force`;
- `wechat_sync: false` skips a post; so does an existing `wechat_link`
  (already published);
- without `thumb_media_id` in front matter, the post's first image is uploaded
  as a permanent material and used as the cover (its media_id is kept in
  state.json, so a retry does not upload it again).

Duplicate protection:
- a post is recorded in state.json right after `draft/add` succeeds and is
  never sent again;
- before creating, the draft box (and the 20 latest published articles, when
  the account may call that API) is checked for the same title; a match is
  recorded instead of creating a new draft.

Failure log:
- failures are written to one special WeChat draft titled FAILURE_DRAFT_TITLE.
  It lists every post that currently fails with its reason, and the latest
  ones that recovered. There is only ever one such draft: it is created on the
  first failure and updated in place afterwards, and only when something
  changed (a post is retried every run, but the same error is not rewritten).
  It also reports when the copy of these scripts on the server differs from
  scripts/ in the repo (a fix that was never deployed).
- optionally, when NOTIFY_URL is set, the same events are also sent as
  Telegram messages. The server cannot reach api.telegram.org itself;
  NOTIFY_URL is a relay that can (scripts/telegram-relay), authenticated with
  NOTIFY_SECRET.

Usage:
    python3 wechat_auto_sync.py run [--dry-run] [--recheck]
    python3 wechat_auto_sync.py notify-test                      # send a test notification
    python3 wechat_auto_sync.py status
    python3 wechat_auto_sync.py mark _posts/2026-09-25-xxx.md     # record as done, never create
    python3 wechat_auto_sync.py forget _posts/2026-09-26-xxx.md   # sync it again
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import wechat_draft_sync as wds  # noqa: E402
from wechat_upload_thumb import add_material_image  # noqa: E402

REPO = os.getenv("GITHUB_REPO", "yuqianyi1001/yuqianyi1001.github.io")
BRANCH = os.getenv("GITHUB_BRANCH", "master")
SYNC_SINCE = os.getenv("SYNC_SINCE", "2026-09-25")
BASE_DIR = pathlib.Path(__file__).resolve().parent
STATE_DIR = pathlib.Path(os.getenv("WECHAT_SYNC_STATE_DIR", str(BASE_DIR / "state")))
WORK_DIR = pathlib.Path(os.getenv("WECHAT_SYNC_WORK_DIR", str(BASE_DIR / "work")))

# What scripts/wechat_auto_sync_deploy.sh copies to the server, from scripts/ in the repo.
DEPLOYED_FILES = (
    "wechat_auto_sync.py",
    "wechat_draft_sync.py",
    "wechat_upload_thumb.py",
    "markdown_.css",
    "wechat_footer.html",
)

FAILURE_DRAFT_TITLE = "【同步失败】公众号草稿同步失败记录"
RECOVERED_KEEP = 20  # how many recovered entries the failure log keeps
# Failures that are not about one post.
KEY_DEPLOY = "服务器上的同步脚本"
KEY_WECHAT = "微信接口"
WECHAT_ERROR_NOTES = {
    "45004": "摘要 description 超过 120 字",
    "40164": "服务器 IP 不在公众号的 IP 白名单里",
}

POST_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-.+\.md$")
# Image URLs that point back into this repo, e.g. raw.githubusercontent.com/<repo>/master/images/x.jpg
REPO_RAW_RE = re.compile(
    r"^https?://raw\.githubusercontent\.com/" + re.escape(REPO) + r"/[^/]+/(.+)$", re.IGNORECASE
)
REPO_PAGES_RE = re.compile(
    r"^https?://" + re.escape(REPO.split("/")[1]) + r"/(images/.+)$", re.IGNORECASE
)
WECHAT_IMAGE_HOSTS = ("mmbiz.qpic.cn", "mmbiz.qlogo.cn")


def log(message: str) -> None:
    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {message}", flush=True)


# Notifications ----------------------------------------------------------------


def notify(text: str) -> bool:
    """Send `text` through the relay. Returns False (and logs) if it is not configured or fails."""

    url = os.getenv("NOTIFY_URL")
    if not url:
        return False
    request = urllib.request.Request(
        url,
        data=json.dumps({"text": text}, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('NOTIFY_SECRET', '')}",
            "User-Agent": "wechat-auto-sync",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response.read()
    except Exception as exc:  # noqa: BLE001 - a notification must never break the sync
        log(f"notify failed: {exc}")
        return False
    return True


def error_signature(exc: object) -> str:
    """The stable part of an error: WeChat appends a different hint/rid to every response."""

    text = str(exc)
    match = re.search(r'"errcode":\s*(-?\d+).*?"errmsg":\s*"([^"]*)"', text)
    if match:
        code, message = match.group(1), re.sub(r"\s*(hint:|rid:).*", "", match.group(2)).strip()
        known = WECHAT_ERROR_NOTES.get(code)
        return f"微信接口错误 {code}：{message}" + (f"（{known}）" if known else "")
    return re.sub(r"\s*(hint:|rid:).*", "", text).strip()[:300]


def now_iso() -> str:
    return dt.datetime.now().isoformat(sep=" ", timespec="seconds")


def record_failure(state: Dict[str, object], key: str, title: str, exc: object) -> None:
    """Remember that `key` (a post, or KEY_DEPLOY / KEY_WECHAT) fails. The same error is kept as is."""

    failing: Dict[str, Dict[str, object]] = state.setdefault("failing", {})  # type: ignore[assignment]
    signature = error_signature(exc)
    entry = failing.get(key)
    if entry and entry.get("error") == signature:
        return
    failing[key] = {
        "title": title,
        "error": signature,
        "since": entry["since"] if entry else now_iso(),
        "notified": False,
    }
    save_state(state)


def record_recovery(state: Dict[str, object], key: str) -> bool:
    """Move `key` from the failing list to the recovered list. True if it was failing."""

    failing: Dict[str, Dict[str, object]] = state.setdefault("failing", {})  # type: ignore[assignment]
    entry = failing.pop(key, None)
    if entry is None:
        return False
    recovered: List[Dict[str, object]] = state.setdefault("recovered", [])  # type: ignore[assignment]
    recovered.append({"key": key, "title": entry.get("title"), "error": entry.get("error"),
                      "since": entry.get("since"), "recovered_at": now_iso()})
    del recovered[:-RECOVERED_KEEP]
    save_state(state)
    return True


def send_failure_notifications(state: Dict[str, object]) -> None:
    """Telegram (optional): one message per failure that has not been sent yet."""

    for key, entry in state.get("failing", {}).items():  # type: ignore[union-attr]
        if entry.get("notified"):
            continue
        subject = f"《{entry['title']}》\n{key}" if entry.get("title") else key
        if notify(f"❌ 公众号草稿同步失败\n{subject}\n原因：{entry['error']}\n每 10 分钟自动重试；同一原因不再重复通知。"):
            entry["notified"] = True  # left unset when the relay is down, so it is sent next run
            save_state(state)


def render_failure_log(state: Dict[str, object]) -> Tuple[str, str, str]:
    """Return (signature, digest, html) of the failure-log draft for the current state."""

    failing: Dict[str, Dict[str, object]] = state.get("failing", {})  # type: ignore[assignment]
    recovered: List[Dict[str, object]] = state.get("recovered", [])  # type: ignore[assignment]
    esc = html.escape

    def block(key: str, entry: Dict[str, object], extra: str) -> str:
        head = f"《{esc(str(entry['title']))}》" if entry.get("title") else esc(key)
        where = f"文件：{esc(key)}<br>" if entry.get("title") else ""
        return f"<p><strong>{head}</strong><br>{where}原因：{esc(str(entry.get('error')))}<br>{extra}</p>"

    parts = ["<p>这是同步脚本自动维护的失败记录，不是文章，请不要发布。内容有变化时会自动更新；失败的文章每 10 分钟自动重试。</p>"]
    parts.append(f"<h2>当前同步失败（{len(failing)}）</h2>")
    if failing:
        parts += [block(key, entry, f"首次失败：{esc(str(entry.get('since')))}") for key, entry in sorted(failing.items())]
    else:
        parts.append("<p>当前没有同步失败的文章。</p>")
    if recovered:
        parts.append(f"<h2>已恢复（最近 {len(recovered)} 条）</h2>")
        parts += [
            block(str(entry["key"]), entry, f"失败于：{esc(str(entry.get('since')))}<br>恢复于：{esc(str(entry.get('recovered_at')))}")
            for entry in reversed(recovered)
        ]
    signature = hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()
    parts.append(f"<p>更新时间：{now_iso()}</p>")
    if failing:
        names = "；".join(str(entry.get("title") or key) for key, entry in sorted(failing.items()))
        digest = f"当前 {len(failing)} 项同步失败：{names}"
    else:
        digest = "当前没有同步失败的文章。"
    return signature, digest, "".join(parts)


def sync_failure_draft(client: "wds.WeChatClient", state: Dict[str, object], titles: Dict[str, str]) -> None:
    """Create or update the single failure-log draft, only when its content changed."""

    record: Dict[str, object] = state.setdefault("failure_log", {})  # type: ignore[assignment]
    failing = state.get("failing", {})
    signature, digest, content = render_failure_log(state)
    if record.get("signature") == signature:
        return
    media_id = record.get("media_id") or titles.get(FAILURE_DRAFT_TITLE)
    if not failing and not media_id:
        return  # nothing has failed yet: no draft
    try:
        thumbs = list(state.get("thumbs", {}).values())  # type: ignore[union-attr]
        if not thumbs:
            raise RuntimeError("no cover image has been uploaded yet, and a draft needs one")
        payload = wds.build_article_payload(
            {"title": FAILURE_DRAFT_TITLE, "digest": digest, "thumb_media_id": thumbs[-1]}, content
        )
        if media_id:
            try:
                client.update_draft(str(media_id), 0, payload)
            except wds.WeChatAPIError as exc:
                log(f"failure log: cannot update draft {media_id} ({error_signature(exc)})")
                media_id = None  # e.g. the draft was deleted by hand
        if not media_id:
            if not failing:
                record.clear()  # the log was deleted and there is nothing to report
                save_state(state)
                return
            media_id = client.add_draft([payload])
        record.update({"media_id": media_id, "signature": signature, "updated_at": now_iso()})
        save_state(state)
        log(f"failure log draft {media_id}: {digest}")
    except Exception as exc:  # noqa: BLE001 - the log must never break the sync
        log(f"failure log: could not write the draft: {exc}")


def report_success(state: Dict[str, object], key: str, title: str) -> None:
    retried = record_recovery(state, key)
    notify(f"✅ 公众号草稿已创建{'（重试成功）' if retried else ''}\n《{title}》\n{key}")


# GitHub -----------------------------------------------------------------------


def github_get(path: str, *, raw: bool = False) -> bytes:
    headers = {
        "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json",
        "User-Agent": "wechat-auto-sync",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def github_json(path: str) -> Dict[str, object]:
    return json.loads(github_get(path).decode("utf-8"))


def latest_commit() -> str:
    data = github_json(f"/repos/{REPO}/commits/{BRANCH}")
    return str(data["sha"])


def list_posts(commit: str) -> Dict[str, str]:
    """Return {filename: blob_sha} for the Markdown files in _posts at `commit`."""

    data = github_json(f"/repos/{REPO}/git/trees/{commit}:_posts")
    if data.get("truncated"):
        raise RuntimeError("GitHub tree listing for _posts was truncated")
    return {
        str(item["path"]): str(item["sha"])
        for item in data.get("tree", [])
        if item.get("type") == "blob" and str(item.get("path", "")).endswith(".md")
    }


def fetch_repo_file(commit: str, repo_path: str) -> bytes:
    quoted = urllib.parse.quote(repo_path)
    return github_get(f"/repos/{REPO}/contents/{quoted}?ref={commit}", raw=True)


def stale_code(commit: str) -> List[str]:
    """Names of the files next to this script that differ from scripts/ in the repo at `commit`.

    The server's copy is installed by hand (wechat_auto_sync_deploy.sh), so a fix
    that is committed but not deployed would otherwise go unnoticed.
    """

    data = github_json(f"/repos/{REPO}/git/trees/{commit}:scripts")
    in_repo = {str(item["path"]): str(item["sha"]) for item in data.get("tree", [])}
    stale = []
    for name in DEPLOYED_FILES:
        path = BASE_DIR / name
        if name not in in_repo or not path.is_file():
            continue
        content = path.read_bytes()
        blob_sha = hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()
        if blob_sha != in_repo[name]:
            stale.append(name)
    return stale


# State ------------------------------------------------------------------------


def load_state() -> Dict[str, object]:
    path = STATE_DIR / "state.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"synced": {}, "old_blobs": {}, "thumbs": {}, "last_commit": None}


def save_state(state: Dict[str, object]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "state.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


# Posts ------------------------------------------------------------------------


def split_front_matter(text: str) -> Tuple[Dict[str, object], str]:
    wds.ensure_yaml_available()
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise RuntimeError("Malformed front matter")
    metadata = wds.yaml.safe_load(parts[1]) or {}
    if not isinstance(metadata, dict):
        raise RuntimeError("Front matter must be a mapping")
    return metadata, parts[2]


def sync_flag(metadata: Dict[str, object]) -> str:
    value = metadata.get("wechat_sync")
    if value is False or str(value).strip().lower() in ("false", "no", "off"):
        return "off"
    if str(value).strip().lower() == "force":
        return "force"
    return ""


def repo_path_for_image(ref: str) -> Optional[str]:
    """Map an image reference to a path inside the repo, or None if external."""

    match = REPO_RAW_RE.match(ref) or REPO_PAGES_RE.match(ref)
    if match:
        return urllib.parse.unquote(match.group(1))
    if ref.startswith(("http://", "https://")):
        return None
    if ref.startswith("/"):
        return ref.lstrip("/")
    resolved = os.path.normpath(os.path.join("_posts", ref))
    if resolved.startswith(".."):
        raise RuntimeError(f"Image path escapes the repo: {ref}")
    return resolved


def localize_images(text: str, commit: str, work_dir: pathlib.Path) -> str:
    """Download every non-WeChat image the post references and point it at the local copy."""

    downloaded: Dict[str, str] = {}

    def download(ref: str) -> str:
        if ref in downloaded:
            return downloaded[ref]
        host = urllib.parse.urlparse(ref).netloc.lower()
        if host.endswith(WECHAT_IMAGE_HOSTS):
            return ref
        repo_path = repo_path_for_image(ref)
        if repo_path is not None:
            data = fetch_repo_file(commit, repo_path)
            target = work_dir / repo_path
        else:
            request = urllib.request.Request(ref, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            name = pathlib.PurePosixPath(urllib.parse.urlparse(ref).path).name or "image.jpg"
            target = work_dir / "external" / f"{len(downloaded):02d}-{name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        downloaded[ref] = str(target)
        return downloaded[ref]

    def replace_inline(match: re.Match) -> str:
        alt_text, ref = match.groups()
        return f"![{alt_text}]({download(ref)})"

    def replace_reference(match: re.Match) -> str:
        label, ref, suffix = match.groups()
        return f"[{label}]: {download(ref)}{suffix}"

    text = wds.MARKDOWN_IMAGE_PATTERN.sub(replace_inline, text)
    return wds.MARKDOWN_REF_IMAGE_PATTERN.sub(replace_reference, text)


# WeChat -----------------------------------------------------------------------


def _titles_from_items(payload: Dict[str, object]) -> Dict[str, str]:
    titles: Dict[str, str] = {}
    for item in payload.get("item", []) or []:
        media_id = str(item.get("media_id") or item.get("article_id") or "")
        for article in (item.get("content") or {}).get("news_item", []) or []:
            title = str(article.get("title", "")).strip()
            if title:
                titles.setdefault(title, media_id)
    return titles


def existing_wechat_titles(client: wds.WeChatClient) -> Dict[str, str]:
    """Titles already in the draft box (all pages) or among the 20 latest published articles."""

    titles: Dict[str, str] = {}
    offset = 0
    while True:
        page = client.list_drafts(offset, 20, no_content=0)
        titles.update(_titles_from_items(page))
        count = len(page.get("item", []) or [])
        offset += count
        if count == 0 or offset >= int(page.get("total_count", 0)):
            break
    try:
        published = client._do_api_request(
            "POST", "/cgi-bin/freepublish/batchget", {"offset": 0, "count": 20, "no_content": 1}
        )
    except wds.WeChatAPIError as exc:
        # 48001: this account has no permission for the published-list API;
        # published posts are then recognised only by `wechat_link`.
        if "48001" not in str(exc):
            raise
        published = {}
    for title, media_id in _titles_from_items(published).items():
        titles.setdefault(title, media_id)
    return titles


def cover_media_id(client: wds.WeChatClient, state: Dict[str, object], key: str, local_text: str) -> str:
    """Upload the post's first image as a permanent material and return its media_id."""

    thumbs: Dict[str, str] = state["thumbs"]  # type: ignore[assignment]
    if key in thumbs:
        return thumbs[key]
    match = wds.MARKDOWN_IMAGE_PATTERN.search(local_text)
    image_path = pathlib.Path(match.group(2)) if match else None
    if image_path is None or not image_path.is_file():
        raise RuntimeError("no local image to use as cover")
    media_id = str(add_material_image(client, image_path)["media_id"])
    thumbs[key] = media_id
    save_state(state)
    log(f"uploaded cover {image_path.name} for {key}: {media_id}")
    return media_id


# Run --------------------------------------------------------------------------


def pick_candidates(
    posts: Dict[str, str], commit: str, state: Dict[str, object]
) -> List[Tuple[str, Dict[str, object], str]]:
    """Return [(name, metadata, text)] for posts that need a draft."""

    synced: Dict[str, object] = state["synced"]  # type: ignore[assignment]
    old_blobs: Dict[str, str] = state["old_blobs"]  # type: ignore[assignment]
    first_run = not old_blobs and state.get("last_commit") is None
    candidates = []
    for name, blob in sorted(posts.items()):
        key = f"_posts/{name}"
        if key in synced:
            continue
        match = POST_NAME_RE.match(name)
        is_new = bool(match) and match.group(1) >= SYNC_SINCE
        if not is_new:
            # Older posts only matter when a `wechat_sync: force` mark is added,
            # which changes the blob; unchanged blobs are not re-read.
            if first_run or old_blobs.get(name) == blob:
                old_blobs[name] = blob
                continue
        text = fetch_repo_file(commit, key).decode("utf-8")
        metadata, _ = split_front_matter(text)
        flag = sync_flag(metadata)
        if not is_new:
            old_blobs[name] = blob
            if flag != "force":
                continue
        if flag == "off":
            log(f"skip {key}: wechat_sync is false")
            continue
        if metadata.get("wechat_link"):
            log(f"skip {key}: already published (wechat_link)")
            synced[key] = {"how": "published", "title": metadata.get("title"), "commit": commit}
            continue
        if not str(metadata.get("thumb_media_id") or "").strip() and not wds.MARKDOWN_IMAGE_PATTERN.search(text):
            log(f"wait {key}: no thumb_media_id and no image to use as cover")
            continue
        candidates.append((name, metadata, text))
    return candidates


def cmd_run(args: argparse.Namespace) -> int:
    state = load_state()
    commit = latest_commit()
    state.setdefault("thumbs", {})
    if commit == state.get("last_commit") and not (args.dry_run or args.recheck):
        return 0

    log(f"commit {commit[:10]} on {BRANCH}")
    state.pop("failures", None)  # replaced by "failing"
    failing: Dict[str, Dict[str, object]] = state.setdefault("failing", {})  # type: ignore[assignment]
    if (state.get("code_checked") != commit or KEY_DEPLOY in failing) and not args.dry_run:
        stale = stale_code(commit)
        if stale:
            log(f"STALE CODE: {', '.join(stale)} differ from the repo; run scripts/wechat_auto_sync_deploy.sh")
            record_failure(
                state, KEY_DEPLOY, "", f"和仓库里的不一致（{'、'.join(stale)}），请运行 scripts/wechat_auto_sync_deploy.sh"
            )
        else:
            record_recovery(state, KEY_DEPLOY)
        state["code_checked"] = commit
        save_state(state)
    posts = list_posts(commit)
    candidates = pick_candidates(posts, commit, state)
    if not args.dry_run:
        # A post that failed before but is no longer a candidate needs no draft any more
        # (published, switched off, removed, or waiting for a cover).
        wanted = {f"_posts/{name}" for name, _, _ in candidates}
        for key in [k for k in failing if k.startswith("_posts/") and k not in wanted]:
            record_recovery(state, key)
    log_pending = bool(failing or state.get("failure_log", {}).get("media_id")) and (
        render_failure_log(state)[0] != state.get("failure_log", {}).get("signature")
    )
    if not candidates and not log_pending:
        log("no posts to sync")
        if not args.dry_run:
            state["last_commit"] = commit
            save_state(state)
        return 0

    client = wds.WeChatClient(
        app_id=os.getenv("WECHAT_APP_ID"), app_secret=os.getenv("WECHAT_APP_SECRET")
    )
    titles = existing_wechat_titles(client)
    if not args.dry_run:
        record_recovery(state, KEY_WECHAT)  # the WeChat API answers again
    failed_now = set()
    synced: Dict[str, object] = state["synced"]  # type: ignore[assignment]
    failures = 0

    for name, metadata, text in candidates:
        key = f"_posts/{name}"
        title = str(metadata.get("title", "")).strip()
        if title in titles:
            log(f"adopt {key}: a WeChat article titled 《{title}》 already exists ({titles[title]})")
            if not args.dry_run:
                synced[key] = {"how": "adopted", "media_id": titles[title], "title": title, "commit": commit}
                save_state(state)
            continue
        if args.dry_run:
            log(f"would create draft for {key} 《{title}》")
            continue

        work_dir = WORK_DIR / commit[:10]
        try:
            local_text = localize_images(text, commit, work_dir)
            md_path = work_dir / "_posts" / name
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(local_text, encoding="utf-8")
            meta, html_content = wds.load_markdown_article(md_path, client)
            if not str(meta.get("thumb_media_id") or "").strip():
                meta["thumb_media_id"] = cover_media_id(client, state, key, local_text)
            media_id = client.add_draft([wds.build_article_payload(meta, html_content)])
        except Exception as exc:  # noqa: BLE001 - one bad post must not block the others
            failures += 1
            failed_now.add(key)
            log(f"FAIL {key}: {exc}")
            record_failure(state, key, title, exc)
            continue
        synced[key] = {
            "how": "created",
            "media_id": media_id,
            "title": title,
            "commit": commit,
            "synced_at": dt.datetime.now().isoformat(timespec="seconds"),
        }
        report_success(state, key, title)
        save_state(state)
        titles[title] = media_id
        log(f"created draft {media_id} for {key} 《{title}》")
        shutil.rmtree(work_dir, ignore_errors=True)

    if not args.dry_run:
        # A candidate that did not fail this run (created, or adopted by title) has recovered.
        for key in [k for k in failing if k.startswith("_posts/") and k not in failed_now]:
            record_recovery(state, key)
        sync_failure_draft(client, state, titles)
        send_failure_notifications(state)
    if failures == 0 and not args.dry_run:
        state["last_commit"] = commit
        save_state(state)
    return 1 if failures else 0


def cmd_notify_test(_args: argparse.Namespace) -> int:
    if not os.getenv("NOTIFY_URL"):
        print("NOTIFY_URL is not set")
        return 1
    ok = notify(f"🔔 公众号同步通知测试\n{dt.datetime.now():%Y-%m-%d %H:%M:%S}")
    print("sent" if ok else "failed (see the log line above)")
    return 0 if ok else 1


def cmd_status(_args: argparse.Namespace) -> int:
    state = load_state()
    print(f"last_commit: {state.get('last_commit')}")
    print(f"since: {SYNC_SINCE}   old posts tracked: {len(state.get('old_blobs', {}))}")
    for key, info in sorted(state.get("synced", {}).items()):
        print(f"- {key}: {info.get('how')} {info.get('media_id', '')} 《{info.get('title')}》")
    for key, entry in sorted(state.get("failing", {}).items()):
        print(f"! {key}: failing since {entry.get('since')}: {entry.get('error')}")
    print(f"failure log draft: {state.get('failure_log', {}).get('media_id')}")
    return 0


def cmd_mark(args: argparse.Namespace) -> int:
    state = load_state()
    key = args.post if args.post.startswith("_posts/") else f"_posts/{args.post}"
    state["synced"][key] = {"how": "marked", "synced_at": dt.datetime.now().isoformat(timespec="seconds")}
    save_state(state)
    print(f"marked {key} as done; no draft will be created for it")
    return 0


def cmd_forget(args: argparse.Namespace) -> int:
    state = load_state()
    key = args.post if args.post.startswith("_posts/") else f"_posts/{args.post}"
    if state["synced"].pop(key, None) is None:
        print(f"{key} is not in state")
        return 1
    state["last_commit"] = None
    save_state(state)
    print(f"forgot {key}; it will be synced again on the next run")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    wds.apply_dotenv()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", help="Sync new posts to WeChat drafts")
    run_parser.add_argument("--dry-run", action="store_true", help="Report what would happen; no writes")
    run_parser.add_argument("--recheck", action="store_true", help="Run even if master has no new commit")
    run_parser.set_defaults(func=cmd_run)
    sub.add_parser("status", help="Show recorded state").set_defaults(func=cmd_status)
    sub.add_parser("notify-test", help="Send a test notification").set_defaults(func=cmd_notify_test)
    mark_parser = sub.add_parser("mark", help="Record a post as done without creating a draft")
    mark_parser.add_argument("post", help="e.g. _posts/2026-09-25-xxx.md")
    mark_parser.set_defaults(func=cmd_mark)
    forget_parser = sub.add_parser("forget", help="Remove a post from state so it syncs again")
    forget_parser.add_argument("post", help="e.g. _posts/2026-09-26-xxx.md")
    forget_parser.set_defaults(func=cmd_forget)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (urllib.error.URLError, TimeoutError) as exc:
        log(f"network error, will retry next run: {exc}")
        return 1
    except wds.WeChatAPIError as exc:
        # Raised outside the per-post loop (token, draft listing): nothing can be synced.
        # The failure-log draft cannot be written either; Telegram, if configured, still can.
        log(f"WeChat API error: {exc}")
        state = load_state()
        record_failure(state, KEY_WECHAT, "", exc)
        send_failure_notifications(state)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
