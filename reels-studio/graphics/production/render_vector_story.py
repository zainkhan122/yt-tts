"""Render a director-supplied vector story using actual strict narration alignment.

Example: python -m graphics.production.render_vector_story --directory path
The directory needs narration.json (list of spoken scenes), direction.json, and
voice.wav. The direction is external input: this CLI does not infer it.
"""
import argparse,json
from pathlib import Path
from .alignment import run_alignment,FasterWhisperBackend,require_verified
from .vector_motion import compile_story,render

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--directory',required=True);ap.add_argument('--model',default='small.en');ap.add_argument('--audio',default='voice.wav');args=ap.parse_args()
    root=Path(args.directory).resolve();audio=root/args.audio;lines=json.loads((root/'narration.json').read_text());story=json.loads((root/'direction.json').read_text())
    if not isinstance(lines,list) or not all(isinstance(v,str) and v.strip() for v in lines):raise ValueError('Narration lines required')
    transcript=' '.join(lines);print('Running strict alignment...',flush=True)
    alignment=run_alignment(audio,transcript,FasterWhisperBackend(args.model));report=require_verified(alignment,audio,transcript)
    report,scheduled,compiled=compile_story(story,audio,transcript,alignment)
    (root/'alignment-executed.json').write_text(json.dumps(report,indent=2));(root/'scheduled.json').write_text(json.dumps(scheduled,indent=2));(root/'compiled-scenes.json').write_text(json.dumps(compiled,indent=2))
    print('Strict alignment and scheduler passed; rendering review only.',flush=True)
    result=render(compiled,audio,report['audio_duration'],root/'animation-review.mp4',words=report['words'],cover=(root/'cover.jpg') if (root/'cover.jpg').exists() else None)
    result['review_status']='human_review_required';print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
