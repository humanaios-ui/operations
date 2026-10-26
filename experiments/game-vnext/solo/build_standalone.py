"""Build a single-file offline edition from repaired, first-party modular sources.
No network, no external scripts, no model calls.
"""
from pathlib import Path
import re
root=Path(__file__).resolve().parent
html=(root/'index.html').read_text(encoding='utf-8')
css=(root/'style.css').read_text(encoding='utf-8')
engine=(root/'engine.mjs').read_text(encoding='utf-8')
ui=(root/'ui.mjs').read_text(encoding='utf-8')
match=re.search(r"^import\s+\{[^}]+\}\s+from\s+'\./engine\.mjs';\s*",ui,re.MULTILINE)
assert match, 'modular UI import not found'
ui=ui[:match.start()]+ui[match.end():]
engine=re.sub(r'\bexport (const|function)\b',r'\1',engine)
link='<link rel="stylesheet" href="style.css">'
script='<script type="module" src="ui.mjs"></script>'
assert link in html and script in html
html=html.replace(link,'<style>'+css+'</style>',1)
html=html.replace(script,'<script>'+engine+'\n'+ui+'</script>',1)
assert 'src="ui.mjs"' not in html and 'href="style.css"' not in html
out=root/'PLAY_OFFLINE.html'
out.write_text(html,encoding='utf-8')
print(f'Built {out.name}: {out.stat().st_size} bytes')
