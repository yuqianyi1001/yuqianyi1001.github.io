// 旁白：阿里云百炼 Qwen-TTS（声音复刻音色），config.json tts.engine = "bailian" 时 wb tts / wb build 走这里。
// 环境变量：BAILIAN_TTS_MODEL（如 qwen3-tts-vc-2026-01-22）、BAILIAN_QWEN_TTS_VOICE_YUQIANYI（复刻音色 ID，
//   变量名可在 config.json tts.bailian.voiceEnv 改）、DASHSCOPE_API_KEY（可选：云端环境由代理注入凭证时不需要）。
// 请求走 curl（云端环境的出网代理对 curl 放行，Node 内置 fetch 会被拒）。
// 用 SSE 流式接口，音频以 base64 随响应返回（结果 OSS 链接的域名在云端环境里不一定放行）。
// Qwen-TTS 不返回逐字时间戳：按句合成，句子时长是真实的，句内按字数均分，供字幕和画图节奏对齐。
// 合成后处理：tts.bailian.speed 用 ffmpeg atempo 逐句变速（不变调，结果按倍率另存缓存）；
//   tts.bailian.loudness 目标响度（LUFS）：全期所有场景用同一个增益，再过限幅器，场景之间音量一致。
// 输出 <build>/audio/<scene>.wav + <scene>.json（duration / segmentStarts / wordList），与 tts-volc.mjs 同格式。
import fs from "fs";
import path from "path";
import crypto from "crypto";
import { execFile, execFileSync, spawnSync } from "child_process";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const paths = require("./paths.cjs");
const { cfg } = paths;

const P = paths.projectPaths(paths.resolveProject(process.argv[2]));
const only = process.argv[3];
const B = cfg.tts.bailian || {};
const MODEL = process.env.BAILIAN_TTS_MODEL || B.model;
const VOICE = process.env[B.voiceEnv || "BAILIAN_QWEN_TTS_VOICE_YUQIANYI"] || B.voice;
if (!MODEL || !VOICE) throw new Error("缺少百炼模型或音色：设 BAILIAN_TTS_MODEL 与 BAILIAN_QWEN_TTS_VOICE_YUQIANYI（或 config.json tts.bailian）");
const URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation";
const FIXES = B.pronunciation || [];          // [["原词", "同音替换"], ...]，只改送给 TTS 的文本，字幕仍用原文
const GAP = B.sentenceGap ?? 0.12, BEAT_GAP = B.beatGap ?? 0.3, PAR = B.parallel || 4;
const SPEED = B.speed || 1, LUFS = B.loudness ?? null, TP = B.truePeak ?? -1.5;
const RATE = 24000, BPS = RATE * 2;           // 24kHz 单声道 16bit
const FF = ["-hide_banner", "-loglevel", "error"], RAW = ["-f", "s16le", "-ar", String(RATE), "-ac", "1"];
const ffPcm = (pcm, af) => execFileSync("ffmpeg", [...FF, ...RAW, "-i", "-", "-af", af, ...RAW, "-"], { input: pcm, maxBuffer: 256 << 20 });

const script = JSON.parse(fs.readFileSync(P.script));
const cacheDir = path.join(P.audio, "cache");
fs.mkdirSync(cacheDir, { recursive: true });

const fix = (t) => FIXES.reduce((s, [a, b]) => s.split(a).join(b), t);
const splitSentences = (seg) => seg.split(/(?<=[。？！；])/).map((s) => s.trim()).filter((s) => /[\p{L}\p{N}]/u.test(s));

function curlPost(url, headers, data) {
  const args = ["-sS", "-N", "--fail-with-body", "-m", "120", url, "--data-binary", "@-"];
  for (const [k, v] of Object.entries(headers)) args.push("-H", `${k}: ${v}`);
  return new Promise((resolve, reject) => {
    const p = execFile("curl", args, { maxBuffer: 64 << 20 }, (err, out) => (err ? reject(new Error(`${err.message.split("\n")[0]} ${String(out).slice(0, 200)}`)) : resolve(out)));
    p.stdin.end(data);
  });
}

async function synth(text) {
  const key = crypto.createHash("sha1").update([MODEL, VOICE, text].join("\n")).digest("hex");
  const file = path.join(cacheDir, key + ".pcm");
  if (fs.existsSync(file) && process.env.FORCE_TTS !== "1") return fs.readFileSync(file);
  const headers = { "Content-Type": "application/json", "X-DashScope-SSE": "enable" };
  if (process.env.DASHSCOPE_API_KEY) headers.Authorization = `Bearer ${process.env.DASHSCOPE_API_KEY}`;
  for (let attempt = 1; ; attempt++) {
    try {
      const body = await curlPost(URL, headers, JSON.stringify({ model: MODEL, input: { text, voice: VOICE } }));
      const chunks = [];
      for (const line of body.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const j = JSON.parse(line.slice(5));
        if (j.code) throw new Error(`${j.code} ${j.message}`);
        const d = j.output?.audio?.data;
        if (d) chunks.push(Buffer.from(d, "base64"));
      }
      let buf = Buffer.concat(chunks);
      if (buf.subarray(0, 4).toString() === "RIFF") buf = buf.subarray(buf.indexOf("data") + 8);
      if (buf.length < BPS * 0.2) throw new Error("音频过短");
      fs.writeFileSync(file, buf);
      return buf;
    } catch (e) {
      if (attempt >= 3) throw new Error(`合成失败「${text}」：${e.message}`);
      await new Promise((r) => setTimeout(r, 1500 * attempt));
    }
  }
}

// 逐句变速，按原音频哈希 + 倍率缓存
function tempo(pcm) {
  const f = path.join(cacheDir, crypto.createHash("sha1").update(pcm).digest("hex") + `.x${SPEED}.pcm`);
  if (fs.existsSync(f)) return fs.readFileSync(f);
  const out = ffPcm(pcm, `atempo=${SPEED}`);
  fs.writeFileSync(f, out);
  return out;
}

function wavHeader(n) {
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + n, 4); h.write("WAVE", 8); h.write("fmt ", 12);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22); h.writeUInt32LE(RATE, 24);
  h.writeUInt32LE(BPS, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34); h.write("data", 36); h.writeUInt32LE(n, 40);
  return h;
}
const silence = (sec) => Buffer.alloc(Math.round(sec * RATE) * 2);

// 并发合成全部句子
const jobs = [];
for (const sc of script) {
  if (only && sc.name !== only) continue;
  sc._sent = sc.segments.map((seg) => splitSentences(seg).map((s) => { const j = { text: s }; jobs.push(j); return j; }));
}
let next = 0, done = 0;
await Promise.all(Array.from({ length: PAR }, async () => {
  while (next < jobs.length) {
    const j = jobs[next++];
    j.pcm = await synth(fix(j.text));
    if (SPEED !== 1) j.pcm = tempo(j.pcm);
    process.stdout.write(`\r合成 ${++done}/${jobs.length}`);
  }
}));
console.log();

for (const sc of script) {
  if (!sc._sent) continue;
  const parts = [], starts = [], words = [];
  let t = 0;
  sc._sent.forEach((sents, bi) => {
    if (bi > 0) { parts.push(silence(BEAT_GAP)); t += BEAT_GAP; }
    starts.push(t);
    sents.forEach((s, si) => {
      if (si > 0) { parts.push(silence(GAP)); t += GAP; }
      const dur = s.pcm.length / BPS;
      const chars = [...s.text];
      const n = chars.filter((c) => /[\p{L}\p{N}]/u.test(c)).length;
      // 句首句尾各留一点静音余量，字在中间均分
      const a = t + Math.min(0.1, dur * 0.05), step = (dur - Math.min(0.25, dur * 0.12)) / n;
      let k = 0;
      for (const c of chars) {
        if (/[\p{L}\p{N}]/u.test(c)) { words.push({ w: c, s: +(a + k * step).toFixed(3), e: +(a + (k + 1) * step).toFixed(3) }); k++; }
        else if (words.length) words[words.length - 1].w += c;
      }
      parts.push(s.pcm); t += dur;
    });
  });
  sc._pcm = Buffer.concat(parts);
  fs.writeFileSync(path.join(P.audio, `${sc.name}.json`), JSON.stringify({ name: sc.name, duration: t, segmentStarts: starts, segments: sc.segments,
    engine: "bailian", model: MODEL, wordList: words }, null, 1));
  console.log(`${sc.name}: ${t.toFixed(1)}s  starts=${starts.map((x) => x.toFixed(1)).join(",")}`);
}

// 响度：测本次合成的全部场景拼起来的整体响度（只重配单个场景时就按该场景算），统一增益 + 限幅，写 wav
const done_ = script.filter((sc) => sc._pcm);
let gain = 0;
function measure(pcm) {
  const r = spawnSync("ffmpeg", ["-hide_banner", ...RAW, "-i", "-", "-af", "ebur128", "-f", "null", "-"], { input: pcm, maxBuffer: 256 << 20 });
  const m = [...String(r.stderr).matchAll(/I:\s+(-?[\d.]+) LUFS/g)].pop();
  return m ? Number(m[1]) : null;
}
if (LUFS != null) {
  const I = measure(Buffer.concat(done_.map((sc) => sc._pcm)));
  if (I != null) gain = LUFS - I;
  console.log(`响度 ${I} LUFS → 目标 ${LUFS} LUFS，增益 ${gain.toFixed(1)} dB，限幅 ${TP} dBTP`);
}
for (const sc of done_) {
  const pcm = LUFS != null ? ffPcm(sc._pcm, `volume=${gain.toFixed(2)}dB,alimiter=limit=${Math.pow(10, TP / 20).toFixed(3)}:level=disabled`) : sc._pcm;
  fs.writeFileSync(path.join(P.audio, `${sc.name}.wav`), Buffer.concat([wavHeader(pcm.length), pcm]));
}
