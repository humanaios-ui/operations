"""Wardens' Council: bounded room governance prototype (not HumanAIOS admission authority).

Local SQLite specimen. Single writer/process only. Production Azure deployment requires a
PostgreSQL transaction adapter, authenticated game-server membership sync, and review.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path


class CouncilError(ValueError):
    pass


def _json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def validate_change(change):
    if not isinstance(change, dict) or not change:
        raise CouncilError("a room rule needs a bounded change")
    if set(change) - {"hints_enabled", "turn_timer_seconds"}:
        raise CouncilError("unsupported room rule")
    if "hints_enabled" in change and type(change["hints_enabled"]) is not bool:
        raise CouncilError("hints_enabled must be boolean")
    if "turn_timer_seconds" in change and (type(change["turn_timer_seconds"]) is not int or not 30 <= change["turn_timer_seconds"] <= 180):
        raise CouncilError("turn_timer_seconds must be 30..180")
    return change


class Council:
    def __init__(self, path):
        self.path = str(Path(path))
        with self.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS members(room TEXT, subject TEXT, PRIMARY KEY(room, subject));
            CREATE TABLE IF NOT EXISTS proposals(
                id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT NOT NULL, author TEXT NOT NULL,
                kind TEXT NOT NULL, title TEXT NOT NULL, detail TEXT NOT NULL,
                change_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft', closes_at INTEGER);
            CREATE TABLE IF NOT EXISTS comments(
                id INTEGER PRIMARY KEY AUTOINCREMENT, proposal INTEGER NOT NULL, room TEXT NOT NULL,
                author TEXT NOT NULL, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS electorate(proposal INTEGER, subject TEXT,
                PRIMARY KEY(proposal, subject));
            CREATE TABLE IF NOT EXISTS votes(proposal INTEGER, subject TEXT, choice TEXT,
                PRIMARY KEY(proposal, subject));
            CREATE TABLE IF NOT EXISTS rules(room TEXT PRIMARY KEY, version INTEGER NOT NULL,
                rules_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(
                seq INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT NOT NULL, kind TEXT NOT NULL,
                ref INTEGER NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL,
                digest TEXT NOT NULL);
            """)

    def db(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        return db

    def _begin(self, db):
        db.execute("BEGIN IMMEDIATE")

    def _member(self, db, room, subject):
        if not db.execute("SELECT 1 FROM members WHERE room=? AND subject=?", (room, subject)).fetchone():
            raise CouncilError("room membership required")

    def _proposal(self, db, room, prop):
        row = db.execute("SELECT * FROM proposals WHERE id=? AND room=?", (prop, room)).fetchone()
        if not row:
            raise CouncilError("proposal not in room")
        return row

    def _event(self, db, room, kind, ref, payload):
        row = db.execute("SELECT digest FROM events WHERE room=? ORDER BY seq DESC LIMIT 1", (room,)).fetchone()
        prev = row["digest"] if row else "0" * 64
        data = _json({"room": room, "kind": kind, "ref": ref, "payload": payload})
        digest = hashlib.sha256((prev + data).encode()).hexdigest()
        db.execute("INSERT INTO events(room,kind,ref,payload,prev_hash,digest) VALUES(?,?,?,?,?,?)",
                   (room, kind, ref, data, prev, digest))

    def set_members(self, room, members):
        """Call only from authenticated game SERVER; replacing roster is authoritative."""
        if not isinstance(members, list) or not 1 <= len(members) <= 8 or not all(
            isinstance(s, str) and 1 <= len(s) <= 100 for s in members
        ) or len(set(members)) != len(members):
            raise CouncilError("roster must be 1..8 distinct server-verified subjects")
        with self.db() as db:
            self._begin(db)
            db.execute("DELETE FROM members WHERE room=?", (room,))
            db.executemany("INSERT INTO members VALUES(?,?)", [(room, s) for s in members])
            self._event(db, room, "roster_updated", 0, {"count": len(members)})
            db.commit()

    def create(self, room, author, kind, title, detail, change=None):
        if kind not in ("gameplay", "design", "lore", "code"):
            raise CouncilError("invalid kind")
        if not isinstance(title, str) or not 5 <= len(title.strip()) <= 100:
            raise CouncilError("title must be 5..100 chars")
        if not isinstance(detail, str) or not 1 <= len(detail.strip()) <= 2000:
            raise CouncilError("detail must be 1..2000 chars")
        if kind == "gameplay":
            validate_change(change)
        elif change is not None:
            raise CouncilError("design/lore/code suggestions cannot carry executable patches")
        with self.db() as db:
            self._begin(db)
            self._member(db, room, author)
            active = db.execute("SELECT COUNT(*) n FROM proposals WHERE room=? AND author=? AND status IN ('draft','voting')", (room,author)).fetchone()["n"]
            if active >= 3:
                raise CouncilError("three active proposals maximum")
            cur = db.execute("INSERT INTO proposals(room,author,kind,title,detail,change_json) VALUES(?,?,?,?,?,?)",
                             (room, author, kind, title.strip(), detail.strip(), _json(change or {})))
            prop = cur.lastrowid
            self._event(db, room, "proposed", prop, {"kind": kind})
            db.commit()
            return prop

    def comment(self, room, author, prop, body):
        if not isinstance(body, str) or not 1 <= len(body.strip()) <= 1000:
            raise CouncilError("comment must be 1..1000 characters")
        with self.db() as db:
            self._begin(db)
            self._member(db, room, author)
            self._proposal(db, room, prop)
            n = db.execute("SELECT COUNT(*) n FROM comments WHERE proposal=? AND author=?", (prop, author)).fetchone()["n"]
            if n >= 5:
                raise CouncilError("comment limit reached")
            cursor = db.execute("INSERT INTO comments(proposal,room,author,body) VALUES(?,?,?,?)",
                                (prop, room, author, body.strip()))
            self._event(db, room, "comment_added", prop, {"comment_id": cursor.lastrowid})
            db.commit()
            return cursor.lastrowid

    def list_comments(self, room, prop):
        with self.db() as db:
            self._proposal(db, room, prop)
            return [dict(r) for r in db.execute("SELECT id,author,body FROM comments WHERE room=? AND proposal=? ORDER BY id LIMIT 100", (room, prop))]

    def open_ballot(self, room, subject, prop):
        with self.db() as db:
            self._begin(db)
            self._member(db, room, subject)
            row = self._proposal(db, room, prop)
            if row["status"] != "draft":
                raise CouncilError("ballot already opened")
            roster = [r["subject"] for r in db.execute("SELECT subject FROM members WHERE room=?", (room,))]
            if len(roster) < 2:
                raise CouncilError("at least two room members required")
            db.executemany("INSERT INTO electorate VALUES(?,?)", [(prop, s) for s in roster])
            db.execute("UPDATE proposals SET status='voting', closes_at=? WHERE id=?", (int(time.time()) + 86400, prop))
            self._event(db, room, "ballot_open", prop, {"eligible": len(roster)})
            db.commit()

    def vote(self, room, subject, prop, choice):
        if choice not in ("yes", "no"):
            raise CouncilError("vote must be yes or no")
        with self.db() as db:
            self._begin(db)
            self._member(db, room, subject)
            row = self._proposal(db, room, prop)
            if row["status"] != "voting":
                raise CouncilError("ballot not open")
            if not db.execute("SELECT 1 FROM electorate WHERE proposal=? AND subject=?", (prop, subject)).fetchone():
                raise CouncilError("not eligible for this ballot")
            try:
                db.execute("INSERT INTO votes VALUES(?,?,?)", (prop, subject, choice))
            except sqlite3.IntegrityError as exc:
                raise CouncilError("already voted") from exc
            self._event(db, room, "voted", prop, {"choice": choice})
            db.commit()

    def close_ballot(self, room, subject, prop):
        with self.db() as db:
            self._begin(db)
            self._member(db, room, subject)
            row = self._proposal(db, room, prop)
            if row["status"] != "voting":
                raise CouncilError("ballot not open")
            eligible = db.execute("SELECT COUNT(*) n FROM electorate WHERE proposal=?", (prop,)).fetchone()["n"]
            yes = db.execute("SELECT COUNT(*) n FROM votes WHERE proposal=? AND choice='yes'", (prop,)).fetchone()["n"]
            no = db.execute("SELECT COUNT(*) n FROM votes WHERE proposal=? AND choice='no'", (prop,)).fetchone()["n"]
            if yes + no < eligible and time.time() < row["closes_at"]:
                raise CouncilError("ballot remains open until all vote or deadline")
            # Majority of the frozen electorate, not merely those who cast ballots.
            approved = yes > eligible // 2
            status = ("approved_pending_checkpoint" if row["kind"] == "gameplay" else "endorsed_advisory") if approved else "rejected"
            db.execute("UPDATE proposals SET status=? WHERE id=?", (status, prop))
            self._event(db, room, "ballot_closed", prop, {"eligible": eligible, "yes": yes, "no": no, "status": status})
            db.commit()
            return {"status": status, "eligible": eligible, "yes": yes, "no": no}

    def apply(self, room, prop, checkpoint):
        """Call only as authenticated game SERVER at a validated checkpoint."""
        if not isinstance(checkpoint, str) or not 1 <= len(checkpoint) <= 80:
            raise CouncilError("game checkpoint required")
        with self.db() as db:
            self._begin(db)
            row = self._proposal(db, room, prop)
            if row["status"] != "approved_pending_checkpoint" or row["kind"] != "gameplay":
                raise CouncilError("cannot apply non-approved room rule")
            current = db.execute("SELECT version,rules_json FROM rules WHERE room=?", (room,)).fetchone()
            rules = json.loads(current["rules_json"]) if current else {}
            rules.update(validate_change(json.loads(row["change_json"])))
            version = (current["version"] + 1) if current else 1
            db.execute("INSERT INTO rules VALUES(?,?,?) ON CONFLICT(room) DO UPDATE SET version=excluded.version,rules_json=excluded.rules_json", (room, version, _json(rules)))
            db.execute("UPDATE proposals SET status='applied' WHERE id=?", (prop,))
            self._event(db, room, "rule_applied", prop, {"checkpoint": checkpoint, "version": version})
            db.commit()
            return {"version": version, "rules": rules}

    def get_rules(self, room):
        with self.db() as db:
            row = db.execute("SELECT version,rules_json FROM rules WHERE room=?", (room,)).fetchone()
            return {"version": row["version"], "rules": json.loads(row["rules_json"])} if row else {"version": 0, "rules": {}}

    def list_proposals(self, room):
        with self.db() as db:
            return [dict(r) for r in db.execute("SELECT id,author,kind,title,detail,status FROM proposals WHERE room=? ORDER BY id DESC LIMIT 100", (room,))]

    def verify_events(self, room):
        with self.db() as db:
            prev = "0" * 64
            count = 0
            for row in db.execute("SELECT * FROM events WHERE room=? ORDER BY seq", (room,)):
                if row["prev_hash"] != prev or hashlib.sha256((prev + row["payload"]).encode()).hexdigest() != row["digest"]:
                    return {"valid": False, "events": count}
                prev = row["digest"]
                count += 1
            return {"valid": True, "events": count, "head": prev}
