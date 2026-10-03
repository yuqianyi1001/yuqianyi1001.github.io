// 文章评论区。后端和账号与今文佛典（sutratoday.com）共用：浏览公开，发表需登录。
// 登录在 sutratoday.com 上完成：点“登录”跳到那边的 sso.html，已经登录的话立刻带着一次性短码
// 跳回来（地址末尾的 #sso=…），这里用短码向后端换到同一个登录。说明见后端 README 的“跳转登录”。
// 用法见 _layouts/post.html：<div id="yq-comments" data-slug="blog-文章名"></div>
(function () {
  'use strict';

  var root = document.getElementById('yq-comments');
  if (!root) return;
  var slug = root.getAttribute('data-slug');

  // 本地开发：localStorage.setItem('yq_api_base', 'http://localhost:8787')
  var API_BASE = read('yq_api_base', true) || 'https://api.sutratoday.com';
  // 本地开发：localStorage.setItem('yq_sso_url', 'http://localhost:8080/sso.html')
  var SSO_URL = read('yq_sso_url', true) || 'https://sutratoday.com/sso.html';
  var SESSION_KEY = 'yq_account_session';
  var ACCOUNT_NOTE = '评论用今文佛典（sutratoday.com）的账号：点下面的按钮去那边登录或注册，完成后会自动回到这里；已经在那边登录过的，点一下就好。';

  var STYLE =
    '#yq-comments { font-size: 16px; line-height: 1.7; }' +
    '.yq-note, .yq-empty, .yq-hint { color: #666; font-size: 14px; margin: 0 0 12px; }' +
    '.yq-list { list-style: none; margin: 0 0 20px; padding: 0; }' +
    '.yq-comment { padding: 12px 0; border-bottom: 1px solid #eee; }' +
    '.yq-meta { display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px; font-size: 14px; color: #666; }' +
    '.yq-meta strong { color: #222; }' +
    '.yq-quote { margin: 8px 0 0; padding: 2px 12px; border-left: 2px solid #ccc; color: #666; font-size: 15px; white-space: pre-wrap; }' +
    '.yq-body { margin: 6px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; }' +
    '.yq-link { font: inherit; font-size: 14px; padding: 0; border: 0; background: none; color: #4183c4; cursor: pointer; }' +
    '.yq-link:hover { text-decoration: underline; }' +
    '.yq-form textarea { box-sizing: border-box; width: 100%; font: inherit; padding: 10px; border: 1px solid #ccc; border-radius: 6px; resize: vertical; }' +
    '.yq-actions { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; margin-top: 8px; }' +
    '.yq-actions .yq-hint { margin: 0; }' +
    '.yq-button { font: inherit; font-size: 15px; padding: 7px 18px; border: 1px solid #4183c4; border-radius: 999px; background: #4183c4; color: #fff; cursor: pointer; }' +
    '.yq-button.is-plain { background: transparent; color: #4183c4; }' +
    '.yq-button:disabled { opacity: .5; cursor: default; }' +
    '.yq-error { color: #b3261e; font-size: 14px; min-height: 1.4em; margin: 6px 0 0; }';


  function read(key, raw) {
    try {
      var value = localStorage.getItem(key);
      return raw ? value : JSON.parse(value);
    } catch (e) {
      return null; // 隐私模式，或不是 JSON
    }
  }
  function write(key, value) {
    try {
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      /* 存不进去时，这次登录只在当前页面有效 */
    }
  }

  var session = read(SESSION_KEY);
  var comments = [];
  var state = 'loading'; // loading | error | ready
  var loadId = 0;

  // 在其他标签页登录或退出时同步
  window.addEventListener('storage', function (event) {
    if (event.key !== SESSION_KEY) return;
    session = read(SESSION_KEY);
    load();
  });

  // ---------------------------------------------------------------- 后端

  function request(method, path, body, auth) {
    var headers = { 'Content-Type': 'application/json' };
    var withAuth = auth !== false && session;
    if (withAuth) headers.Authorization = 'Bearer ' + session.token;
    return fetch(API_BASE + path, { method: method, headers: headers, body: body === undefined ? undefined : JSON.stringify(body) })
      .catch(function () {
        throw new Error('连不上服务器，请检查网络');
      })
      .then(function (response) {
        return response
          .json()
          .catch(function () {
            return {};
          })
          .then(function (data) {
            if (response.ok) return data;
            if (response.status === 401 && withAuth) {
              session = null; // 登录已过期或已在别处退出
              write(SESSION_KEY, null);
              render();
            }
            throw new Error(data.message || '出错了，请稍后再试');
          });
      });
  }

  function load() {
    var id = ++loadId;
    state = 'loading';
    render();
    request('GET', '/comments?slug=' + encodeURIComponent(slug))
      .then(function (data) {
        if (id !== loadId) return;
        comments = data.comments || [];
        state = 'ready';
        render();
      })
      .catch(function () {
        if (id !== loadId) return;
        state = 'error';
        render();
      });
  }

  // ---------------------------------------------------------------- 页面

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function formatTime(ms) {
    var d = new Date(ms);
    var pad = function (n) {
      return String(n).padStart(2, '0');
    };
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  }

  function renderComment(c) {
    var item = el('li', 'yq-comment');
    var meta = el('div', 'yq-meta');
    meta.appendChild(el('strong', '', c.author));
    meta.appendChild(el('span', '', formatTime(c.createdAt)));
    if (c.mine) {
      var del = el('button', 'yq-link', '删除');
      del.type = 'button';
      del.onclick = function () {
        if (!confirm('确定删除这条评论吗？')) return;
        request('DELETE', '/comments/' + c.id)
          .then(function () {
            comments = comments.filter(function (other) {
              return other.id !== c.id;
            });
            render();
          })
          .catch(function (error) {
            alert(error.message);
          });
      };
      meta.appendChild(del);
    }
    item.appendChild(meta);
    if (c.quote) item.appendChild(el('blockquote', 'yq-quote', c.quote));
    if (c.body) item.appendChild(el('p', 'yq-body', c.body));
    return item;
  }

  function renderForm() {
    var form = el('form', 'yq-form');
    var textarea = el('textarea');
    textarea.name = 'body';
    textarea.rows = 4;
    textarea.maxLength = 2000;
    textarea.required = true;
    textarea.placeholder = '写下你的评论、疑问或建议…';
    var actions = el('div', 'yq-actions');
    var hint = el('span', 'yq-hint', '以 ' + session.user.username + ' 的身份发表 · ');
    var out = el('button', 'yq-link', '退出登录');
    out.type = 'button';
    out.onclick = logout;
    hint.appendChild(out);
    var submit = el('button', 'yq-button', '发表评论');
    submit.type = 'submit';
    var error = el('p', 'yq-error');
    error.setAttribute('role', 'alert');
    actions.appendChild(hint);
    actions.appendChild(submit);
    form.appendChild(textarea);
    form.appendChild(actions);
    form.appendChild(error);
    form.onsubmit = function (event) {
      event.preventDefault();
      var body = textarea.value.trim();
      if (!body) return;
      submit.disabled = true;
      error.textContent = '';
      request('POST', '/comments', { slug: slug, body: body })
        .then(function (data) {
          comments.push(data.comment);
          render();
        })
        .catch(function (e) {
          // 登录过期时 request 已经重画成登录提示，这里的 form 不在页面上了
          error.textContent = e.message;
          submit.disabled = false;
        });
    };
    return form;
  }

  function renderLogin() {
    var box = el('div', 'yq-login');
    box.appendChild(el('p', 'yq-note', '登录后才能发表评论。' + ACCOUNT_NOTE));
    var button = el('button', 'yq-button', '登录 / 注册后评论');
    button.type = 'button';
    button.onclick = function () {
      location.href = SSO_URL + '?return=' + encodeURIComponent(location.href.split('#')[0]);
    };
    box.appendChild(button);
    if (loginError) box.appendChild(el('p', 'yq-error', loginError));
    return box;
  }

  function render() {
    // 重画会清掉输入框；只有登录状态或评论列表变了才会走到这里
    root.textContent = '';
    if (state === 'loading') root.appendChild(el('p', 'yq-empty', '正在加载评论…'));
    else if (state === 'error') root.appendChild(el('p', 'yq-empty', '评论加载失败，请稍后刷新重试。'));
    else if (!comments.length) root.appendChild(el('p', 'yq-empty', '还没有评论。'));
    else {
      var list = el('ol', 'yq-list');
      comments.forEach(function (c) {
        list.appendChild(renderComment(c));
      });
      root.appendChild(list);
    }
    root.appendChild(session ? renderForm() : renderLogin());
  }

  // ---------------------------------------------------------------- 登录

  var loginError = '';

  // 从 sutratoday.com 跳回来时，地址末尾带着 #sso=短码
  function finishLogin() {
    var match = /^#sso=([\w-]+)$/.exec(location.hash);
    if (!match) return false;
    history.replaceState(null, '', location.pathname + location.search);
    request('POST', '/auth/sso/exchange', { code: match[1] }, false)
      .then(function (data) {
        session = { token: data.token, user: data.user };
        write(SESSION_KEY, session);
      })
      .catch(function (e) {
        loginError = e.message;
      })
      .then(function () {
        load(); // 重新拉取，才能认出哪些是自己的评论
        root.scrollIntoView();
      });
    return true;
  }

  function logout() {
    request('POST', '/auth/logout')
      .catch(function () {
        /* 网络失败也清掉本地登录态 */
      })
      .then(function () {
        session = null;
        write(SESSION_KEY, null);
        load();
      });
  }

  var style = document.createElement('style');
  style.textContent = STYLE;
  document.head.appendChild(style);
  if (!finishLogin()) load();
})();
