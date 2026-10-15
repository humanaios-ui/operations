"""Checks for ui/intent-form.html: template parity, no network, behavior of build()."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FORM = ROOT / "ui" / "intent-form.html"
TEMPLATE = ROOT / "intent.md"

# Minimal DOM stub: enough for the form script to load and call build() under Node.
HARNESS = r"""
const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");
const script = src.split("<script>")[1].split("</script>")[0];
const el = () => ({ value: "", textContent: "", className: "", disabled: false,
  setAttribute() {}, addEventListener() {}, appendChild() {}, remove() {}, focus() {} });
globalThis.window = globalThis;
globalThis.document = { getElementById: el, querySelector: () => null,
  querySelectorAll: () => [], createElement: el, body: { appendChild() {} } };
globalThis.localStorage = { getItem: () => null, setItem() {}, removeItem() {} };
eval(script);
const base = { name: "n", author: "a", problem: "p", outcome: "o", affected: "",
  constraints: "", questions: "", falsifier: "f", smag: "0.5", calib: "" };
const cases = {
  valid: { ...base },
  boundary_zero: { ...base, smag: "0" },
  boundary_one: { ...base, smag: "1" },
  empty_falsifier: { ...base, falsifier: "   " },
  smag_negative: { ...base, smag: "-0.1" },
  smag_over_one: { ...base, smag: "1.5" },
  smag_blank: { ...base, smag: "" },
  smag_text: { ...base, smag: "abc" },
};
const out = {};
for (const [k, d] of Object.entries(cases)) {
  const r = window.intentForm.build(d);
  out[k] = { ok: r.ok, errors: Object.keys(r.errors).sort(), md: r.md };
}
process.stdout.write(JSON.stringify(out));
"""


def _form() -> str:
    return FORM.read_text(encoding="utf-8")


def _template_headings() -> list[str]:
    return [line[3:].strip() for line in TEMPLATE.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")]


@pytest.fixture(scope="module")
def built():
    if shutil.which("node") is None:
        pytest.skip("node not installed")
    harness = ROOT / "tests" / ".tmp_intent_form_harness.js"
    harness.write_text(HARNESS, encoding="utf-8")
    try:
        result = subprocess.run(["node", str(harness), str(FORM)],
                                capture_output=True, text=True, timeout=30)
    finally:
        harness.unlink(missing_ok=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


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


def test_status_span_is_live_region():
    assert 'id="status" role="status" aria-live="polite"' in _form()


def test_valid_draft_is_ok(built):
    assert built["valid"]["ok"] is True
    assert built["valid"]["errors"] == []


@pytest.mark.parametrize("case", ["boundary_zero", "boundary_one"])
def test_smag_bounds_are_inclusive(built, case):
    assert built[case]["ok"] is True
    assert built[case]["errors"] == []


def test_zero_smag_renders_as_zero(built):
    assert "`smag_p: 0`" in built["boundary_zero"]["md"]


def test_empty_falsifier_blocks_draft(built):
    assert built["empty_falsifier"]["ok"] is False
    assert built["empty_falsifier"]["errors"] == ["falsifier"]


@pytest.mark.parametrize("case", ["smag_negative", "smag_over_one", "smag_blank", "smag_text"])
def test_out_of_range_or_missing_smag_blocks_draft(built, case):
    assert built[case]["ok"] is False
    assert built[case]["errors"] == ["smag"]
    assert "`smag_p: [0..1]`" in built[case]["md"]
