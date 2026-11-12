import unittest
from types import SimpleNamespace

from app import Handler


def request(*, bound="127.0.0.1", peer="127.0.0.1",
            host="127.0.0.1:8766", origin=None):
    headers = {"Host": host}
    if origin is not None:
        headers["Origin"] = origin
    return SimpleNamespace(
        server=SimpleNamespace(server_address=(bound, 8766)),
        client_address=(peer, 8888),
        headers=headers,
    )


class PrivateRouteBoundaryTest(unittest.TestCase):
    def test_local_loopback_is_still_supported(self):
        self.assertTrue(Handler._local_opportunities_allowed(request()))
        self.assertTrue(Handler._local_opportunities_allowed(
            request(origin="http://127.0.0.1:8766")))

    def test_public_server_binding_does_not_enable_private_data(self):
        self.assertFalse(Handler._local_opportunities_allowed(
            request(bound="0.0.0.0")))
        self.assertFalse(Handler._local_opportunities_allowed(
            request(bound="192.168.1.20")))

    def test_nonloopback_phone_peer_cannot_use_private_route(self):
        self.assertFalse(Handler._local_opportunities_allowed(
            request(peer="192.168.1.42")))

    def test_host_and_origin_do_not_override_loopback_policy(self):
        self.assertFalse(Handler._local_opportunities_allowed(
            request(host="public.example:8766")))
        self.assertFalse(Handler._local_opportunities_allowed(
            request(origin="https://public.example")))
        self.assertFalse(Handler._local_opportunities_allowed(
            request(host="127.0.0.1:8766", origin="http://localhost:8771")))


if __name__ == "__main__":
    unittest.main()
