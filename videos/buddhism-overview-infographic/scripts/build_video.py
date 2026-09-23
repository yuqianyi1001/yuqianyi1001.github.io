#!/usr/bin/env python3
"""把 out-16x9/card-N.png 和 audio/NN.wav 合成视频，并生成字幕。

输出到 video/：
  buddhism-overview.mp4       无字幕
  buddhism-overview.srt/.ass  字幕
  buddhism-overview-hard.mp4  硬字幕
字幕按 VIDEO-PRODUCTION-GUIDE.md 的约定：句末标点必换行，逗号类在当前行 ≥12 字时换行，
时长按字数比例分配到每段音频。
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "out-16x9"
AUDIO = ROOT / "audio"
NOTES = ROOT / "notes"
OUT = ROOT / "video"
SEG = ROOT / "segments"
FFMPEG = str(Path.home() / "miniforge3/bin/ffmpeg")
FFPROBE = str(Path.home() / "miniforge3/bin/ffprobe")
SLUG = "buddhism-overview"
TAIL_SILENCE = 0.4
FRAMERATE = 30
MIN_DURATION = 0.6
MAX_LINE = 34

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Heiti SC,38,&H00182430,&H00182430,&H30E5F4FB,&H30E5F4FB,0,0,0,0,100,100,0,0,3,8,0,2,60,60,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def run(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def split_lines(text):
    """把一段口播稿切成字幕行。"""
    lines = []
    for para in [p.strip() for p in text.splitlines() if p.strip()]:
        cur = ""
        for ch in para:
            cur += ch
            if ch in "。？！":
                lines.append(cur); cur = ""
            elif ch in "，；：" and len(cur) >= 12:
                lines.append(cur); cur = ""
            elif ch == "、" and len(cur) >= MAX_LINE - 6:
                lines.append(cur); cur = ""
        if cur.strip():
            lines.append(cur)
    out = []
    for l in lines:
        l = l.strip().rstrip("，；。：、").strip("—").strip()
        if l:
            out.append(l)
    return out


def ts_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def ts_ass(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def main():
    OUT.mkdir(exist_ok=True)
    SEG.mkdir(exist_ok=True)
    notes = sorted(NOTES.glob("*.txt"))
    cues, t0, parts = [], 0.0, []
    for i, note in enumerate(notes, 1):
        card, wav = CARDS / f"card-{i}.png", AUDIO / f"{note.stem}.wav"
        assert card.exists() and wav.exists(), (card, wav)
        adur = duration(wav)
        seg = SEG / f"{note.stem}.mp4"
        run([FFMPEG, "-y", "-v", "error", "-loop", "1", "-framerate", str(FRAMERATE), "-i", str(card), "-i", str(wav),
             "-af", f"apad=pad_dur={TAIL_SILENCE}", "-t", f"{adur + TAIL_SILENCE:.3f}",
             "-c:v", "libx264", "-tune", "stillimage", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", str(seg)])
        parts.append(seg)
        seg_dur = duration(seg)
        # 字幕：按字数比例分配本段音频时长
        lines = split_lines(note.read_text())
        total = sum(len(l) for l in lines)
        acc = 0
        for l in lines:
            s = t0 + adur * acc / total
            acc += len(l)
            e = max(t0 + adur * acc / total, s + MIN_DURATION)
            cues.append((s, e, l))
        t0 += seg_dur
        print(f"{note.stem}: {seg_dur:.1f}s, {len(lines)} 行字幕", flush=True)

    concat = SEG / "list.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in parts))
    base = OUT / f"{SLUG}.mp4"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy",
         "-movflags", "+faststart", str(base)])

    srt = "".join(f"{n}\n{ts_srt(s)} --> {ts_srt(e)}\n{l}\n\n" for n, (s, e, l) in enumerate(cues, 1))
    (OUT / f"{SLUG}.srt").write_text(srt)
    ass = ASS_HEADER + "".join(f"Dialogue: 0,{ts_ass(s)},{ts_ass(e)},Default,,0,0,0,,{l}\n" for s, e, l in cues)
    ass_path = OUT / f"{SLUG}.ass"
    ass_path.write_text(ass)

    hard = OUT / f"{SLUG}-hard.mp4"
    run([FFMPEG, "-y", "-v", "error", "-stats", "-i", str(base), "-vf", f"ass={ass_path}",
         "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy",
         "-movflags", "+faststart", str(hard)])
    print(f"done: {base.name}, {hard.name}, {len(cues)} 条字幕, 总长 {duration(base):.1f}s")


if __name__ == "__main__":
    main()
