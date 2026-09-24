import fs from 'node:fs';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';

export const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
export function fileDigest(file) {
  const hash = createHash('sha256');
  const fd = fs.openSync(file, 'r');
  const buffer = Buffer.allocUnsafe(1024 * 1024);
  try { let n; while ((n = fs.readSync(fd, buffer, 0, buffer.length, null))) hash.update(buffer.subarray(0, n)); }
  finally { fs.closeSync(fd); }
  return hash.digest('hex');
}
export function assetFingerprint(value) {
  const url = String(value);
  if (/^https?:\/\//.test(url)) return { url, remote: true }; // 远程源需先落本地才能核实内容
  const file = path.resolve(url.replace(/^file:\/\//, ''));
  try { return { file, sha256: fileDigest(file) }; } catch { return { file, missing: true }; }
}
export function footageFingerprint(shotList) {
  const urls = [...new Set((shotList.scenes || []).flatMap(s => {
    const v = s.visual?.footage_url;
    return Array.isArray(v) ? v : v ? [v] : [];
  }))];
  return urls.map(assetFingerprint);
}
export function atomicJSON(file, data) {
  const tmp = `${file}.${randomUUID()}.tmp`;
  try { fs.writeFileSync(tmp, JSON.stringify(data)); fs.renameSync(tmp, file); }
  finally { fs.rmSync(tmp, { force: true }); }
}
export function readAudioCache(file, key) {
  try {
    const entry = JSON.parse(fs.readFileSync(`${file}.cache.json`, 'utf8'));
    if (entry.version !== 1 || entry.key !== key || entry.sha256 !== fileDigest(file)
      || !Number.isFinite(entry.duration) || !(entry.duration > 0) || !Array.isArray(entry.words)) return null;
    return { path: file, duration: entry.duration, words: entry.words };
  } catch { return null; }
}
export function writeAudioCache(file, key, audio) {
  if (!Number.isFinite(audio.duration) || audio.duration <= 0) throw new Error("不能缓存无效音频时长");
  atomicJSON(`${file}.cache.json`, { version: 1, key, sha256: fileDigest(file), duration: audio.duration, words: audio.words || [] });
}
export function ttsIdentity(text, voice, env = process.env) {
  if (env.TTS_ENGINE === 'say') return { version: 1, text, engine: 'say', voice: env.SAY_VOICE || 'Tingting', rate: env.SAY_RATE || '200', wav: '24000-mono' };
  return { version: 1, text, engine: 'volc', resource: env.VOLC_TTS_RESOURCE_ID || 'seed-tts-1.0',
    speaker: voice?.includes('_') ? voice : env.VOLC_TTS_VOICE || 'zh_female_shuangkuaisisi_moon_bigtts',
    speed: Number(env.VOLC_TTS_SPEED || 0), style: env.VOLC_TTS_STYLE || '',
    format: 'mp3', sampleRate: 24000, bitRate: 128000, timestamp: true, wav: '44100-stereo' };
}

// 总管线与逐镜缓存都看内容；产物缺失/被替换不能被 manifest 的旧状态掩盖。
export function stageMediaFingerprint(stage, paths, shotList, videoIndex) {
  const beds = (videoIndex.items || []).filter(i => i.video).map(i => assetFingerprint(path.join(paths.dir, i.video)));
  if (stage === 'video') return { sources: footageFingerprint(shotList), beds };
  return { beds, audio: (shotList.scenes || []).flatMap(s => [
    assetFingerprint(path.join(paths.audio, `${s.id}.wav`)),
    assetFingerprint(path.join(paths.audio, `${s.id}.wav.cache.json`)),
  ]) };
}
