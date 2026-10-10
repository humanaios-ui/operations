"""GitHub OIDC identity verifier for the SCVC default-branch witness job.

Authenticates the *workflow execution identity*, not the correctness of its
output, repository governance authorization, or an artifact's authorship.
No candidate-provided bearer/JWKS/URL is accepted by the production CLI.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import os
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

AUDIENCE = "humanaios:scvc-witness:v0.2"
ISSUER = "https://token.actions.githubusercontent.com"
JWKS_URL = "https://token.actions.githubusercontent.com/.well-known/jwks"
REPO = "humanaios-ui/operations"
WORKFLOW_REF = "humanaios-ui/operations/.github/workflows/scvc-milestone-witness.yml@refs/heads/main"


class IdentityError(Exception):
    """OIDC issuer, signature, temporal or workflow identity is not established."""


def require(condition, code):
    if not condition:
        raise IdentityError(code)


def _decode(token_part):
    require(isinstance(token_part, str) and 0 < len(token_part) < 12000,
            "INVALID_JWT_PART")
    try:
        return base64.urlsafe_b64decode(token_part + "=" * (-len(token_part) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise IdentityError("INVALID_BASE64") from exc


def verify_token(jwt, jwks, ctx, *, now=None):
    """Verify GitHub-signed RS256 JWT against issuer JWKS and exact run claims."""
    require(isinstance(jwt, str) and len(jwt) < 15000
            and jwt.count(".") == 2, "MALFORMED_JWT")
    h, p, sig = jwt.split(".")
    try:
        header = json.loads(_decode(h))
        claims = json.loads(_decode(p))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise IdentityError("MALFORMED_JWT_JSON") from exc
    require(isinstance(header, dict) and isinstance(claims, dict), "INVALID_JWT_STRUCTURE")
    require(header.get("alg") == "RS256" and isinstance(header.get("kid"), str),
            "UNSUPPORTED_JWT_ALGORITHM")
    require(isinstance(jwks, dict) and isinstance(jwks.get("keys"), list)
            and len(jwks["keys"]) <= 50, "MALFORMED_GITHUB_JWKS")
    keys = [k for k in jwks["keys"] if isinstance(k, dict) and
            k.get("kid") == header["kid"] and k.get("kty") == "RSA" and
            k.get("use") in ("sig", None)]
    require(len(keys) == 1, "UNTRUSTED_JWT_KEY_ID")
    try:
        n = int.from_bytes(_decode(keys[0]["n"]), "big")
        e = int.from_bytes(_decode(keys[0]["e"]), "big")
        require(e == 65537 and n.bit_length() >= 2048, "WEAK_JWT_RSA_KEY")
        pubkey = rsa.RSAPublicNumbers(e=e, n=n).public_key()
        pubkey.verify(_decode(sig), (h + "." + p).encode("ascii"),
                      padding.PKCS1v15(), hashes.SHA256())
    except (ValueError, TypeError, KeyError, InvalidSignature) as exc:
        raise IdentityError("OIDC_SIGNATURE_INVALID") from exc

    moment = datetime.now(timezone.utc).timestamp() if now is None else now
    try:
        exp = claims["exp"]
        iat = claims["iat"]
        nbf = claims.get("nbf", iat)
        require(all(type(x) is int for x in (exp, iat, nbf)), "INVALID_JWT_TIMES")
        require(iat - 60 <= moment <= exp + 30 and moment + 60 >= nbf,
                "EXPIRED_OR_FUTURE_JWT")
        require(exp - iat <= 900, "OIDC_TOKEN_LIFETIME_TOO_LONG")
        require(claims["iss"] == ISSUER and claims["aud"] == AUDIENCE,
                "OIDC_ISSUER_OR_AUDIENCE_MISMATCH")
        require(claims["repository"] == REPO
                and claims["ref"] == "refs/heads/main"
                and claims["sub"] == "repo:humanaios-ui/operations:ref:refs/heads/main"
                and claims["workflow_ref"] == WORKFLOW_REF,
                "OIDC_REPOSITORY_OR_WORKFLOW_MISMATCH")
        require(claims["sha"] == ctx["checkout_sha"]
                and claims["run_id"] == str(ctx["run_id"])
                and claims["run_attempt"] == str(ctx["run_attempt"]),
                "OIDC_EXACT_RUN_CONTEXT_MISMATCH")
    except (KeyError, ValueError, TypeError) as exc:
        raise IdentityError("OIDC_CLAIMS_MISSING_OR_INVALID") from exc
    return {
        "identity_verified": True, "issuer": ISSUER,
        "audience": AUDIENCE, "workflow_ref": WORKFLOW_REF,
        "run_id": ctx["run_id"], "run_attempt": ctx["run_attempt"],
        "subject_head_sha": ctx["checkout_sha"],
        "jwt_kid": header["kid"],
    }


def _get_json(url, *, bearer=None):
    parsed = urlparse(url)
    if bearer:
        require(parsed.scheme == "https" and parsed.hostname in (
            "pipelines.actions.githubusercontent.com",
            "token.actions.githubusercontent.com"), "OIDC_REQUEST_URL_UNTRUSTED")
    else:
        require(url == JWKS_URL, "JWKS_URL_UNTRUSTED")
    headers = {"Accept": "application/json", "User-Agent": "humanaios-scvc-oidc"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    req = Request(url, headers=headers)
    with urlopen(req, timeout=15) as response:
        payload = response.read(160000)
    require(len(payload) < 160000, "OIDC_RESPONSE_OVERSIZE")
    return json.loads(payload)


def verify_current_workflow(ctx, *, request_json=_get_json):
    """Request a short-lived GitHub OIDC identity and verify issuer signature."""
    url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    require(url and token, "OIDC_PERMISSION_MISSING")
    sep = "&" if "?" in url else "?"
    raw = request_json(url + sep + urlencode({"audience": AUDIENCE}), bearer=token)
    require(isinstance(raw, dict) and isinstance(raw.get("value"), str),
            "OIDC_TOKEN_REQUEST_FAILED")
    jwks = request_json(JWKS_URL)
    return verify_token(raw["value"], jwks, ctx)
