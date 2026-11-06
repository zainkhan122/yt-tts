"""Approval binds the image actually previewed, not just a newly fetched kit."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from tools.youtube import cover_ctl


def test_cover_approval_refuses_changed_preview(tmp_path):
    queue = tmp_path / "publish.json"
    queue.write_text(json.dumps({"items": [{"video_id": "test-01"}]}))
    previews = tmp_path / "previews"
    previews.mkdir()
    (previews / "test-01-cover.jpg").write_bytes(b"reviewed")
    live = tmp_path / "live.jpg"
    live.write_bytes(b"different")
    with patch.object(cover_ctl, "queue_path", return_value=queue), \
         patch.object(cover_ctl, "PREVIEW_DIR", previews), \
         patch.object(cover_ctl, "config", return_value={}), \
         patch.object(cover_ctl, "fetch_kit_cover", return_value=live):
        with pytest.raises(SystemExit, match="preview differs"):
            cover_ctl.approve(["test-01"])
    assert "cover_sha256" not in json.loads(queue.read_text())["items"][0]
