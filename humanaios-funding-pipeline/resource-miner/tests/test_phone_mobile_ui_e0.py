"""iPhone Home Screen read-only UX and strict private-route contract."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PhonePilotUITest(unittest.TestCase):
    def test_mobile_screen_has_touch_layout_and_home_screen_identity(self):
        for name in ("intent-os.html", "on-track.html", "my-opportunities.html"):
            with self.subTest(name=name):
                html = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn("viewport-fit=cover", html)
                self.assertIn('rel="manifest" href="/app.webmanifest"', html)
                self.assertIn('aria-label="Phone navigation"', html)
                self.assertIn("safe-area-inset-bottom", html)
                self.assertIn("min-height:48px", html)

    def test_public_phone_ui_does_not_offer_private_data_route(self):
        for name in ("intent-os.html", "on-track.html"):
            with self.subTest(name=name):
                html = (ROOT / name).read_text(encoding="utf-8")
                nav = html.split('<nav class="mobile-tabs"', 1)[1].split("</nav>", 1)[0]
                self.assertIn("Private locked", nav)
                self.assertNotIn('href="/my-opportunities"', nav)

    def test_manifest_is_public_identity_only(self):
        manifest = json.loads((ROOT / "app.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["start_url"], "/intent-os")
        self.assertEqual(manifest["display"], "standalone")
        self.assertNotIn("credentials", str(manifest).lower())
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('if parsed.path == "/app.webmanifest":', app)
        self.assertIn("manifest-src 'self'", app)
        self.assertIn("bound.is_loopback and peer.is_loopback", app)


if __name__ == "__main__":
    unittest.main()
