#!/usr/bin/env python3
"""Rebuild wechat-articles.md from a fabiao_all.json exported from the MP backend.

Usage: python3 scripts/build_wechat_articles_page.py ~/Downloads/fabiao_all.json

Export fabiao_all.json by running this in DevTools Console on the logged-in
mp.weixin.qq.com homepage (token is read from the page URL):

    (async () => {
      const token = new URLSearchParams(location.search).get('token');
      const out = [];
      for (let begin = 0; begin < 400; begin += 10) {
        const r = await fetch(`/cgi-bin/appmsgpublish?sub=list&begin=${begin}&count=10&token=${token}&lang=zh_CN&f=json&ajax=1`, {credentials: 'include'});
        out.push(await r.json());
        await new Promise(res => setTimeout(res, 800));
      }
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([JSON.stringify(out)], {type: 'application/json'}));
      a.download = 'fabiao_all.json';
      a.click();
    })()
"""
import datetime, difflib, glob, json, os, pathlib, re, sys, time

REPO = pathlib.Path(__file__).resolve().parent.parent
KIND = {"0": "文章", "8": "图文", "5": "视频", "10": "其他"}
OVERRIDES = {"忆家": "missing-hometown", "依法不依人": "bu-yi-ren"}


def norm(t):
    t = re.sub(r"[〇一二三四五六七八九十百]", "#", t)
    t = re.sub(r"\d+", "#", t)
    return re.sub(r"[\s｜|·—\-——:：,，。？?!！【】《》#\"\"''\"()（）]", "", t).lower()


def load_rows(path):
    rows = []
    for pg in json.loads(pathlib.Path(path).read_text()):
        pp = json.loads(pg["publish_page"])
        for item in pp.get("publish_list", []):
            info = json.loads(item["publish_info"])
            st = (info.get("sent_info") or {}).get("time")
            for a in (info.get("appmsgex") or info.get("appmsg_info") or []):
                ct = st or a.get("create_time")
                dt = time.strftime("%Y-%m-%d", time.localtime(int(ct))) if ct else "?"
                rows.append({"date": dt, "ist": str(a.get("item_show_type")),
                             "title": a.get("title", ""), "url": a.get("content_url", "")})
    return rows


def load_post_titles():
    posts = []
    for f in glob.glob(str(REPO / "_posts" / "*.md")):
        txt = pathlib.Path(f).read_text(errors="replace")
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", pathlib.Path(f).name)[:-3]
        names = []
        m = re.search(r"^title:\s*(.+)$", txt, re.M)
        if m:
            names.append(m.group(1).strip())
        names += [h.strip() for h in re.findall(r"^#\s+(.+)$", txt, re.M)[:3]]
        for n in names:
            posts.append((norm(n), slug))
    return posts


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads/fabiao_all.json")
    rows = load_rows(src)
    posts = load_post_titles()

    def match(title):
        for k, v in OVERRIDES.items():
            if k in title:
                return v
        nt = norm(title)
        best = max(posts, key=lambda p: difflib.SequenceMatcher(None, nt, p[0]).ratio())
        return best[1] if difflib.SequenceMatcher(None, nt, best[0]).ratio() >= 0.6 else None

    snap = datetime.datetime.fromtimestamp(os.path.getmtime(src)).strftime("%Y-%m-%d %H:%M")
    esc = lambda t: t.replace("|", "｜").replace("\n", " ")

    by_year, undated = {}, []
    for r in rows:
        (undated if r["date"] == "?" else by_year.setdefault(r["date"][:4], [])).append(r)

    L = ["---", "layout: page", "title: 公众号发表记录索引", "permalink: /wechat-articles/", "---", "",
         "微信公众号「愚千一」的全部发表记录快照，从公众号后台「发表记录」导出。", "",
         f"* 快照时间：**{snap}**（此后新发表的内容不在本表中）",
         f"* 共 **{len(rows)}** 条（文章 / 图文 / 视频 / 其他）",
         "* 「博客」列为对应的本站文章（按标题匹配，图文与文章同标题的共用一篇）", ""]

    def row_md(r, with_date=True):
        m = match(r["title"])
        blog = f"[✓](/{m}/)" if m else ""
        link = f"[{esc(r['title'])}]({r['url']})" if r["url"] else esc(r["title"])
        date_col = f" {r['date']} |" if with_date else ""
        return f"|{date_col} {KIND.get(r['ist'], r['ist'])} | {link} | {blog} |"

    for year in sorted(by_year, reverse=True):
        yr = sorted(by_year[year], key=lambda r: r["date"], reverse=True)
        L += [f"\n## {year} 年（{len(yr)} 条）", "", "| 日期 | 类型 | 标题 | 博客 |", "| --- | --- | --- | --- |"]
        L += [row_md(r) for r in yr]
    if undated:
        L += [f"\n## 无日期记录（{len(undated)} 条）", "", "| 类型 | 标题 | 博客 |", "| --- | --- | --- |"]
        L += [row_md(r, with_date=False) for r in undated]

    L += ["", "## 如何更新本页", "",
          "1. 登录[公众号后台](https://mp.weixin.qq.com/)，在首页打开浏览器 DevTools Console；",
          "2. 运行 `scripts/build_wechat_articles_page.py` 文件头注释里的导出脚本，得到 `fabiao_all.json`；",
          "3. 运行 `python3 scripts/build_wechat_articles_page.py <fabiao_all.json 路径>` 重新生成本页。", ""]

    out = REPO / "wechat-articles.md"
    out.write_text("\n".join(L))
    print(f"wrote {out}: {len(rows)} rows, snapshot {snap}")


if __name__ == "__main__":
    main()
