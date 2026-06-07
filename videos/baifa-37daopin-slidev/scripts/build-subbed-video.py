"""
Generate SRT from notes/*.txt + audio/*.mp3 (timing by char-proportion),
then mux into existing MP4 as a soft subtitle track.

Output:
  video/baifa-relations.srt        - editable subtitle file
  video/baifa-relations-soft.mp4   - MP4 with embedded subtitle track
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = ROOT / "notes"
AUDIO_DIR = ROOT / "audio"
VIDEO_DIR = ROOT / "video"
SRT_PATH = VIDEO_DIR / "baifa-relations.srt"
INPUT_MP4 = VIDEO_DIR / "baifa-relations.mp4"
OUTPUT_MP4 = VIDEO_DIR / "baifa-relations-soft.mp4"

TAIL_SILENCE = 0.4          # silence padded after each slide's audio (matches build-video.py)
SOFT_BREAK_MIN_CHARS = 12   # only break on ，； when current chunk has at least this many chars
MIN_DURATION = 0.6          # minimum on-screen time per subtitle (seconds)
N_SLIDES = 37


def get_duration(p: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(p),
    ])
    return float(out.strip())


def format_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_sentences(text: str) -> list[str]:
    """Split Chinese text into subtitle-sized chunks.

    Strong break: 。！？ -> always split here.
    Soft break:   ，； -> split only if accumulated chunk has >= SOFT_BREAK_MIN_CHARS.
    """
    text = text.replace("\n", " ").strip()
    parts = re.split(r"([。！？，；])", text)
    chunks: list[str] = []
    buf = ""
    for p in parts:
        if not p:
            continue
        buf += p
        if p in "。！？":
            stripped = buf.strip()
            if stripped:
                chunks.append(stripped)
            buf = ""
        elif p in "，；":
            stripped = buf.strip()
            if len(stripped) >= SOFT_BREAK_MIN_CHARS:
                chunks.append(stripped)
                buf = ""
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def build_srt() -> int:
    entries: list[tuple[int, float, float, str]] = []
    cum_offset = 0.0
    entry_idx = 1

    for i in range(1, N_SLIDES + 1):
        note_file = NOTES_DIR / f"{i:02d}.txt"
        audio_file = AUDIO_DIR / f"{i:02d}.mp3"
        if not note_file.exists() or not audio_file.exists():
            print(f"  [skip] slide {i:02d}: missing notes or audio")
            continue

        text = note_file.read_text(encoding="utf-8").strip()
        duration = get_duration(audio_file)

        chunks = split_sentences(text)
        total_chars = sum(len(c) for c in chunks)

        if total_chars == 0:
            cum_offset += duration + TAIL_SILENCE
            continue

        time_per_char = duration / total_chars
        t = cum_offset
        for chunk in chunks:
            chunk_dur = max(len(chunk) * time_per_char, MIN_DURATION)
            entries.append((entry_idx, t, t + chunk_dur, chunk))
            entry_idx += 1
            t += chunk_dur

        # Move past this slide's audio + trailing silence
        cum_offset += duration + TAIL_SILENCE

    SRT_PATH.parent.mkdir(exist_ok=True)
    with open(SRT_PATH, "w", encoding="utf-8") as f:
        for idx, start, end, text in entries:
            f.write(f"{idx}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text}\n\n")

    print(f"[srt] {len(entries)} subtitle entries → {SRT_PATH.name}")
    return len(entries)


def mux_soft_subs() -> None:
    if not INPUT_MP4.exists():
        sys.exit(f"[error] input MP4 not found: {INPUT_MP4}")

    print(f"[mux] embedding subtitle track into {OUTPUT_MP4.name} ...")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(INPUT_MP4),
            "-i", str(SRT_PATH),
            "-c", "copy",                       # no re-encode
            "-c:s", "mov_text",                 # MP4-compatible subtitle codec
            "-metadata:s:s:0", "language=chi",
            "-metadata:s:s:0", "title=简体中文",
            "-disposition:s:0", "default",      # turn on by default
            "-movflags", "+faststart",
            str(OUTPUT_MP4),
        ],
        check=True,
        stderr=subprocess.DEVNULL,
    )

    size_mb = OUTPUT_MP4.stat().st_size / 1024 / 1024
    dur = get_duration(OUTPUT_MP4)
    m, s = divmod(int(dur), 60)
    print(f"[done] {OUTPUT_MP4}")
    print(f"       duration: {m}m {s}s")
    print(f"       size:     {size_mb:.1f} MB")


def main() -> None:
    if not NOTES_DIR.exists() or not AUDIO_DIR.exists():
        sys.exit("[error] notes/ or audio/ directory missing")
    build_srt()
    mux_soft_subs()


if __name__ == "__main__":
    main()
