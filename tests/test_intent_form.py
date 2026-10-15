"""Checks for ui/intent-form.html: template parity, no network, valid JS."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FORM = ROOT / "ui" / "intent-form.html"
TEMPLATE = ROOT / "intent.md"


def _form() -> str:
    return FORM.read_text(encoding="utf-8")


def _template_headings() -> list[str]:
    return [line[3:].strip() for line in TEMPLATE.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")]


def test_form_exists():
    assert FORM.is_file()


def test_form_emits_every_template_heading_in_order():
    src = _form()
    pos = [src.find("## " + h) for h in _template_headings()]
    assert all(p >= 0 for p in pos), "missing heading in form output"
    assert pos == sorted(pos), "heading order differs from intent.md"


def test_form_makes_no_network_calls():
    src = _form()
    for pattern in [r"<script[^>]*\bsrc=", r"<link[^>]*href=\"http", r"\bfetch\s*\(",
                    r"XMLHttpRequest", r"sendBeacon", r"WebSocket"]:
        assert not re.search(pattern, src), pattern


def test_form_never_signs_or_submits():
    src = _form()
    assert "Signature: none" in src
    assert "Submitted: not yet" in src
    assert "Ed25519" not in src.split("<script>")[1]


def test_form_requires_falsifier_and_bounded_smag():
    src = _form()
    assert "A falsifier is required" in src
    assert "Enter a number from 0 to 1." in src


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_form_script_parses():
    src = _form()
    script = src.split("<script>", 1)[1].split("</script>", 1)[0]
    tmp = ROOT / "tests" / ".tmp_intent_form.js"
    tmp.write_text(script, encoding="utf-8")
    try:
        result = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    finally:
        tmp.unlink(missing_ok=True)
    assert result.returncode == 0, result.stderr
