"""备胎旁白：edge-tts（微软在线 TTS）。用法: python3 lib/tts-edge.py <projectDir> [scene...]
输出 <project>/audio/<scene>.mp3 和 .json。正式出片用火山克隆音 lib/tts-volc.mjs。
"""
import asyncio, json, os, subprocess, sys
import edge_tts

ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
VOICE = os.environ.get("VOICE", "zh-CN-YunxiNeural")
RATE = os.environ.get("RATE", "+2%")

def norm(s: str) -> str:
    return "".join(ch for ch in s if ch.isalnum())

async def one(scene):
    name, segs = scene["name"], scene["segments"]
    full = "".join(segs)
    mp3 = os.path.join(ROOT, "audio", f"{name}.mp3")
    comm = edge_tts.Communicate(full, VOICE, rate=RATE, boundary="WordBoundary")
    words = []  # (offset_sec, text)
    with open(mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append((chunk["offset"] / 1e7, chunk["text"]))
    # 把 word boundary 映射到「规范化字符位置」
    pos_time = []  # (char_pos, time)
    acc = 0
    for t, w in words:
        pos_time.append((acc, t))
        acc += len(norm(w))
    total_norm = len(norm(full))
    # 每段起点的规范化字符位置
    starts = []
    p = 0
    for sg in segs:
        starts.append(p)
        p += len(norm(sg))
    seg_times = []
    for sp in starts:
        best = 0.0
        for cp, t in pos_time:
            if cp <= sp:
                best = t
            else:
                break
        seg_times.append(best)
    seg_times[0] = 0.0
    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3]).decode().strip())
    info = {"name": name, "duration": dur, "segmentStarts": seg_times, "segments": segs,
            "wordsMatched": len(pos_time), "normChars": total_norm}
    with open(os.path.join(ROOT, "audio", f"{name}.json"), "w") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    print(f"{name}: {dur:.1f}s  starts={[round(t,1) for t in seg_times]}")

async def main():
    os.makedirs(os.path.join(ROOT, "audio"), exist_ok=True)
    scenes = json.load(open(os.path.join(ROOT, "scenes", "script.json")))
    only = sys.argv[2:]
    for sc in scenes:
        if only and sc["name"] not in only:
            continue
        await one(sc)

asyncio.run(main())
