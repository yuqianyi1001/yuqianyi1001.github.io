// TTS 配音层 —— 只用火山引擎(豆包)语音合成大模型(音色由 .env VOLC_TTS_VOICE 指定, 当前擎苍)。每段旁白产出一个 wav, 返回真实时长。
// 时长很关键: 它决定每个分镜在时间轴上的长度(音画同步)。
// 失败就抛错、不回退到别的引擎(保证音色一致); 火山 403 就去续授权/额度, 别拿其它声音顶替。
// 按正文、引擎、音色、参数与 WAV 内容指纹自动复用；FORCE_TTS=1 强制重配。
import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { digest, ttsIdentity, readAudioCache, writeAudioCache } from "./content-cache.mjs";

// 火山 HTTP 单向接口: 一次性输入文本, 一个请求拿到完整音频(fetch 自动收齐分块, 我们无需流式)。
// 文档: https://www.volcengine.com/docs/6561/1598757
const VOLC_HTTP_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional";

export function getDuration(file) {
  const out = execFileSync("ffprobe", [
    "-v", "quiet", "-show_entries", "format=duration",
    "-of", "csv=p=0", file,
  ]).toString().trim();
  return parseFloat(out) || 0;
}

// mp3 → 44100/立体声 wav(对齐管线其余环节)
function toWav(src, outWav) {
  execFileSync("ffmpeg", ["-y", "-i", src, "-ar", "44100", "-ac", "2", outWav], { stdio: "ignore" });
}

// 从环境变量拼鉴权头与音色(新版控制台 API Key / 旧版 AppId+Token 二选一)
function volcConfig(voice) {
  const resourceId = process.env.VOLC_TTS_RESOURCE_ID || "seed-tts-1.0";
  const headers = {
    "Content-Type": "application/json",
    "X-Api-Resource-Id": resourceId,
    "X-Api-Connect-Id": randomUUID(),
  };
  if (process.env.VOLC_TTS_API_KEY) {
    headers["X-Api-Key"] = process.env.VOLC_TTS_API_KEY;
  } else if (process.env.VOLC_TTS_APP_ID && process.env.VOLC_TTS_ACCESS_TOKEN) {
    headers["X-Api-App-Id"] = process.env.VOLC_TTS_APP_ID;
    headers["X-Api-Access-Key"] = process.env.VOLC_TTS_ACCESS_TOKEN;
  } else {
    throw new Error("缺少火山凭证: 在 .env 配 VOLC_TTS_API_KEY(新版控制台) 或 VOLC_TTS_APP_ID+VOLC_TTS_ACCESS_TOKEN(旧版)");
  }
  // shotlist 的 voice 是 macOS 旧值(如 Tingting, 无下划线), 不是火山音色; 仅当像火山音色才采用。
  const speaker = voice && voice.includes("_")
    ? voice
    : (process.env.VOLC_TTS_VOICE || "zh_female_shuangkuaisisi_moon_bigtts");
  return { headers, speaker };
}

// 火山流式响应是一串 JSON(每个含 base64 音频片段)。无论 NDJSON 还是 SSE(event:/data:)分隔,
// 都用花括号配平扫出每个顶层 JSON 对象, 避免依赖具体换行/前缀格式。
function extractJsonObjects(text) {
  const objs = [];
  let depth = 0, start = -1, inStr = false, esc = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === "\\") esc = true;
      else if (c === '"') inStr = false;
    } else if (c === '"') inStr = true;
    else if (c === "{") { if (depth++ === 0) start = i; }
    else if (c === "}") { if (--depth === 0 && start >= 0) { objs.push(text.slice(start, i + 1)); start = -1; } }
  }
  return objs;
}

// 递归收集逐字时间戳: 火山把它放在 sentence.words, 与音频分片穿插在同一串 JSON 里。
// ⚠️别再丢掉它(2026-08-21 之前 collectAudio 只捞音频, 字幕只能按字数线性估时间 → 断句飘)。
function collectWords(node, out) {
  if (!node || typeof node !== "object") return;
  if (Array.isArray(node.words) && node.words.length) out.push(...node.words);
  for (const v of Object.values(node)) if (v && typeof v === "object") collectWords(v, out);
}

// 递归收集音频: 取任意层级下 key 为 data/audio 的 base64 字符串(火山可能把音频包在 header/payload 内)。
function collectAudio(node, out) {
  if (!node || typeof node !== "object") return;
  for (const [k, v] of Object.entries(node)) {
    if ((k === "data" || k === "audio") && typeof v === "string" && v) out.push(Buffer.from(v, "base64"));
    else if (v && typeof v === "object") collectAudio(v, out);
  }
}

// 对一段文本生成配音, 返回 { path, duration }。**只用火山, 失败就抛错(不回退别的引擎)**。
// REUSE_AUDIO 不再跳过内容校验；缓存命中同时恢复本次音频对应的 words。
export async function synthesize(text, outWav, { voice } = {}) {
  fs.mkdirSync(path.dirname(outWav), { recursive: true });
  const key = digest(ttsIdentity(text, voice));
  // 无元数据的旧 WAV 是未验证缓存，不猜测其来源。强制重配用 FORCE_TTS=1。
  const cached = process.env.FORCE_TTS !== '1' && readAudioCache(outWav, key);
  if (cached) return cached;
  const remember = audio => { writeAudioCache(outWav, key, audio); return audio; };
  // ⚠️ 占位通道(2026-09-05 火山全账号 403 时加): TTS_ENGINE=say 用 macOS say 出临时配音, 只为验版式/时间轴,
  //   正式出片必须删掉 wav 换回火山重配。不带逐字时间戳(words=[])。
  if (process.env.TTS_ENGINE === "say") {
    const { execFileSync } = await import("node:child_process");
    const aiff = outWav.replace(/\.wav$/, ".aiff");
    execFileSync("say", ["-v", process.env.SAY_VOICE || "Tingting", "-r", process.env.SAY_RATE || "200", "-o", aiff, text]);
    execFileSync("ffmpeg", ["-nostdin", "-y", "-v", "error", "-i", aiff, "-ar", "24000", "-ac", "1", outWav]);
    fs.rmSync(aiff, { force: true });
    return remember({ path: outWav, duration: getDuration(outWav), words: [] });
  }
  const { headers, speaker } = volcConfig(voice);

  // 逐字时间戳(sentence.words[{word,startTime,endTime,confidence}]), 两个开关都放 audio_params 里:
  //   enable_timestamp → 仅 TTS 1.0 音色生效(字为 tn 后文本);
  //   enable_subtitle  → TTS 2.0 / ICL 2.0 音色生效(字为原文, 以 TTSSubtitle 事件穿插返回, 可能晚于音频帧)。
  // ⚠️2026-09-14 实测: seed-tts-2.0 + *_uranus_bigtts 只开 enable_timestamp 返回 words=[]; 加 enable_subtitle 后每字一条, 1.2 倍速也准。
  //   官方文档 https://docs.volcengine.com/docs/6561/1598757 §2.4。有了它字幕对齐不再需要 whisper ASR。
  const audioParams = { format: "mp3", sample_rate: 24000, bit_rate: 128000, enable_timestamp: true, enable_subtitle: true };
  const speed = Number(process.env.VOLC_TTS_SPEED || 0); // [-50,100], 0=原速
  if (speed) audioParams.speech_rate = speed;

  // 2.0 音色的自然语言风格控制(VOLC_TTS_STYLE, 如"低沉沙哑的深夜电台女主播"):
  // additions 必须是 JSON 序列化字符串, context_texts 只取第一条, 不计字符费。仅 *_uranus_bigtts 家族响应。
  const reqParams = { text, speaker, audio_params: audioParams };
  const style = process.env.VOLC_TTS_STYLE || "";
  if (style) reqParams.additions = JSON.stringify({ context_texts: [style] });

  const resp = await fetch(VOLC_HTTP_URL, {
    method: "POST",
    headers,
    body: JSON.stringify({
      user: { uid: "whiteboard-video" },
      req_params: reqParams,
    }),
  });
  const raw = await resp.text();
  if (!resp.ok) throw new Error(`火山 TTS HTTP ${resp.status}: ${raw.slice(0, 300)}`);

  const chunks = [];
  const words = [];
  for (const objStr of extractJsonObjects(raw)) {
    let o;
    try { o = JSON.parse(objStr); } catch { continue; }
    collectAudio(o, chunks);
    collectWords(o, words);
  }
  if (!chunks.length) throw new Error("火山 TTS 未返回音频: " + raw.slice(0, 300));

  const mp3 = outWav.replace(/\.wav$/, ".mp3");
  fs.writeFileSync(mp3, Buffer.concat(chunks));
  toWav(mp3, outWav);
  fs.rmSync(mp3, { force: true });
  // words: [{word,startTime,endTime,confidence}] — 逐字对齐, 给字幕分段/卡拉OK高亮用。
  // ⚠️时间戳只描述「这一遍合成的音频」: 火山非确定性(同句两次时长实测差 0.07-0.24s),
  //   拿它去套另一条已存在的 wav 会飘, 必须与音频同一次产出。
  return remember({ path: outWav, duration: getDuration(outWav), words });
}

// CLI 自测凭证: node src/tts.mjs "要合成的文本" [输出.wav]
// (单跑时管线的 config.mjs 不会执行, 这里自己加载根目录 .env)
if (import.meta.url === `file://${process.argv[1]}`) {
  try { process.loadEnvFile(path.resolve(import.meta.dirname, "../../.env")); } catch { /* 无 .env 忽略 */ }
  const text = process.argv[2] || "你好，我是火山引擎的语音合成服务。这是一段测试旁白。";
  const out = path.resolve(process.argv[3] || "tts-test.wav");
  const r = await synthesize(text, out, {});
  console.log(`[tts] ✓ ${r.path}  时长 ${r.duration.toFixed(2)}s`);
}
