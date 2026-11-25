# HAIOS-MM-ACAT-003 digest scorer (E0). Usage: python3 -I score_digest.py <dir with raw/DAY.txt and judg/DAY.json>
# Words: whitespace split after dropping quoted (>) and "On ... wrote:" lines and message headers.
# Ask position: word offset of each rubric locator; buried = offset > 200.
import json, glob, re, sys, os
base = sys.argv[1]
HDR = re.compile(r'^=== (MESSAGE|FROM THREAD)')
def clean(text):
    out=[]
    for ln in text.splitlines():
        s=ln.strip()
        if s.startswith('>'): continue
        if re.match(r'^On .{5,80}wrote:\s*$', s): continue
        out.append(ln)
    return out
rows=[]
for jf in sorted(glob.glob(os.path.join(base,'judg','*.json'))):
    d=json.load(open(jf)); day=d['date']
    raw=open(os.path.join(base,'raw',day+'.txt')).read()
    lines=clean(raw)
    body=[l for l in lines if not HDR.match(l.strip())]
    text='\n'.join(body)
    words=text.split()
    total=len(words)
    nlines=sum(1 for l in body if l.strip())
    # word offsets of asks
    norm=' '.join(words)
    offs=[]; missing=0
    for a in d['asks']:
        loc=' '.join(a['locator'].split())
        i=norm.find(loc)
        if i<0: missing+=1; continue
        offs.append(len(norm[:i].split()))
    first=min(offs) if offs else total
    buried=sum(1 for o in offs if o>200)
    msgs=raw.count('=== MESSAGE')
    rows.append(dict(day=day,msgs=msgs,words=total,lines=nlines,first_ask_word=first,asks=len(d['asks']),
        linked=sum(a['has_direct_link'] for a in d['asks']),buried=buried,loc_missing=missing,
        tagged=d['claim_tags']['tagged_items'],untagged=d['claim_tags']['untagged_factual_items'],
        id_err=len(d['id_errors']),counts=len(d['status_counts']),counts_timed=sum(s['has_read_time'] for s in d['status_counts']),
        carried=len(d['carried_items']),carried_unchecked=sum(1 for c in d['carried_items'] if c['rechecked_today']!='yes'),
        packets=sum(1 for m in d['messages'] if m['is_packet']),
        packets_full=sum(1 for m in d['messages'] if m['is_packet'] and all(m['header_fields'].values())),
        legs=sorted(set(m['leg'] for m in d['messages']))))
json.dump(rows,open(os.path.join(base,'baseline_metrics.json'),'w'),indent=1)
for r in rows: print(r)
