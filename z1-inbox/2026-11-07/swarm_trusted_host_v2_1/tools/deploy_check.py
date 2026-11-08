#!/usr/bin/env python3
"""Out-of-process check of the DEPLOYED tree against the frozen plan. Stdlib only; it loads no module of the package it checks.

In-process pin checks are made by the code being checked: a modified module can delete its own check, and pins.py
defines the table every check reads. This tool is the independent half. The deployer runs it in a SEPARATE process
(python -I) before the writer starts, with the plan hash it was given out of band, and starts nothing on exit 2.

It proves the BYTES on disk match the plan's pins and that nothing else could be loaded in their place. It does not
prove what a running process executes, that this tool itself is genuine (pin its hash separately), or that the host
is honest. Exit 0 = ok, 2 = problems (JSON on stdout either way)."""
import argparse
import hashlib
import json
import os
import stat
import sys

# Copied on purpose from the package pins table (a test asserts the two are equal): this tool must not trust that module.
EXPECTED_FILES = {
    "writer_sha256": "src/writer.py",
    "bridge_sha256": "integration/bridge_v2.py",
    "scorer_sha256": "integration/scoring.py",
    "oracle_sha256": "integration/oracle.py",
    "readback_sha256": "integration/readback.py",
    "service_sha256": "src/service.py",
    "verifier_sha256": "src/verifier.py",
    "pins_sha256": "src/pins.py",
    "responses_sha256": "src/responses.py",
}
# Package initializers run when the package is imported, so they are code. They must be EMPTY (zero bytes).
INITIALIZERS = {"src/__init__.py", "integration/__init__.py"}
# A demo module no pinned module imports (a test asserts that). It is tolerated only because it never loads
# on its own; do not execute it in a deployment.
UNPINNED_PYTHON_OK = {"src/offline_pipe_demo.py"}
CODE_DIRS = ("src", "integration")
BAD_SUFFIXES = (".pyc", ".pyo", ".pth", ".so", ".pyd")
# Top-level directories that may exist next to the code. Anything else (json/, cryptography/ ...) could shadow a
# library whenever the package root is on sys.path. Names starting with "." cannot be imported.
ALLOWED_TOP_DIRS = {"src", "integration", "tests", "tools", "docs", "evidence"}
BAD_TOP_LEVEL = {"sitecustomize.py", "usercustomize.py"}


def _read_regular(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise OSError("not a regular file")
        return handle.read()


def _canonical_sha(value):
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def check(package_root, plan_path, plan_sha256):
    problems = []
    try:
        plan = json.loads(_read_regular(plan_path).decode("utf-8"))
        if _canonical_sha(plan) != plan_sha256:
            problems.append("PLAN_HASH_MISMATCH")
        pins = plan.get("protocol_pins") if isinstance(plan, dict) else None
        if not isinstance(pins, dict):
            problems.append("PLAN_HAS_NO_PINS")
            pins = {}
    except (OSError, ValueError, UnicodeDecodeError, TypeError):
        return {"ok": False, "problems": ["PLAN_UNREADABLE"]}
    for name, rel in sorted(EXPECTED_FILES.items()):
        want = pins.get(name)
        if not isinstance(want, str):
            problems.append("PIN_MISSING_IN_PLAN:" + name)
            continue
        full = os.path.join(package_root, rel)
        try:
            info = os.lstat(full)
        except FileNotFoundError:
            problems.append("MISSING:" + name)
            continue
        if not stat.S_ISREG(info.st_mode):
            problems.append("NOT_A_REGULAR_FILE:" + name)
            continue
        try:
            got = hashlib.sha256(_read_regular(full)).hexdigest()
        except OSError:
            problems.append("NOT_A_REGULAR_FILE:" + name)
            continue
        if got != want:
            problems.append("HASH_MISMATCH:" + name)
    # lstat does not follow the LAST component only, so a symlinked src/ or integration/ would let every file under it
    # hash correctly while living somewhere else. The code roots, and the path we were given, must be real directories.
    if os.path.realpath(package_root) != os.path.abspath(package_root):
        problems.append("PACKAGE_ROOT_NOT_CANONICAL")
    for code_dir in CODE_DIRS:
        if os.path.islink(os.path.join(package_root, code_dir)):
            problems.append("SYMLINK_PRESENT:" + code_dir)
    pinned_paths = set(EXPECTED_FILES.values())
    for top in sorted(os.listdir(package_root)) if os.path.isdir(package_root) else []:
        if top in BAD_TOP_LEVEL or top.endswith(".py"):
            problems.append("UNEXPECTED_PYTHON_FILE:" + top)
        elif top == "__pycache__" or top.endswith((".pyc", ".pyo")):
            problems.append("BYTECODE_PRESENT:" + top)  # a top-level src.pyc can win the import of "src"
        elif top.endswith((".so", ".pyd", ".pth")):
            problems.append("LOADABLE_FILE_PRESENT:" + top)
        elif (os.path.isdir(os.path.join(package_root, top)) or os.path.islink(os.path.join(package_root, top))) \
                and top not in ALLOWED_TOP_DIRS and not top.startswith("."):
            problems.append("UNEXPECTED_TOP_LEVEL_DIR:" + top)
    for rel in sorted(INITIALIZERS):
        # Without src/__init__.py the name "src" can resolve to a sibling module or a namespace package instead.
        if not os.path.lexists(os.path.join(package_root, rel)):
            problems.append("MISSING_INITIALIZER:" + rel)
    for code_dir in CODE_DIRS:
        base = os.path.join(package_root, code_dir)
        if os.path.islink(base):
            continue  # already reported; os.walk would follow a symlink given as its starting point
        for current, dirs, files in os.walk(base, followlinks=False):
            for entry in list(dirs) + files:
                full = os.path.join(current, entry)
                rel = os.path.relpath(full, package_root).replace(os.sep, "/")
                if os.path.islink(full):
                    problems.append("SYMLINK_PRESENT:" + rel)
                elif entry == "__pycache__" or entry.endswith(BAD_SUFFIXES):
                    problems.append("BYTECODE_PRESENT:" + rel if entry == "__pycache__" or entry.endswith((".pyc", ".pyo"))
                                    else "LOADABLE_FILE_PRESENT:" + rel)
                elif rel in INITIALIZERS:
                    try:
                        if _read_regular(full) != b"":
                            problems.append("INITIALIZER_NOT_EMPTY:" + rel)
                    except OSError:
                        problems.append("INITIALIZER_NOT_EMPTY:" + rel)
                elif entry.endswith(".py") and rel not in pinned_paths and rel not in UNPINNED_PYTHON_OK:
                    problems.append("UNEXPECTED_PYTHON_FILE:" + rel)
    return {"ok": not problems, "problems": sorted(set(problems))}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check the deployed swarm trusted host tree against the frozen plan")
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args(argv)
    result = check(args.package_root, args.plan, args.plan_sha256)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
