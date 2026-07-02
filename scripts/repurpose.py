#!/usr/bin/env python3
"""
repurpose.py — one Witness Stand markdown post -> four channel drafts.

Turns a single post (e.g. deliverables/witness-stand-post-1.md) into:
  - substack.md   : clean article body
  - linkedin.md   : LinkedIn-newsletter version
  - x-thread.txt  : a numbered X/Twitter thread
  - notes.txt     : 3 standalone Substack Notes

DESIGN INTENT (read this): this script FORMATS ONLY. It never logs in,
posts, schedules, or contacts anyone. That's deliberate — it keeps the
whole flow ToS-clean and Tradition-11-clean: the machine prepares, a
human reviews and publishes via the native tools (Substack scheduler;
a compliant official-API scheduler for LinkedIn/X). Stdlib only, no deps.

Usage:
    python3 scripts/repurpose.py deliverables/witness-stand-post-1.md
    # -> writes out/witness-stand-post-1/{substack.md,linkedin.md,x-thread.txt,notes.txt}
"""
import re
import sys
import pathlib

TWEET_LIMIT = 268  # leaves room for " (n/N)"


def strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def parse(md: str):
    body = strip_html_comments(md).strip()
    m = re.search(r"^#\s+(.+)$", body, flags=re.M)
    title = m.group(1).strip() if m else "Untitled"
    sm = re.search(r"^\*(.+?)\*\s*$", body, flags=re.M)
    subhead = sm.group(1).strip() if sm else ""
    links = re.findall(r"^-\s+.*?\((https?://[^)]+)\)", body, flags=re.M)
    return title, subhead, body, links


def clean_body(body: str) -> str:
    out = []
    seen_sub = False
    for ln in body.splitlines():
        if re.match(r"^#\s+", ln):            # title line
            continue
        if not seen_sub and re.match(r"^\*.+\*\s*$", ln):  # subhead italics
            seen_sub = True
            continue
        if ln.strip() == "---":
            continue
        out.append(ln)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def to_x_thread(title, subhead, body, links) -> str:
    tweets = [f"{title}\n\n{subhead}".strip()]
    prose = re.sub(r"[*_#>`]", "", clean_body(body)).replace("\n", " ")
    sentences = re.split(r"(?<=[.!?])\s+", prose)
    buf = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(buf) + len(s) + 1 <= TWEET_LIMIT:
            buf = (buf + " " + s).strip()
        else:
            if buf:
                tweets.append(buf)
            buf = s[:TWEET_LIMIT]
    if buf:
        tweets.append(buf)
    if links:
        tweets.append("Paper, open data & more:\n" + "\n".join(dict.fromkeys(links[:3])))
    n = len(tweets)
    return "\n\n———\n\n".join(f"{t}\n\n({i + 1}/{n})" for i, t in enumerate(tweets))


def to_notes(body: str, subhead: str) -> str:
    paras = [p.strip() for p in re.split(r"\n{2,}", clean_body(body))]
    picks = [p for p in paras if 40 <= len(p) <= 260 and not p.startswith("-")][:3]
    if not picks and subhead:
        picks = [subhead]
    return "\n\n———\n\n".join(picks)


def main(path: str) -> None:
    src = pathlib.Path(path)
    md = src.read_text(encoding="utf-8")
    title, subhead, body, links = parse(md)
    body_clean = clean_body(body)
    out = pathlib.Path("out") / src.stem
    out.mkdir(parents=True, exist_ok=True)

    (out / "substack.md").write_text(
        f"# {title}\n\n*{subhead}*\n\n{body_clean}\n", encoding="utf-8")
    (out / "linkedin.md").write_text(
        f"**{title}**\n\n{subhead}\n\n{body_clean}\n\n"
        f"Read the research: {links[0] if links else 'https://humanaios.ai'}\n",
        encoding="utf-8")
    (out / "x-thread.txt").write_text(
        to_x_thread(title, subhead, body, links), encoding="utf-8")
    (out / "notes.txt").write_text(
        to_notes(body, subhead), encoding="utf-8")

    print(f"Wrote 4 channel drafts to {out}/")
    print("Review each before publishing — this script posted nothing.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python3 scripts/repurpose.py <post.md>")
        sys.exit(1)
    main(sys.argv[1])
