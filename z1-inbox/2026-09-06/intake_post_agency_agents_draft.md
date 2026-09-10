# Free behavior audit for anyone running agency-agents in production — 10 slots, criteria published before we look

**Status: DRAFT for Z2 ratification. Venue: github.com/msitarzewski/agency-agents → Discussions. Not posted.**

---

If you've dropped a set of these agents into Claude Code, Cursor or Codex and shipped something real with them, I'll audit how they *behave* — free, for the first ten people who sign a scope.

**What I check (and nothing else):**
- Does untrusted text in your inputs change the agent's instructions? (prompt-injection paths)
- Does the same prompt answer differently after a model update? (drift, checked with a pinned prompt set)
- Does the answer flip when the question is reworded? (flip rate)
- Do the agents contradict each other on the same fact? (contradiction score)
- Are cited sources real? (citation verification)
- Is there a spend cap, a halt, an audit log, and a written scope — or can the agent run until something breaks?

**What I don't check:** secrets, SQL injection, auth, infrastructure. I have no tooling for it and won't pretend to.

**How it's different from a scan:**
1. The pass/fail criteria are written and hashed *before* I touch your system. You get the hash first.
2. Every finding comes with the sentence that would prove it wrong.
3. Findings go into a public append-only log. You get a Merkle receipt you can verify without trusting me.

**What you sign first:** that you own the system, what's in scope, what's out, a time window, and your provider stack. Nothing runs until that scope is signed and hashed. If you're on Anthropic's API, injection probes wait for their authorization — that's their rule, not mine.

**Why free:** I'm measuring base rates — how often each of these actually shows up in shipped agent stacks, and how long a real audit takes. Ten engagements, results published in aggregate with no client names. You get the audit; I get the data. If it's worth paying for later, that's a separate conversation.

Reply here or open a thread. First ten signed scopes get a slot.

---

*Z1 notes for Z2 (not part of the post):*
- Every claim above has a receipt path except "free" — that's a Z2 commitment, not a tool.
- Post contains no numbers we haven't operated. No find rates, no prices, no "we found X."
- Etiquette: Discussions, not Issues. One post; no reposting if ignored.
- Before posting: IC-SCOPE-05 gate must exist in code, not just as a form. Otherwise the first reply outruns the gate.
- Ten free slots = ~20–60 Z2 hours by the report's unknown-range estimate. That's the real cost.
