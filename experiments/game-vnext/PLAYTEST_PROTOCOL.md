# R2 Human Playtest Protocol — AI OFF (five first-time players)

**Status:** approved as a test template within draft PR #1028; no actual human playtests reported.  
**Source:** `descent/PLAY_OFFLINE.html` (standalone offline file), game-vNext charter #1020 R2.  
**Purpose:** Determine whether a first-time player understands and enjoys one 7×5 tactical Descent without generative AI.

## Trial conditions
- Explain once: "Choose a card. Move to the specimen. Extract before your threat reaches the limit. You may restart." Offer no route solution.
- Use a fresh browser profile or choose "New run" first. No real identity or sensitive personal questions.
- Test at least 5 voluntary adults from outside implementation team (one optional accessibility test with screen reader/keyboard and one with muted audio or hearing alternative).
- All gameplay is fictional and local. Research/usage telemetry is OFF. Ask permission before taking any screen recording. Use manual anonymous notes only.
- Let a player stop whenever they wish. The game is not a psychological or aptitude test.

## Per-player questions (ask only after playing)
1. "What was your objective?" (free text; did they identify *specimen + extraction*?)
2. "What did Quiet Footfall and Prism Ward trade off?" (can they identify a meaningful choice?)
3. "Did a failure feel understandable? What would you change?" (capture surprising softlock/confusion)
4. "Did you understand the Resonant Kin signal without sound?" (caption/icon comprehension)
5. "Would you play another short mission?" (yes/no and why; desire to replay)
6. Optional 1–5 ratings: first-move clarity, agency, challenge fairness, visual readability, desire to continue.

Record: player alias, deck, upper/lower/both route, completed/failure, actions used, time to first valid move, whether guidance needed, blockers and volunteered suggestions. Do **not** infer hidden personality from route or card choice.

## Release criteria for *next staging only* (not production)
- All tested runs terminate or recover; **zero unresolvable softlocks**.
- At least 4/5 explain specimen+extraction without hints; at least 4/5 understand a Deck tradeoff.
- At least 4/5 can explain why a failure happened.
- No critical keyboard or muted-audio comprehension failures.
- Record confusion and dissent, not just favorable responses. Adjust only after player feedback and regression tests.

Any critical blocker fails the gate. Report measured values, including failures. This document is not evidence those thresholds were achieved.
