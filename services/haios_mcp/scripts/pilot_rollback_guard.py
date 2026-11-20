#!/usr/bin/env python3
"""Conservative macOS E0.3 pilot rollback pre-deletion guard.

The pilot is an isolated review copy, not a service to modify in place.
This tool never deletes files, starts services, reads Keychain or calls providers.
It checks two exact ownership markers and refuses rollback whenever process
inspection is unavailable or ANY possible pilot/Witness process remains.
"""
from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Callable

MARKER = '.witness-pilot-e03-z1'
PILOT_TEXT = b'E0.3 Witness pilot, not released\n'
CONTEXT_TEXT = b'E0.3 Witness public context snapshot\n'


class RollbackRefused(RuntimeError):
    """Fail-closed rollback refusal; never expose command/process details."""


def pilot_paths(home: Path) -> tuple[Path, Path]:
    base = home / 'Library' / 'Application Support' / 'HumanAIOS'
    return base / 'witness-pilot-e03-z1', base / 'witness-pilot-e03-context'


def verify_ownership(pilot: Path, context: Path) -> None:
    """Reject path redirects and non-owned folders before any remove action."""
    if pilot.parent != context.parent:
        raise RollbackRefused('Pilot paths do not share the expected parent.')
    for folder, expected_name, text in (
        (pilot, 'witness-pilot-e03-z1', PILOT_TEXT),
        (context, 'witness-pilot-e03-context', CONTEXT_TEXT),
    ):
        if folder.name != expected_name:
            raise RollbackRefused('Unexpected pilot folder name.')
        # Parent components must not redirect to an unrelated destination.
        for component in (folder, *folder.parents):
            if component.is_symlink():
                raise RollbackRefused('Pilot path contains a symlink; refusing rollback.')
        if not folder.is_dir():
            raise RollbackRefused('Pilot folder is missing or is not a directory.')
        marker = folder / MARKER
        if marker.is_symlink() or not marker.is_file():
            raise RollbackRefused('Pilot ownership marker missing or linked.')
        if not hasattr(os, 'O_NOFOLLOW'):
            raise RollbackRefused('No-follow marker check unavailable.')
        try:
            fd = os.open(marker, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode) or os.read(fd, 256) != text:
                    raise RollbackRefused('Pilot ownership marker contents do not match.')
            finally:
                os.close(fd)
        except OSError:
            raise RollbackRefused('Pilot marker cannot be read safely.') from None


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=20,
                              check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise RollbackRefused('Process inspection unavailable; nothing removed.') from None


def _lsof_pids(args: list[str], run: Callable = run_command) -> set[int]:
    result = run(args)
    # lsof exit 1 with no stdout and no stderr means no matches. An error or
    # partial listing must never be taken as proof that the pilot is idle.
    if result.returncode not in (0, 1) or result.stderr.strip():
        raise RollbackRefused('lsof could not establish a clean process state.')
    pids = set()
    for line in result.stdout.splitlines():
        value = line.strip()
        if not value.isdecimal():
            raise RollbackRefused('Unexpected lsof output; refusing rollback.')
        pids.add(int(value))
    return pids


def _ps_hits(output: str, pilot: Path, context: Path, ignored: set[int] | None = None) -> set[int]:
    matches = set()
    ignored = ignored or set()
    rows = output.splitlines()
    if not rows:
        raise RollbackRefused('Empty process listing; refusing rollback.')
    exact_paths = (str(pilot), str(context))
    # A running MCP process started with PYTHONPATH but no pilot path in its
    # command is still blocked by the service/module name. Intentionally broad.
    witness_names = ('haios_mcp', 'haios-mcp')
    for line in rows:
        m = re.match(r'^\s*(\d+)\s+(.+)$', line)
        if m is None:
            raise RollbackRefused('Malformed process listing; refusing rollback.')
        pid, command = int(m.group(1)), m.group(2)
        if pid in ignored:
            continue  # this guard and its invoking rollback shell are expected
        if any(path in command for path in exact_paths) or any(name in command for name in witness_names):
            matches.add(pid)
    return matches


def require_idle(pilot: Path, context: Path, run: Callable = run_command) -> None:
    """Check file/cwd access and command lines, independent of listening port."""
    # Fail closed if another program listens on legacy port; do NOT rely on it.
    for args in (
        ['/usr/sbin/lsof', '-nP', '-t', '-iTCP:8768', '-sTCP:LISTEN'],
        ['/usr/sbin/lsof', '-nP', '-t', '+D', str(pilot)],
        ['/usr/sbin/lsof', '-nP', '-t', '+D', str(context)],
    ):
        if _lsof_pids(args, run):
            raise RollbackRefused('Pilot or service process is active; nothing removed.')
    result = run(['/bin/ps', '-Aww', '-o', 'pid=', '-o', 'command='])
    if result.returncode != 0 or result.stderr.strip():
        raise RollbackRefused('Process listing unavailable; nothing removed.')
    if _ps_hits(result.stdout, pilot, context, {os.getpid(), os.getppid()}):
        raise RollbackRefused('Possible Witness process is active; nothing removed.')


def check(home: Path, run: Callable = run_command) -> None:
    pilot, context = pilot_paths(home)
    verify_ownership(pilot, context)
    require_idle(pilot, context, run)


def main() -> int:
    try:
        if sys.platform != 'darwin':
            raise RollbackRefused('macOS required; nothing removed.')
        home = Path(os.environ['HOME'])
        if not home.is_absolute() or home.is_symlink():
            raise RollbackRefused('Invalid HOME; nothing removed.')
        check(home)
    except (KeyError, RollbackRefused) as exc:
        print(f'ROLLBACK REFUSED: {exc}', file=sys.stderr)
        return 3
    print('ROLLBACK CHECK PASS: ownership markers match; no detected pilot process.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
