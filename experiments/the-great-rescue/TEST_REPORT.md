# S0 acceptance report — local implementation

## Verified
- Node 22 local deterministic engine and API suite: **9/9 pass** (run after final source edit).
- Empty gap fails; connected four-platform layout delivers capsule; standard scoring returns **82/100** and 3/3 stable runs.
- Two isolated bearer clients create/join one room; action propagation, trading consent, out-of-authority mutation rejection, duplicate-action idempotency, two-run cap, winner and rematch exercised.
- Chromium inlined-document bridge to real host: two browser contexts (1280px desktop and 430px mobile), host/join/build/test/official/finish/results; no JavaScript page errors; mobile scroll width fits viewport.

## Not verified / blocked
- Chromium **direct** navigation to local server was blocked by sandbox policy; the inlined-document bridge tests UI code plus real host API, not network navigation.
- Real two-physical-device join over public HTTPS: **NOT TESTED**.
- External public URL and Handshake submission: **NOT DEPLOYED**.
- Independent new-player enjoyment and accessibility review: **NOT TESTED**.
- Production durability / scale / authentication: **NOT IMPLEMENTED**.
- Human merge/admission: **NOT APPROVED**.
