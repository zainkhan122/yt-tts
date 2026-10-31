"""OAuth can finish after its sandbox was replaced. No real Google requests."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.youtube import oauth_connect as oauth
from tools.youtube.oauth_handoff import validate_response


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.pending,self.url=oauth.make_flow({'client_id':'test.apps.googleusercontent.com','client_secret':'test-secret'},now=100)
        self.response={'kind':'hypeless-youtube-oauth-response','version':1,'code':'one-time-test-code','state':self.pending['state']}

    def test_link_has_no_sandbox_dependency(self):
        from urllib.parse import parse_qs,urlparse
        q=parse_qs(urlparse(self.url).query)
        self.assertEqual(urlparse(self.url).hostname,'accounts.google.com')
        self.assertEqual(q['redirect_uri'],[oauth.CALLBACK])
        self.assertEqual(q['code_challenge_method'],['S256'])
        self.assertNotIn('e2b.app',self.url)
        self.assertNotIn('origin',self.pending)
        self.assertNotIn('test-secret',self.url)

    def test_persisted_state_works_in_a_fresh_process(self):
        restored=json.loads(json.dumps(self.pending))
        code,state=validate_response(self.response,restored,now=100+3600)
        self.assertEqual(code,'one-time-test-code')
        self.assertEqual(state,restored['state'])

    def test_expired_request_rejected(self):
        with self.assertRaises(ValueError):validate_response(self.response,self.pending,now=100+86401)

    def test_wrong_or_tampered_state_rejected(self):
        response={**self.response,'state':self.response['state']+'x'}
        with self.assertRaises(ValueError):validate_response(response,self.pending,now=200)

    def test_client_json_is_not_a_connection_response(self):
        with self.assertRaises(ValueError):validate_response({'web':{'client_id':'example'}},self.pending,now=200)

    def test_missing_code_is_not_sent_to_google(self):
        response={**self.response,'code':''}
        with self.assertRaises(ValueError):validate_response(response,self.pending,now=200)

    def test_wrong_channel_never_saves_refresh_credentials(self):
        pending,_=oauth.make_flow({'client_id':'test.apps.googleusercontent.com','client_secret':'test-secret'})
        session=Mock()
        session.post.return_value.status_code=200
        session.post.return_value.json.return_value={'access_token':'test-access','refresh_token':'test-refresh','scope':' '.join(oauth.SCOPES)}
        session.get.return_value.status_code=200
        session.get.return_value.json.return_value={'items':[{'id':'wrong-channel'}]}
        with patch.object(oauth,'secure_write') as save,patch.object(oauth,'store_github_secret') as gh:
            with self.assertRaises(ValueError):oauth.complete(pending,'short-lived-test-code',pending['state'],session=session)
            save.assert_not_called();gh.assert_not_called()

    def test_callback_has_no_network_or_sandbox_redirect(self):
        html=(ROOT/'cloud/pages/oauth-callback.html').read_text()
        self.assertNotIn('e2b.app',html)
        self.assertNotIn('location.replace(',html)
        self.assertNotIn('fetch(',html)
        self.assertIn("connect-src 'none'",html)
        self.assertIn('hypeless-youtube-connection.json',html)
        self.assertIn("history.replaceState(null,'',location.pathname)",html)

    def test_callback_browser_logic_accepts_good_and_rejects_bad_data(self):
        # Run inline browser logic in a dependency-free, isolated Node DOM harness.
        html=(ROOT/'cloud/pages/oauth-callback.html').read_text()
        script=html.split('<script>',1)[1].split('</script>',1)[0]
        harness=r'''
const vm=require('vm');const script=JSON.parse(process.argv[1]);
function run(search){
 const nodes={};const get=id=>nodes[id]||(nodes[id]={hidden:true,value:'',textContent:'',className:''});
 const historyCalls=[];
 const context={location:{search,pathname:'/yt-tts/oauth/callback/'},history:{replaceState:(...a)=>historyCalls.push(a)},URLSearchParams,atob,Date,JSON,Error,Blob,URL,setTimeout:()=>{},navigator:{},document:{getElementById:get},console};
 vm.runInNewContext(script,context);return {nodes,historyCalls};
}
const fields={handoff:'file',nonce:'unit-test-nonce-with-enough-entropy',expires:Math.floor(Date.now()/1000)+3600};
const state=Buffer.from(JSON.stringify(fields)).toString('base64url')+'.test-signature';
const good=run('?code=temporary-test-code&state='+encodeURIComponent(state));
if(good.nodes.success.hidden!==false)throw Error('Good response not offered');
const data=JSON.parse(good.nodes.response.value);
if(data.kind!=='hypeless-youtube-oauth-response'||data.code!=='temporary-test-code')throw Error('Wrong handoff');
if(good.historyCalls[0][2]!=='/yt-tts/oauth/callback/')throw Error('Sensitive query retained');
const bad=run('?code=x&state=bad');if(bad.nodes.status.className!=='error')throw Error('Bad response accepted');
const denied=run('?error=access_denied');if(denied.nodes.status.className!=='error')throw Error('Cancellation accepted');
console.log('Callback DOM logic passed');
'''
        result=subprocess.run(['node','-e',harness,json.dumps(script)],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
