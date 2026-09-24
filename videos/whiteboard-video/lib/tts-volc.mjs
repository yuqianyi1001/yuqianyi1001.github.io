// 旁白：火山引擎语音合成（lib/tts/tts.mjs，凭证在仓库根目录 .env，字段见 .env.example）。
// 输出 <project>/audio/<scene>.wav + <scene>.json（duration / segmentStarts，渲染器按段起点对齐画图节奏）。
// 用法：node lib/tts-volc.mjs <projectDir> [scene...]   FORCE_TTS=1 强制重配
import fs from "node:fs";
import path from "node:path";

import paths from "./paths.cjs";
const { cfg, projectPaths } = paths;
const P = projectPaths(process.argv[2] || ".");
const only = process.argv.slice(3);

try { process.loadEnvFile(path.join(paths.ROOT, ".env")); } catch { /* 没有 .env 就只用环境变量 */ }
if (cfg.tts.resourceId) process.env.VOLC_TTS_RESOURCE_ID = cfg.tts.resourceId;
// 语速：config tts.speed 倍率 → 火山 speech_rate（[-50,100]，100=2 倍速，-50=0.5 倍速）
const SPEED = Number(cfg.tts.speed || 1);
process.env.VOLC_TTS_SPEED = String(Math.max(-50, Math.min(100, Math.round((SPEED - 1) * 100))));
process.env.FORCE_TTS = process.env.FORCE_TTS || "0";
const { synthesize } = await import("./tts/tts.mjs");

const VOICE = cfg.tts.voice || process.env.VOLC_TTS_VOICE;
if (!VOICE) throw new Error("没有音色：在 .env 填 VOLC_TTS_VOICE，或在 config.json tts.voice 填音色 ID");
const norm = (s) => [...s].filter((c) => /[\p{L}\p{N}]/u.test(c)).join("");
const scenes = JSON.parse(fs.readFileSync(P.script));
fs.mkdirSync(P.audio, { recursive: true });

for (const sc of scenes) {
  if (only.length && !only.includes(sc.name)) continue;
  const full = sc.segments.join("");
  const wav = path.join(P.audio, `${sc.name}.wav`);
  const need = norm(full).length;
  let r, tries = 0;
  while (true) {
    try {
      r = await synthesize(full, wav, { voice: VOICE });
      const got = r.words.reduce((n, w) => n + norm(w.word).length, 0);
      if (got >= need * 0.85) break;
      // 火山偶尔只返回半段音频：按逐字数校验，不够就强制重配
      console.log(`  truncated ${sc.name}: ${got}/${need} chars, retry`);
      process.env.FORCE_TTS = "1";
    } catch (e) { console.log("  retry", sc.name, e.message.slice(0, 80)); }
    if (++tries >= 4) throw new Error("TTS failed: " + sc.name);
  }
  process.env.FORCE_TTS = "0";
  // 逐字时间 → 每个旁白段的起始秒
  let acc = 0; const posTime = [];
  for (const w of r.words) { posTime.push([acc, w.startTime]); acc += norm(w.word).length; }
  const starts = []; let p = 0;
  for (const seg of sc.segments) { starts.push(p); p += norm(seg).length; }
  const segStarts = starts.map((sp) => { let best = 0; for (const [cp, t] of posTime) { if (cp <= sp) best = t; else break; } return best; });
  segStarts[0] = 0;
  fs.writeFileSync(path.join(P.audio, `${sc.name}.json`), JSON.stringify({ name: sc.name, duration: r.duration, segmentStarts: segStarts, segments: sc.segments, voice: VOICE, words: r.words.length, normChars: p,
    wordList: r.words.map((w) => ({ w: w.word, s: +w.startTime.toFixed(3), e: +w.endTime.toFixed(3) })) }, null, 1));
  console.log(`${sc.name}: ${r.duration.toFixed(1)}s @${SPEED}x  starts=${segStarts.map((t) => t.toFixed(1)).join(",")}  words=${r.words.length}/${p}`);
}
