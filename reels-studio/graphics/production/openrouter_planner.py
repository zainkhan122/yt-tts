"""Adapter for the existing OpenRouter pilot client; obeys all its owner gates."""
import json
from tools.agent.openrouter_client import json_content
from .semantic import TREATMENTS

SYSTEM='''You are a visual director. Return a single JSON object only, with key beats.
Choose a sequence of visually meaningful beats covering every indexed narration word in order.
Each beat has id, word_start and word_end (zero-based, end exclusive), meaning, visual_objective,
treatment, scene_description, subject, objects (array of strings), composition, camera, transition,
assets (array), events (array). Each asset has id, kind, description, reuse_of (null or prior asset id).
Each event has id, trigger_phrase (exact contiguous spoken words within that beat), occurrence
(1-based occurrence within beat), action, target, animation_type, duration (positive seconds),
camera, asset_id (a beat asset), transition. Use multiple events where appropriate. Pick physically
meaningful motion rather than decorative zoom. Keep event durations short enough to fit speech.
Do not invent facts or claim rendered outputs. Recommend real visual assets and reuse for continuity.
Treatment must be one of: '''+', '.join(sorted(TREATMENTS))

class OpenRouterSemanticPlanner:
    def __init__(self,client,role): self.client=client;self.role=role
    def plan(self,*,transcript,words):
        payload={'transcript':transcript,'indexed_words':[{'index':i,'word':w} for i,w in enumerate(words)]}
        message=self.client.chat(self.role,[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}],label='semantic-visual-plan')
        return json_content(message)
