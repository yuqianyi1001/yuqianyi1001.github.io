#!/usr/bin/env python3
"""Sync WeChat Official Account drafts to and from the local filesystem.

create a post

python3 scripts/wechat_draft_sync.py create --markdown _posts/2025-09-29-buddhism-sharing-in-2022.md

"""

from __future__ import annotations

import argparse
import dataclasses
import json
import mimetypes
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Dict, Iterable, List, Optional, Tuple

try:  # Optional dependency for front matter parsing
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    yaml = None

try:  # Optional dependency for Markdown conversion
    import markdown  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    markdown = None


API_BASE = "https://api.weixin.qq.com"
DOTENV_FILENAME = ".env"
MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
MARKDOWN_REF_IMAGE_PATTERN = re.compile(r"^\[([^\]]+)\]:\s*(\S+)(.*)$", re.MULTILINE)
DEFAULT_THUMB_MEDIA_ID = "LJGNckXOaezci8bZiAJY7N5Ubz6wjqAIk079wmXjBhmS0HTLjQcurh4xfcNBS_QF"


class WeChatAPIError(RuntimeError):
    """Raised when the WeChat API returns an error payload."""


def load_env_from_file(env_path: pathlib.Path) -> Dict[str, str]:
    """Parse key=value pairs from a dotenv-style file."""

    values: Dict[str, str] = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def apply_dotenv() -> None:
    """Populate os.environ using values from a nearby .env file if present."""

    script_dir = pathlib.Path(__file__).resolve().parent
    candidate_paths = [
        pathlib.Path.cwd() / DOTENV_FILENAME,
        script_dir.parent / DOTENV_FILENAME,
    ]

    for env_path in candidate_paths:
        if not env_path.exists():
            continue
        for key, value in load_env_from_file(env_path).items():
            os.environ.setdefault(key, value)


def slugify(value: str) -> str:
    """Return a filesystem-friendly slug based on the provided value."""

    slug = re.sub(r"[^0-9a-zA-Z]+", "-", value).strip("-")
    return slug.lower()[:48] or "article"


@dataclasses.dataclass
class ArticleBundle:
    index: int
    directory: pathlib.Path
    meta_path: pathlib.Path
    content_path: pathlib.Path
    metadata: Dict[str, object]
    content: str


class WeChatClient:
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> None:
        self._app_id = app_id
        self._app_secret = app_secret
        self._access_token = access_token
        self._token_timestamp: Optional[float] = None

    @property
    def access_token(self) -> str:
        if self._access_token and not self._needs_refresh():
            return self._access_token
        if not self._app_id or not self._app_secret:
            raise RuntimeError(
                "Access token expired or missing; supply WECHAT_APP_ID and WECHAT_APP_SECRET",
            )
        self._refresh_access_token()
        assert self._access_token
        return self._access_token

    def _needs_refresh(self) -> bool:
        if not self._token_timestamp or not self._access_token:
            return True
        # Tokens are valid for ~7200s; refresh five minutes early.
        return time.time() - self._token_timestamp > 7200 - 300

    def _refresh_access_token(self) -> None:
        params = {
            "grant_type": "client_credential",
            "appid": self._app_id,
            "secret": self._app_secret,
        }
        url = f"{API_BASE}/cgi-bin/token?{urllib.parse.urlencode(params)}"
        data = self._http_request("GET", url)
        if "access_token" not in data:
            raise WeChatAPIError(json.dumps(data, ensure_ascii=False))
        self._access_token = data["access_token"]
        self._token_timestamp = time.time()

    def _do_api_request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, object]] = None,
        retry_on_auth_error: bool = True,
    ) -> Dict[str, object]:
        token = self.access_token
        url = f"{API_BASE}{path}?access_token={urllib.parse.quote(token)}"
        data_bytes = None
        headers = {}
        if payload is not None:
            data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        response = self._http_request(method, url, data_bytes, headers)

        if isinstance(response, dict) and response.get("errcode") not in (0, None):
            errcode = response["errcode"]
            if errcode in {40001, 42001} and retry_on_auth_error and self._app_id and self._app_secret:
                self._access_token = None
                self._token_timestamp = None
                return self._do_api_request(method, path, payload, retry_on_auth_error=False)
            raise WeChatAPIError(json.dumps(response, ensure_ascii=False))
        return response

    @staticmethod
    def _http_request(
        method: str,
        url: str,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, object]:
        request = urllib.request.Request(url, data=data, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(request) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:  # pragma: no cover - network errors surface directly
            raise RuntimeError(f"HTTP error {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - propagated upwards
            raise RuntimeError(f"Network error: {exc.reason}") from exc

        try:
            return json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Unexpected non-JSON response from WeChat API") from exc

    # Draft management helpers -------------------------------------------------

    def list_drafts(self, offset: int, count: int, no_content: int = 1) -> Dict[str, object]:
        payload = {"offset": offset, "count": count, "no_content": no_content}
        return self._do_api_request("POST", "/cgi-bin/draft/batchget", payload)

    def get_draft(self, media_id: str) -> Dict[str, object]:
        payload = {"media_id": media_id}
        return self._do_api_request("POST", "/cgi-bin/draft/get", payload)

    def update_draft(self, media_id: str, index: int, article: Dict[str, object]) -> None:
        payload = {"media_id": media_id, "index": index, "articles": article}
        self._do_api_request("POST", "/cgi-bin/draft/update", payload)

    def upload_article_image(self, image_path: pathlib.Path) -> str:
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        mime_type, _ = mimetypes.guess_type(image_path.name)
        mime_type = mime_type or "application/octet-stream"
        boundary = uuid.uuid4().hex
        with image_path.open("rb") as fh:
            file_bytes = fh.read()

        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"media\"; filename=\"{image_path.name}\"\r\n"
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        result = self._http_request(
            "POST",
            f"{API_BASE}/cgi-bin/media/uploadimg?access_token={urllib.parse.quote(self.access_token)}",
            data=body,
            headers=headers,
        )
        url = result.get("url") if isinstance(result, dict) else None
        if not url:
            raise WeChatAPIError(json.dumps(result, ensure_ascii=False))
        return url

    def add_draft(self, articles: List[Dict[str, object]]) -> str:
        if not articles:
            raise ValueError("At least one article is required to create a draft")
        response = self._do_api_request("POST", "/cgi-bin/draft/add", {"articles": articles})
        media_id = response.get("media_id") if isinstance(response, dict) else None
        if not media_id:
            raise WeChatAPIError(json.dumps(response, ensure_ascii=False))
        return str(media_id)


def ensure_storage_dir(path: pathlib.Path) -> pathlib.Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_draft(draft: Dict[str, object], storage_dir: pathlib.Path) -> pathlib.Path:
    media_id = draft.get("media_id") or draft.get("news_item", [{}])[0].get("media_id")
    if not media_id:
        raise RuntimeError("Unable to determine media_id from draft payload")

    draft_dir = ensure_storage_dir(storage_dir / media_id)
    metadata_path = draft_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps({k: draft.get(k) for k in ("media_id", "create_time", "update_time")}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    news = draft.get("news_item") or draft.get("content", {}).get("news_item", [])
    for idx, article in enumerate(news):
        title = article.get("title", f"article-{idx}")
        article_dir = ensure_storage_dir(draft_dir / f"{idx:02d}_{slugify(title)}")
        article_meta = {
            "title": article.get("title", ""),
            "author": article.get("author", ""),
            "digest": article.get("digest", ""),
            "content_source_url": article.get("content_source_url", ""),
            "thumb_media_id": article.get("thumb_media_id", ""),
            "show_cover_pic": article.get("show_cover_pic", 0),
            "need_open_comment": article.get("need_open_comment", 0),
            "only_fans_can_comment": article.get("only_fans_can_comment", 0),
            "open_comment": article.get("open_comment"),
            "is_deleted": article.get("is_deleted"),
            "url": article.get("url"),
            "thumb_url": article.get("thumb_url"),
            "cover_url": article.get("cover_url"),
        }
        (article_dir / "article.json").write_text(
            json.dumps(article_meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (article_dir / "content.html").write_text(article.get("content", ""), encoding="utf-8")

    return draft_dir


def load_article_bundles(draft_dir: pathlib.Path) -> List[ArticleBundle]:
    bundles: List[ArticleBundle] = []
    for child in sorted(draft_dir.iterdir()):
        if not child.is_dir():
            continue
        match = re.match(r"^(\d+)_", child.name)
        if not match:
            continue
        index = int(match.group(1))
        meta_path = child / "article.json"
        content_path = child / "content.html"
        if not meta_path.exists() or not content_path.exists():
            continue
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        content = content_path.read_text(encoding="utf-8")
        bundles.append(
            ArticleBundle(
                index=index,
                directory=child,
                meta_path=meta_path,
                content_path=content_path,
                metadata=metadata,
                content=content,
            )
        )
    return sorted(bundles, key=lambda b: b.index)


def ensure_yaml_available() -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required for front matter parsing. Install it with `pip install pyyaml`.")


def ensure_markdown_available() -> None:
    if markdown is None:
        raise RuntimeError("The `markdown` package is required. Install it with `pip install markdown`.")


def sanitize_html(html: str) -> str:
    html = re.sub(r"\s+id=\"[^\"]*\"", "", html)
    html = re.sub(r"href=\"#[^\"]*\"", 'href="javascript:void(0)"', html)
    return html


def build_preview_document(body_html: str) -> str:
    css_path = pathlib.Path(__file__).resolve().parent / "markdown_.css"
    css_content = ""
    if css_path.exists():
        css_content = css_path.read_text(encoding="utf-8")

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"zh-CN\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "  <title>WeChat Draft Preview</title>\n"
        "  <style>\n"
        f"{css_content}\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <main class=\"wechat-preview\">\n"
        f"{body_html}\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def load_markdown_article(
    markdown_path: pathlib.Path,
    client: Optional[WeChatClient],
    *,
    upload_images: bool = True,
    converter: str = "markdown",
) -> Tuple[Dict[str, object], str]:
    ensure_yaml_available()
    if converter != "markdown":
        raise ValueError(f"Unsupported converter: {converter}")

    ensure_markdown_available()

    text = markdown_path.read_text(encoding="utf-8")
    metadata: Dict[str, object] = {}
    body = text

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) < 3:
            raise RuntimeError(f"Malformed front matter in {markdown_path}")
        _, front_matter, remainder = parts
        metadata = yaml.safe_load(front_matter) or {}
        if not isinstance(metadata, dict):
            raise RuntimeError(f"Front matter in {markdown_path} must define a mapping")
        body = remainder.lstrip("\n")

    body_for_conversion = body
    if upload_images:
        if client is None:
            raise RuntimeError("WeChat client is required when upload_images is enabled")

        image_cache: Dict[str, str] = {}

        def resolve_image_url(image_ref: str) -> str:
            if image_ref.startswith("http://") or image_ref.startswith("https://"):
                return image_ref

            resolved_path = (markdown_path.parent / image_ref).resolve()
            cached = image_cache.get(str(resolved_path))
            if cached is None:
                url = client.upload_article_image(resolved_path)
                image_cache[str(resolved_path)] = url
            else:
                url = cached
            return url

        def replace_image(match: re.Match[str]) -> str:
            alt_text, image_ref = match.groups()
            url = resolve_image_url(image_ref)
            return f"![{alt_text}]({url})"

        body_for_conversion = MARKDOWN_IMAGE_PATTERN.sub(replace_image, body_for_conversion)

        def replace_reference(match: re.Match[str]) -> str:
            label, image_ref, suffix = match.groups()
            url = resolve_image_url(image_ref)
            return f"[{label}]: {url}{suffix}"

        body_for_conversion = MARKDOWN_REF_IMAGE_PATTERN.sub(replace_reference, body_for_conversion)

    html_content = markdown.markdown(body_for_conversion, extensions=["extra", "sane_lists", "toc"])

    html_content = sanitize_html(html_content)
    return metadata, html_content


def build_article_payload(metadata: Dict[str, object], html_content: str) -> Dict[str, object]:
    title = metadata.get("title") if isinstance(metadata.get("title"), str) else None
    if not title:
        raise RuntimeError("Article metadata must include a 'title'")

    digest = metadata.get("digest") if isinstance(metadata.get("digest"), str) else None
    if not digest:
        for key in ("description", "excerpt"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                digest = value.strip()
                break
    if not digest:
        plain = re.sub(r"<[^>]+>", "", html_content)
        digest = plain.strip()[:120]

    thumb_media_id = metadata.get("thumb_media_id") if isinstance(metadata.get("thumb_media_id"), str) else None
    if not thumb_media_id:
        thumb_media_id = DEFAULT_THUMB_MEDIA_ID

    author = metadata.get("author") if isinstance(metadata.get("author"), str) else None
    content_source_url = metadata.get("content_source_url") if isinstance(metadata.get("content_source_url"), str) else None
    if not content_source_url:
        alt_source = metadata.get("source_url")
        if isinstance(alt_source, str):
            content_source_url = alt_source

    show_cover_pic = metadata.get("show_cover_pic")
    if isinstance(show_cover_pic, str) and show_cover_pic.isdigit():
        show_cover_pic = int(show_cover_pic)
    if show_cover_pic not in (0, 1):
        show_cover_pic = 0

    need_open_comment = metadata.get("need_open_comment")
    if isinstance(need_open_comment, str) and need_open_comment.isdigit():
        need_open_comment = int(need_open_comment)
    if need_open_comment not in (0, 1):
        need_open_comment = 0

    only_fans_can_comment = metadata.get("only_fans_can_comment")
    if isinstance(only_fans_can_comment, str) and only_fans_can_comment.isdigit():
        only_fans_can_comment = int(only_fans_can_comment)
    if only_fans_can_comment not in (0, 1):
        only_fans_can_comment = 0

    article_payload: Dict[str, object] = {
        "title": title.strip(),
        "digest": digest.strip(),
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "show_cover_pic": show_cover_pic,
        "need_open_comment": need_open_comment,
        "only_fans_can_comment": only_fans_can_comment,
    }

    if author:
        article_payload["author"] = author.strip()
    if content_source_url:
        article_payload["content_source_url"] = content_source_url.strip()

    return article_payload


def cmd_list(client: WeChatClient, args: argparse.Namespace) -> None:
    payload = client.list_drafts(args.offset, args.count, no_content=0 if args.include_content else 1)
    total = payload.get("total_count", 0)
    print(f"Total drafts: {total}")
    for item in payload.get("item", []):
        media_id = item.get("media_id")
        update_time = item.get("update_time")
        news_items = item.get("content", {}).get("news_item", [])
        titles = ", ".join(art.get("title", "") for art in news_items)
        print(f"- media_id={media_id} updated={update_time} titles={titles}")


def cmd_pull(client: WeChatClient, args: argparse.Namespace) -> None:
    draft = client.get_draft(args.media_id)
    draft["media_id"] = args.media_id
    draft_dir = store_draft(draft, args.storage_dir)
    print(f"Draft saved under {draft_dir}")


def cmd_push(client: WeChatClient, args: argparse.Namespace) -> None:
    if args.markdown:
        if args.articles and len(args.articles) != len(args.markdown):
            raise RuntimeError("Specify the same number of --articles indexes as markdown files")

        for position, markdown_path in enumerate(args.markdown):
            article_index = args.articles[position] if args.articles else position
            metadata, html_content = load_markdown_article(markdown_path, client)
            article_payload = build_article_payload(metadata, html_content)
            client.update_draft(args.media_id, article_index, article_payload)
            print(
                "Updated media_id="
                f"{args.media_id} index={article_index} from markdown {markdown_path}",
            )
        return

    draft_dir = args.storage_dir / args.media_id
    if not draft_dir.exists():
        raise RuntimeError(f"Local draft directory not found: {draft_dir}")

    bundles = load_article_bundles(draft_dir)
    if not bundles:
        raise RuntimeError(f"No article bundles discovered in {draft_dir}")

    target_indexes: Optional[Iterable[int]] = None
    if args.articles:
        target_indexes = set(args.articles)

    for bundle in bundles:
        if target_indexes is not None and bundle.index not in target_indexes:
            continue
        article_payload = build_article_payload(bundle.metadata, bundle.content)
        client.update_draft(args.media_id, bundle.index, article_payload)
        print(f"Updated media_id={args.media_id} index={bundle.index} from {bundle.directory}")


def cmd_create(client: WeChatClient, args: argparse.Namespace) -> None:
    articles: List[Dict[str, object]] = []
    for markdown_path in args.markdown:
        metadata, html_content = load_markdown_article(markdown_path, client)
        articles.append(build_article_payload(metadata, html_content))

    media_id = client.add_draft(articles)
    print(f"Created draft media_id={media_id}")

    if args.skip_download:
        return

    draft = client.get_draft(media_id)
    draft["media_id"] = media_id
    draft_dir = store_draft(draft, args.storage_dir)
    print(f"Draft saved under {draft_dir}")


def cmd_preview(client: WeChatClient, args: argparse.Namespace) -> None:
    markdown_path = args.markdown
    if not markdown_path.exists():
        raise RuntimeError(f"Markdown file not found: {markdown_path}")

    _, html_content = load_markdown_article(
        markdown_path,
        None,
        upload_images=False,
        converter="markdown",
    )

    rendered = build_preview_document(html_content)

    output_path = args.output or markdown_path.with_suffix(".preview.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Preview HTML written to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--app-id",
        default=os.getenv("WECHAT_APP_ID"),
        help="WeChat Official Account app id (defaults to WECHAT_APP_ID env)",
    )
    parser.add_argument(
        "--app-secret",
        default=os.getenv("WECHAT_APP_SECRET"),
        help="WeChat Official Account app secret (defaults to WECHAT_APP_SECRET env)",
    )
    parser.add_argument(
        "--access-token",
        default=os.getenv("WECHAT_ACCESS_TOKEN"),
        help="Existing access token (defaults to WECHAT_ACCESS_TOKEN env)",
    )
    parser.add_argument(
        "--storage-dir",
        type=pathlib.Path,
        default=pathlib.Path("wechat_drafts"),
        help="Local directory used to store draft payloads (default: ./wechat_drafts)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List remote drafts")
    list_parser.add_argument("--offset", type=int, default=0, help="Offset into the draft list")
    list_parser.add_argument("--count", type=int, default=20, help="Number of drafts to fetch")
    list_parser.add_argument(
        "--include-content",
        action="store_true",
        help="Request content payloads (WeChat may return fewer results when enabled)",
    )
    list_parser.set_defaults(func=cmd_list)

    pull_parser = subparsers.add_parser("pull", help="Download a draft and store it locally")
    pull_parser.add_argument("media_id", help="Media id of the draft to download")
    pull_parser.set_defaults(func=cmd_pull)

    push_parser = subparsers.add_parser("push", help="Update a draft on WeChat using local edits")
    push_parser.add_argument("media_id", help="Media id of the draft to update")
    push_parser.add_argument(
        "--articles",
        type=int,
        nargs="*",
        help="Optional list of article indexes to push (defaults to all)",
    )
    push_parser.add_argument(
        "--markdown",
        type=pathlib.Path,
        nargs="*",
        help="Markdown source files to sync (front matter will populate article metadata)",
    )
    push_parser.set_defaults(func=cmd_push)

    create_parser = subparsers.add_parser("create", help="Create a new draft from Markdown sources")
    create_parser.add_argument(
        "--markdown",
        type=pathlib.Path,
        nargs="+",
        required=True,
        help="Markdown files used to build the draft (order defines article order)",
    )
    create_parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Do not fetch and store the created draft locally after upload",
    )
    create_parser.set_defaults(func=cmd_create)

    preview_parser = subparsers.add_parser(
        "preview",
        help="Render Markdown to HTML locally without uploading images",
    )
    preview_parser.add_argument(
        "--markdown",
        type=pathlib.Path,
        required=True,
        help="Markdown file to render locally",
    )
    preview_parser.add_argument(
        "--output",
        type=pathlib.Path,
        help="Optional output HTML path (defaults to <markdown>.preview.html)",
    )
    preview_parser.set_defaults(func=cmd_preview)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    apply_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    storage_dir = ensure_storage_dir(args.storage_dir)
    client = WeChatClient(app_id=args.app_id, app_secret=args.app_secret, access_token=args.access_token)

    try:
        args.func(client, argparse.Namespace(**{**vars(args), "storage_dir": storage_dir}))
    except WeChatAPIError as exc:
        print(f"WeChat API error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - surfaces unexpected issues to the user
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
