"""Offline-only research proposal validation; no Supabase calls."""
import hashlib, ipaddress, json, re
from urllib.parse import urlsplit

class InvalidProposal(ValueError): pass

def public_https(url):
    try:
        p=urlsplit(url)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443): return False
        h=p.hostname.rstrip('.').lower()
        if h in ('localhost','localhost.localdomain') or h.endswith(('.localhost','.local','.internal')): return False
        try: return ipaddress.ip_address(h.strip('[]')).is_global
        except ValueError: return bool(re.fullmatch(r'[a-z0-9.-]{1,253}',h)) and '.' in h
    except ValueError: return False

def validate(p):
    if not isinstance(p,dict): raise InvalidProposal('object required')
    for k in ('proposal_id','question','claims','evidence','uncertainty','status','origin','created_at','guild_id'):
        if k not in p: raise InvalidProposal('missing '+k)
    if p['status']!='proposed' or p['origin']!='camelbot': raise InvalidProposal('authority boundary')
    if not isinstance(p['question'],str) or not 5<=len(p['question'])<=2000: raise InvalidProposal('question')
    if not isinstance(p['claims'],list) or not isinstance(p['evidence'],list) or not p['evidence']: raise InvalidProposal('evidence')
    if len(p['evidence'])>20: raise InvalidProposal('too many sources')
    for e in p['evidence']:
        if not isinstance(e,dict) or not public_https(e.get('url','')): raise InvalidProposal('unsafe source URL')
        for k in ('title','accessed_at','excerpt'):
            if not isinstance(e.get(k),str) or not e[k] or len(e[k])>4000: raise InvalidProposal('bad evidence '+k)
    canonical=json.dumps({'guild_id':p['guild_id'],'question':p['question'].strip().casefold(),'urls':sorted(e['url'] for e in p['evidence'])},sort_keys=True)
    return {'proposal_id':p['proposal_id'],'status':'proposed','dedupe_key':hashlib.sha256(canonical.encode()).hexdigest(),'validated':True}
