#!/usr/bin/env python3
"""Fail-closed E0.3 macOS staging preflight and pinned public-source copy.

No provider, Keychain, network, installation or LaunchAgent action.
The shell owns directory creation; this helper verifies source and destinations,
then copies only the exact bytes it has read and hashed from no-follow FDs.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys

from pilot_rollback_guard import verify_ownership, RollbackRefused

EXPECTED = {
    "CURRENT.md": "d719fc3242fb3b3b2a05e85d2c024c45cb011de5f3291233b835f4e4cf13015e",
    "REGISTERED.md": "da56fc433bb928cc433982055e3d39d3e1dc460873a1de3c1a98c5e6b1f097cc",
    "GOVERNANCE.md": "1c1b76ce91e039301ce45422f6950a5446b3b9927951e2c0322482c4ca8acb2a",
}
MAX_FILE_BYTES = 1024 * 1024


class StagingRefused(RuntimeError):
    """Safety refusal with no secrets or private document bytes in message."""


def destinations(base: Path, home: Path) -> tuple[Path, Path]:
    expected = home / "Library" / "Application Support" / "HumanAIOS"
    if not home.is_absolute() or home.is_symlink() or base != expected:
        raise StagingRefused("Unexpected HOME or pilot destination.")
    for p in (base, *base.parents):
        if p.is_symlink():
            raise StagingRefused("Destination has a symlinked ancestor.")
    return base / "witness-pilot-e03-z1", base / "witness-pilot-e03-context"


def port_idle(run=subprocess.run) -> None:
    args = ["/usr/sbin/lsof", "-nP", "-t", "-iTCP:8768", "-sTCP:LISTEN"]
    try:
        result = run(args, capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise StagingRefused("Port inspection unavailable; no staging allowed.") from None
    out = result.stdout.strip()
    err = result.stderr.strip()
    if result.returncode == 1 and not out and not err:
        return
    if result.returncode == 0 and out and not err and all(x.isdecimal() for x in out.splitlines()):
        raise StagingRefused("Port 8768 is in use; no staging allowed.")
    raise StagingRefused("Port inspection failed or was ambiguous; no staging allowed.")


def read_pinned_documents(root: Path) -> dict[str, bytes]:
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise StagingRefused("Invalid public operations source root.")
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise StagingRefused("No-follow file safety controls unavailable.")
    out: dict[str, bytes] = {}
    try:
        root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for name, expected in EXPECTED.items():
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=root_fd)
                try:
                    info = os.fstat(fd)
                    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
                        raise StagingRefused("Public source is non-regular or oversized.")
                    chunks = []
                    total = 0
                    while True:
                        chunk = os.read(fd, min(65536, MAX_FILE_BYTES + 1 - total))
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_FILE_BYTES:
                            raise StagingRefused("Public source exceeds byte limit.")
                        chunks.append(chunk)
                    payload = b"".join(chunks)
                finally:
                    os.close(fd)
                if hashlib.sha256(payload).hexdigest() != expected:
                    raise StagingRefused("Pinned public document digest mismatch.")
                out[name] = payload
        finally:
            os.close(root_fd)
    except OSError:
        raise StagingRefused("Cannot open pinned public sources safely.") from None
    return out


def preflight(root: Path, base: Path, home: Path, run=subprocess.run) -> None:
    pilot, context = destinations(base, home)
    if pilot.exists() or pilot.is_symlink() or context.exists() or context.is_symlink():
        raise StagingRefused("Pilot folders already exist; refusing overwrite.")
    port_idle(run)
    read_pinned_documents(root)


def copy_public(root: Path, base: Path, home: Path, run=subprocess.run) -> None:
    pilot, context = destinations(base, home)
    # Both stage markers are created only after successful preflight.
    try:
        verify_ownership(pilot, context)
    except RollbackRefused:
        raise StagingRefused("Pilot ownership cannot be verified.") from None
    port_idle(run)
    # Read and digest all source bytes BEFORE writing any destination file.
    # Nothing reopens the original sources after this point.
    pinned = read_pinned_documents(root)
    try:
        folder_fd = os.open(context, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for name, payload in pinned.items():
                fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=folder_fd)
                try:
                    os.fchmod(fd, 0o600)
                    with os.fdopen(fd, "wb", closefd=False) as handle:
                        handle.write(payload)
                        handle.flush()
                    os.fsync(fd)
                finally:
                    os.close(fd)
        finally:
            os.close(folder_fd)
    except OSError:
        raise StagingRefused("Cannot safely write pinned public snapshot; inspect partial staging.") from None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "copy-public"))
    parser.add_argument("root")
    parser.add_argument("base")
    args = parser.parse_args()
    try:
        if sys.platform != "darwin":
            raise StagingRefused("macOS required.")
        home = Path(os.environ["HOME"])
        root, base = Path(args.root), Path(args.base)
        if args.mode == "preflight":
            preflight(root, base, home)
            print("STAGING PREFLIGHT PASS: pinned no-follow sources, destination and port.")
        else:
            copy_public(root, base, home)
            print("PINNED PUBLIC SNAPSHOT COPIED: exact checked bytes only.")
    except (KeyError, StagingRefused) as exc:
        print(f"STAGING REFUSED: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
