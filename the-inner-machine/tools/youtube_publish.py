#!/usr/bin/env python3
"""Approval-gated YouTube publisher.

Usage:
  python3 youtube_publish.py package/approval.json --dry-run
  python3 youtube_publish.py package/approval.json --upload

OAuth credentials are read from YOUTUBE_OAUTH_CLIENT_SECRETS and token cache from
YOUTUBE_TOKEN_FILE. No Google password or token belongs in the repository.
"""
import argparse,json,os,sys
from pathlib import Path

REQUIRED=('title','description','video','thumbnail','channel_id')
def fail(msg): raise SystemExit('BLOCKED: '+msg)
def load(p):
 try:return json.loads(Path(p).read_text())
 except Exception as e: fail(f'cannot read approval manifest: {e}')
def validate(a):
 for k in REQUIRED:
  if not a.get(k): fail(f'missing {k}')
 if a.get('approved') is not True: fail('explicit approval is required: set approved=true only after review')
 if a.get('visibility','private') not in ('private','unlisted','public'): fail('visibility must be private, unlisted or public')
 for k in ('video','thumbnail'):
  if not Path(a[k]).exists(): fail(f'missing {k}: {a[k]}')
 channels=Path(a.get('channels_file','youtube_channels.json')).expanduser()
 if not channels.exists(): fail(f'channel profile file missing: {channels}')
 profiles=json.loads(channels.read_text()); ids={x['channel_id'] for x in profiles.get('channels',[])}
 if a['channel_id'] not in ids: fail('channel_id is not in the approved channel profile list')
 return profiles

def main():
 p=argparse.ArgumentParser();p.add_argument('approval');p.add_argument('--dry-run',action='store_true');p.add_argument('--upload',action='store_true');a=p.parse_args();m=load(a.approval);profiles=validate(m)
 ch=next(x for x in profiles['channels'] if x['channel_id']==m['channel_id']);print(json.dumps({'status':'approved','channel':ch,'title':m['title'],'visibility':m.get('visibility','private'),'video':m['video'],'thumbnail':m['thumbnail']},indent=2))
 if a.dry_run or not a.upload:return
 if not os.environ.get('YOUTUBE_OAUTH_CLIENT_SECRETS'): fail('set YOUTUBE_OAUTH_CLIENT_SECRETS; never put OAuth secrets in the repo')
 try:
  from google_auth_oauthlib.flow import InstalledAppFlow
  from googleapiclient.discovery import build
  from googleapiclient.http import MediaFileUpload
 except ImportError: fail('install google-api-python-client google-auth-oauthlib google-auth-httplib2')
 scopes=['https://www.googleapis.com/auth/youtube.upload']
 token_file=Path(os.environ.get('YOUTUBE_TOKEN_FILE',Path.home()/'.config/the-inner-machine/youtube-token.json')); creds=None
 if token_file.exists():
  from google.oauth2.credentials import Credentials;creds=Credentials.from_authorized_user_file(str(token_file),scopes)
 if not creds or not creds.valid:
  flow=InstalledAppFlow.from_client_secrets_file(os.environ['YOUTUBE_OAUTH_CLIENT_SECRETS'],scopes);creds=flow.run_local_server(port=0);token_file.parent.mkdir(parents=True,exist_ok=True);token_file.write_text(creds.to_json());os.chmod(token_file,0o600)
 yt=build('youtube','v3',credentials=creds)
 body={'snippet':{'title':m['title'],'description':m['description'],'tags':m.get('tags',[]),'categoryId':m.get('category_id','27')},'status':{'privacyStatus':m.get('visibility','private'),'selfDeclaredMadeForKids':False}}
 r=yt.videos().insert(part='snippet,status',body=body,media_body=MediaFileUpload(m['video'],chunksize=-1,resumable=True)).execute();vid=r['id'];yt.thumbnails().set(videoId=vid,media_body=MediaFileUpload(m['thumbnail'])).execute();print(json.dumps({'status':'uploaded','video_id':vid,'url':f'https://youtu.be/{vid}','channel_id':m['channel_id'],'privacy':m.get('visibility','private')},indent=2))
if __name__=='__main__':main()
