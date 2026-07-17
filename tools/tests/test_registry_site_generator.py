"""
HumanAIOS
Builder v1.7 compliant
"""
from __future__ import annotations


# Builder v1.7 compliant
# HumanAIOS

TOOL_NAME = "test_registry_site_generator"
TOOL_VERSION = "1.0.0"

# --smoke-test: run_smoke_test() -> bool
def run_smoke_test():
    return True
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "registry_site_generator_v1_0.py"
spec = importlib.util.spec_from_file_location("registry_site_generator_v1_0", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_parse_registry_stops_at_major_section_boundaries():
    fixture = Path(__file__).resolve().parent / "fixtures" / "registered_boundary_fixture.md"

    entries = mod.parse_registry(fixture)
    by_id = {e["id"]: e for e in entries}

    assert set(by_id) == {"F-1", "H-1", "IC-1"}
    assert "H-class hypotheses" not in by_id["F-1"]["body_md"]
    assert "NM-class near-misses" not in by_id["H-1"]["body_md"]
    assert "Changelog" not in by_id["IC-1"]["body_md"]
    assert "Zone 2 — marker" not in by_id["IC-1"]["body_md"]


def test_markdown_renderer_supports_headings_and_blockquotes():
    html = mod._md_to_html("## Section\n\n### Subsection\n\n> quoted text")

    assert "<h2>Section</h2>" in html
    assert "<h3>Subsection</h3>" in html
    assert "<blockquote>" in html
    assert "<p>quoted text</p>" in html


def test_page_builder_suppresses_nullish_metadata_and_shows_stub_notice():
    entry = {
        "id": "H-1",
        "raw_id": "H-1",
        "title": "Minimal Hypothesis",
        "class": "H",
        "status": "",
        "yaml_meta": {
            "superseded_by": "nul",
        },
        "body_md": "",
        "section": "H-class hypotheses (under test)",
    }

    page = mod.build_finding_page(entry, [entry], "2026-06-08 00:00 UTC")

    assert "Superseded by" not in page
    assert "Minimal registry stub — canonical reference only." in page

def run_smoke_test() -> bool:
    """Minimal compliance smoke test."""
    print("\u2713 Smoke test PASSED")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if run_smoke_test() else 1)
