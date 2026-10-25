"""Build a one-file offline version from checked-in first-party sources."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent
html=(root/'index.html').read_text(encoding='utf-8')
css=(root/'style.css').read_text(encoding='utf-8')
engine=(root/'engine.mjs').read_text(encoding='utf-8')
ui=(root/'ui.mjs').read_text(encoding='utf-8')
ui=re.sub(r"^import\s+\{[^}]+\}\s+from\s+'\./engine\.mjs';\s*",'',ui,count=1,flags=re.MULTILINE)
engine=re.sub(r'\bexport (const|function)\b',r'\1',engine)
marker='<link rel="stylesheet" href="style.css"><script type="module" src="ui.mjs"></script>'
assert marker in html, 'index template marker changed'
html=html.replace(marker,'<style>'+css+'</style>')
html=html.replace('</body>','<script>'+engine+'\n'+ui+'</script></body>')
out=root/'PLAY_OFFLINE.html'
out.write_text(html,encoding='utf-8')
print(f'Built {out.name}: {out.stat().st_size} bytes')
