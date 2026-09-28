#!/usr/bin/env python3
"""Build the deterministic public HARC v0.2 trial capsule from ./source."""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
OUTPUT = ROOT / "HARC-v0.2-public.zip"
EXPECTED_SHA256 = "c2284c9be2f0fef6a6b942e6659803e7084bfd1678ab5460ae45547e22d6c463"
FIXED_TIME = (2026, 9, 24, 0, 0, 0)


def main() -> int:
    files = sorted(p for p in SOURCE.rglob("*") if p.is_file())
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            relative = Path("HARC-v0.2") / path.relative_to(SOURCE)
            info = zipfile.ZipInfo(str(relative), date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print(f"files={len(files)}")
    print(f"sha256={digest}")
    print(f"expected={EXPECTED_SHA256}")
    if digest != EXPECTED_SHA256:
        print("ARTIFACT_MISMATCH")
        return 1
    print("ARTIFACT_MATCH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
