"""Fail-closed tests for the GitHub-signed SCVC witness identity contract."""
import base64
import json
import os
import unittest
from unittest.mock import patch

from experiments.scvc_v02 import oidc_identity as oidc


def part(value):
    raw = json.dumps(value, sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


class OidcNegativeTests(unittest.TestCase):
    def setUp(self):
        self.context = {"checkout_sha": "a" * 40, "run_id": 555, "run_attempt": 1}
        self.header = {"alg": "none", "kid": "unknown"}
        self.payload = {"iss": oidc.ISSUER, "aud": oidc.AUDIENCE}

    def supplied(self):
        return part(self.header) + "." + part(self.payload) + ".AA"

    def test_unsigned_algorithm_rejected(self):
        with self.assertRaises(oidc.IdentityError):
            oidc.verify_token(self.supplied(), {"keys": []}, self.context)

    def test_incomplete_token_rejected(self):
        with self.assertRaises(oidc.IdentityError):
            oidc.verify_token("not-a-token", {"keys": []}, self.context)

    def test_unrecognized_key_rejected(self):
        self.header["alg"] = "RS256"
        with self.assertRaises(oidc.IdentityError):
            oidc.verify_token(self.supplied(), {"keys": []}, self.context)

    def test_bad_jwks_rejected(self):
        self.header["alg"] = "RS256"
        with self.assertRaises(oidc.IdentityError):
            oidc.verify_token(self.supplied(), {"keys": "not-a-list"}, self.context)

    def test_no_oidc_permission_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(oidc.IdentityError):
                oidc.verify_current_workflow(self.context)

    def test_token_request_url_cannot_be_untrusted_host(self):
        with self.assertRaises(oidc.IdentityError):
            oidc._get_json("https://example.com/tokens", bearer="synthetic")

    def test_jwks_url_pinned(self):
        with self.assertRaises(oidc.IdentityError):
            oidc._get_json("https://example.com/keys")


if __name__ == "__main__":
    unittest.main()
