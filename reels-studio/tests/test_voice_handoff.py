"""The voice handoff must give the render job exactly the audio the voice job checked."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import voice_handoff as vh  # noqa: E402


class Npf:  # stands in for a numpy scalar (has .item())
    def __init__(self, v):
        self.v = v

    def item(self):
        return self.v


def _wav(tmp_path, data=b"RIFFfake-audio"):
    p = tmp_path / "src.wav"
    p.write_bytes(data)
    return p


def test_round_trip_preserves_timing_order_duration_engine(tmp_path):
    timing = {"hook": {"start": 0.0, "end": 1.5, "words": [{"w": "hi", "t": 0.1}], "caption": True},
              "point1": {"start": 1.5, "end": 4.0, "words": [], "lang": "en-us"}}
    vh.write_handoff(tmp_path / "h", _wav(tmp_path), timing=timing, order=["hook", "point1"],
                     duration=4.25, engine="chatterbox")
    got = vh.read_handoff(tmp_path / "h")
    assert got["timing"] == json.loads(json.dumps(timing))
    assert got["order"] == ["hook", "point1"] and got["duration"] == 4.25 and got["engine"] == "chatterbox"
    assert got["wav"].read_bytes() == b"RIFFfake-audio"


def test_handoff_carries_the_option_3_audit_string_for_the_queue_gate(tmp_path):
    """A render that reuses the handoff must still record WHICH approved voice produced the audio.

    Regression (7 Nov 2026): repo-poki-01 rendered through the voice->render split recorded only
    "chatterbox", so tools/post/common.check_manifest refused to queue an approved-voice render."""
    detail = "chatterbox exag0.7 cfg0.4 ref michael-ref.wav, flow (7 chunks, worst match 99%)"
    vh.write_handoff(tmp_path / "h", _wav(tmp_path), timing={"a": {"words": []}}, order=["a"],
                     duration=1.0, engine="chatterbox", engine_detail=detail)
    got = vh.read_handoff(tmp_path / "h")
    assert got["engine"] == "chatterbox" and got["engine_detail"] == detail
    text = json.dumps({"engine": got["engine_detail"]}).lower()  # what the stage writes into manifest.json
    assert all(t in text for t in ("chatterbox", "exag0.7", "cfg0.4", "michael-ref.wav", "flow"))


def test_numpy_like_scalars_become_plain_numbers(tmp_path):
    vh.write_handoff(tmp_path / "h", _wav(tmp_path), timing={"a": {"start": Npf(1.25)}},
                     order=["a"], duration=2.0, engine="kokoro")
    assert vh.read_handoff(tmp_path / "h")["timing"]["a"]["start"] == 1.25


def test_unknown_types_are_refused_not_stringified(tmp_path):
    with pytest.raises(TypeError):
        vh.write_handoff(tmp_path / "h", _wav(tmp_path), timing={"a": {"x": object()}},
                         order=["a"], duration=1.0, engine="kokoro")


def test_changed_audio_is_refused(tmp_path):
    vh.write_handoff(tmp_path / "h", _wav(tmp_path), timing={}, order=[], duration=1.0, engine="kokoro")
    (tmp_path / "h" / "vo.wav").write_bytes(b"re-synthesized")
    with pytest.raises(ValueError, match="audio changed"):
        vh.read_handoff(tmp_path / "h")


def test_missing_files_are_refused(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        vh.read_handoff(tmp_path / "nothing")


def test_wrong_schema_is_refused(tmp_path):
    vh.write_handoff(tmp_path / "h", _wav(tmp_path), timing={}, order=[], duration=1.0, engine="kokoro")
    m = json.loads((tmp_path / "h" / "voice.json").read_text())
    m["schema"] = 99
    (tmp_path / "h" / "voice.json").write_text(json.dumps(m))
    with pytest.raises(ValueError, match="schema"):
        vh.read_handoff(tmp_path / "h")
