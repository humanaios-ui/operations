"""Browser-level checks for ui/intent-form.html: render, draft restore, download, clear.

Skipped unless Playwright and a Chromium build are available. The Node-based checks in
test_intent_form.py cover build() without a browser.
"""
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FORM = (ROOT / "ui" / "intent-form.html").as_uri()

sync_api = pytest.importorskip("playwright.sync_api", reason="playwright not installed")


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        # INTENT_FORM_CHROMIUM overrides Playwright's bundled build (used on machines with a preinstalled browser).
        exe = os.environ.get("INTENT_FORM_CHROMIUM") or None
        if exe:
            # An explicit override must launch. A bad path fails the run instead of skipping it.
            b = p.chromium.launch(executable_path=exe)
        else:
            try:
                b = p.chromium.launch()
            except Exception as exc:  # optional bundled browser not installed
                # GitHub Actions sets CI=true; there a missing browser is a failure, not a skip.
                if os.environ.get("CI"):
                    pytest.fail(f"bundled chromium missing in CI: {exc}")
                pytest.skip(f"bundled chromium not available: {exc}")
        yield b
        b.close()


@pytest.fixture()
def page(browser):
    ctx = browser.new_context(accept_downloads=True)
    pg = ctx.new_page()
    pg.goto(FORM)
    yield pg
    ctx.close()


def _fill_valid(pg):
    pg.fill("#name", "Browser intent")
    pg.fill("#author", "Carly")
    pg.fill("#problem", "Ops need a form.")
    pg.fill("#outcome", "A draft file.")
    pg.fill("#falsifier", "If the draft is not parsed, this fails.")
    pg.fill("#smag", "0.72")


def test_preview_updates_and_buttons_enable(page):
    assert page.is_disabled("#copy")
    assert page.is_disabled("#download")
    _fill_valid(page)
    assert page.is_enabled("#copy")
    assert page.is_enabled("#download")
    assert "`smag_p: 0.72`" in page.text_content("#out")


def test_empty_falsifier_shows_error_and_disables(page):
    _fill_valid(page)
    page.fill("#falsifier", "")
    assert "A falsifier is required" in page.text_content("#err-falsifier")
    assert page.get_attribute("#falsifier", "aria-invalid") == "true"
    assert page.is_disabled("#download")


def test_download_writes_markdown_file(page, tmp_path):
    _fill_valid(page)
    with page.expect_download() as info:
        page.click("#download")
    dl = info.value
    assert dl.suggested_filename == "intent-browser-intent.md"
    dl.save_as(tmp_path / dl.suggested_filename)
    text = (tmp_path / dl.suggested_filename).read_text(encoding="utf-8")
    assert "# Intent: Browser intent" in text
    assert "Signature: none" in text
    assert "Submitted: not yet" in text


def test_draft_restores_after_reload(page):
    _fill_valid(page)
    page.check("input[name=calib][value=revise]")
    page.reload()
    assert page.input_value("#name") == "Browser intent"
    assert page.input_value("#smag") == "0.72"
    assert page.is_checked("input[name=calib][value=revise]")
    assert page.is_enabled("#copy")


def test_clear_resets_fields_and_draft(page):
    _fill_valid(page)
    page.click("#clear")
    assert page.input_value("#name") == ""
    assert page.input_value("#smag") == ""
    page.reload()
    assert page.input_value("#name") == ""
    assert page.is_disabled("#copy")


def test_status_announces_ready(page):
    _fill_valid(page)
    assert re.search(r"Ready\. Draft, unsigned\.", page.text_content("#status"))
