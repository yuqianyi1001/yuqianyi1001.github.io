"""Test 「了 liǎo」 SSML variants — figure out which one actually works."""
import os, sys
from pathlib import Path

env_file = Path.home() / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat

dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY")
ROOT = Path(__file__).resolve().parent.parent
VOICE_ID = (ROOT / ".bailian_voice_id").read_text().strip()

OUT = ROOT / "liao-test"
OUT.mkdir(exist_ok=True)

CASES = [
    # variant 1: full sentence with phoneme wrap (current production format)
    ("v1-full-spaced", '<speak>体性 是 <phoneme alphabet="py" ph="liao3">了</phoneme>别 境界——眼识 <phoneme alphabet="py" ph="liao3">了</phoneme> 色，耳识 <phoneme alphabet="py" ph="liao3">了</phoneme> 声。</speak>'),
    # variant 2: short minimal
    ("v2-minimal", '<speak>眼识 <phoneme alphabet="py" ph="liao3">了</phoneme> 色。</speak>'),
    # variant 3: no spaces inside
    ("v3-nospace", '<speak>眼识<phoneme alphabet="py" ph="liao3">了</phoneme>色。</speak>'),
    # variant 4: try alphabet="pinyin"
    ("v4-pinyin", '<speak>眼识 <phoneme alphabet="pinyin" ph="liao3">了</phoneme> 色。</speak>'),
    # variant 5: 瞭 instead (traditional liǎo char)
    ("v5-traditional", '<speak>眼识 瞭 色。耳识 瞭 声。</speak>'),
    # variant 6: 「了」单独成行
    ("v6-isolated", '<phoneme alphabet="py" ph="liao3">了</phoneme>。<phoneme alphabet="py" ph="liao3">了</phoneme>。<phoneme alphabet="py" ph="liao3">了</phoneme>。'),
    # variant 7: 用 sub alias - 别字替代
    ("v7-sub", '<speak>眼识 <sub alias="瞭解的瞭">了</sub> 色。</speak>'),
    # variant 8: plain "了别" only (should work — already confirmed in prev tests?)
    ("v8-liaobie", '<speak><phoneme alphabet="py" ph="liao3">了</phoneme>别。</speak>'),
    # variant 9: 「能了」without space
    ("v9-able", '<speak>眼识能<phoneme alphabet="py" ph="liao3">了</phoneme>色。</speak>'),
    # variant 10: control - what does it sound like with NO ssml?
    ("v10-control", "眼识 了 色。耳识 了 声。"),
]

for label, text in CASES:
    out = OUT / f"{label}.mp3"
    print(f"\n[{label}]")
    print(f"  text: {text}")
    try:
        synth = SpeechSynthesizer(model="cosyvoice-v2", voice=VOICE_ID,
                                   format=AudioFormat.MP3_22050HZ_MONO_256KBPS, speech_rate=1.0)
        audio = synth.call(text)
        if audio:
            out.write_bytes(audio)
            print(f"  ✓ {len(audio)/1024:.0f} KB")
        else:
            print(f"  ✗ empty")
    except Exception as e:
        print(f"  ✗ {e}")

print(f"\n试听 {OUT}/ 里的 mp3，告诉我哪个「了」读对 liǎo")
