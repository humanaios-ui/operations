"""Wardens Lineage v0.1: persistent, scoped SQLite *single-worker* prototype.

For a deployed multi-worker game, port transactions to Azure PostgreSQL first.
The game server owns gameplay writes; this is only a memory projection.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

class BoundaryError(ValueError):
    pass


def iso_time():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


class Lineage:
    def __init__(self, path):
        self.path = str(Path(path))
        with self.conn() as db:
            db.executescript('''
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS players (
                  player_id TEXT PRIMARY KEY, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS links (
                  provider TEXT NOT NULL, subject TEXT NOT NULL, player_id TEXT NOT NULL
                  REFERENCES players(player_id), PRIMARY KEY(provider,subject)
                );
                CREATE INDEX IF NOT EXISTS links_player ON links(player_id);
                CREATE TABLE IF NOT EXISTS consent (
                  player_id TEXT NOT NULL REFERENCES players(player_id), purpose TEXT NOT NULL,
                  enabled INTEGER NOT NULL CHECK(enabled IN (0,1)), changed_at TEXT NOT NULL,
                  PRIMARY KEY(player_id,purpose)
                );
                CREATE TABLE IF NOT EXISTS consent_log (
                  id INTEGER PRIMARY KEY AUTOINCREMENT, player_id TEXT NOT NULL,
                  purpose TEXT NOT NULL, enabled INTEGER NOT NULL, changed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS campaigns (
                  campaign_id TEXT PRIMARY KEY, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS membership (
                  campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
                  player_id TEXT NOT NULL REFERENCES players(player_id),
                  ordinal INTEGER NOT NULL, joined_at TEXT NOT NULL,
                  PRIMARY KEY(campaign_id,player_id), UNIQUE(campaign_id,ordinal)
                );
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  campaign_id TEXT NOT NULL, player_id TEXT NOT NULL,
                  source_ref TEXT NOT NULL, source_digest TEXT NOT NULL,
                  kind TEXT NOT NULL, summary TEXT NOT NULL, visibility TEXT NOT NULL,
                  created_at TEXT NOT NULL, previous_digest TEXT NOT NULL, digest TEXT NOT NULL,
                  UNIQUE(campaign_id,source_ref)
                );
                CREATE INDEX IF NOT EXISTS events_player ON events(player_id,id);
                CREATE INDEX IF NOT EXISTS events_campaign ON events(campaign_id,id);
                CREATE TABLE IF NOT EXISTS attestations (
                  id INTEGER PRIMARY KEY AUTOINCREMENT, player_id TEXT NOT NULL,
                  event_id INTEGER NOT NULL REFERENCES events(id),
                  choice TEXT NOT NULL, created_at TEXT NOT NULL,
                  UNIQUE(player_id,event_id,choice)
                );
                CREATE TABLE IF NOT EXISTS oauth_states (
                  state_hash TEXT PRIMARY KEY, player_id TEXT NOT NULL,
                  verifier TEXT NOT NULL, expires_at INTEGER NOT NULL
                );
            ''')

    @contextmanager
    def conn(self):
        db = sqlite3.connect(self.path, timeout=8, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def write(self):
        with self.conn() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    def resolve_player(self, provider, subject):
        """SERVER-ONLY: provider identity already verified by the auth issuer."""
        if provider not in ('firstparty', 'discord') or not isinstance(subject, str) or not 1 <= len(subject) <= 160:
            raise BoundaryError('invalid identity claim')
        with self.write() as db:
            row = db.execute('SELECT player_id FROM links WHERE provider=? AND subject=?', (provider,subject)).fetchone()
            if row:
                return row['player_id']
            if provider != 'firstparty':
                raise BoundaryError('Discord cannot create an orphan player; link a first-party identity')
            player_id = str(uuid.uuid4())
            db.execute('INSERT INTO players VALUES (?,?)', (player_id, iso_time()))
            db.execute('INSERT INTO links VALUES (?,?,?)', (provider, subject, player_id))
            return player_id

    def find(self, provider, subject):
        with self.conn() as db:
            row = db.execute('SELECT player_id FROM links WHERE provider=? AND subject=?', (provider,subject)).fetchone()
            return row['player_id'] if row else None

    def link_discord(self, player_id, discord_subject):
        if not isinstance(discord_subject,str) or not discord_subject.isdecimal() or not 5 <= len(discord_subject) <= 24:
            raise BoundaryError('Discord subject must come from verified /users/@me')
        with self.write() as db:
            if not db.execute('SELECT 1 FROM players WHERE player_id=?',(player_id,)).fetchone():
                raise BoundaryError('unknown player')
            row=db.execute('SELECT player_id FROM links WHERE provider=? AND subject=?',('discord',discord_subject)).fetchone()
            if row and row['player_id'] != player_id:
                raise BoundaryError('Discord account already linked to another player')
            current=db.execute('SELECT subject FROM links WHERE player_id=? AND provider=?',(player_id,'discord')).fetchone()
            if current and current['subject'] != discord_subject:
                raise BoundaryError('unlink existing Discord account first')
            db.execute('INSERT OR IGNORE INTO links VALUES(?,?,?)',('discord',discord_subject,player_id))

    def unlink_discord(self, player_id):
        with self.write() as db:
            db.execute('DELETE FROM links WHERE provider=? AND player_id=?',('discord',player_id))

    def set_consent(self, player_id, purpose, enabled):
        if purpose not in ('WITNESS','RESEARCH') or type(enabled) is not bool:
            raise BoundaryError('invalid consent change')
        when=iso_time()
        with self.write() as db:
            if not db.execute('SELECT 1 FROM players WHERE player_id=?',(player_id,)).fetchone():
                raise BoundaryError('unknown player')
            db.execute('INSERT INTO consent VALUES(?,?,?,?) ON CONFLICT(player_id,purpose) DO UPDATE SET enabled=excluded.enabled, changed_at=excluded.changed_at', (player_id,purpose,int(enabled),when))
            db.execute('INSERT INTO consent_log(player_id,purpose,enabled,changed_at) VALUES(?,?,?,?)',(player_id,purpose,int(enabled),when))

    def has_consent(self, player_id, purpose):
        with self.conn() as db:
            row=db.execute('SELECT enabled FROM consent WHERE player_id=? AND purpose=?',(player_id,purpose)).fetchone()
            return bool(row and row['enabled'])

    def join(self, campaign_id, player_id, source_ref, source_digest):
        self._validate_evidence(source_ref,source_digest)
        with self.write() as db:
            if not db.execute('SELECT 1 FROM players WHERE player_id=?',(player_id,)).fetchone():
                raise BoundaryError('unknown player')
            db.execute('INSERT OR IGNORE INTO campaigns VALUES(?,?)',(campaign_id,iso_time()))
            old=db.execute('SELECT ordinal FROM membership WHERE campaign_id=? AND player_id=?',(campaign_id,player_id)).fetchone()
            if old:
                return old['ordinal']
            row=db.execute('SELECT COALESCE(MAX(ordinal),0)+1 AS n FROM membership WHERE campaign_id=?',(campaign_id,)).fetchone()
            ordinal=row['n']
            # Must have an engine-supplied source reference; no self-asserted client joins.
            db.execute('INSERT INTO membership VALUES(?,?,?,?)',(campaign_id,player_id,ordinal,iso_time()))
            self._append(db,campaign_id,player_id,source_ref,source_digest,'GENESIS_EVENT',f'Player joined campaign (position {ordinal})','PRIVATE')
            return ordinal

    def _validate_evidence(self, source_ref, source_digest):
        if not isinstance(source_ref,str) or not 1 <= len(source_ref) <= 160:
            raise BoundaryError('source event ref required')
        if not isinstance(source_digest,str) or len(source_digest) != 64 or any(c not in '0123456789abcdef' for c in source_digest):
            raise BoundaryError('source event sha256 required')

    def _append(self,db,campaign_id,player_id,source_ref,source_digest,kind,summary,visibility):
        prior=db.execute('SELECT * FROM events WHERE campaign_id=? AND source_ref=?',(campaign_id,source_ref)).fetchone()
        payload=dict(campaign_id=campaign_id,player_id=player_id,source_ref=source_ref,source_digest=source_digest,kind=kind,summary=summary,visibility=visibility)
        if prior:
            if all(prior[k] == v for k,v in payload.items()):
                return prior['id']
            raise BoundaryError('source event ref collision')
        last=db.execute('SELECT digest FROM events WHERE campaign_id=? ORDER BY id DESC LIMIT 1',(campaign_id,)).fetchone()
        prev=last['digest'] if last else '0'*64
        digest=stable_hash({'previous':prev,**payload})
        return db.execute('INSERT INTO events(campaign_id,player_id,source_ref,source_digest,kind,summary,visibility,created_at,previous_digest,digest) VALUES(?,?,?,?,?,?,?,?,?,?)', (*payload.values(),iso_time(),prev,digest)).lastrowid

    def record(self, campaign_id, player_id, source_ref, source_digest, kind, summary, visibility):
        self._validate_evidence(source_ref,source_digest)
        if kind not in ('MILESTONE','EVOLUTION','DECISION','DISCOVERY','COUNCIL_RECORD'):
            raise BoundaryError('event type not allowlisted')
        if visibility not in ('PRIVATE','CAMPAIGN','PUBLIC') or not isinstance(summary,str) or not 1 <= len(summary) <= 350:
            raise BoundaryError('invalid event scope/content')
        with self.write() as db:
            if not db.execute('SELECT 1 FROM membership WHERE campaign_id=? AND player_id=?',(campaign_id,player_id)).fetchone():
                raise BoundaryError('actor is not a campaign member')
            return self._append(db,campaign_id,player_id,source_ref,source_digest,kind,summary,visibility)

    def history(self, player_id, limit=40):
        # For personal W1, show own events across ALL campaigns, plus events explicitly
        # shared with participants in joined campaigns. Other people's PRIVATE never shown.
        if not self.has_consent(player_id,'WITNESS'):
            raise BoundaryError('WITNESS consent required')
        if not isinstance(limit,int) or not 1<=limit<=100:
            raise BoundaryError('bounded limit required')
        with self.conn() as db:
            rows=db.execute('''SELECT e.id,e.campaign_id,e.player_id,e.kind,e.summary,e.visibility,
                   e.source_ref,e.source_digest,e.digest,e.created_at
                   FROM events e WHERE e.player_id=? OR (e.visibility IN ('CAMPAIGN','PUBLIC')
                   AND EXISTS (SELECT 1 FROM membership m WHERE m.campaign_id=e.campaign_id AND m.player_id=?))
                   ORDER BY e.id DESC LIMIT ?''',(player_id,player_id,limit)).fetchall()
            return [dict(r) for r in rows]

    def attest(self,player_id,event_id,choice):
        if choice not in ('ACKNOWLEDGE','CONTEST','DECLINE'):
            raise BoundaryError('invalid W2 choice')
        with self.write() as db:
            event=db.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
            if not event or event['player_id'] != player_id or event['kind'] != 'GENESIS_EVENT':
                raise BoundaryError('human attestation limited to own genesis')
            try:
                cur=db.execute('INSERT INTO attestations(player_id,event_id,choice,created_at) VALUES(?,?,?,?)',(player_id,event_id,choice,iso_time()))
            except sqlite3.IntegrityError:
                raise BoundaryError('duplicate attestation') from None
            return cur.lastrowid

    def integrity(self,campaign_id):
        with self.conn() as db:
            prev='0'*64
            for e in db.execute('SELECT * FROM events WHERE campaign_id=? ORDER BY id',(campaign_id,)):
                payload={k:e[k] for k in ('campaign_id','player_id','source_ref','source_digest','kind','summary','visibility')}
                if e['previous_digest']!=prev or e['digest'] !=stable_hash({'previous':prev,**payload}):
                    return False
                prev=e['digest']
            return True

    def put_oauth_state(self,state,player_id,verifier,ttl=300):
        with self.write() as db:
            db.execute('DELETE FROM oauth_states WHERE expires_at<?',(int(time.time()),))
            db.execute('INSERT INTO oauth_states VALUES(?,?,?,?)',(hashlib.sha256(state.encode()).hexdigest(),player_id,verifier,int(time.time())+ttl))

    def take_oauth_state(self,state):
        # Atomic consume; retry and replay must fail.
        with self.write() as db:
            hashed=hashlib.sha256(state.encode()).hexdigest()
            row=db.execute('SELECT player_id,verifier,expires_at FROM oauth_states WHERE state_hash=?',(hashed,)).fetchone()
            db.execute('DELETE FROM oauth_states WHERE state_hash=?',(hashed,))
            if not row or row['expires_at']<=time.time():
                raise BoundaryError('expired or replayed OAuth state')
            return row['player_id'],row['verifier']