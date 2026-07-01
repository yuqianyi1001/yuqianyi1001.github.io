"""
Synthesize all 26 slide notes from slides.md into audio/NN.mp3 files,
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
    """Return ordered list of note text.

    Prefer reading from notes/NN.txt files (one per slide, hand-written).
    Fall back to extracting from slides.md's <!-- ... --> blocks if notes/ is empty.
    """
    txt_files = sorted(NOTES_DIR.glob("*.txt"))
    if txt_files:
        return [p.read_text(encoding="utf-8").strip() for p in txt_files]
    text = slides_md.read_text(encoding="utf-8")
    notes = re.findall(r"<!--\n(.*?)\n-->", text, flags=re.DOTALL)
    return [n.strip() for n in notes]


# TTS pronunciation fixes — use cosyvoice-v2 SSML <phoneme> tags for
# multi-tone Chinese chars. Confirmed working format:
#   <phoneme alphabet="py" ph="xing2">行</phoneme>
# - alphabet="py" required (x-aliyun-py / no alphabet → 411/413 errors)
# - ph must use pinyin letters + tone number 1-5 (no diacritics)
# Source notes/*.txt keep original chars; only TTS text gets SSML.
# Subtitles read from notes — always show original chars.
def _ph(char: str, py: str) -> str:
    return f'<phoneme alphabet="py" ph="{py}">{char}</phoneme>'

PRONUNCIATION_FIXES = [
    # 「行」xíng — TTS defaults to héng. Order: longest first.
    ("十六行相", "十六" + _ph("行", "xing2") + _ph("相", "xiang4")),
    ("加行", "加" + _ph("行", "xing2")),
    ("行舍", _ph("行", "xing2") + "舍"),
    ("行相", _ph("行", "xing2") + _ph("相", "xiang4")),
    ("行蕴", _ph("行", "xing2") + "蕴"),
    ("梵行", "梵" + _ph("行", "xing2")),
    # 「了」liǎo — TTS defaults to le (sentence particle)
    ("了别", _ph("了", "liao3") + "别"),
    # notes 用「眼识能了色」格式（v9 实测最自然）— 加「能」做上下文 + 无空格紧贴
    ("眼识能了色", "眼识能" + _ph("了", "liao3") + "色"),
    ("耳识能了声", "耳识能" + _ph("了", "liao3") + "声"),
    ("鼻识能了香", "鼻识能" + _ph("了", "liao3") + "香"),
    ("舌识能了味", "舌识能" + _ph("了", "liao3") + "味"),
    ("身识能了触", "身识能" + _ph("了", "liao3") + "触"),
    # 「转」zhuǎn 3rd tone — TTS defaults to zhuàn 4th tone in 转依
    ("转依", _ph("转", "zhuan3") + "依"),
    # 「相」xiàng 4th tone — TTS defaults to xiāng 1st tone (行相 already above)
    ("相分", _ph("相", "xiang4") + "分"),
    # 「恶」è 4th tone — TTS defaults to ě 3rd tone in 恶心
    ("恶心", _ph("恶", "e4") + "心"),
    # 「二个」èr ge — substitute to 两个 liǎng ge (no good SSML fix for char swap)
    ("二个", "两个"),
]


_HTML_NON_SSML_TAG = re.compile(r"</?(?:strong|em|b|i|u|br)(?:\s[^>]*)?\s*/?>", re.I)


def strip_html(text: str) -> str:
    """Remove HTML tags that aren't valid SSML (strong/em/b/i/u/br).
    Keep speak/phoneme/break — those are valid SSML."""
    return _HTML_NON_SSML_TAG.sub("", text)


def fix_pronunciation(text: str) -> str:
    for orig, repl in PRONUNCIATION_FIXES:
        text = text.replace(orig, repl)
    return text


SENTENCE_END = ("。", "！", "？")


def add_breaks(text: str) -> str:
    """Insert <break time="300ms"/> after sentence-ending punctuation to
    prevent cosyvoice-v2 from running consecutive sentences together
    (e.g., 「身识能了触。所缘 = ...」being read as 「触所缘」)."""
    for p in SENTENCE_END:
        text = text.replace(p, p + '<break time="300ms"/>')
    return text


def synth_one(idx: int, text: str) -> tuple[int, str]:
    """Synthesize one note. Returns (idx, status_message)."""
    label = f"{idx:02d}"
    out = AUDIO_DIR / f"{label}.mp3"
    if out.exists() and out.stat().st_size > 0:
        return idx, f"skip (already exists, {out.stat().st_size/1024:.0f} KB)"

    tts_text = strip_html(text)
    tts_text = fix_pronunciation(tts_text)
    # NOTE: do NOT call add_breaks() globally — <break> caused cosyvoice-v2
    # to read multi-char terms (凡夫位, 圣者位) as choppy single chars in P01.
    # Rely on 。 for natural sentence breaks. Restructure specific run-on
    # notes (e.g., 触/所缘) instead of universal break injection.
    # Always wrap in <speak> — phoneme tags require SSML root
    tts_text = f"<speak>{tts_text}</speak>"
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            synth = SpeechSynthesizer(
                model=TARGET_MODEL,
                voice=VOICE_ID,
                format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
                speech_rate=SPEECH_RATE,
            )
            audio = synth.call(tts_text)
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
    print(f"[setup] {len(notes)} notes loaded, voice_id={VOICE_ID}, rate={SPEECH_RATE}")

    # Persist each note to notes/NN.txt only if not present yet (idempotent)
    for i, n in enumerate(notes, start=1):
        path = NOTES_DIR / f"{i:02d}.txt"
        if not path.exists():
            path.write_text(n + "\n", encoding="utf-8")

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
