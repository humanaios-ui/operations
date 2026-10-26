"""Produce a no-network single HTML file from checked-in R2 source."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent
html=(root/'index.html').read_text(encoding='utf-8')
css=(root/'style.css').read_text(encoding='utf-8')
engine=(root/'engine.mjs').read_text(encoding='utf-8')
ui=(root/'ui.mjs').read_text(encoding='utf-8')
ui=re.sub(r"^import\s+\{[^}]+\}\s+from\s+'\./engine\.mjs';\s*",'',ui,count=1,flags=re.MULTILINE)
engine=re.sub(r'\bexport (const|function)\b',r'\1',engine)
assert ui.startswith('const KEY=')
assert '<link rel="stylesheet" href="style.css">' in html
assert '<script type="module" src="ui.mjs"></script>' in html
html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+css+'</style>')
html=html.replace('<script type="module" src="ui.mjs"></script>','<script>'+engine+'\n'+ui+'</script>')
assert 'src="ui.mjs"' not in html and 'href="style.css"' not in html
out=root/'PLAY_OFFLINE.html'
out.write_text(html,encoding='utf-8')
print(f'Built {out.name}: {out.stat().st_size} bytes')
