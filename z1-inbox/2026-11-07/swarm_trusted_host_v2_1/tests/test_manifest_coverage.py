"""Follow-up to PR #1153 (CodeRabbit on MANIFEST.sha256): the manifest omitted the evidence/ records, so review claims
about them had no digest binding. The manifest must list EVERY file in the package except itself and build
byproducts, each with its true digest. Written BEFORE the manifest was extended (author-run)."""
import hashlib
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
MANIFEST = PKG / "MANIFEST.sha256"


def entries():
    out = []
    for number, line in enumerate(MANIFEST.read_text().splitlines(), 1):
        digest, sep, name = line.partition("  ")
        out.append((number, digest, name if sep else None))
    return out


def package_files():
    found = set()
    for path in PKG.rglob("*"):
        rel = path.relative_to(PKG).as_posix()
        if path.is_file() and "__pycache__" not in path.parts and not rel.endswith((".pyc", ".pyo")) \
                and rel != "MANIFEST.sha256":
            found.add(rel)
    return found


class ManifestCoversThePackage(unittest.TestCase):
    def test_every_line_is_a_well_formed_entry(self):
        for number, digest, name in entries():
            with self.subTest(line=number):
                self.assertIsNotNone(name, "needs two spaces between digest and path")
                self.assertRegex(digest, r"^[0-9a-f]{64}$")
                self.assertFalse(name.startswith("/") or ".." in Path(name).parts, name)

    def test_no_file_is_listed_twice_and_none_is_missing_from_disk(self):
        names = [name for _, _, name in entries()]
        self.assertEqual(len(names), len(set(names)), "duplicate entries")
        self.assertEqual([n for n in names if not (PKG / n).is_file()], [])

    def test_every_package_file_is_listed(self):
        listed = {name for _, _, name in entries()}
        self.assertEqual(sorted(package_files() - listed), [], "files with no digest binding")
        self.assertEqual(sorted(listed - package_files()), [])

    def test_the_evidence_records_are_bound(self):
        listed = {name for _, _, name in entries()}
        evidence = {p for p in package_files() if p.startswith("evidence/")}
        self.assertTrue(evidence, "expected evidence/ records")
        self.assertEqual(sorted(evidence - listed), [])

    def test_every_digest_matches_the_file(self):
        for number, digest, name in entries():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((PKG / name).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
