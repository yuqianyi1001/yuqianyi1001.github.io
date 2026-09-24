// 字幕：文本用原文（scenes.js 里的旁白），时间借火山逐字时间戳。
// 对齐方式：按标点把原文和 TTS 词序列各切成小句，数量一致就一一配对（时间准、文本原样）；
// 不一致则退回按规范化字数累计映射。之后把太短的小句合并、太长的拆开，得到 6~18 字的 cue。
// 供渲染器烧录；并导出期目录 字幕.srt（发平台用）。
const fs = require('fs');
const path = require('path');
const { cfg, projectPaths, resolveProject } = require('./paths.cjs');

const CAP = cfg.captions;
const LEAD = cfg.render.leadSeconds, HOLD = cfg.render.holdSeconds;
const PUNCT = /[，。？！；：、]/;
const HARD = /[。？！；]$/;
const TRIM_END = /[，。；：、]+$/;
const norm = (s) => [...s].filter((c) => /[\p{L}\p{N}]/u.test(c)).join('');
const nlen = (s) => norm(s).length;

// 原文按标点切小句（标点留在句尾）
function splitText(text) {
  return text.replace(/\s+/g, ' ').split(/(?<=[，。？！；：、])/).map((s) => s.trim()).filter((s) => nlen(s) > 0);
}
// TTS 词按标点切小句
function splitWords(words) {
  const out = []; let buf = [];
  for (const w of words) { buf.push(w); if (PUNCT.test(w.w.slice(-1))) { out.push(buf); buf = []; } }
  if (buf.length) out.push(buf);
  return out.filter((g) => g.some((w) => nlen(w.w) > 0));
}

// 一个场景的 cue 列表（时间为场景内秒，已含 LEAD）
function cuesForScene(info) {
  const words = info.wordList || [];
  if (!words.length) return [];
  const text = (info.segments || []).join('');
  const tc = splitText(text), wc = splitWords(words);
  let clauses;
  if (tc.length === wc.length) {
    clauses = tc.map((t, i) => ({ text: t, start: wc[i][0].s, end: wc[i][wc[i].length - 1].e }));
  } else {
    // 退回：规范化字数累计映射
    const pos = []; let acc = 0;
    for (const w of words) { pos.push({ p0: acc, p1: acc + nlen(w.w), s: w.s, e: w.e }); acc += nlen(w.w); }
    const timeAt = (p, useEnd) => { let best = useEnd ? words[words.length - 1].e : words[0].s; for (const x of pos) { if (useEnd ? x.p1 <= p : x.p0 <= p) best = useEnd ? x.e : x.s; else break; } return best; };
    let p = 0; clauses = [];
    for (const t of tc) { const n = nlen(t); clauses.push({ text: t, start: timeAt(p, false), end: timeAt(p + n, true) }); p += n; }
  }
  // 合并短句（软标点后且合并不超长）
  const merged = [];
  for (const c of clauses) {
    const last = merged[merged.length - 1];
    if (last && !HARD.test(last.text) && nlen(last.text) < CAP.minChars && nlen(last.text) + nlen(c.text) <= CAP.maxChars) {
      last.text += c.text; last.end = c.end;
    } else if (last && !HARD.test(last.text) && nlen(c.text) < 3 && nlen(last.text) + nlen(c.text) <= CAP.maxChars) {
      last.text += c.text; last.end = c.end;
    } else merged.push({ ...c });
  }
  // 拆长句：只在汉字之间（或空格处）断，取离等分点最近的位置；时间按字数比例分
  const isCJK = (ch) => /[\u4e00-\u9fff]/.test(ch);
  const cues = [];
  const splitLong = (c) => {
    const n = nlen(c.text);
    if (n <= CAP.maxChars) { cues.push(c); return; }
    const chars = [...c.text];
    // 累计规范化字数 → 字符索引
    const cum = []; let k = 0; for (const ch of chars) { cum.push(k); k += nlen(ch); }
    const ideal = n / Math.ceil(n / CAP.maxChars);
    let best = -1, bestD = Infinity;
    for (let i = 1; i < chars.length; i++) {
      const ok = chars[i] === ' ' || (isCJK(chars[i - 1]) && isCJK(chars[i]));
      if (!ok) continue;
      const d = Math.abs(cum[i] - ideal);
      if (d < bestD) { bestD = d; best = i; }
    }
    if (best < 0) { cues.push(c); return; }
    const a = chars.slice(0, best).join('').trim(), b = chars.slice(best).join('').trim();
    const na = nlen(a), t = c.start + (c.end - c.start) * (na / n);
    cues.push({ text: a, start: c.start, end: t });
    splitLong({ text: b, start: t, end: c.end });
  };
  for (const c of merged) splitLong(c);
  // 显示文本去句尾标点；加 LEAD；首尾微调且不重叠
  for (let i = 0; i < cues.length; i++) {
    cues[i].text = cues[i].text.replace(TRIM_END, '');
    cues[i].start += LEAD; cues[i].end += LEAD;
  }
  for (let i = 0; i < cues.length; i++) {
    const prev = cues[i - 1], next = cues[i + 1];
    cues[i].start = Math.max(prev ? prev.end : 0, cues[i].start - CAP.leadSeconds);
    cues[i].end = Math.min(cues[i].end + CAP.tailSeconds, next ? next.start - 0.02 : info.duration + LEAD + HOLD);
    if (next && cues[i].end < cues[i].start + 0.3) cues[i].end = Math.min(cues[i].start + 0.3, next.start);
  }
  return cues.filter((c) => c.text);
}

function sceneInfos(P) {
  const script = JSON.parse(fs.readFileSync(P.script));
  return script.map((sc) => JSON.parse(fs.readFileSync(path.join(P.audio, `${sc.name}.json`))));
}

// 全片 SRT（按场景累计偏移）
function writeSrt(projectDir) {
  const P = projectPaths(projectDir);
  const infos = sceneInfos(P);
  let offset = 0, n = 0; const lines = [];
  const ts = (t) => { const ms = Math.round(t * 1000); const h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, s = Math.floor(ms / 1000) % 60; return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms % 1000).padStart(3, '0')}`; };
  for (const info of infos) {
    for (const c of cuesForScene(info)) lines.push(`${++n}\n${ts(offset + c.start)} --> ${ts(offset + c.end)}\n${c.text}\n`);
    offset += info.duration + LEAD + HOLD;
  }
  const out = path.join(P.project, '字幕.srt');
  fs.writeFileSync(out, lines.join('\n'));
  return { file: out, count: n };
}

module.exports = { cuesForScene, writeSrt };

if (require.main === module) {
  const P = projectPaths(resolveProject(process.argv[2] || '.'));
  if (process.argv.includes('--dump')) {
    for (const info of sceneInfos(P)) { console.log(`## ${info.name}`); for (const c of cuesForScene(info)) console.log(`  ${c.start.toFixed(2)}-${c.end.toFixed(2)}  ${c.text}`); }
  } else { const r = writeSrt(P.project); console.log(`字幕 ${r.count} 条 → ${r.file}`); }
}
