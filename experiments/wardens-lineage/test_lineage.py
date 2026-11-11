import hashlib
import json
import time
from urllib.parse import urlparse,parse_qs
import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient
from lineage_store import Lineage,BoundaryError
from identity import issue, verify, AuthError
from discord_integration import start_oauth,complete_oauth,verify_signature
from api import create_app

KEY='first-party-game-assertion-private-key-over-32'
SERVER='server-only-backend-token-more-than-32-chars'
HEX='f'*64

def test_restart_and_cross_campaign(tmp_path):
    path=tmp_path/'memory.db'
    s=Lineage(path)
    p=s.resolve_player('firstparty','u1')
    assert p==s.resolve_player('firstparty','u1')
    s.join('c1',p,'join1',HEX)
    s.record('c1',p,'battle',HEX,'MILESTONE','Escaped the first cave','PRIVATE')
    s.join('c2',p,'join2',HEX)
    s.record('c2',p,'morph',HEX,'EVOLUTION','Chose augmented eyes','PRIVATE')
    s.set_consent(p,'WITNESS',True)
    s2=Lineage(path)
    assert s2.find('firstparty','u1')==p
    assert {e['campaign_id'] for e in s2.history(p)}=={'c1','c2'}
    assert s2.integrity('c1') and s2.integrity('c2')

def test_private_scope_and_first_join_not_governance(tmp_path):
    s=Lineage(tmp_path/'mem.db')
    a=s.resolve_player('firstparty','a')
    b=s.resolve_player('firstparty','b')
    assert s.join('a-room',a,'join-a',HEX)==1
    assert s.join('a-room',b,'join-b',HEX)==2
    s.record('a-room',a,'private',HEX,'DECISION','My private thoughts','PRIVATE')
    s.record('a-room',a,'shared',HEX,'DISCOVERY','Found blue stones','CAMPAIGN')
    s.set_consent(a,'WITNESS',True)
    s.set_consent(b,'WITNESS',True)
    h=s.history(b)
    assert not any(x['summary']=='My private thoughts' for x in h)
    assert any(x['summary']=='Found blue stones' for x in h)
    assert s.integrity('a-room')
    assert s.join('a-room',b,'join-b',HEX)==2

def test_consent_revocation_and_research_separate(tmp_path):
    s=Lineage(tmp_path/'mem.db')
    p=s.resolve_player('firstparty','p')
    s.join('room',p,'join',HEX)
    with pytest.raises(BoundaryError,match='consent'):
        s.history(p)
    s.set_consent(p,'RESEARCH',True)
    with pytest.raises(BoundaryError):
        s.history(p)
    s.set_consent(p,'WITNESS',True)
    assert s.history(p)
    s.set_consent(p,'WITNESS',False)
    with pytest.raises(BoundaryError):
        s.history(p)
    assert s.has_consent(p,'RESEARCH')

def test_ingestion_replay_and_collision(tmp_path):
    s=Lineage(tmp_path/'m.db')
    p=s.resolve_player('firstparty','p')
    s.join('r',p,'join',HEX)
    x=s.record('r',p,'source1',HEX,'MILESTONE','One milestone','PRIVATE')
    assert x==s.record('r',p,'source1',HEX,'MILESTONE','One milestone','PRIVATE')
    with pytest.raises(BoundaryError,match='collision'):
        s.record('r',p,'source1',HEX,'MILESTONE','Altered','PRIVATE')
    with pytest.raises(BoundaryError):
        s.record('r',p,'source2','bad','EVOLUTION','No','PRIVATE')
    with s.conn() as db:
        db.execute("UPDATE events SET summary='tamper' WHERE id=?",(x,))
    assert not s.integrity('r')

def test_attestation_only_own_genesis(tmp_path):
    s=Lineage(tmp_path/'m.db')
    a=s.resolve_player('firstparty','a'); b=s.resolve_player('firstparty','b')
    s.join('r',a,'j1',HEX); s.join('r',b,'j2',HEX)
    with s.conn() as db:
        genesis=db.execute("SELECT id FROM events WHERE source_ref='j1'").fetchone()['id']
    with pytest.raises(BoundaryError):
        s.attest(b,genesis,'ACKNOWLEDGE')
    assert s.attest(a,genesis,'CONTEST')>0
    with pytest.raises(BoundaryError):
        s.attest(a,genesis,'CONTEST')

def test_discord_unlink_keeps_player(tmp_path):
    s=Lineage(tmp_path/'m.db')
    p=s.resolve_player('firstparty','a'); q=s.resolve_player('firstparty','b')
    s.link_discord(p,'123456789012345678')
    assert s.find('discord','123456789012345678')==p
    with pytest.raises(BoundaryError,match='already linked'):
        s.link_discord(q,'123456789012345678')
    s.unlink_discord(p)
    assert s.find('firstparty','a')==p
    assert s.find('discord','123456789012345678') is None

def test_oauth_pkce_state_verification(tmp_path):
    s=Lineage(tmp_path/'m.db')
    p=s.resolve_player('firstparty','a')
    url=start_oauth(s,p,'app-id','https://test.example/callback')
    params=parse_qs(urlparse(url).query)
    assert params['scope']==['identify']
    assert params['code_challenge_method']==['S256']
    state=params['state'][0]
    def handler(req):
        if req.url.path=='/api/v10/oauth2/token':
            assert req.method=='POST' and 'code_verifier' in req.content.decode()
            return httpx.Response(200,json={'access_token':'temporary-access'})
        if req.url.path=='/api/v10/users/@me':
            assert req.headers['Authorization']=='Bearer temporary-access'
            return httpx.Response(200,json={'id':'123456789012345678','username':'ignore'})
        return httpx.Response(404)
    player=complete_oauth(s,state,'oauth-code','app-id','server-secret','https://test.example/callback',httpx.MockTransport(handler))
    assert player==p and s.find('discord','123456789012345678')==p
    with pytest.raises(BoundaryError,match='replayed'):
        complete_oauth(s,state,'oauth-code','app-id','server-secret','https://test.example/callback',httpx.MockTransport(handler))

def test_identity_assertion_expiry_and_tamper():
    token=issue(KEY,'acct-1')
    assert verify(KEY,token)=='acct-1'
    with pytest.raises(AuthError):verify(KEY,token+'wrong')
    with pytest.raises(AuthError):verify(KEY,issue(KEY,'acct-1',seconds=-1))

def test_api_restricts_public_ingestion(tmp_path):
    app=create_app(tmp_path/'m.db',KEY,SERVER)
    client=TestClient(app)
    h={'Authorization':'Bearer '+issue(KEY,'acct-1')}
    s={'Authorization':'Bearer '+SERVER}
    assert client.post('/v1/server/players/resolve',json={'firstparty_subject':'acct-1'},headers=h).status_code==401
    p=client.post('/v1/server/players/resolve',json={'firstparty_subject':'acct-1'},headers=s).json()['player_id']
    assert client.get('/v1/me',headers=h).json()['player_id']==p
    assert client.post('/v1/server/campaigns/r/join',json={'firstparty_subject':'acct-1','source_ref':'j','source_digest':HEX},headers=s).status_code==200
    assert client.post('/v1/server/campaigns/r/events',json={'firstparty_subject':'acct-1','source_ref':'x','source_digest':HEX,'kind':'MILESTONE','summary':'Done','visibility':'PRIVATE'},headers=h).status_code==401
    assert client.get('/v1/me/witness/history',headers=h).status_code==409
    assert client.post('/v1/me/consent',json={'purpose':'WITNESS','enabled':True},headers=h).status_code==200
    result=client.get('/v1/me/witness/history',headers=h).json()
    assert len(result['events'])==1 and result['authority_effect']=='NONE'

def test_discord_signature_and_private_response(tmp_path):
    key=Ed25519PrivateKey.generate()
    pub=key.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw).hex()
    app=create_app(tmp_path/'m.db',KEY,SERVER,discord_public_key=pub)
    client=TestClient(app)
    def send(payload,valid=True):
        raw=json.dumps(payload).encode(); ts=str(int(time.time()));sig=key.sign(ts.encode()+raw).hex()
        if not valid: sig='00'*64
        return client.post('/v1/discord/interactions',content=raw,headers={'X-Signature-Ed25519':sig,'X-Signature-Timestamp':ts})
    assert send({'type':1}).json()=={'type':1}
    assert send({'type':2,'data':{'name':'witness'},'user':{'id':'123456789012345678'}}).json()['data']['flags']==64
    assert send({'type':1},valid=False).status_code==401
    assert not verify_signature(pub,'00'*64,str(int(time.time())-1000),b'{}')
