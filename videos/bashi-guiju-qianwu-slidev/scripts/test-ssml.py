"""Test cosyvoice-v2 SSML pronunciation control with multi-tone Chinese chars."""
import os
import sys
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

dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY")
ROOT = Path(__file__).resolve().parent.parent
VOICE_ID = (ROOT / ".bailian_voice_id").read_text().strip()

# Test multiple SSML formats to find what cosyvoice-v2 supports
TEST_CASES = [
    # Format 1: <speak> wrapper + <phoneme alphabet="py">
    ("ssml-py", '<speak>加<phoneme alphabet="py" ph="xing2">行</phoneme>是 jiā xíng。圣者要<phoneme alphabet="py" ph="zhuan3">转</phoneme>依。<phoneme alphabet="py" ph="xiang4">相</phoneme>分的相，读 xiàng 四声。</speak>'),
    # Format 2: No <speak>, only <phoneme>
    ("phoneme-only", '加<phoneme alphabet="py" ph="xing2">行</phoneme>。圣者要<phoneme alphabet="py" ph="zhuan3">转</phoneme>依。<phoneme alphabet="py" ph="xiang4">相</phoneme>分。'),
    # Format 3: x-aliyun-py alphabet
    ("ssml-aliyun", '<speak>加<phoneme alphabet="x-aliyun-py" ph="xing2">行</phoneme>。圣者要<phoneme alphabet="x-aliyun-py" ph="zhuan3">转</phoneme>依。</speak>'),
    # Format 4: ph without alphabet
    ("phoneme-noalphabet", '<speak>加<phoneme ph="xing2">行</phoneme>。圣者要<phoneme ph="zhuan3">转</phoneme>依。</speak>'),
    # Format 5: ph with diacritic
    ("phoneme-diacritic", '<speak>加<phoneme alphabet="py" ph="xíng">行</phoneme>。圣者要<phoneme alphabet="py" ph="zhuǎn">转</phoneme>依。</speak>'),
    # Format 6: plain (control)
    ("plain", "加行。圣者要转依。相分。"),
]

OUT_DIR = ROOT / "ssml-test"
OUT_DIR.mkdir(exist_ok=True)

for label, text in TEST_CASES:
    out = OUT_DIR / f"{label}.mp3"
    print(f"\n[{label}] testing...")
    print(f"  text: {text[:100]}...")
    try:
        synth = SpeechSynthesizer(
            model="cosyvoice-v2",
            voice=VOICE_ID,
            format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
            speech_rate=1.0,
        )
        audio = synth.call(text)
        if audio:
            out.write_bytes(audio)
            print(f"  ✓ {len(audio)/1024:.0f} KB → {out.name}")
        else:
            print(f"  ✗ empty audio response (format not supported)")
    except Exception as e:
        print(f"  ✗ exception: {e}")

print(f"\n所有测试结果在 {OUT_DIR}/")
print("请听各个 mp3 — 听到「加形」「转依」「象分」(正确读音) 的格式 = 成功")
