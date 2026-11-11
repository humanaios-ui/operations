"""Strict, versioned, claim-only contracts; no free-form research/event payloads."""
import json
import math
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

class ValidationError(ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]

def validate(kind, record):
    path = ROOT / ('ui_contract' if kind in {'action_card', 'resource_card', 'checkin'} else 'schemas') / f'{kind}.schema.json'
    schema = json.loads(path.read_text())
    _validate(schema, record)
    return record

def _validate(schema, value):
    """Validate the closed subset used by these contracts, using only stdlib.

    Published schemas remain Draft 2020-12 for independent consumer validation.
    This is not a general-purpose JSON Schema implementation.
    """
    types = schema.get('type', [])
    types = [types] if isinstance(types, str) else types
    matches = {'object': isinstance(value, dict), 'array': isinstance(value, list),
               'string': isinstance(value, str), 'boolean': isinstance(value, bool),
               'null': value is None, 'number': type(value) in (int, float) and math.isfinite(value)}
    if types and not any(matches[t] for t in types):
        raise ValidationError('invalid value type')
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']):
        # JSON numbers compare numerically (0 and 0.0), but booleans do not.
        if not (type(value) in (int, float) and type(schema['const']) in (int, float) and value == schema['const']):
            raise ValidationError('constant mismatch')
    if 'enum' in schema and value not in schema['enum']:
        raise ValidationError('unknown enumeration')
    if isinstance(value, dict):
        props = schema.get('properties', {})
        if any(k not in value for k in schema.get('required', [])):
            raise ValidationError('required field missing')
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ValidationError('unexpected field')
        for key, item in value.items():
            if key in props:
                _validate(props[key], item)
    if isinstance(value, list):
        if schema.get('uniqueItems') and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            raise ValidationError('duplicate item')
        for item in value:
            _validate(schema.get('items', {}), item)
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or ('pattern' in schema and not re.search(schema['pattern'], value)):
            raise ValidationError('invalid string')
        try:
            fmt = schema.get('format')
            if fmt == 'uri' and (not urlsplit(value).scheme or any(c.isspace() for c in value)):
                raise ValueError('absolute URI required')
            if fmt == 'date':
                date.fromisoformat(value)
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                    raise ValueError('invalid date')
            if fmt == 'date-time' and datetime.fromisoformat(value.replace('Z', '+00:00')).tzinfo is None:
                raise ValueError('timezone required')
        except ValueError as error:
            raise ValidationError('invalid format') from error
    if type(value) in (int, float) and (value < schema.get('minimum', -math.inf) or value > schema.get('maximum', math.inf)):
        raise ValidationError('out of range')
    for constraint in schema.get('allOf', []):
        try:
            _validate(constraint['if'], value)
        except ValidationError:
            continue
        _validate(constraint['then'], value)
