"""Optional Wardens identity + Witness view API (no direct game mutations).

Set env vars before deployment. Not a hosted game and not suitable for Azure
multi-replica use before PostgreSQL adapter / first-party OIDC integration.
"""
from __future__ import annotations

import json
import os
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from lineage_store import Lineage, BoundaryError
from identity import verify, AuthError
from discord_integration import start_oauth,complete_oauth,verify_signature,interaction_response

class ConsentIn(BaseModel):
    purpose:str
    enabled:bool

class JoinIn(BaseModel):
    firstparty_subject:str
    source_ref:str
    source_digest:str

class EventIn(BaseModel):
    firstparty_subject:str
    source_ref:str
    source_digest:str
    kind:str
    summary:str
    visibility:str

class AttestIn(BaseModel):
    event_id:int
    choice:str


def create_app(database, player_secret, server_key, discord_client_id='', discord_client_secret='',discord_redirect='',discord_public_key='',oauth_transport=None):
    if min(len(player_secret),len(server_key)) < 32 or player_secret == server_key:
        raise ValueError('distinct 32+ character auth keys required')
    store=Lineage(database)
    app=FastAPI(title='Wardens Lineage (experimental)')

    def player(auth):
        if not auth or not auth.startswith('Bearer '):
            raise HTTPException(401,'first-party login required')
        try:
            sub=verify(player_secret,auth[7:])
        except AuthError as err:
            raise HTTPException(401,str(err)) from err
        pid=store.find('firstparty',sub)
        if pid is None:
            raise HTTPException(404,'game account not provisioned')
        return pid

    def server(auth):
        import hmac
        if not auth or not auth.startswith('Bearer ') or not hmac.compare_digest(auth[7:],server_key):
            raise HTTPException(401,'trusted game server required')

    def guarded(action,*args,**kwargs):
        try:
            return action(*args,**kwargs)
        except BoundaryError as ex:
            raise HTTPException(409,str(ex)) from ex

    @app.get('/healthz')
    def health():
        return {'ok':True,'kind':'lineage-prototype','authority':'NONE'}

    @app.post('/v1/server/players/resolve')
    def resolve(body:dict,authorization:str|None=Header(None)):
        server(authorization)
        return {'player_id':guarded(store.resolve_player,'firstparty',body.get('firstparty_subject'))}

    @app.post('/v1/server/campaigns/{campaign_id}/join')
    def join(campaign_id:str,body:JoinIn,authorization:str|None=Header(None)):
        server(authorization)
        pid=store.find('firstparty',body.firstparty_subject)
        if not pid:
            raise HTTPException(404,'player unknown')
        return {'ordinal':guarded(store.join,campaign_id,pid,body.source_ref,body.source_digest)}

    @app.post('/v1/server/campaigns/{campaign_id}/events')
    def record(campaign_id:str,body:EventIn,authorization:str|None=Header(None)):
        server(authorization)
        pid=store.find('firstparty',body.firstparty_subject)
        if not pid:
            raise HTTPException(404,'player unknown')
        eid=guarded(store.record,campaign_id,pid,body.source_ref,body.source_digest,body.kind,body.summary,body.visibility)
        return {'event_id':eid}

    @app.get('/v1/me')
    def me(authorization:str|None=Header(None)):
        pid=player(authorization)
        return {'player_id':pid,'witness_enabled':store.has_consent(pid,'WITNESS')}

    @app.post('/v1/me/consent')
    def consent(body:ConsentIn,authorization:str|None=Header(None)):
        pid=player(authorization)
        guarded(store.set_consent,pid,body.purpose,body.enabled)
        return {'enabled':body.enabled,'purpose':body.purpose}

    @app.get('/v1/me/witness/history')
    def history(authorization:str|None=Header(None)):
        pid=player(authorization)
        return {'authority_effect':'NONE','can_authorize':False,
                'events':guarded(store.history,pid)}

    @app.post('/v1/me/witness/attestation')
    def attest(body:AttestIn,authorization:str|None=Header(None)):
        pid=player(authorization)
        return {'attestation_id':guarded(store.attest,pid,body.event_id,body.choice),'authority_effect':'NONE'}

    @app.get('/v1/me/discord/link')
    def link(authorization:str|None=Header(None)):
        pid=player(authorization)
        return {'url':guarded(start_oauth,store,pid,discord_client_id,discord_redirect)}

    @app.get('/v1/discord/callback')
    def callback(state:str,code:str):
        if not all((discord_client_id,discord_client_secret,discord_redirect)):
            raise HTTPException(503,'Discord is not configured')
        try:
            complete_oauth(store,state,code,discord_client_id,discord_client_secret,discord_redirect,oauth_transport)
        except (BoundaryError,ValueError):
            raise HTTPException(401,'OAuth linking failed') from None
        except Exception:
            raise HTTPException(502,'Discord verification unavailable') from None
        return {'linked':True,'note':'Discord linked to existing Wardens account; no memory migrated'}

    @app.delete('/v1/me/discord/link')
    def unlink(authorization:str|None=Header(None)):
        pid=player(authorization)
        store.unlink_discord(pid)
        return {'linked':False,'player_id':pid}

    @app.post('/v1/discord/interactions')
    async def discord_interaction(request:Request, x_signature_ed25519:str|None=Header(None), x_signature_timestamp:str|None=Header(None)):
        raw=await request.body()
        if len(raw)>50_000 or not discord_public_key or not verify_signature(discord_public_key,x_signature_ed25519,x_signature_timestamp,raw):
            raise HTTPException(401,'invalid Discord signature')
        try:
            payload=json.loads(raw)
            return JSONResponse(interaction_response(store,payload))
        except (ValueError,TypeError):
            raise HTTPException(400,'invalid interaction') from None

    return app


if __name__ == '__main__':
    import uvicorn
    app=create_app(os.environ['LINEAGE_DB'],os.environ['PLAYER_ASSERTION_KEY'],os.environ['GAME_SERVICE_KEY'],
        os.environ.get('DISCORD_CLIENT_ID',''),os.environ.get('DISCORD_CLIENT_SECRET',''),
        os.environ.get('DISCORD_REDIRECT_URI',''),os.environ.get('DISCORD_PUBLIC_KEY',''))
    uvicorn.run(app,host='127.0.0.1',port=8080)
