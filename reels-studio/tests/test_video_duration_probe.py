"""FFprobe can append side-data commas to CSV; both audio guards need a clean duration."""
import json
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from lib.pipeline import video_duration_seconds


def test_probe_uses_json_and_returns_numeric_duration():
    with patch('lib.pipeline.subprocess.run', return_value=SimpleNamespace(stdout=json.dumps({'streams':[{'duration':'44.133333','side_data_list':[{}]}]}))) as run:
        assert video_duration_seconds('video.mp4') == '44.133333'
        assert 'json' in run.call_args.args[0]

@pytest.mark.parametrize('data', ['{}', '{"streams":[]}', '{"streams":[{"duration":"N/A"}]}', '{"streams":[{"duration":"nan"}]}', 'not json'])
def test_bad_duration_fails_closed(data):
    with patch('lib.pipeline.subprocess.run', return_value=SimpleNamespace(stdout=data)):
        with pytest.raises(ValueError):
            video_duration_seconds('video.mp4')
