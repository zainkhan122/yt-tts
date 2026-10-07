#!/usr/bin/env python3
"""
Machine intelligibility check for a TTS voice: Kokoro speaks the text -> whisper.cpp transcribes it ->
character-level match between what was meant and what was heard. Use it before trusting a voice
for a new language. It is a proxy, not a replacement for a native listener.

  python3 tools/tts_roundtrip.py --voice hf_alpha --lang hi --wlang hi --text "आज हम अंग्रेज़ी सीखेंगे।"
  python3 tools/tts_roundtrip.py --suite      # English control + Hindi + Urdu-script test
"""
import argparse
import difflib
import pathlib
import re
import subprocess
import unicodedata

import soundfile as sf

HOME = pathlib.Path.home()
MODEL = HOME / ".cache/hyperframes/tts/models/kokoro-v1.0.onnx"
VOICES = HOME / ".cache/hyperframes/tts/voices/voices-v1.0.bin"
WHISPER = HOME / ".cache/hyperframes/whisper/whisper.cpp/build/bin/whisper-cli"
WMODEL = HOME / ".cache/hyperframes/whisper/models/ggml-base.bin"  # multilingual

SUITE = [
    ("English control", "af_heart", "en-us", "en",
     "Today we will learn how to ask a question in English. Follow for a new tip every day."),
    ("Hindi (Devanagari)", "hf_alpha", "hi", "hi",
     "आज हम सीखेंगे कि अंग्रेज़ी में सवाल कैसे पूछते हैं। रोज़ नई टिप के लिए फ़ॉलो कीजिए।"),
    ("Hindi male voice", "hm_omega", "hi", "hi",
     "आज हम सीखेंगे कि अंग्रेज़ी में सवाल कैसे पूछते हैं। रोज़ नई टिप के लिए फ़ॉलो कीजिए।"),
    ("Urdu script via espeak 'ur'", "hf_alpha", "ur", "ur",
     "آج ہم سیکھیں گے کہ انگریزی میں سوال کیسے پوچھتے ہیں۔ روز نئی ٹپ کے لیے فالو کریں۔"),
]


def norm(s):
    s = unicodedata.normalize("NFC", s.lower())
    s = s.replace("\u093c", "")  # nukta: ज़ vs ज are both acceptable spellings
    return re.sub(r"[\W_]+", "", s)


def roundtrip(label, voice, lang, wlang, text, k):
    try:
        samples, sr = k.create(text, voice=voice, speed=1.0, lang=lang)
    except Exception as e:  # e.g. phonemizer has no such language
        return label, voice, lang, None, f"TTS failed: {str(e)[:80]}"
    wav = pathlib.Path("/tmp") / f"rt-{voice}-{lang}.wav"
    sf.write(wav, samples, sr)
    p = subprocess.run([str(WHISPER), "-m", str(WMODEL), "-l", wlang, "-nt", "-np", "-f", str(wav)],
                       capture_output=True, text=True)
    heard = " ".join(p.stdout.split())
    a, b = norm(text), norm(heard)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    score = sum(x.size for x in sm.get_matching_blocks()) / max(1, len(a))
    return label, voice, lang, score, heard


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", action="store_true")
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--lang", default="en-us")
    ap.add_argument("--wlang", default="en")
    ap.add_argument("--text", default="Hello world.")
    a = ap.parse_args()
    from kokoro_onnx import Kokoro
    k = Kokoro(str(MODEL), str(VOICES))
    jobs = SUITE if a.suite else [("custom", a.voice, a.lang, a.wlang, a.text)]
    print("| Test | Voice | Phonemizer | Whisper (base) heard | Char match |\n|---|---|---|---|---|")
    for label, voice, lang, wlang, text in jobs:
        label, voice, lang, score, heard = roundtrip(label, voice, lang, wlang, text, k)
        pct = f"{100 * score:.0f}%" if score is not None else "n/a"
        print(f"| {label} | `{voice}` | `{lang}` | {heard[:90]} | **{pct}** |")


if __name__ == "__main__":
    main()
