"""Discord OAuth account linking and read-only slash command interaction adapter.

No bot token or OAuth access token is kept as Witness memory.
"""
import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

from lineage_store import BoundaryError

DISCORD_API='https://discord.com/api/v10'


def start_oauth(store,player_id,client_id,redirect_uri):
    if not client_id or not redirect_uri.startswith('https://'):
        raise BoundaryError('OAuth not configured securely')
    state=secrets.token_urlsafe(40)
    verifier=secrets.token_urlsafe(48)
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    store.put_oauth_state(state,player_id,verifier)
    return 'https://discord.com/oauth2/authorize?'+urlencode({
        'client_id':client_id,'response_type':'code','redirect_uri':redirect_uri,
        'scope':'identify','state':state,'code_challenge':challenge,'code_challenge_method':'S256',
    })


def complete_oauth(store,state,code,client_id,client_secret,redirect_uri,transport=None):
    # OAuth state atomically consumed before outbound requests.
    player_id,verifier=store.take_oauth_state(state)
    if not code or len(code)>4096 or not client_id or not client_secret:
        raise BoundaryError('invalid Discord code/configuration')
    with httpx.Client(timeout=8.0,transport=transport,follow_redirects=False) as client:
        token=client.post(f'{DISCORD_API}/oauth2/token',data={
            'grant_type':'authorization_code','code':code,'redirect_uri':redirect_uri,
            'client_id':client_id,'client_secret':client_secret,'code_verifier':verifier,
        },headers={'Content-Type':'application/x-www-form-urlencoded'})
        token.raise_for_status()
        access_token=token.json().get('access_token')
        if not isinstance(access_token,str) or not access_token:
            raise BoundaryError('Discord did not provide a token')
        who=client.get(f'{DISCORD_API}/users/@me',headers={'Authorization':'Bearer '+access_token})
        who.raise_for_status()
        discord_id=who.json().get('id')
    store.link_discord(player_id,discord_id)
    return player_id


def verify_signature(public_key_hex,signature_hex,timestamp,body):
    try:
        if abs(time.time()-int(timestamp))>300:
            return False
        key=Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        key.verify(bytes.fromhex(signature_hex),timestamp.encode()+body)
        return True
    except (ValueError,InvalidSignature,TypeError,OverflowError):
        return False


def interaction_response(store,interaction):
    if interaction.get('type')==1:
        return {'type':1}
    if interaction.get('type')!=2:
        return {'type':4,'data':{'content':'Unsupported interaction.','flags':64}}
    user=(interaction.get('member') or {}).get('user') or interaction.get('user') or {}
    discord_id=user.get('id')
    player=store.find('discord',str(discord_id)) if discord_id else None
    if not player:
        message='Link Discord from your authenticated Wardens account first.'
    else:
        command=(interaction.get('data') or {}).get('name')
        if command not in ('witness','lineage'):
            message='Unknown command.'
        else:
            try:
                events=store.history(player,limit=5)
                if events:
                    # No LLM in this prototype. Only verified, scoped historical observation.
                    lines=[f"[{e['campaign_id'][:18]}] {e['kind']}: {e['summary'][:120]} (event {e['id']})" for e in events]
                    message='Recorded history (not advice):\n'+'\n'.join(lines)
                else:
                    message='No permitted game events are recorded.'
            except BoundaryError:
                message='Enable optional Witness memory in your Wardens account first.'
    return {'type':4,'data':{'content':message[:1900],'flags':64,'allowed_mentions':{'parse':[]}}}
