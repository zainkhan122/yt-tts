"""Evidence-limited first-party analytics adjustment for topic selection.

Only actual 24–48-hour YouTube snapshots available by the decision time are used.
Curated comparisons are directional proxies, not measured performance for candidates.
"""
import datetime as dt
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = ROOT / 'tracker/analytics.json'
# Human-reviewed examples. A new topic is not treated as having its own performance.
ANCHORS = {
    'agent_workflow': ['repo-coop-anything-01', 'news-gemini-agent-01', 'repo-whatsapp-mcp-01'],
    'creative_media': ['tool-higgsfield-01', 'tool-mosa-01', 'tool-pomelli-01'],
}
KEYWORDS = {
    'agent_workflow': ('agent', 'worktrunk', 'gstack', 'career-ops', 'computer use', 'parallel coding', 'automation'),
    'creative_media': ('video', 'image', 'voice', 'audio', 'vibevoice', 'scenario-labs', 'moneyprinter'),
}


def timestamp(value):
    try:
        v=dt.datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return v if v.tzinfo else v.replace(tzinfo=dt.timezone.utc)
    except (ValueError, TypeError): return None


def cohort(data, now, max_age_days=45):
    """One observation per video, choose snapshot nearest 36h; reject future/stale data."""
    rows=[]
    for vid, info in data.get('videos', {}).items():
        valid=[]
        for snap in info.get('snapshots', []):
            taken=timestamp(snap.get('taken_at')); age=snap.get('age_hours'); views=snap.get('views')
            if (taken is None or taken > now or now-taken > dt.timedelta(days=max_age_days)
                or isinstance(age, bool) or not isinstance(age, (int,float)) or not 24 <= age <= 48
                or isinstance(views, bool) or not isinstance(views, (int,float)) or views < 0): continue
            valid.append(snap)
        if valid:
            chosen=min(valid,key=lambda s:(abs(s['age_hours']-36),s['taken_at']))
            rows.append({'video_id':vid,'views':chosen['views'],'age_hours':chosen['age_hours'],'taken_at':chosen['taken_at']})
    return rows


def signal(candidate, rows):
    text=' '.join([candidate.get('name',''),candidate.get('description','')] + [p.get('title','') for p in candidate.get('posts',[])] + candidate.get('titles',[])).lower()
    tags=candidate.get('analytics_tags')
    if tags is None:
        tags=[tag for tag, words in KEYWORDS.items() if any(w in text for w in words)]
    baseline=statistics.median([r['views'] for r in rows]) if len(rows)>=5 else None
    result={'status':'insufficient evidence','adjustment':0.0,'baseline_n':len(rows),'baseline_median':baseline,'tags':tags,'comparisons':[]}
    if baseline is None or baseline <= 0: return result
    for tag in tags:
        selected=[r for r in rows if r['video_id'] in ANCHORS.get(tag, [])]
        if len(selected)<2: continue
        median=statistics.median(r['views'] for r in selected)
        bonus=max(-1.5,min(1.5, math.log2((median+1)/(baseline+1))))
        result['comparisons'].append({'tag':tag,'n':len(selected),'median_views':median,'videos':selected,'adjustment':round(bonus,3)})
    if result['comparisons']:
        result['adjustment']=round(statistics.mean(c['adjustment'] for c in result['comparisons']),3)
        result['status']='directional, small sample'
    return result


def load_rows(now, path=ANALYTICS):
    try:
        return cohort(json.loads(Path(path).read_text()), now)
    except (OSError, ValueError, TypeError):
        return []


def score_candidate(candidate, rows, discovery_score):
    evidence=signal(candidate,rows)
    return {'discovery_score':round(discovery_score,3), 'analytics':evidence,
            'total_score':round(discovery_score+evidence['adjustment'],3)}
