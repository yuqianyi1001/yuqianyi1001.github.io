---
layout: page
title: 工具合集
permalink: /tools/
---

<ul>
  <li><a href="/text-image">标题图片：文字转图片的工具</a></li>
  <li><a href="/wechat-cover">公众号封面生成器：标题一键生成 2.35:1 首图 + 1:1 次图</a></li>
{% for tool in site.tools %}
  <li>
    <a href="{{ tool.url | relative_url }}">{{ tool.title }}</a>
    {% if tool.description %} — {{ tool.description }}{% endif %}
  </li>
{% endfor %}
</ul>
