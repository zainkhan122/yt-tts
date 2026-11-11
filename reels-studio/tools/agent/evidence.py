"""Bounded public-source tools. Web text is DATA, never agent instructions.
No authenticated browsing, arbitrary hosts, localhost, or credential forwarding.
"""
import datetime as dt
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import socket
import unicodedata
from urllib.parse import urljoin,urlparse

import requests
from bs4 import BeautifulSoup

from tools.post.common import iso,now_utc,save_json
from tools.agent.openrouter_client import PilotBlocked


def normalized(value):
    text=unicodedata.normalize('NFKC',value or '')
    # Typography normalization only; words/numbers/negation are never changed.
    text=text.translate(str.maketrans({'’':"'",'‘':"'",'“':'"','”':'"','–':'-','—':'-','−':'-'}))
    return ' '.join(text.split())


def safe_url(url,hosts,resolver=socket.getaddrinfo):
    p=urlparse(url)
    if p.scheme!='https' or p.hostname not in set(hosts) or p.username or p.password or p.port not in (None,443):
        raise PilotBlocked('Source URL is outside the explicit public HTTPS allowlist')
    if p.fragment: url=url.split('#',1)[0]
    if re.search(r'(?:token|api_key|password|client_secret|authorization|access_key)=',p.query,re.I):
        raise PilotBlocked('Credential-like URL query rejected')
    try:addresses={r[4][0] for r in resolver(p.hostname,443,type=socket.SOCK_STREAM)}
    except OSError:raise PilotBlocked('Source DNS unavailable')
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise PilotBlocked('Private/non-global source address rejected')
    return url


def plain_text(html):
    soup=BeautifulSoup(html,'html.parser')
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    published=None
    for attrs in [{'property':'article:published_time'},{'name':'date'},{'itemprop':'datePublished'}]:
        meta=soup.find('meta',attrs=attrs)
        if meta and meta.get('content'):published=meta['content'];break
    for tag in soup(['script','style','noscript','nav','footer','form','header']):tag.decompose()
    main=soup.find('main') or soup.find('article') or soup.body or soup
    text=normalized(main.get_text(' ',strip=True))
    return title,text,published


class EvidenceStore:
    def __init__(self,case,work,limits,session=None,resolver=socket.getaddrinfo):
        self.case=case;self.work=Path(work);self.work.mkdir(parents=True,exist_ok=True)
        self.limits=limits;self.session=session or requests.Session();self.resolver=resolver
        self.sources={s['id']:s for s in case['sources']};self.read_ids=set();self.records={}
        self.hosts=set(case['source_hosts'])

    def read_source(self,source_id):
        if source_id not in self.sources:raise PilotBlocked('Unknown source ID; model cannot invent a fetch target')
        if source_id in self.records:
            self.read_ids.add(source_id);return self.records[source_id]
        spec=self.sources[source_id]
        if spec.get('kind')=='recorded_observation':
            text=normalized(spec['text'])
            row={'id':source_id,'url':spec['url'],'title':spec['title'],'retrieved_at':iso(now_utc()),'published_at':spec.get('observed_at'),
                 'kind':'recorded_observation','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                 'provenance':spec.get('provenance'),'warning':'Previously recorded studio test; not a newly executed autonomous experiment.'}
        else:
            url=spec['url'];response=None
            for _ in range(4):
                url=safe_url(url,self.hosts,self.resolver)
                # Separate unprivileged session; never add Authorization/Cookie headers.
                response=self.session.get(url,headers={'User-Agent':'HypelessResearch/1.0 (public evidence)','Accept':'text/html,text/plain,application/json'},
                                          stream=True,timeout=(10,self.limits['source_timeout_seconds']),allow_redirects=False)
                if response.status_code in (301,302,303,307,308):
                    nxt=response.headers.get('Location');response.close()
                    if not nxt:raise PilotBlocked('Source redirect has no destination')
                    url=urljoin(url,nxt);continue
                break
            else:raise PilotBlocked('Too many source redirects')
            if response.status_code!=200:
                status=response.status_code;response.close();raise PilotBlocked('Primary source unavailable, HTTP '+str(status))
            chunks=[];size=0
            try:
                for block in response.iter_content(65536):
                    size+=len(block)
                    if size>self.limits['max_source_bytes']:raise PilotBlocked('Source exceeds acquisition limit')
                    chunks.append(block)
            finally:response.close()
            raw=b''.join(chunks);ctype=response.headers.get('Content-Type','')
            if not any(x in ctype.lower() for x in ['text/','json','xml']):raise PilotBlocked('Unsupported source document type')
            html=raw.decode('utf-8',errors='replace');title,text,published=plain_text(html)
            if len(text)<200:raise PilotBlocked('Source is empty/blocked, not evidence')
            if any(t in title.lower() for t in ['access denied','just a moment','captcha']):raise PilotBlocked('Do not use access-denied/challenge pages as evidence')
            truncated=len(text)>self.limits['max_source_text_chars'];text=text[:self.limits['max_source_text_chars']]
            row={'id':source_id,'url':url,'original_url':spec['url'],'title':title,'retrieved_at':iso(now_utc()),'published_at':published,
                 'kind':'primary_source','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'raw_sha256':hashlib.sha256(raw).hexdigest(),
                 'truncated':truncated,'source_class':spec.get('source_class','maker_statement'),'warning':'Maker claims/benchmarks are not independent validation.'}
        self.records[source_id]=row;self.read_ids.add(source_id);save_json(self.work/(source_id+'.json'),row)
        return row

    def citation(self,reference):
        sid=reference.get('source_id');quote=normalized(reference.get('quote'))
        if sid not in self.read_ids:raise PilotBlocked('Citation refers to a source the producer did not read')
        if not 25<=len(quote)<=900:raise PilotBlocked('Evidence quote is too short/long')
        record=self.records[sid]
        if hashlib.sha256(record['text'].encode()).hexdigest()!=record['text_sha256']:
            raise PilotBlocked('Evidence snapshot changed after collection')
        index=normalized(record['text']).find(quote)
        if index<0:raise PilotBlocked('Evidence quote does not occur verbatim in the fetched source')
        return {'source_id':sid,'url':record['url'],'quote':quote,'start':index,'end':index+len(quote),'text_sha256':record['text_sha256'],'retrieved_at':record['retrieved_at'],'kind':record['kind']}


def validate_provenance(asset):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.(jpg|jpeg|png|webp|mp4)',asset.get('file','')):
        raise PilotBlocked('Unsafe media filename/path')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',asset.get('digest','')):raise PilotBlocked('Media digest missing')
    if not asset.get('source_url') or not asset.get('kind') or not asset.get('usage_basis'):
        raise PilotBlocked('Asset provenance incomplete')
    if asset.get('contains_credentials'):raise PilotBlocked('Sensitive screenshot rejected')
    return True
