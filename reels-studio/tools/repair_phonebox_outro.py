#!/usr/bin/env python3
"""Replace only the PhoneBox CTA using a fresh, independently transcribed house voice."""
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];d=ROOT/'renders/phonebox-outro-fix';tim=d/'voice-handoff/timings.json';j=json.loads(tim.read_text())
heard=[str(w).lower() for c in j.get('chunks',[]) for w in c.get('heard_words',[])]
if not any(heard[i]=='comment' and heard[i+1]=='phone' for i in range(len(heard)-1)):
 raise SystemExit('Independent speech recognition did not hear the consecutive words COMMENT PHONE: '+repr(heard))
print('Independent recognizer heard COMMENT PHONE; human listening is still required.',flush=True)
subprocess.run(['python3',str(ROOT/'tools/append_house_outro.py'),'--input',str(ROOT/'renders/repo-phonebox-01/phonebox-review.mp4'),'--output',str(d/'phonebox-corrected.mp4'),'--voice',str(d/'voice-handoff/voice.wav'),'--timings',str(tim),'--keyword','PHONE','--body-seconds','19.545'],cwd=ROOT,check=True)
