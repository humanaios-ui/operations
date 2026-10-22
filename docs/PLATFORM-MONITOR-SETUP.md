# Platform Monitor Setup: Real API Integration

**Status:** Testing guide v0.1  
**Date:** 2026-09-27

---

## Quick Start: Get Real Signals Flowing

### Prerequisites

```bash
# Clone the repository (if not done)
git clone https://github.com/humanaios-ui/operations.git
cd operations

# Install dependencies
pip install -r requirements.txt
# Required: python-twitter, praw, requests, python-dotenv

# Copy environment template
cp .env.example .env
```

### 1. Twitter/X API Setup

**Get credentials from:** https://developer.twitter.com/en/portal/dashboard

```bash
# In .env:
TWITTER_BEARER_TOKEN=AAAA...
TWITTER_API_KEY=abc123...
TWITTER_API_SECRET=def456...
TWITTER_ACCESS_TOKEN=ghi789...
TWITTER_ACCESS_TOKEN_SECRET=jkl012...
```

**Test endpoint:**
```bash
python3 -c "
import os
from twitter import Api
api = Api(
    consumer_key=os.getenv('TWITTER_API_KEY'),
    consumer_secret=os.getenv('TWITTER_API_SECRET'),
    access_token_key=os.getenv('TWITTER_ACCESS_TOKEN'),
    access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
    sleep_on_rate_limit=True
)
print('✓ Twitter API connected')
"
```

### 2. Reddit API Setup

**Get credentials from:** https://www.reddit.com/prefs/apps

```bash
# In .env:
REDDIT_CLIENT_ID=abcdef123456...
REDDIT_CLIENT_SECRET=ghijkl789012...
REDDIT_USER_AGENT=HumanAIOS-TopicMonitor/1.0
```

**Test endpoint:**
```bash
python3 -c "
import os
import praw
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)
print(f'✓ Reddit API connected as {reddit.user.me()}')
"
```

### 3. HackerNews API Setup

**Public API — no credentials needed**

```bash
# Test endpoint:
curl https://hacker-news.firebaseio.com/v0/topstories.json | head -c 200
```

### 4. LessWrong API Setup

**Get API key from:** https://www.lesswrong.com/account

```bash
# In .env:
LESSWRONG_API_URL=https://www.lesswrong.com/api/graphql
LESSWRONG_API_KEY=your_key_here
```

**Test endpoint:**
```bash
curl -X POST https://www.lesswrong.com/api/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${LESSWRONG_API_KEY}" \
  -d '{"query": "{ posts(limit: 1) { nodes { title } } }"}'
```

### 5. GitHub Discussions Setup

```bash
# In .env:
GITHUB_TOKEN=ghp_...
GITHUB_ORG=humanaios-ui
GITHUB_REPO=lasting-light-ai
```

**Test endpoint:**
```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/humanaios-ui/lasting-light-ai/discussions
```

---

## Run Your First Signal Collection

### Option A: Mock Data (Fastest)

```bash
cd /home/user/operations
python3 scripts/platform-monitor.py --mode mock
```

**Output:** Populates `data/public-discourse-signals.jsonl` with test data

**Example output:**
```
2026-09-27 21:20:57,044 - __main__ - INFO - Starting Public Discourse Signal Monitor
2026-09-27 21:20:57,044 - __main__ - INFO - Monitoring Twitter for ai-jailbreaks
2026-09-27 21:20:57,044 - __main__ - INFO - Monitoring Reddit in ['MachineLearning', 'LanguageModels']
...
2026-09-27 21:20:57,044 - __main__ - INFO - Appended 18 signals to data/public-discourse-signals.jsonl
```

### Option B: Real APIs (Production)

```bash
python3 scripts/platform-monitor.py --mode real
```

**What happens:**
1. Loads API credentials from `.env`
2. Queries each platform for topic keywords
3. Aggregates signals with confidence scores
4. Appends to `data/public-discourse-signals.jsonl`

**Expected runtime:** 3-5 minutes (Twitter is slowest)

### Option C: Single Platform Test

```bash
# Test Twitter only
python3 scripts/platform-monitor.py --platform twitter --topic ai-jailbreaks

# Test Reddit only
python3 scripts/platform-monitor.py --platform reddit --topic llm-hallucinations
```

---

## Verify Signal Quality

### Check JSONL is Valid

```bash
python3 -c "
import json
with open('data/public-discourse-signals.jsonl', 'r') as f:
    lines = [l for l in f if l.strip() and not l.startswith('#')]
    for i, line in enumerate(lines[-5:]):  # Last 5 signals
        signal = json.loads(line)
        print(f'Signal {i}: {signal[\"topic_id\"]} on {signal[\"platform\"]}')
        print(f'  Volume: {signal[\"discussion_volume\"]}, Strength: {signal[\"signal_strength\"]}')
"
```

### Inspect Latest Signal

```bash
tail -1 data/public-discourse-signals.jsonl | python3 -m json.tool
```

**Example output:**
```json
{
  "timestamp": "2026-09-27T21:25:00Z",
  "topic_id": "ai-jailbreaks",
  "platform": "twitter",
  "discussion_volume": 342,
  "trending_trajectory": "up_strong",
  "key_concerns": ["prompt injection", "authorization bypass"],
  "signal_strength": 0.85,
  "source_count": 47,
  "sentiment": "concerned",
  "urls": [
    "https://twitter.com/search?q=...",
    "..."
  ]
}
```

---

## Run the Full Pipeline

### Test End-to-End

```bash
# 1. Collect signals
python3 scripts/platform-monitor.py

# 2. Map to mitigation
python3 scripts/map-to-mitigation.py

# 3. Detect gaps
python3 scripts/gap-detector.py

# 4. Check outputs
ls -lh docs/TOPIC_RESPONSE_MATRIX.md data/public-discourse-signals.jsonl
```

### Check Mapping Quality

```bash
# Show current topic responses
head -50 docs/TOPIC_RESPONSE_MATRIX.md

# Show gap analysis
python3 scripts/gap-detector.py | jq '.research_gaps[0]'
```

---

## Deploy via GitHub Actions

### Test Workflow

```bash
# Push to a test branch
git checkout -b feature/signal-test
git add data/ docs/ .env.example
git commit -m "test: configure platform monitors"
git push -u origin feature/signal-test

# Check: Does CI workflow run?
# https://github.com/humanaios-ui/operations/actions
```

### Schedule Production Run

**Currently configured in `.github/workflows/daily-topic-digest.yml`:**
```yaml
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
```

To change schedule:
```bash
# Edit workflow
vim .github/workflows/daily-topic-digest.yml

# Change cron schedule (see crontab.guru)
# Commit and push
git add .github/workflows/daily-topic-digest.yml
git commit -m "chore: adjust monitor schedule to 6 AM UTC"
git push origin main
```

---

## Troubleshooting

### "No signals appended"

**Cause 1: API credentials invalid**
```bash
python3 scripts/platform-monitor.py --debug
# Look for: "Authentication failed" or "401 Unauthorized"
```

**Fix:** Regenerate credentials in provider dashboard

**Cause 2: No matching posts**
```bash
# Try broader keywords
python3 scripts/platform-monitor.py --keywords "hallucination,AI"
```

**Fix:** Adjust keywords in `platform-monitor.py` TOPICS dict

### "JSON parse error in JSONL"

**Cause:** Incomplete line written

**Fix:**
```bash
# Remove last incomplete line
head -n -1 data/public-discourse-signals.jsonl > /tmp/clean.jsonl
mv /tmp/clean.jsonl data/public-discourse-signals.jsonl
```

### Rate limits hit

**Cause:** Platform API throttling

**Expected:** Twitter hits limit after ~30 requests

**Fix:** Wait 15 minutes or use mock mode

```bash
python3 scripts/platform-monitor.py --mode mock
```

---

## Success Criteria

| Check | Expected | How to Verify |
|---|---|---|
| **Signals collected** | 18+ signals per run | `wc -l data/public-discourse-signals.jsonl` |
| **Topics mapped** | 3 topics documented | `grep "## " docs/TOPIC_RESPONSE_MATRIX.md \| wc -l` |
| **Gaps detected** | 4+ gaps identified | `python3 scripts/gap-detector.py \| jq '.summary'` |
| **JSONL valid** | All lines parse as JSON | `python3 -c "import json; [json.loads(l) for l in open('data/public-discourse-signals.jsonl')]"` |
| **No secrets in logs** | No API keys exposed | `grep -i "bearer\|secret\|token" *.log` (should be empty) |
| **Workflow runs** | GitHub Actions succeeds | Check `.github/workflows/daily-topic-digest.yml` status |

---

## Next Steps After Testing

1. **Commit base infrastructure**
   ```bash
   git add data/public-discourse-signals.jsonl docs/TOPIC_RESPONSE_MATRIX.md .env.example
   git commit -m "feat: baseline signals from two-week test run"
   git push origin main
   ```

2. **Add registry↔signal linking**
   - Create `data/finding-to-signal-map.json`
   - Link each REGISTERED.md finding to triggering signal

3. **Add research velocity dashboard**
   - Create `public/research-priorities.html`
   - Wire to priority queue from gap-detector

4. **Deploy Voice + Navigator integration**
   - Implement EpistemicDJ class
   - Wire to caveat-to-navigator-map.json
   - Test on staging before production

---

## Production Safeguards

### Rate Limiting

All API calls include exponential backoff:
```python
max_retries = 3
delay = [1, 2, 4]  # seconds

for attempt in range(max_retries):
    try:
        response = api.query(...)
        return response
    except RateLimitError:
        if attempt < max_retries - 1:
            sleep(delay[attempt])
        else:
            raise
```

### Privacy & Ethics

- No personal data collection (only public posts)
- No sentiment analysis of individual users
- Topics are aggregated, not attributed
- Clear data retention policy (90 days default)

### Data Validation

Every signal is validated:
```python
assert signal['discussion_volume'] > 0
assert 0 <= signal['signal_strength'] <= 1.0
assert signal['trending_trajectory'] in ['up', 'down', 'stable', 'up_strong']
assert len(signal['key_concerns']) > 0
```

---

## Documentation References

- **Workflow:** `.github/workflows/daily-topic-digest.yml`
- **Scripts:** `scripts/platform-monitor.py`, `scripts/map-to-mitigation.py`, `scripts/gap-detector.py`
- **Data schema:** `data/public-discourse-signals.jsonl` (see comments at top)
- **Topic mapping:** `docs/TOPIC_RESPONSE_MATRIX.md`
- **Integration:** `docs/SYSTEM-INTEGRATION-MAP.md`
