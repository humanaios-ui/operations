"""E0 frozen public-evidence adapter: no network, no authority, no claim promotion."""
from __future__ import annotations
import hashlib
import json
import re
from datetime import date
from urllib.parse import urlsplit

MAX_BYTES = 256_000
MAX_ROWS = 64
MAX_REFS = 64
HOSTS = frozenset({'www.epa.gov','www.army.mil','www.iowapublicradio.org','epa.illinois.gov'})
KINDS = frozenset({'primary_regulatory','agency_statement','independent_reporting','state_notice'})
TOPICS = frozenset({'alternatives','engagement','monitoring','reporting'})
STATES = frozenset({'REFERENCED','REQUIRED'})
ID = re.compile(r'[A-Z][A-Z0-9-]{0,47}\Z')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def _text(v, maxlen=1000):
    if not isinstance(v,str) or not v.strip() or len(v)>maxlen or any(ord(x)<32 for x in v):
        raise ValueError('invalid text')
    return v

def _id(v):
    if not isinstance(v,str) or not ID.fullmatch(v): raise ValueError('invalid id')
    return v

def _date(v):
    if not isinstance(v,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',v): raise ValueError('invalid date')
    return date.fromisoformat(v)

def _url(v):
    v=_text(v,2000); u=urlsplit(v)
    if u.scheme!='https' or u.netloc not in HOSTS or not u.path.startswith('/') or u.fragment or u.query or '\\' in v or any(c.isspace() for c in v):
        raise ValueError('URL outside exact public allowlist')
    return v

def _fields(obj, fields):
    if not isinstance(obj,dict) or set(obj)!=set(fields): raise ValueError('unexpected or missing fields')

def load_frozen(blob, expected_sha):
    if not isinstance(blob,bytes) or len(blob)>MAX_BYTES: raise ValueError('input bound')
    if digest(blob)!=expected_sha: raise ValueError('frozen input digest mismatch')
    def pairs(items):
        out={}
        for k,v in items:
            if k in out: raise ValueError('duplicate JSON key')
            out[k]=v
        return out
    obj=json.loads(blob,object_pairs_hook=pairs)
    _fields(obj,('schema','as_of','sources'))
    if obj['schema']!='humanaios.public_evidence.fixture.v1': raise ValueError('schema')
    as_of=_date(obj['as_of']); sources=obj['sources']
    if not isinstance(sources,list) or not 1<=len(sources)<=MAX_ROWS: raise ValueError('source count')
    seen=set(); ref_count=0
    for s in sources:
        _fields(s,('id','url','kind','document_date','note','references'))
        sid=_id(s['id']); _url(s['url']); _text(s['note'],1600)
        if sid in seen: raise ValueError('duplicate source id')
        seen.add(sid)
        if s['kind'] not in KINDS or _date(s['document_date'])>as_of: raise ValueError('kind/date')
        refs=s['references']
        if not isinstance(refs,list): raise ValueError('references')
        if refs and s['kind']!='primary_regulatory': raise ValueError('reference origin not regulatory')
        ref_count+=len(refs)
        if ref_count>MAX_REFS: raise ValueError('reference count')
        for r in refs:
            _fields(r,('id','title','topic','locator','state','record_date'))
            _id(r['id']); _text(r['title'],180); _text(r['locator'],120)
            if r['topic'] not in TOPICS or r['state'] not in STATES: raise ValueError('reference taxonomy')
            if r['record_date'] is not None and _date(r['record_date'])>as_of: raise ValueError('future record date')
    return obj

def discover(blob, expected_sha):
    obj=load_frozen(blob,expected_sha)
    rows={}
    for s in obj['sources']:
        for r in s['references']:
            identity=r['id']; core={k:v for k,v in r.items() if k!='locator'}
            evidence={'source_id':s['id'],'url':s['url'],'locator':r['locator'],'source_date':s['document_date']}
            if identity not in rows:
                rows[identity]={**core,'provenance':[],'retrieval_state':'NOT_RETRIEVED','verification_state':'UNVERIFIED_REFERENCE','authority_effect':'NONE'}
            else:
                if any(rows[identity][k]!=v for k,v in core.items()): raise ValueError('conflicting reference identity')
            if evidence not in rows[identity]['provenance']: rows[identity]['provenance'].append(evidence)
    result=[]
    for identity in sorted(rows):
        row=rows[identity];row['provenance'].sort(key=lambda x:(x['source_id'],x['locator']))
        result.append(row)
    return {'schema':'humanaios.public_evidence.discovery.v1','input_sha256':expected_sha,'as_of':obj['as_of'],'authority_effect':'NONE','execution':'DISABLED','coverage':'SUPPLIED_FROZEN_NOTES_ONLY','candidates':result}

def to_planning_requirements(result):
    """Projection compatible with planning.py requirement shape; never asserts adequacy."""
    return [{'requirement_id':r['id'],'label':r['title'],'objective':'Obtain public or lawfully releasable record; verify origin and completeness.',
             'resource_types':['public_record'],'affordances':['evidence_access'],'signals':[r['topic']],
             'activation_state':'ACTIVE','resolution_mode':'ACQUIRE_EXTERNAL','mine_external':True,
             'satisfied_when':'Underlying record obtained and independently reviewed','work_package_ids':['WP-RECORDS'],'capability_ids':['CAP-REVIEW']} for r in result['candidates']]
