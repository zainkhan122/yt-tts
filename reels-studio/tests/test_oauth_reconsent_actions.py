import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nacl.secret import SecretBox
from tools.youtube import oauth_reconsent_actions as flow

class ReconsentActionsTests(unittest.TestCase):
    def test_start_encrypts_pending_and_finish_uses_verified_response(self):
        key = base64.urlsafe_b64encode(bytes(range(SecretBox.KEY_SIZE))).decode()
        pending = {'client': {'client_id': 'client', 'client_secret': 'very-secret-client'},
                   'verifier': 'verifier-secret', 'state': 'state', 'signing': 'signing', 'expires': 9999999999}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'YOUTUBE_STATE_KEY': key}, clear=False):
            with patch.object(flow, 'youtube_credentials', return_value=pending['client']), patch.object(flow, 'make_flow', return_value=(pending, 'https://example.test/consent')):
                with patch('sys.argv', ['reconsent', 'start', tmp]): flow.main()
            blob = (Path(tmp)/'pending.enc').read_bytes()
            self.assertNotIn(b'very-secret-client', blob)
            self.assertEqual(json.loads(SecretBox(base64.urlsafe_b64decode(key)).decrypt(blob)), pending)
            response = base64.b64encode(json.dumps({'code':'test-code','state':'state'}).encode()).decode()
            with patch.dict(os.environ, {'YOUTUBE_OAUTH_RESPONSE_B64':response}), patch.object(flow, 'validate_response', return_value=('test-code','state')) as validate, patch.object(flow, 'complete', return_value={'secret_stored': True}) as complete:
                with patch('sys.argv', ['reconsent', 'finish', tmp]): flow.main()
                validate.assert_called_once();complete.assert_called_once_with(pending, 'test-code', 'state')

if __name__ == '__main__': unittest.main()
