---
layout: page
title: 佛学概念词典
permalink: /dict/
---

<ul>
{% assign sorted_dict = site.dict | sort: 'title' %}
{% for entry in sorted_dict %}
  <li>
    <a href="{{ entry.url | relative_url }}">{{ entry.title }}</a>
    {% if entry.description %} — {{ entry.description }}{% endif %}
    {% if entry.alias %}<br><small>别名：{{ entry.alias | join: '，' }}</small>{% endif %}
  </li>
{% endfor %}
</ul>
