"""
Combine preview/{N}.png + audio/{NN}.mp3 (N = 1..36) into a single MP4.

For each slide:
  - Loop the PNG for (audio_duration + TAIL_SILENCE) seconds
  - Audio = the slide's mp3, padded with TAIL_SILENCE seconds of silence
  - Encode H.264 + AAC

Then concat all 36 segments into video/baifa-jiandao.mp4.

Idempotent: existing segments are reused. To rebuild, delete segments/.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "preview"
AUDIO = ROOT / "audio"
SEGMENTS = ROOT / "segments"
VIDEO_DIR = ROOT / "video"
SEGMENTS.mkdir(exist_ok=True)
VIDEO_DIR.mkdir(exist_ok=True)
OUT = VIDEO_DIR / "baifa-jiandao.mp4"

TAIL_SILENCE = 0.4  # seconds after each slide's audio for natural breath
FRAMERATE = 30


def get_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(out.strip())


def build_segment(idx: int) -> Path:
    label = f"{idx:02d}"
    img = PREVIEW / f"{idx}.png"
    aud = AUDIO / f"{label}.mp3"
    seg = SEGMENTS / f"{label}.mp4"

    if seg.exists() and seg.stat().st_size > 0:
        return seg

    if not img.exists() or not aud.exists():
        sys.exit(f"missing assets for slide {label}: img={img.exists()} aud={aud.exists()}")

    audio_dur = get_duration(aud)
    total_dur = audio_dur + TAIL_SILENCE

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-framerate",
        str(FRAMERATE),
        "-i",
        str(img),
        "-i",
        str(aud),
        # Pad audio with trailing silence so video doesn't cut to next slide instantly
        "-af",
        f"apad=pad_dur={TAIL_SILENCE}",
        # Ensure dims are even (H.264 requires) and yuv420p for max compatibility
        "-vf",
        "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-tune",
        "stillimage",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "44100",
        "-r",
        str(FRAMERATE),
        "-t",
        f"{total_dur:.3f}",
        str(seg),
    ]
    print(f"[seg {label}] audio={audio_dur:.1f}s total={total_dur:.1f}s", flush=True)
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
    return seg


def main() -> None:
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found in PATH")

    # 1. Build 33 segments
    segments = []
    for i in range(1, 27):
        segments.append(build_segment(i))

    # 2. Build concat list
    concat_list = SEGMENTS / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{seg.name}'" for seg in segments) + "\n",
        encoding="utf-8",
    )
    print(f"[concat] {len(segments)} segments listed in {concat_list}", flush=True)

    # 3. Concat (stream-copy; all segments share identical codec params)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(OUT),
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)

    dur = get_duration(OUT)
    size_mb = OUT.stat().st_size / 1024 / 1024
    m, s = divmod(int(dur), 60)
    print(f"\n[done] {OUT}")
    print(f"       duration: {dur:.1f}s ({m}m {s}s)")
    print(f"       size:     {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
