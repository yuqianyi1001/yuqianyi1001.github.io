"""
Clone a voice on Aliyun 百炼 (DashScope) using the user's reference WAV,
then synthesize 3 test segments (P1 / P9 / P35) from baifa slides notes.

Flow:
  1) Upload ref.wav to DashScope OSS, get a public URL
  2) Create a cloned voice via VoiceEnrollmentService -> voice_id (persisted to .voice_id)
  3) Use SpeechSynthesizer(model=cosyvoice-v2, voice=voice_id) to TTS each text file
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Load .env first so DASHSCOPE_API_KEY is available
env_file = Path.home() / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

import dashscope  # noqa: E402
from dashscope.audio.tts_v2 import (  # noqa: E402
    SpeechSynthesizer,
    VoiceEnrollmentService,
    AudioFormat,
)
from dashscope.utils.oss_utils import OssUtils  # noqa: E402

API_KEY = os.environ.get("DASHSCOPE_API_KEY")
if not API_KEY:
    sys.exit("ERROR: DASHSCOPE_API_KEY not found in environment / ~/.env")

dashscope.api_key = API_KEY

ROOT = Path(__file__).resolve().parent.parent
REF_WAV = Path.home() / "tools/GPT-SoVITS/voices/yuqianyi/ref.wav"
VOICE_ID_FILE = ROOT / ".bailian_voice_id"
TARGET_MODEL = "cosyvoice-v2"

OUT_DIR = ROOT / "audio-test"
OUT_DIR.mkdir(exist_ok=True)

TEXTS = {
    "p1-bailian": ROOT / "audio-test/p1.txt",
    "p9-bailian": ROOT / "audio-test/p9.txt",
    "p35-bailian": ROOT / "audio-test/p35.txt",
}


def get_or_create_voice() -> str:
    if VOICE_ID_FILE.exists():
        vid = VOICE_ID_FILE.read_text().strip()
        if vid:
            print(f"[voice] reuse existing voice_id from {VOICE_ID_FILE}: {vid}")
            return vid

    if not REF_WAV.exists():
        sys.exit(f"ERROR: reference wav not found at {REF_WAV}")

    # The reference mp3 is committed to the public GitHub Pages repo at a
    # location Jekyll ignores (_unfinished_posts/). Aliyun servers can reach
    # raw.githubusercontent.com from inside China.
    file_url = (
        "https://raw.githubusercontent.com/yuqianyi1001/yuqianyi1001.github.io"
        "/master/_unfinished_posts/baifa-slidev/.voice-ref/yuqianyi.mp3"
    )
    print(f"[ref] using public url: {file_url}")

    print(f"[enroll] creating cloned voice (prefix=yuqianyi, target={TARGET_MODEL}) ...")
    service = VoiceEnrollmentService(api_key=API_KEY)
    voice_id = service.create_voice(
        target_model=TARGET_MODEL,
        prefix="yuqianyi",
        url=file_url,
    )
    print(f"[enroll] voice_id = {voice_id}")

    VOICE_ID_FILE.write_text(voice_id)
    print(f"[enroll] saved voice_id to {VOICE_ID_FILE}")
    return voice_id


def synth(voice_id: str, label: str, text_file: Path) -> None:
    text = text_file.read_text(encoding="utf-8").strip()
    out = OUT_DIR / f"{label}.mp3"
    print(f"[tts] {label}: {len(text)} chars -> {out.name}")
    synthesizer = SpeechSynthesizer(
        model=TARGET_MODEL,
        voice=voice_id,
        format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
        speech_rate=0.9,  # slightly slower for sutra commentary feel
    )
    audio = synthesizer.call(text)
    if not audio:
        print(f"[tts] FAILED for {label}: empty response")
        return
    out.write_bytes(audio)
    print(f"[tts] {label}: wrote {out} ({len(audio)/1024:.1f} KB)")


def main() -> None:
    voice_id = get_or_create_voice()
    for label, text_file in TEXTS.items():
        if not text_file.exists():
            print(f"[skip] {text_file} missing")
            continue
        synth(voice_id, label, text_file)
    print("[done] all synth jobs finished")


if __name__ == "__main__":
    main()
