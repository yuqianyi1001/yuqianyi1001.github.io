"""
Synthesize all 36 slide notes from slides.md into audio/NN.mp3 files,
using the cloned 愚千一 voice on Aliyun 百炼 (cosyvoice-v2).

Reads voice_id from .bailian_voice_id (created by clone-and-synth.py).
Skips slides whose audio already exists (idempotent).
Runs up to MAX_PARALLEL synth calls concurrently.
Retries each call up to MAX_RETRIES times on transient failure.
"""
from __future__ import annotations

import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

env_file = Path.home() / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

import dashscope  # noqa: E402
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat  # noqa: E402

API_KEY = os.environ.get("DASHSCOPE_API_KEY")
if not API_KEY:
    sys.exit("ERROR: DASHSCOPE_API_KEY not found")
dashscope.api_key = API_KEY

ROOT = Path(__file__).resolve().parent.parent
VOICE_ID = (ROOT / ".bailian_voice_id").read_text().strip()
TARGET_MODEL = "cosyvoice-v2"
SPEECH_RATE = 1.0

NOTES_DIR = ROOT / "notes"
AUDIO_DIR = ROOT / "audio"
NOTES_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

MAX_PARALLEL = 4
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3


def extract_notes(slides_md: Path) -> list[str]:
    """Return ordered list of note text from each slide's <!-- ... --> block."""
    text = slides_md.read_text(encoding="utf-8")
    notes = re.findall(r"<!--\n(.*?)\n-->", text, flags=re.DOTALL)
    return [n.strip() for n in notes]


def synth_one(idx: int, text: str) -> tuple[int, str]:
    """Synthesize one note. Returns (idx, status_message)."""
    label = f"{idx:02d}"
    out = AUDIO_DIR / f"{label}.mp3"
    if out.exists() and out.stat().st_size > 0:
        return idx, f"skip (already exists, {out.stat().st_size/1024:.0f} KB)"

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            synth = SpeechSynthesizer(
                model=TARGET_MODEL,
                voice=VOICE_ID,
                format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
                speech_rate=SPEECH_RATE,
            )
            audio = synth.call(text)
            if not audio:
                raise RuntimeError("empty audio response")
            out.write_bytes(audio)
            return idx, f"ok ({len(audio)/1024:.0f} KB)"
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
    return idx, f"FAILED after {MAX_RETRIES} attempts: {last_err}"


def main() -> None:
    notes = extract_notes(ROOT / "slides.md")
    print(f"[setup] {len(notes)} notes extracted, voice_id={VOICE_ID}, rate={SPEECH_RATE}")

    # Persist each note to notes/NN.txt for record-keeping / future regen
    for i, n in enumerate(notes, start=1):
        (NOTES_DIR / f"{i:02d}.txt").write_text(n + "\n", encoding="utf-8")
    print(f"[setup] notes written to {NOTES_DIR}")

    start = time.time()
    results: list[tuple[int, str]] = []
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = {
            pool.submit(synth_one, i, n): i for i, n in enumerate(notes, start=1)
        }
        done = 0
        for fut in as_completed(futures):
            idx, msg = fut.result()
            done += 1
            print(f"[{done:02d}/{len(notes)}] slide {idx:02d}: {msg}")
            results.append((idx, msg))

    elapsed = time.time() - start
    failures = [r for r in results if "FAILED" in r[1]]
    print(f"\n[done] {len(notes)} jobs in {elapsed:.1f}s; failures: {len(failures)}")
    if failures:
        for idx, msg in sorted(failures):
            print(f"  - slide {idx:02d}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
