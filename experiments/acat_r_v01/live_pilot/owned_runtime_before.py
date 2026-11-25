#!/usr/bin/env python3
"""KNOWN-FAULT CONTROL: deliberately flawed transaction and numeric input layer.

Runs actual CPython + native SQLite; faults are in THIS OWNED SCRIPT,
not in CPython/SQLite. No network, only in-memory databases.
"""
import json
import sqlite3
import sys


def evaluate(req):
    operation = req['operation']
    if operation == 'transfer':
        db = sqlite3.connect(':memory:', isolation_level=None)  # AUTOCOMMIT BUG
        db.executescript('CREATE TABLE accounts (id TEXT PRIMARY KEY, balance INTEGER);'
                         "INSERT INTO accounts VALUES('A', 100);"
                         "INSERT INTO accounts VALUES('B', 0);")
        db.execute("UPDATE accounts SET balance=balance-10 WHERE id='A'")
        try:
            if req['scenario'] == 'partial_failure':
                db.execute("UPDATE missing_account_table SET balance=balance+10 WHERE id='B'")
            else:
                db.execute("UPDATE accounts SET balance=balance+10 WHERE id='B'")
        except sqlite3.Error:
            pass  # BUG: first UPDATE is already committed
        total = db.execute('SELECT SUM(balance) FROM accounts').fetchone()[0]
        return {'ok': True, 'status': 'OK', 'metrics': {'total': total}}
    if operation == 'quantity':
        value = float(req['value'])  # BUG: silently accepts numeric strings
        return {'ok': True, 'status': 'OK', 'metrics': {'amount': value}}
    if operation == 'finite':
        value = float(req['value'])  # BUG: silently accepts nonfinite strings
        out = 'NaN' if value != value else value
        return {'ok': True, 'status': 'OK', 'metrics': {'measurement': out}}
    if operation == 'unique':
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE items (code TEXT UNIQUE NOT NULL)')
        db.execute("INSERT INTO items VALUES ('A')")
        try:
            db.execute('INSERT INTO items VALUES (?)', (req['code'],))
        except sqlite3.IntegrityError:
            return {'ok': False, 'status': 'REFUSED', 'reason': 'unique constraint'}
        return {'ok': True, 'status': 'OK', 'metrics': {
            'count': db.execute('SELECT COUNT(*) FROM items').fetchone()[0]}}
    return {'ok': False, 'status': 'REFUSED', 'reason': 'unsupported operation'}


if __name__ == '__main__':
    request = json.load(sys.stdin)
    try:
        result = evaluate(request)
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        result = {'ok': False, 'status': 'REFUSED', 'reason': type(exc).__name__}
    print(json.dumps(result, sort_keys=True, allow_nan=False))
