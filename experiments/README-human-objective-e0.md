# HumanAIOS E0 — first human test

**State:** experimental / not admitted / not deployed. **Authority:** NONE. **Execution:** DISABLED.

This is the smallest *offline* proof of the intent → evidence → understandable recommendation loop. It is not yet an email-driven service, a real Resource Miner, or an always-on agent. It intentionally does **not** import #756 or claim that URA admission has passed.

## Run
From repository root:

```bash
python3 experiments/human_objective_e0.py --objective "Find training certification"
python3 -m unittest discover -s tests -p 'test_human_objective_e0.py' -v
```

Expected: a clearly labeled **synthetic** candidate, evidence limitations, what the system can/cannot do, and a SHA256 reproducibility identifier. Try `--objective "Find sustainable farming irrigation"`: it should abstain.

## Human-first protocol

1. Read the implementation email and reply with **one objective**, not passwords, documents, private medical/financial information, or personal account details.
2. This **does not** create an automated inbox processor. A human/authorized reviewer must read the email and intentionally enter a suitable non-sensitive objective into the CLI; no automatic acknowledgment or recommendation will be sent.
3. Compare the output with the original objective; record whether the explanation was understandable, whether boundaries were clear, and what evidence would be needed for a real-world recommendation.
4. Record a test receipt in issue #760 with objective redacted if sensitive. Do not post a private email or its contents to the public repository.

## Explicit boundaries

- Fixtures are invented examples; no eligibility, grant, certification or real program is verified.
- SHA256 identifies local inputs; it is **not** a cryptographic signature, independent witness, verified provenance or authorization.
- Keyword overlap is a *demonstration*, not semantic reasoning, contextual recommendation, or validated matching.
- Candidates containing unauthorized keys, unsupported provenance, or non-synthetic fixture declarations are rejected.
- The CLI does no networking, sending, access to Gmail, account actions, or real transactions.
- No PR merge/admission is inferred from green tests. Existing coordinator and URA gates remain independent.

## Next gate (not part of E0)
After a human-reviewed test, assess if the interface merits a separately admitted email intake adapter with consent, idempotent thread correlation, data minimization, sender authentication, retention policy, and reply-only-after-review semantics.
