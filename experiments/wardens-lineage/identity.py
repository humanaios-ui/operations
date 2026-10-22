"""Short-lived first-party identity assertion; server-to-server trust boundary.

This helper is ONLY for a trusted game auth service, never exposed as an endpoint.
Production should use the platform's existing OIDC/JWKS issuer instead of HMAC.
"""
import base64
import hashlib
import hmac
import json
import time

class AuthError(ValueError):
    pass


def _b64(b):
    return base64.urlsafe_b64encode(b).decode().rstrip('=')


def issue(secret, subject, seconds=300):
    if not secret or len(secret)<32 or not subject or len(subject)>160:
        raise AuthError('invalid assertion configuration')
    body=_b64(json.dumps({'aud':'wardens-lineage','iss':'trusted-game-auth','sub':subject,'exp':int(time.time())+seconds},sort_keys=True,separators=(',',':')).encode())
    sig=_b64(hmac.new(secret.encode(),body.encode(),hashlib.sha256).digest())
    return body+'.'+sig


def verify(secret,token):
    try:
        body,signature=token.split('.')
        expected=_b64(hmac.new(secret.encode(),body.encode(),hashlib.sha256).digest())
        if not hmac.compare_digest(expected,signature):
            raise AuthError('invalid assertion')
        claims=json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
        if claims.get('aud')!='wardens-lineage' or claims.get('iss')!='trusted-game-auth' or type(claims.get('exp')) is not int or claims['exp']<=time.time() or not isinstance(claims.get('sub'),str) or not 1<=len(claims['sub'])<=160:
            raise AuthError('invalid assertion')
        return claims['sub']
    except (ValueError,TypeError,KeyError,UnicodeDecodeError) as ex:
        raise AuthError('invalid assertion') from ex
