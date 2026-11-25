#!/usr/bin/env python3
"""CORRECTED owned application wrapper: SQLite atomicity and finite numeric gates.

Runs actual CPython + native SQLite. No changes to either engine and no network.
"""
import json
import math
import sqlite3
import sys


def evaluate(req):
    operation = req['operation']
    if operation == 'transfer':
        db = sqlite3.connect(':memory:', isolation_level=None)
        db.executescript('CREATE TABLE accounts (id TEXT PRIMARY KEY, balance INTEGER);'
                         "INSERT INTO accounts VALUES('A', 100);"
                         "INSERT INTO accounts VALUES('B', 0);")
        db.execute('BEGIN')
        try:
            db.execute("UPDATE accounts SET balance=balance-10 WHERE id='A'")
            if req['scenario'] == 'partial_failure':
                db.execute("UPDATE missing_account_table SET balance=balance+10 WHERE id='B'")
            else:
                db.execute("UPDATE accounts SET balance=balance+10 WHERE id='B'")
            db.execute('COMMIT')
        except sqlite3.Error:
            db.execute('ROLLBACK')  # FIX: preserve the balance invariant
        total = db.execute('SELECT SUM(balance) FROM accounts').fetchone()[0]
        return {'ok': True, 'status': 'OK', 'metrics': {'total': total}}
    if operation in ('quantity', 'finite'):
        value = req['value']
        if type(value) not in (float, int) or not math.isfinite(value):
            return {'ok': False, 'status': 'REFUSED', 'reason': 'finite numeric input required'}
        key = 'amount' if operation == 'quantity' else 'measurement'
        return {'ok': True, 'status': 'OK', 'metrics': {key: value}}
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
