"""Minimal authenticated API adapter. All signatures minted by trusted game server.

Never place COUNCIL_SIGNING_KEY inside browser code. Do not deploy this SQLite
prototype on multi-replica Azure Container Apps: replace store with Postgres first.
"""
import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from council import Council, CouncilError


def b64(bytes_):
    return base64.urlsafe_b64encode(bytes_).rstrip(b"=").decode()


def mint(key, *, subject, room, role="player", ttl=300):
    """SERVER-ONLY helper, not an HTTP endpoint."""
    data = {"aud": "wardens-commons", "sub": subject, "room": room,
            "role": role, "exp": int(time.time()) + ttl}
    body = b64(json.dumps(data, sort_keys=True, separators=(",", ":")).encode())
    sig = b64(hmac.new(key.encode(), body.encode(), hashlib.sha256).digest())
    return body + "." + sig


def verify(key, token, room, role=None):
    try:
        body, sig = token.split(".", 1)
        expected = b64(hmac.new(key.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        claims = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if claims.get("aud") != "wardens-commons" or claims.get("room") != room or claims.get("exp", 0) <= time.time():
            raise ValueError("wrong scope or expired")
        if claims.get("role") not in ("player", "server") or not isinstance(claims.get("sub"), str) or not claims["sub"]:
            raise ValueError("invalid identity")
        if role and claims["role"] != role:
            raise ValueError("server authority required")
        return claims
    except (ValueError, KeyError, TypeError, binascii.Error, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=401, detail="invalid council assertion") from exc


class Roster(BaseModel):
    members: list[str]


class NewProposal(BaseModel):
    kind: str
    title: str
    detail: str
    change: dict | None = None


class Comment(BaseModel):
    body: str


class Vote(BaseModel):
    choice: str


class Apply(BaseModel):
    checkpoint: str


def create_app(database, key):
    if not key or len(key) < 32:
        raise ValueError("signing key must be 32+ characters")
    council = Council(database)
    app = FastAPI(title="Wardens' Council — experimental")

    def auth(room, authorization, role=None):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="bearer assertion required")
        return verify(key, authorization[7:], room, role)

    def run(f, *args):
        try:
            return f(*args)
        except CouncilError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.put("/v1/rooms/{room}/members")
    def members(room: str, body: Roster, authorization: str | None = Header(None)):
        auth(room, authorization, "server")
        run(council.set_members, room, body.members)
        return {"ok": True}

    @app.post("/v1/rooms/{room}/proposals")
    def create(room: str, body: NewProposal, authorization: str | None = Header(None)):
        claim = auth(room, authorization)
        if claim["role"] != "player":
            raise HTTPException(status_code=403, detail="player only")
        return {"id": run(council.create, room, claim["sub"], body.kind, body.title, body.detail, body.change)}

    @app.get("/v1/rooms/{room}/proposals")
    def listing(room: str, authorization: str | None = Header(None)):
        auth(room, authorization)
        return council.list_proposals(room)

    @app.post("/v1/rooms/{room}/proposals/{prop}/comments")
    def comment(room: str, prop: int, body: Comment, authorization: str | None = Header(None)):
        claim = auth(room, authorization)
        if claim["role"] != "player":
            raise HTTPException(status_code=403, detail="player only")
        return {"id": run(council.comment, room, claim["sub"], prop, body.body)}

    @app.get("/v1/rooms/{room}/proposals/{prop}/comments")
    def comments(room: str, prop: int, authorization: str | None = Header(None)):
        auth(room, authorization)
        return run(council.list_comments, room, prop)

    @app.post("/v1/rooms/{room}/proposals/{prop}/open")
    def open_vote(room: str, prop: int, authorization: str | None = Header(None)):
        claim = auth(room, authorization)
        run(council.open_ballot, room, claim["sub"], prop)
        return {"ok": True}

    @app.post("/v1/rooms/{room}/proposals/{prop}/vote")
    def cast(room: str, prop: int, body: Vote, authorization: str | None = Header(None)):
        claim = auth(room, authorization)
        if claim["role"] != "player":
            raise HTTPException(status_code=403, detail="player only")
        run(council.vote, room, claim["sub"], prop, body.choice)
        return {"ok": True}

    @app.post("/v1/rooms/{room}/proposals/{prop}/close")
    def close(room: str, prop: int, authorization: str | None = Header(None)):
        claim = auth(room, authorization)
        return run(council.close_ballot, room, claim["sub"], prop)

    @app.post("/v1/rooms/{room}/proposals/{prop}/apply")
    def apply(room: str, prop: int, body: Apply, authorization: str | None = Header(None)):
        auth(room, authorization, "server")
        return run(council.apply, room, prop, body.checkpoint)

    @app.get("/v1/rooms/{room}/rules")
    def rules(room: str, authorization: str | None = Header(None)):
        auth(room, authorization)
        return council.get_rules(room)

    @app.get("/v1/rooms/{room}/integrity")
    def integrity(room: str, authorization: str | None = Header(None)):
        auth(room, authorization, "server")
        return council.verify_events(room)

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app(os.environ.get("COUNCIL_DB", "council.sqlite"), os.environ["COUNCIL_SIGNING_KEY"])
    uvicorn.run(app, host="127.0.0.1", port=8010)
