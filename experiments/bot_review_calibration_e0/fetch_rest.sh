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

# CodeRabbit inline findings: severity tag only, no comment text kept.
gh api "$R/pulls/comments?per_page=100" --paginate \
  --jq '.[] | select(.user.login|test("coderabbit";"i")) | {pr:(.pull_request_url|split("/")|last|tonumber),at:.created_at,sev:((.body|capture("(?<s>🔴 Critical|🟠 Major|🟡 Minor|🔵 Trivial|🧹 Nitpick|⚠️ Potential issue|🛠️ Refactor suggestion)")|.s)//"none"),in_reply:(.in_reply_to_id!=null)}' \
  > "$o/cr_inline.jsonl"

# Bot reviews per PR: verdict line and quota failure only, no review text kept.
JQ='.[] | select(.user.type=="Bot") | {pr:(.pull_request_url|split("/")|last|tonumber),bot:.user.login,state:.state,at:.submitted_at,quota_fail:((.body//"")|test("insufficient remaining quota|unable to review";"i")),verdict:(((.body//"")|capture("(?<v>Changes recommended|Needs a closer look|Approval recommended)")|.v)//null)}'
: > "$o/reviews.jsonl"
for n in $(jq -r .pr "$o/prs.jsonl"); do
  gh api "$R/pulls/$n/reviews?per_page=100" --jq "$JQ" >> "$o/reviews.jsonl" || true
done
wc -l "$o"/*.jsonl
