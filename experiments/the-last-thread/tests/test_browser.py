# Optional manual browser check
# pip install playwright; playwright install chromium
# Current sandbox blocks navigation, but HTML injection via page.set_content worked locally.
from pathlib import Path
from playwright.sync_api import sync_playwright
html=Path(__file__).resolve().parents[1].joinpath('PLAY_OFFLINE.html').read_text()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    page.set_content(html)
    page.locator('#newGame').click()
    assert page.locator('#clock').inner_text() == '30'
    page.locator('#actions button').filter(has_text='Rootvault').first.click()
    assert page.locator('#clock').inner_text() == '29'
    browser.close()
print('PASS: local Chromium first action')
