"""Offline evidence preservation gate. Does not grant authority or verify remote receipts."""
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

MAX_BYTES = 32 * 1024 * 1024
MAX_FILES = 512
HEX = re.compile(r"[a-f0-9]{64}\Z")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe(name):
    p = PurePosixPath(name)
    require(bool(name) and not p.is_absolute() and ".." not in p.parts
            and "\\" not in name and str(p) == name, "unsafe path: " + name)
    return name


def verify(root):
    root = Path(root)
    receipt = json.loads((root / "baseline_receipt.json").read_text())
    require(receipt["authority_effect"] == "NONE", "authority boundary")
    expected = receipt["archive_sha256"]
    require(HEX.fullmatch(expected), "missing pinned archive digest")
    archive = root / "baseline" / "public_evidence_e0.zip"
    require(not archive.is_symlink() and archive.stat().st_size <= MAX_BYTES, "archive type or size")
    require(sha(archive.read_bytes()) == expected, "archive digest mismatch")
    extracted = root / "baseline" / "public_evidence_e0"
    require(not extracted.is_symlink(), "extracted root symlink")
    files = {}
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        require(len(infos) <= MAX_FILES and sum(i.file_size for i in infos) <= MAX_BYTES, "archive bounds")
        seen = set()
        for i in infos:
            name = safe(i.filename.rstrip("/"))
            require(name not in seen, "duplicate archive entry")
            seen.add(name)
            require(not stat.S_ISLNK(i.external_attr >> 16), "archive symlink")
            require(name == "public_evidence_e0" or name.startswith("public_evidence_e0/"), "archive root")
            if not i.is_dir():
                files[name.split("/", 1)[1]] = z.read(i)
    actual = set()
    for p in extracted.rglob("*"):
        require(not p.is_symlink(), "extracted symlink")
        if p.is_file():
            n = p.relative_to(extracted).as_posix()
            actual.add(n)
            require(n in files and p.stat().st_size == len(files[n]) and p.read_bytes() == files[n], "extracted bytes mismatch: " + n)
    require(actual == set(files), "missing or extra extracted files")
    manifest = {}
    for line in files["MANIFEST.sha256"].decode("utf-8").splitlines():
        h, n = line.split("  ", 1)
        n = safe(n.removeprefix("./"))
        require(HEX.fullmatch(h) and n not in manifest, "invalid manifest entry")
        manifest[n] = h
    require(set(manifest) == set(files) - {"MANIFEST.sha256"}, "manifest coverage mismatch")
    for n, h in manifest.items():
        require(sha(files[n]) == h, "manifest mismatch: " + n)
    return {"local_byte_integrity": "PASS", "archive_sha256": expected,
            "manifest_entries": len(manifest), "extracted_files": len(files),
            "repository_readback": "REQUIRED_SEPARATELY", "authority_effect": "NONE"}


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
    except (OSError, ValueError, KeyError, IndexError, TypeError, zipfile.BadZipFile) as e:
        print("HOLD: " + str(e), file=sys.stderr)
        sys.exit(1)
