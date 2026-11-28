#!/usr/bin/env bash
# BOT-REVIEW-CALIBRATION-E0: read-only GitHub REST fetch. Writes no comments, no labels, nothing remote.
# Usage: fetch_rest.sh OUT_DIR   (needs an authenticated gh CLI)
set -euo pipefail
o="$1"; R=repos/humanaios-ui/operations
mkdir -p "$o"

# Every PR: number, state, merged, author, base.
gh api "$R/pulls?state=all&per_page=100" --paginate \
  --jq '.[] | {pr:.number,state:.state,merged:(.merged_at!=null),created:.created_at,author:.user.login,base:.base.ref,draft:.draft}' \
  > "$o/prs.jsonl"

# CodeRabbit inline findings: severity word from the comment header (first 400 chars) only,
# no comment text kept. Both header styles match: emoji + word, and icon image + bold word.
# No match is recorded as "unparsed", never as clean.
gh api "$R/pulls/comments?per_page=100" --paginate \
  --jq '.[] | select(.user.login|test("coderabbit";"i")) | {pr:(.pull_request_url|split("/")|last|tonumber),at:.created_at,sev:(((.body//"")[0:400]|capture("(?<s>Critical|Major|Minor|Trivial|Nitpick|Potential issue|Refactor suggestion)")|.s)//"unparsed"),in_reply:(.in_reply_to_id!=null)}' \
  > "$o/cr_inline.jsonl"

# Bot reviews per PR: verdict line and quota failure only, no review text kept.
JQ='.[] | select(.user.type=="Bot") | {pr:(.pull_request_url|split("/")|last|tonumber),bot:.user.login,state:.state,at:.submitted_at,quota_fail:((.body//"")|test("insufficient remaining quota|unable to review";"i")),verdict:(((.body//"")|capture("(?<v>Changes recommended|Needs a closer look|Approval recommended)")|.v)//null)}'
# A failed request is recorded in fetch_errors.jsonl so the PR is not read as "no bot review".
# 8 requests at a time; each PR writes its own part file, joined in PR order at the end.
export R JQ o
mkdir -p "$o/parts"
jq -r .pr "$o/prs.jsonl" | xargs -P 8 -I{} bash -c '
  if out=$(gh api "$R/pulls/{}/reviews?per_page=100" --paginate --jq "$JQ"); then
    printf "%s" "$out" > "$o/parts/{}.ok"
  else
    : > "$o/parts/{}.err"
  fi'
: > "$o/reviews.jsonl"; : > "$o/fetch_errors.jsonl"
for n in $(jq -r .pr "$o/prs.jsonl"); do
  if [ -f "$o/parts/$n.ok" ]; then
    [ -s "$o/parts/$n.ok" ] && { cat "$o/parts/$n.ok"; echo; } >> "$o/reviews.jsonl"
  else
    echo "{\"pr\":$n,\"what\":\"reviews\"}" >> "$o/fetch_errors.jsonl"
  fi
done
rm -rf "$o/parts"
wc -l "$o"/*.jsonl
