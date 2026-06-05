# main.py v2.3 patch — comment-posting repair + N=50 hold annotation

Session context: B/C isolation held in Z3 until N=50 resolved. Option A
(li_is_placeholder) is the active guard. SUPABASE_KEY confirmed = service_role
(bypasses RLS — writes will succeed).

## Fixes applied (all in the comment path; everything else unchanged)

1. METHOD NAME
- `metaculus_client.post_comment(...)`  →  `post_question_comment(...)`
- method did not exist; correct name confirmed against forecasting_tools 0.2.92
1. PARAMETER NAME
- `question_id=...`  →  `post_id=...`
- confirmed signature: post_question_comment(post_id, comment_text,
  is_private=True, included_forecast=True) -> None
1. RETURN VALUE
- method returns None, not a dict. `response.get("id")` raised AttributeError,
  swallowed by except → comment_id always None → p3_comment_posted always FALSE.
- New semantics: success = no exception raised. On success we synthesize a
  stable marker from id_of_post + timestamp so p3_comment_posted can be TRUE
  honestly (the API gives us no comment id to store).
1. ASYNC/SYNC MISMATCH
- post_question_comment is synchronous (requests.post under
  @retry_with_exponential_backoff). It was being awaited.
- Wrapped in asyncio.to_thread(…) so it runs without blocking the loop and
  without the await-on-sync error.
1. POST ID SOURCE
- Replaced regex _extract_metaculus_id(page_url) for the comment call with
  question.id_of_post (native pydantic field, int | None).
- The old regex `/questions/(\d+)/` does NOT match the diffusion-community
  test URL `/c/diffusion-community/38880/...` → that question would never get
  a comment. id_of_post is populated by the library regardless of URL shape.
- _extract_metaculus_id retained ONLY for the metaculus_question_id Supabase
  column (P1 write), with a fallback to id_of_post.
1. is_private
- Kept is_private=False (public comment — intended behavior). Library default
  is True; we override explicitly.
1. included_forecast
- Set explicitly to False. The ACAT record comment is metadata, not a forecast
  rationale; letting the API attach the forecast is not wanted here.

## NOT changed (out of scope for this build)

- LI=1.0 placeholder semantics — held, Option A guard active.
- BOT_RUN_ID format (S-bot-MMDDYY-auto) — flagged previously, not a blocker.
- Gate 3 real P3 prompt — separate deliverable.