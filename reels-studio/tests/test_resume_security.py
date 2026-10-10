"""Resume/state helpers do not reveal secrets or invoke providers."""
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib import secrets
from tools.maintenance.resume_status import snapshot,markdown


class ResumeSecurityTests(unittest.TestCase):
 def test_restored_credential_modes_are_restricted_again(self):
  with tempfile.TemporaryDirectory() as tmp:
   home=Path(tmp);vault=home/'.config/reels-studio';vault.mkdir(parents=True);vault.chmod(0o755)
   p=vault/'credential';p.write_text('not-a-real-credential');p.chmod(0o644)
   with patch.object(Path,'home',return_value=home):secrets.secure_vault()
   self.assertEqual(stat.S_IMODE(vault.stat().st_mode),0o700)
   self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600)

 def test_symlink_vault_cannot_redirect_secret_reads(self):
  with tempfile.TemporaryDirectory() as tmp:
   home=Path(tmp);(home/'.config').mkdir();outside=home/'other';outside.mkdir();(home/'.config/reels-studio').symlink_to(outside,target_is_directory=True)
   with patch.object(Path,'home',return_value=home):
    with self.assertRaises(RuntimeError):secrets.secure_vault()

 def test_resume_snapshot_reports_presence_not_values(self):
  info=snapshot();encoded=json.dumps(info)
  self.assertIn('local_credentials_present',info)
  self.assertIn('optional_agent',info)
  self.assertNotIn('refresh_token',encoded)
  self.assertNotIn('client_secret',encoded)
  self.assertIn('OPTIONAL producer/critic',markdown(info))


if __name__=='__main__':unittest.main()
