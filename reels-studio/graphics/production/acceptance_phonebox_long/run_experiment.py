"""Replay THIS INTERACTIVE agent's saved plan; no new provider inference occurs."""
import json
from pathlib import Path
from graphics.production.alignment import run_alignment,FasterWhisperBackend
from graphics.production.automated_planner import generate_and_compile
from graphics.production.layer_renderer import render
D=Path(__file__).resolve().parent

def main():
    audio=D/'voice-pace-0.97.wav';script=json.loads((D/'narration.json').read_text())[0];catalog=json.loads((D/'catalog.json').read_text());alignment=run_alignment(audio,script,FasterWhisperBackend('base.en'))
    class RecordedInteractiveAgentPlan:
        def plan_visual(self,payload):
            (D/'planner-input.json').write_text(json.dumps(payload,indent=2)+'\n')
            return json.loads((D/'arena-agent-semantic-response.json').read_text())
    result=generate_and_compile(planner=RecordedInteractiveAgentPlan(),audio=audio,transcript=script,alignment=alignment,catalog=catalog,topic='PhoneBox computer dashboard',audience='people with spare Android devices',style='faithful real UI captures, disclose illustrative animation')
    for name in ('scheduled','design','timeline'):(D/(name+'.json')).write_text(json.dumps(result[name],indent=2)+'\n')
    print(json.dumps(render(result['timeline'],audio,D/'acceptance-experiment.mp4',D/'render-cache',fps=24),indent=2))
if __name__=='__main__':main()
