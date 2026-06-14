"""
Build hard-subtitled MP4.

Approach: generate an ASS file (with styling baked into the file itself),
then burn it into the video via ffmpeg's `ass` filter. This avoids the
escaping nightmare of `subtitles:force_style`.

Steps:
  1. Regenerate SRT (for the soft-sub variant + as a debug artifact).
  2. Generate ASS file with styling.
  3. ffmpeg ass= filter + libx264 re-encode.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# brew ffmpeg lacks libass; conda-forge build has it. Prefer conda.
FFMPEG = str(Path.home() / "miniforge3" / "bin" / "ffmpeg")
NOTES_DIR = ROOT / "notes"
AUDIO_DIR = ROOT / "audio"
VIDEO_DIR = ROOT / "video"
SRT_PATH = VIDEO_DIR / "baifa-jiandao.srt"
ASS_PATH = VIDEO_DIR / "baifa-jiandao.ass"
INPUT_MP4 = VIDEO_DIR / "baifa-jiandao.mp4"
OUTPUT_MP4 = VIDEO_DIR / "baifa-jiandao-hard.mp4"

TAIL_SILENCE = 0.4
SOFT_BREAK_MIN_CHARS = 12
MIN_DURATION = 0.6
N_SLIDES = 26

# Slide PNG canvas (preview/1.png is 1960x1104).
PLAY_RES_X = 1960
PLAY_RES_Y = 1104

# ASS color format is &HAABBGGRR& (alpha + reversed RGB).
#   #302418 (deep brown) → BGR 18 24 30 → &H00182430
#   #FBF4E5 (warm cream) → BGR E5 F4 FB → &HxxE5F4FB
#
# Subtitle box: light warm cream, ~80% opaque, soft padding via Outline.
# OutlineColour == BackColour so the outline blends into the box (looks like padding).
ASS_STYLE = {
    "Fontname": "PingFang SC",
    "Fontsize": 38,                    # was 32, +20% ≈ 38 (lands ~38px on 1104-tall canvas)
    "PrimaryColour": "&H00182430",     # deep brown (text body)
    "SecondaryColour": "&H000000FF",   # unused for karaoke
    "OutlineColour": "&H30E5F4FB",     # same as BackColour → outline blends as padding
    "BackColour": "&H30E5F4FB",        # warm cream box (alpha 30 ≈ 80% opaque, BGR=E5F4FB)
    "Bold": 0,
    "Italic": 0,
    "Underline": 0,
    "StrikeOut": 0,
    "ScaleX": 100,
    "ScaleY": 100,
    "Spacing": 0,
    "Angle": 0,
    "BorderStyle": 3,                  # 3 = opaque box (uses BackColour behind text)
    "Outline": 8,                      # 8px padding (since outline blends with box bg)
    "Shadow": 0,
    "Alignment": 2,                    # 2 = bottom center
    "MarginL": 60,
    "MarginR": 60,
    "MarginV": 70,                     # 70px from bottom
    "Encoding": 1,                     # CP932 / default (libass ignores for unicode anyway)
}


def get_duration(p: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(p),
    ])
    return float(out.strip())


def fmt_srt_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_ass_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int(round((t - int(t)) * 100))
    if cs == 100:
        cs = 0
        s += 1
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def split_sentences(text: str) -> list[str]:
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


def build_subtitle_timeline() -> list[tuple[float, float, str]]:
    """Return list of (start_seconds, end_seconds, text) entries."""
    entries: list[tuple[float, float, str]] = []
    cum_offset = 0.0

    for i in range(1, N_SLIDES + 1):
        note_file = NOTES_DIR / f"{i:02d}.txt"
        audio_file = AUDIO_DIR / f"{i:02d}.mp3"
        if not note_file.exists() or not audio_file.exists():
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
            entries.append((t, t + chunk_dur, chunk))
            t += chunk_dur

        cum_offset += duration + TAIL_SILENCE

    return entries


def write_srt(entries: list[tuple[float, float, str]]) -> None:
    SRT_PATH.parent.mkdir(exist_ok=True)
    with open(SRT_PATH, "w", encoding="utf-8") as f:
        for idx, (start, end, text) in enumerate(entries, start=1):
            f.write(f"{idx}\n")
            f.write(f"{fmt_srt_time(start)} --> {fmt_srt_time(end)}\n")
            f.write(f"{text}\n\n")
    print(f"[srt] {len(entries)} entries → {SRT_PATH.name}")


def write_ass(entries: list[tuple[float, float, str]]) -> None:
    style_order = [
        "Fontname", "Fontsize", "PrimaryColour", "SecondaryColour",
        "OutlineColour", "BackColour", "Bold", "Italic", "Underline",
        "StrikeOut", "ScaleX", "ScaleY", "Spacing", "Angle", "BorderStyle",
        "Outline", "Shadow", "Alignment", "MarginL", "MarginR", "MarginV",
        "Encoding",
    ]
    style_values = [str(ASS_STYLE[k]) for k in style_order]
    style_line = "Default," + ",".join(style_values)

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "Collisions: Normal\n"
        f"PlayResX: {PLAY_RES_X}\n"
        f"PlayResY: {PLAY_RES_Y}\n"
        "Timer: 100.0000\n"
        "WrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: {style_line}\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )

    lines = [header]
    for start, end, text in entries:
        # Escape special ASS chars: commas/curly braces are problematic in Text field
        safe = text.replace("\n", "\\N").replace("{", "(").replace("}", ")")
        lines.append(
            f"Dialogue: 0,{fmt_ass_time(start)},{fmt_ass_time(end)},Default,,0,0,0,,{safe}\n"
        )

    ASS_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"[ass] {len(entries)} dialogue lines → {ASS_PATH.name}")


def burn_subs() -> None:
    if not INPUT_MP4.exists():
        sys.exit(f"[error] input MP4 missing: {INPUT_MP4}")

    print(f"[burn] re-encoding video with ASS subs burned in ...")
    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", str(INPUT_MP4),
            "-vf", f"ass=filename={ASS_PATH}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(OUTPUT_MP4),
        ],
        check=True,
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
    entries = build_subtitle_timeline()
    write_srt(entries)
    write_ass(entries)
    burn_subs()


if __name__ == "__main__":
    main()
